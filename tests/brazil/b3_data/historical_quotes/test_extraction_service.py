from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes import (
    CotahistParserB3,
    ExtractionServiceB3,
    ProcessingModeEnumB3,
    extraction_service,
)
from globaldatafinance.core import ResourceState

temp_parquet_merge = extraction_service.temp_parquet_merge
parse_lines_batch = extraction_service.batch_parser.parse_lines_batch

pytestmark = pytest.mark.unit


class FakeResourceMonitor:
    def __init__(
        self,
        *,
        safe_worker_cap: int = 8,
        safe_batch_size: int | None = None,
        states: list[ResourceState] | None = None,
        process_memory_mb: float = 100.0,
    ) -> None:
        self.safe_worker_cap = safe_worker_cap
        self.safe_batch_size = safe_batch_size
        self.states = list(states or [ResourceState.HEALTHY])
        self.process_memory_mb = process_memory_mb
        self.worker_calls: list[int | None] = []
        self.batch_calls: list[int] = []
        self.check_calls = 0
        self._state_index = 0

    def get_safe_worker_count(self, desired: int | None) -> int:
        self.worker_calls.append(desired)
        if desired is None:
            return self.safe_worker_cap
        return min(desired, self.safe_worker_cap)

    def check_resources(self) -> ResourceState:
        if self._state_index < len(self.states):
            state = self.states[self._state_index]
            self._state_index += 1
        else:
            state = self.states[-1]
        self.check_calls += 1
        return state

    def get_safe_batch_size(self, desired_batch_size: int) -> int:
        self.batch_calls.append(desired_batch_size)
        if self.safe_batch_size is None:
            return desired_batch_size
        return self.safe_batch_size

    def get_process_memory_mb(self) -> float:
        return self.process_memory_mb


class DummyLoop:
    def __init__(self, result):
        self.result = result
        self.calls: list[tuple] = []

    async def run_in_executor(self, executor, func, *args):
        self.calls.append((executor, func, args))
        if self.result is None:
            return func(*args)
        return self.result


class FakeZipReader:
    def __init__(self, files: dict[str, list[str]] | None = None) -> None:
        self.files = files or {}
        self.calls: list[str] = []

    async def read_lines_from_zip(self, zip_path: str):
        self.calls.append(zip_path)
        for line in self.files.get(zip_path, []):
            yield line


class FakeParser:
    def __init__(self, responses: dict[str, dict] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[str, frozenset[str]]] = []

    def parse_line(self, line: str, target_codes: set[str]):
        self.calls.append((line, frozenset(target_codes)))
        if line in self.responses:
            return self.responses[line]
        if 'keep' in line:
            return {'value': line}
        return None


class FakeWriter:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def write_to_parquet(self, data, output_path: Path, mode: str):
        self.calls.append(
            {
                'records': list(data),
                'output_path': output_path,
                'mode': mode,
            }
        )


class DummyPool:
    def __init__(self, max_workers: int | None = None) -> None:
        self.max_workers = max_workers
        self.shutdown_called = False

    def shutdown(
        self, wait: bool = False, cancel_futures: bool = False
    ) -> None:
        _ = wait, cancel_futures
        self.shutdown_called = True


def build_cotahist_line(tpmerc: str) -> str:
    line = [' '] * 245
    line[0:2] = list('01')
    line[2:10] = list('20240101')
    line[10:12] = list('02')
    ticker = 'TESTE12345678'[:12]
    line[12:24] = list(ticker)
    line[24:27] = list(tpmerc)
    return ''.join(line)


async def resources_available(timeout_seconds: int = 30) -> bool:
    """Return a deterministic successful resource wait for service tests."""
    _ = timeout_seconds
    return True


@pytest.fixture(autouse=True)
def suppress_execution_time_logging(monkeypatch):
    @contextmanager
    def noop(*_args, **_kwargs):
        yield

    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.service.log_execution_time',
        noop,
    )


@pytest.fixture
def process_pool_spy(monkeypatch):
    created: list[DummyPool] = []

    def factory(max_workers: int | None = None):
        pool = DummyPool(max_workers)
        created.append(pool)
        return pool

    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.zip_processor.ThreadPoolExecutor',
        factory,
    )
    return created


def test_extraction_service_initialization_fast_mode(
    monkeypatch, process_pool_spy
):
    monitor = FakeResourceMonitor(safe_worker_cap=6)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    assert service.resource_policy.use_parallel_parsing is True
    assert service.resource_policy.max_concurrent_files == 6
    assert service.resource_policy.max_workers == 4
    assert process_pool_spy[0].max_workers == 4
    assert monitor.worker_calls == [15, 4]


def test_extraction_service_initialization_slow_mode(
    monkeypatch, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.SLOW,
    )

    assert service.resource_policy.use_parallel_parsing is False
    assert service.resource_policy.max_concurrent_files == 3
    assert service.resource_policy.max_workers == 1
    assert service.zip_processor.executor_pool is None
    assert monitor.worker_calls == [3]


@pytest.mark.asyncio
async def test_extraction_service_wait_for_resources(
    monkeypatch, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(
        states=[ResourceState.CRITICAL, ResourceState.HEALTHY]
    )
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    async def no_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.asyncio.sleep',
        no_sleep,
    )

    result = await service.resource_policy.wait_for_resources(
        timeout_seconds=7
    )

    assert result is True
    assert monitor.check_calls == 2


@pytest.mark.asyncio
async def test_extraction_service_write_buffer_to_disk(
    monkeypatch, process_pool_spy, tmp_path
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    writer = FakeWriter()
    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=writer,
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    output_path = tmp_path / 'data.parquet'

    await service.buffered_writer.write_buffer_to_disk(
        [{'row': 1}], output_path, 'overwrite'
    )
    await service.buffered_writer.write_buffer_to_disk(
        [{'row': 2}], output_path, 'append'
    )

    assert writer.calls[0]['mode'] == 'overwrite'
    assert writer.calls[1]['mode'] == 'append'
    assert writer.calls[0]['records'] == [{'row': 1}]
    assert writer.calls[1]['records'] == [{'row': 2}]


@pytest.mark.asyncio
async def test_process_and_write_zip_slow_mode(monkeypatch, tmp_path):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    parser = FakeParser()
    zip_reader = FakeZipReader({'sample.zip': ['keep-1', 'skip', 'keep-2']})

    service = ExtractionServiceB3(
        zip_reader=zip_reader,
        parser=parser,
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.SLOW,
    )

    output_path = tmp_path / 'data.parquet'
    result = await service.zip_processor.process(
        zip_file='sample.zip',
        target_tpmerc_codes={'010'},
        output_path=output_path,
    )

    assert result['records'] == 2
    assert zip_reader.calls == ['sample.zip']
    assert parser.calls == [
        ('keep-1', frozenset({'010'})),
        ('skip', frozenset({'010'})),
        ('keep-2', frozenset({'010'})),
    ]


@pytest.mark.asyncio
async def test_processor_temp_paths_include_input_extension(
    monkeypatch, tmp_path
):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    zip_path = 'COTAHIST_A2023.ZIP'
    txt_path = 'COTAHIST_A2023.TXT'
    service = ExtractionServiceB3(
        zip_reader=FakeZipReader({zip_path: ['keep'], txt_path: ['keep']}),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.SLOW,
    )

    zip_result = await service.zip_processor.process(
        zip_file=zip_path,
        target_tpmerc_codes={'010'},
        output_path=tmp_path / 'data.parquet',
    )
    txt_result = await service.zip_processor.process(
        zip_file=txt_path,
        target_tpmerc_codes={'010'},
        output_path=tmp_path / 'data.parquet',
    )

    assert zip_result['temp_file'] != txt_result['temp_file']
    assert zip_result['temp_file'].endswith(
        'data_COTAHIST_A2023.ZIP_temp.parquet'
    )
    assert txt_result['temp_file'].endswith(
        'data_COTAHIST_A2023.TXT_temp.parquet'
    )


@pytest.mark.asyncio
async def test_slow_mode_throttles_flush_checks(monkeypatch, tmp_path):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    lines = [f'keep-{index}' for index in range(7)]
    writer = FakeWriter()
    service = ExtractionServiceB3(
        zip_reader=FakeZipReader({'sample.zip': lines}),
        parser=FakeParser(),
        data_writer=writer,
        processing_mode=ProcessingModeEnumB3.SLOW,
    )
    service.zip_processor.SEQUENTIAL_FLUSH_CHECK_INTERVAL = 3
    service.zip_processor.SEQUENTIAL_RESOURCE_CHECK_INTERVAL = 100

    flush_buffer_sizes: list[int] = []

    async def fake_flush_if_needed(
        buffer,
        temp_output,
        *,
        is_first_write: bool,
    ):
        _ = temp_output
        flush_buffer_sizes.append(len(buffer))
        return 0, is_first_write

    service.buffered_writer.flush_if_needed = fake_flush_if_needed  # type: ignore

    result = await service.zip_processor.process(
        zip_file='sample.zip',
        target_tpmerc_codes={'010'},
        output_path=tmp_path / 'data.parquet',
    )

    assert flush_buffer_sizes == [3, 6]
    assert result['records'] == 7
    assert writer.calls[0]['records'] == [{'value': line} for line in lines]


@pytest.mark.asyncio
async def test_process_and_write_zip_fast_mode(
    monkeypatch, process_pool_spy, tmp_path
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    zip_reader = FakeZipReader({'fast.zip': ['keep-1', 'drop', 'keep-2']})

    service = ExtractionServiceB3(
        zip_reader=zip_reader,
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )
    service.resource_policy.parse_batch_size = 2

    batch_calls: list[list[str]] = []

    async def fake_batch(lines, target_codes):
        _ = target_codes
        batch_calls.append(list(lines))
        return [{'value': line} for line in lines if 'keep' in line]

    service.zip_processor._parse_lines_batch_parallel = fake_batch  # type: ignore

    output_path = tmp_path / 'data.parquet'
    result = await service.zip_processor.process(
        zip_file='fast.zip',
        target_tpmerc_codes={'010'},
        output_path=output_path,
    )

    assert result['records'] == 2
    assert batch_calls[0] == ['keep-1', 'drop']
    assert batch_calls[1] == ['keep-2']


@pytest.mark.asyncio
async def test_process_and_write_zip_propagates_errors(
    monkeypatch, process_pool_spy, tmp_path
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader({'error.zip': ['line']}),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    async def failing_batch(_lines, _codes):
        raise RuntimeError('boom')

    service.zip_processor._parse_lines_batch_parallel = failing_batch  # type: ignore

    output_path = tmp_path / 'data.parquet'
    with pytest.raises(RuntimeError):
        await service.zip_processor.process(
            zip_file='error.zip',
            target_tpmerc_codes={'010'},
            output_path=output_path,
        )


@pytest.mark.asyncio
async def test_parse_lines_batch_parallel_filters_none(
    monkeypatch, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    dummy_loop = DummyLoop(result=[None, {'value': 'ok'}])
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.zip_processor.asyncio.get_running_loop',
        lambda: dummy_loop,
    )

    records = await service.zip_processor._parse_lines_batch_parallel(
        ['line'], {'010'}
    )

    assert records == [{'value': 'ok'}]
    assert dummy_loop.calls


def test_parse_lines_batch_filters_by_target():
    lines = [build_cotahist_line('010'), build_cotahist_line('020')]

    records = parse_lines_batch(lines, {'010'})

    assert len(records) == 1
    assert records[0]['tipo_mercado'] == '010'


def test_parse_lines_batch_matches_sequential_parser():
    lines = [
        '00COTAHIST' + ' ' * 235,  # header -> dropped
        build_cotahist_line('010'),  # kept
        build_cotahist_line('020'),  # filtered out by target codes
        '01' + '20230615' + '02' + 'PETR4       ' + '010' + ' ' * 217,  # kept
        '0120230615',  # too short -> dropped
        '99TRAILER' + ' ' * 235,  # trailer -> dropped
    ]
    target_codes = {'010'}

    batch_records = parse_lines_batch(lines, target_codes)

    sequential_parser = CotahistParserB3()
    sequential_records = [
        record
        for record in (
            sequential_parser.parse_line(line, target_codes) for line in lines
        )
        if record is not None
    ]

    assert batch_records == sequential_records


@pytest.mark.asyncio
async def test_merge_single_temp_file_replaces_existing_output(
    monkeypatch, tmp_path
):
    temp_file = tmp_path / 'temp.parquet'
    final_output = tmp_path / 'final.parquet'
    temp_file.write_text('new content')
    final_output.write_text('old content')

    monkeypatch.setattr(
        temp_parquet_merge,
        'count_parquet_rows',
        lambda _path: 42,
    )

    async def fail_if_called():
        raise AssertionError('single-file merge should not check resources')

    rows = await temp_parquet_merge.merge_temp_files_streaming(
        [temp_file],
        final_output,
        check_resources=fail_if_called,
    )

    assert rows == 42
    assert final_output.read_text() == 'new content'
    assert not temp_file.exists()


@pytest.mark.asyncio
async def test_extract_from_zip_files_success(
    monkeypatch, tmp_path, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 4)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    wait_calls: list[int] = []

    async def fake_wait(timeout_seconds: int = 30) -> bool:
        wait_calls.append(timeout_seconds)
        return True

    service.resource_policy.wait_for_resources = fake_wait  # type: ignore

    process_calls: list[tuple[str, set]] = []

    async def fake_process(
        zip_file: str, target_tpmerc_codes: set[str], output_path: Path
    ):
        _ = output_path
        process_calls.append((zip_file, target_tpmerc_codes))
        if zip_file == 'file_a.zip':
            (tmp_path / 'temp_a.parquet').touch()
            return {
                'records': 2,
                'temp_file': str(tmp_path / 'temp_a.parquet'),
            }
        (tmp_path / 'temp_b.parquet').touch()
        return {'records': 1, 'temp_file': str(tmp_path / 'temp_b.parquet')}

    service.zip_processor.process = fake_process  # type: ignore

    async def fake_merge(temp_files, final_output, **kwargs) -> int:
        _ = temp_files, kwargs
        final_output.touch()
        return 3

    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.service.merge_temp_files_streaming',
        fake_merge,
    )

    output_path = tmp_path / 'out.parquet'

    result = await service.extract_from_zip_files(
        ['file_a.zip', 'file_b.zip'],
        {'010'},
        output_path,
    )

    assert result['total_files'] == 2
    assert result['success_count'] == 2
    assert result['error_count'] == 0
    assert result['total_records'] == 3
    assert len(process_calls) == 2
    assert wait_calls == [30, 30]
    assert result['output_file'] == str(output_path)


@pytest.mark.asyncio
async def test_extract_from_zip_files_reports_merge_failure(
    monkeypatch, tmp_path, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 4)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    async def fake_wait(timeout_seconds: int = 30) -> bool:
        _ = timeout_seconds
        return True

    async def fake_process(
        zip_file: str, target_tpmerc_codes: set[str], output_path: Path
    ):
        _ = target_tpmerc_codes, output_path
        temp_file = tmp_path / f'{zip_file}.parquet'
        temp_file.touch()
        return {'records': 1, 'temp_file': str(temp_file)}

    async def fake_merge(*_args, **_kwargs) -> int:
        raise OSError('merge broke')

    service.resource_policy.wait_for_resources = fake_wait  # type: ignore
    service.zip_processor.process = fake_process  # type: ignore
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.service.merge_temp_files_streaming',
        fake_merge,
    )

    result = await service.extract_from_zip_files(
        {'file_a.zip', 'file_b.zip'},
        {'010'},
        tmp_path / 'out.parquet',
    )

    assert result['success_count'] == 2
    assert result['error_count'] == 1
    assert result['errors']['MERGE'] == 'merge broke'
    assert result['output_file'] == ''


@pytest.mark.asyncio
async def test_extract_from_zip_files_handles_errors(
    monkeypatch, tmp_path, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 5)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    result = await service.extract_from_zip_files(
        set(),
        {'010'},
        tmp_path / 'out.parquet',
    )

    assert result['total_files'] == 0
    assert result['success_count'] == 0
    assert result['error_count'] == 0


@pytest.mark.asyncio
async def test_extract_from_zip_files_preserves_partial_success(
    monkeypatch, tmp_path, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 4)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )
    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )
    monkeypatch.setattr(
        service.resource_policy,
        'wait_for_resources',
        resources_available,
    )

    async def fake_process(
        zip_file: str, target_tpmerc_codes: set[str], output_path: Path
    ):
        _ = target_tpmerc_codes, output_path
        if zip_file == 'broken.zip':
            raise OSError('input failed')
        temp_file = tmp_path / 'valid.parquet'
        temp_file.touch()
        return {'records': 4, 'temp_file': str(temp_file)}

    async def fake_merge(temp_files, final_output, **kwargs) -> int:
        _ = temp_files, kwargs
        final_output.touch()
        return 4

    monkeypatch.setattr(service.zip_processor, 'process', fake_process)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.service.merge_temp_files_streaming',
        fake_merge,
    )

    result = await service.extract_from_zip_files(
        {'valid.zip', 'broken.zip'}, {'010'}, tmp_path / 'out.parquet'
    )

    assert result['success_count'] == 1
    assert result['error_count'] == 1
    assert result['total_records'] == 4
    assert result['errors']['broken.zip'] == 'input failed'


@pytest.mark.asyncio
async def test_extract_updates_progress_once_per_file_when_resources_exhaust(
    monkeypatch, tmp_path, process_pool_spy
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 4)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    class ProgressSpy:
        def __init__(self, total: int, desc: str) -> None:
            self.total = total
            self.desc = desc
            self.updates: list[int] = []
            self.closed = False
            progress_instances.append(self)

        def update(self, amount: int) -> None:
            self.updates.append(amount)

        def close(self) -> None:
            self.closed = True

    progress_instances: list[ProgressSpy] = []

    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.service.SimpleProgressBar',
        ProgressSpy,
    )
    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )
    availability: Iterator[bool] = iter((False, False))

    async def fake_wait(timeout_seconds: int = 30) -> bool:
        _ = timeout_seconds
        return next(availability)

    monkeypatch.setattr(
        service.resource_policy, 'wait_for_resources', fake_wait
    )

    result = await service.extract_from_zip_files(
        {'file_a.zip', 'file_b.zip'}, {'010'}, tmp_path / 'out.parquet'
    )

    progress = progress_instances[0]
    assert progress.updates == [1, 1]
    assert progress.closed is True
    assert result['error_count'] == 2
    assert set(result['errors']) == {'file_a.zip', 'file_b.zip'}


@pytest.mark.asyncio
async def test_extract_keeps_record_count_when_temp_file_is_missing(
    monkeypatch, tmp_path, process_pool_spy, caplog
):
    _ = process_pool_spy
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 2)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )
    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )
    monkeypatch.setattr(
        service.resource_policy,
        'wait_for_resources',
        resources_available,
    )

    async def fake_process(**_kwargs):
        return {
            'records': 5,
            'temp_file': str(tmp_path / 'missing.parquet'),
        }

    monkeypatch.setattr(service.zip_processor, 'process', fake_process)

    with caplog.at_level('WARNING'):
        result = await service.extract_from_zip_files(
            {'file.zip'}, {'010'}, tmp_path / 'out.parquet'
        )

    assert result['success_count'] == 1
    assert result['error_count'] == 0
    assert result['total_records'] == 5
    assert result['output_file'] == ''
    assert any(
        'Temp file not found' in record.message for record in caplog.records
    )


def test_extraction_service_close_graceful_shutdown(
    monkeypatch, process_pool_spy
):
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    assert len(process_pool_spy) == 1
    pool = process_pool_spy[0]
    assert pool.shutdown_called is False

    service.close()
    service.close()

    assert pool.shutdown_called is True


def test_extraction_service_close_no_pool_in_slow_mode(
    monkeypatch, process_pool_spy
):
    monitor = FakeResourceMonitor(safe_worker_cap=2)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.SLOW,
    )

    assert service.zip_processor.executor_pool is None
    assert len(process_pool_spy) == 0

    service.close()


def test_extraction_service_cleanup_handles_shutdown_errors(
    monkeypatch, process_pool_spy
):
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )

    service = ExtractionServiceB3(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnumB3.FAST,
    )

    def shutdown_with_error(wait: bool = False, cancel_futures: bool = False):
        _ = wait, cancel_futures
        raise RuntimeError('Shutdown error during interpreter cleanup')

    process_pool_spy[0].shutdown = shutdown_with_error

    service.__del__()
