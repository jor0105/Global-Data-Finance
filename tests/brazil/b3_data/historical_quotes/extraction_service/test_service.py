from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes import (
    ExtractionServiceB3,
    ProcessingModeEnumB3,
)
from globaldatafinance.core import ResourceState
from tests.brazil.b3_data.historical_quotes.conftest import (
    FakeParser,
    FakeResourceMonitor,
    FakeWriter,
    FakeZipReader,
    resources_available,
)

pytestmark = pytest.mark.unit


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

    monkeypatch.setattr(
        service.resource_policy,
        'wait_for_resources',
        fake_wait,
    )

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

    monkeypatch.setattr(service.zip_processor, 'process', fake_process)

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

    monkeypatch.setattr(
        service.resource_policy,
        'wait_for_resources',
        fake_wait,
    )
    monkeypatch.setattr(service.zip_processor, 'process', fake_process)
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
async def test_extract_rejects_missing_temporary_parquet(
    monkeypatch, tmp_path, process_pool_spy
):
    """A processed input cannot be successful without a mergeable artifact."""
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

    result = await service.extract_from_zip_files(
        {'file.zip'}, {'010'}, tmp_path / 'out.parquet'
    )

    assert result['success_count'] == 0
    assert result['error_count'] == 1
    assert result['total_records'] == 0
    assert result['output_file'] == ''
    assert result['errors'] == {
        'file.zip': (
            'COTAHIST temporary Parquet was not created: '
            f'{tmp_path / "missing.parquet"}'
        )
    }


@pytest.mark.asyncio
async def test_extract_reports_zero_matching_records_as_no_data(
    monkeypatch, tmp_path, process_pool_spy
):
    """A selected input without requested asset records is not a success."""
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
            'records': 0,
            'temp_file': str(tmp_path / 'not-created.parquet'),
        }

    monkeypatch.setattr(service.zip_processor, 'process', fake_process)

    result = await service.extract_from_zip_files(
        {'file.zip'}, {'010'}, tmp_path / 'out.parquet'
    )

    assert result['success_count'] == 0
    assert result['error_count'] == 1
    assert result['total_records'] == 0
    assert result['output_file'] == ''
    assert result['errors'] == {
        'file.zip': 'No COTAHIST records matched the requested assets'
    }


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

    shutdown = Mock(side_effect=RuntimeError('Shutdown error'))
    process_pool_spy[0].shutdown = shutdown

    service.close()
    service.close()

    shutdown.assert_called_once_with(wait=True, cancel_futures=False)
    assert service.zip_processor.executor_pool is None
