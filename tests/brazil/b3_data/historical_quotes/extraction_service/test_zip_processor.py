import asyncio
from importlib import import_module

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes import (
    ExtractionServiceB3,
    ProcessingModeEnumB3,
)
from globaldatafinance.core import ResourceState
from tests.brazil.b3_data.historical_quotes.conftest import (
    DummyLoop,
    FakeParser,
    FakeResourceMonitor,
    FakeWriter,
    FakeZipReader,
)

zip_processor = import_module(
    'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.zip_processor'
)

pytestmark = pytest.mark.unit


def _service(monkeypatch, *, mode, reader, parser, writer):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )
    return ExtractionServiceB3(
        zip_reader=reader,
        parser=parser,
        data_writer=writer,
        processing_mode=mode,
    )


@pytest.mark.asyncio
async def test_process_and_write_zip_slow_mode(monkeypatch, tmp_path):
    parser = FakeParser()
    reader = FakeZipReader({'sample.zip': ['keep-1', 'skip', 'keep-2']})
    service = _service(
        monkeypatch,
        mode=ProcessingModeEnumB3.SLOW,
        reader=reader,
        parser=parser,
        writer=FakeWriter(),
    )

    result = await service.zip_processor.process(
        zip_file='sample.zip',
        target_tpmerc_codes={'010'},
        output_path=tmp_path / 'data.parquet',
    )

    assert result['records'] == 2
    assert reader.calls == ['sample.zip']
    assert parser.calls == [
        ('keep-1', frozenset({'010'})),
        ('skip', frozenset({'010'})),
        ('keep-2', frozenset({'010'})),
    ]


@pytest.mark.asyncio
async def test_processor_temp_paths_include_input_extension(
    monkeypatch, tmp_path
):
    service = _service(
        monkeypatch,
        mode=ProcessingModeEnumB3.SLOW,
        reader=FakeZipReader(
            {
                'COTAHIST_A2023.ZIP': ['keep'],
                'COTAHIST_A2023.TXT': ['keep'],
            }
        ),
        parser=FakeParser(),
        writer=FakeWriter(),
    )

    zip_result = await service.zip_processor.process(
        zip_file='COTAHIST_A2023.ZIP',
        target_tpmerc_codes={'010'},
        output_path=tmp_path / 'data.parquet',
    )
    txt_result = await service.zip_processor.process(
        zip_file='COTAHIST_A2023.TXT',
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
    lines = [f'keep-{index}' for index in range(7)]
    writer = FakeWriter()
    service = _service(
        monkeypatch,
        mode=ProcessingModeEnumB3.SLOW,
        reader=FakeZipReader({'sample.zip': lines}),
        parser=FakeParser(),
        writer=writer,
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

    monkeypatch.setattr(
        service.buffered_writer,
        'flush_if_needed',
        fake_flush_if_needed,
    )

    result = await service.zip_processor.process(
        zip_file='sample.zip',
        target_tpmerc_codes={'010'},
        output_path=tmp_path / 'data.parquet',
    )

    assert flush_buffer_sizes == [3, 6]
    assert result['records'] == 7
    assert writer.calls[0]['records'] == [{'value': line} for line in lines]


@pytest.mark.asyncio
async def test_process_and_write_zip_fast_mode(monkeypatch, tmp_path):
    service = _service(
        monkeypatch,
        mode=ProcessingModeEnumB3.FAST,
        reader=FakeZipReader({'fast.zip': ['keep-1', 'drop', 'keep-2']}),
        parser=FakeParser(),
        writer=FakeWriter(),
    )
    service.resource_policy.parse_batch_size = 2
    batch_calls: list[list[str]] = []

    async def fake_batch(lines, target_codes):
        _ = target_codes
        batch_calls.append(list(lines))
        return [{'value': line} for line in lines if 'keep' in line]

    monkeypatch.setattr(
        service.zip_processor,
        '_parse_lines_batch_parallel',
        fake_batch,
    )

    result = await service.zip_processor.process(
        zip_file='fast.zip',
        target_tpmerc_codes={'010'},
        output_path=tmp_path / 'data.parquet',
    )

    assert result['records'] == 2
    assert batch_calls == [['keep-1', 'drop'], ['keep-2']]


@pytest.mark.asyncio
async def test_process_and_write_zip_propagates_errors(monkeypatch, tmp_path):
    service = _service(
        monkeypatch,
        mode=ProcessingModeEnumB3.FAST,
        reader=FakeZipReader({'error.zip': ['line']}),
        parser=FakeParser(),
        writer=FakeWriter(),
    )

    async def failing_batch(_lines, _codes):
        raise RuntimeError('boom')

    monkeypatch.setattr(
        service.zip_processor,
        '_parse_lines_batch_parallel',
        failing_batch,
    )

    with pytest.raises(RuntimeError, match='boom'):
        await service.zip_processor.process(
            zip_file='error.zip',
            target_tpmerc_codes={'010'},
            output_path=tmp_path / 'data.parquet',
        )


@pytest.mark.asyncio
async def test_parse_lines_batch_parallel_filters_none(monkeypatch):
    service = _service(
        monkeypatch,
        mode=ProcessingModeEnumB3.FAST,
        reader=FakeZipReader(),
        parser=FakeParser(),
        writer=FakeWriter(),
    )
    dummy_loop = DummyLoop(result=[None, {'value': 'ok'}])
    monkeypatch.setattr(
        zip_processor.asyncio,
        'get_running_loop',
        lambda: dummy_loop,
    )

    records = await service.zip_processor._parse_lines_batch_parallel(
        ['line'], {'010'}
    )

    assert records == [{'value': 'ok'}]
    assert dummy_loop.calls


@pytest.mark.asyncio
async def test_parse_lines_batch_parallel_awaits_executor_without_polling(
    monkeypatch,
):
    service = _service(
        monkeypatch,
        mode=ProcessingModeEnumB3.FAST,
        reader=FakeZipReader(),
        parser=FakeParser(),
        writer=FakeWriter(),
    )
    event_loop = asyncio.get_running_loop()
    future = event_loop.create_future()
    event_loop.call_later(0.01, future.set_result, [None, {'value': 'ok'}])

    class FutureLoop:
        def run_in_executor(self, _executor, _func, *_args):
            return future

    monkeypatch.setattr(
        zip_processor.asyncio,
        'get_running_loop',
        lambda: FutureLoop(),
    )

    async def unexpected_sleep(_delay: float) -> None:
        raise AssertionError('executor completion must be awaited directly')

    monkeypatch.setattr(zip_processor.asyncio, 'sleep', unexpected_sleep)

    records = await service.zip_processor._parse_lines_batch_parallel(
        ['line'], {'010'}
    )

    assert records == [{'value': 'ok'}]
