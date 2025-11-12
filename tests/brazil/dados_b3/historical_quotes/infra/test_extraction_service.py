from contextlib import contextmanager
from pathlib import Path

import pytest

from src.brazil.dados_b3.historical_quotes.domain import ProcessingModeEnum
from src.brazil.dados_b3.historical_quotes.infra.extraction_service import (
    ExtractionService,
    _parse_lines_batch,
)
from src.core import ResourceState


class FakeResourceMonitor:
    def __init__(
        self,
        *,
        safe_worker_cap: int = 8,
        safe_batch_size: int | None = None,
        states: list[ResourceState] | None = None,
        wait_result: bool = True,
    ) -> None:
        self.safe_worker_cap = safe_worker_cap
        self.safe_batch_size = safe_batch_size
        self.states = list(states or [ResourceState.HEALTHY])
        self.wait_result = wait_result
        self.worker_calls: list[int | None] = []
        self.batch_calls: list[int] = []
        self.wait_calls: list[tuple[ResourceState, int]] = []
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

    def wait_for_resources(
        self, required_state: ResourceState, timeout_seconds: int
    ) -> bool:
        self.wait_calls.append((required_state, timeout_seconds))
        return self.wait_result


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
        if "keep" in line:
            return {"value": line}
        return None


class FakeWriter:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def write_to_parquet(self, data, output_path: Path, mode: str):
        self.calls.append(
            {
                "records": list(data),
                "output_path": output_path,
                "mode": mode,
            }
        )


class DummyPool:
    def __init__(self, max_workers: int | None = None) -> None:
        self.max_workers = max_workers
        self.shutdown_called = False

    def shutdown(self, wait: bool = False, cancel_futures: bool = False) -> None:
        self.shutdown_called = True


class DummyLoop:
    def __init__(self, result):
        self.result = result
        self.calls: list[tuple] = []

    async def run_in_executor(self, executor, func, *args):
        self.calls.append((executor, func, args))
        if self.result is None:
            return func(*args)
        return self.result


def build_cotahist_line(tpmerc: str) -> str:
    line = [" "] * 245
    line[0:2] = list("01")
    line[2:10] = list("20240101")
    line[10:12] = list("02")
    ticker = "TESTE12345678"[:12]
    line[12:24] = list(ticker)
    line[24:27] = list(tpmerc)
    return "".join(line)


@pytest.fixture(autouse=True)
def suppress_execution_time_logging(monkeypatch):
    @contextmanager
    def noop(*_args, **_kwargs):
        yield

    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.log_execution_time",
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
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ProcessPoolExecutor",
        factory,
    )
    return created


def test_extraction_service_initialization_fast_mode(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(safe_worker_cap=6)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    assert service.use_parallel_parsing is True
    assert service.max_concurrent_files == 6
    assert service.max_workers == 6
    assert process_pool_spy[0].max_workers == 6
    assert monitor.worker_calls == [10, None]


def test_extraction_service_initialization_slow_mode(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.SLOW,
    )

    assert service.use_parallel_parsing is False
    assert service.max_concurrent_files == 2
    assert service.max_workers == 1
    assert service.process_pool is None
    assert monitor.worker_calls == [2]


def test_extraction_service_adjust_batch_sizes(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(
        safe_worker_cap=6,
        safe_batch_size=5_000,
        states=[ResourceState.WARNING],
    )
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    service._adjust_batch_sizes()

    assert service.batch_size == 5_000
    assert service.parse_batch_size == ExtractionService.MIN_PARSE_BATCH_SIZE
    assert monitor.batch_calls == [ExtractionService.DEFAULT_BATCH_SIZE]


@pytest.mark.asyncio
async def test_extraction_service_wait_for_resources(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(wait_result=False)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    dummy_loop = DummyLoop(result=None)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.asyncio.get_event_loop",
        lambda: dummy_loop,
    )

    result = await service._wait_for_resources(timeout_seconds=7)

    assert result is False
    assert monitor.wait_calls == [(ResourceState.WARNING, 7)]
    assert dummy_loop.calls


@pytest.mark.asyncio
async def test_extraction_service_flush_batch_to_disk(
    monkeypatch, process_pool_spy, tmp_path
):
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    writer = FakeWriter()
    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=writer,
        processing_mode=ProcessingModeEnum.FAST,
    )

    output_path = tmp_path / "data.parquet"

    await service._flush_batch_to_disk([{"row": 1}], output_path, 1)
    await service._flush_batch_to_disk([{"row": 2}], output_path, 2)

    assert writer.calls[0]["mode"] == "overwrite"
    assert writer.calls[1]["mode"] == "append"
    assert writer.calls[0]["records"] == [{"row": 1}]
    assert writer.calls[1]["records"] == [{"row": 2}]


@pytest.mark.asyncio
async def test_process_single_zip_slow_mode(monkeypatch):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    parser = FakeParser()
    zip_reader = FakeZipReader({"sample.zip": ["keep-1", "skip", "keep-2"]})

    service = ExtractionService(
        zip_reader=zip_reader,
        parser=parser,
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.SLOW,
    )

    records = await service._process_single_zip("sample.zip", {"010"})

    assert len(records) == 2
    assert zip_reader.calls == ["sample.zip"]
    assert parser.calls[0][0] == "keep-1"
    assert parser.calls[-1][0] == "keep-2"


@pytest.mark.asyncio
async def test_process_single_zip_fast_mode(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    zip_reader = FakeZipReader({"fast.zip": ["keep-1", "drop", "keep-2"]})

    service = ExtractionService(
        zip_reader=zip_reader,
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )
    service.parse_batch_size = 2

    batch_calls: list[list[str]] = []

    async def fake_batch(lines, target_codes):
        batch_calls.append(list(lines))
        return [{"value": line} for line in lines if "keep" in line]

    service._parse_lines_batch_parallel = fake_batch  # type: ignore

    records = await service._process_single_zip("fast.zip", {"010"})

    assert len(records) == 2
    assert batch_calls[0] == ["keep-1", "drop"]
    assert batch_calls[1] == ["keep-2"]


@pytest.mark.asyncio
async def test_process_single_zip_propagates_errors(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader({"error.zip": ["line"]}),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    async def failing_batch(_lines, _codes):
        raise RuntimeError("boom")

    service._parse_lines_batch_parallel = failing_batch  # type: ignore

    with pytest.raises(RuntimeError):
        await service._process_single_zip("error.zip", {"010"})


@pytest.mark.asyncio
async def test_parse_lines_batch_parallel_filters_none(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    dummy_loop = DummyLoop(result=[None, {"value": "ok"}])
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.asyncio.get_event_loop",
        lambda: dummy_loop,
    )

    records = await service._parse_lines_batch_parallel(["line"], {"010"})

    assert records == [{"value": "ok"}]
    assert dummy_loop.calls


def test_parse_lines_batch_filters_by_target():
    lines = [build_cotahist_line("010"), build_cotahist_line("020")]

    records = _parse_lines_batch(lines, {"010"})

    assert len(records) == 1
    assert records[0]["tpmerc"] == "010"


@pytest.mark.asyncio
async def test_extract_from_zip_files_success(monkeypatch, tmp_path, process_pool_spy):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 4)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )
    service.batch_size = 2
    service._adjust_batch_sizes = lambda: None  # type: ignore

    flush_calls: list[tuple[int, list[dict]]] = []

    async def fake_flush(records, output_path, batch_number):
        flush_calls.append((batch_number, list(records)))

    service._flush_batch_to_disk = fake_flush  # type: ignore

    wait_calls: list[int] = []

    async def fake_wait(timeout_seconds: int = 30) -> bool:
        wait_calls.append(timeout_seconds)
        return True

    service._wait_for_resources = fake_wait  # type: ignore

    async def fake_process(zip_file: str, target_codes: set[str]):
        if zip_file == "file_a.zip":
            return [
                {"zip": zip_file, "row": 1},
                {"zip": zip_file, "row": 2},
            ]
        return [{"zip": zip_file, "row": 3}]

    service._process_single_zip = fake_process  # type: ignore

    output_path = tmp_path / "out.parquet"

    result = await service.extract_from_zip_files(
        ["file_a.zip", "file_b.zip"],
        {"010"},
        output_path,
    )

    assert result["total_files"] == 2
    assert result["success_count"] == 2
    assert result["error_count"] == 0
    assert result["total_records"] == 3
    assert result["batches_written"] == 2
    assert flush_calls[0][0] == 1 and len(flush_calls[0][1]) == 2
    assert flush_calls[1][0] == 2 and len(flush_calls[1][1]) == 1
    assert wait_calls == [30, 30]
    assert result["output_file"] == str(output_path)


@pytest.mark.asyncio
async def test_extract_from_zip_files_handles_errors(
    monkeypatch, tmp_path, process_pool_spy
):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 5)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )
    service.batch_size = 1
    service._adjust_batch_sizes = lambda: None  # type: ignore

    flush_batches: list[int] = []

    async def fake_flush(records, output_path, batch_number):
        flush_batches.append(batch_number)

    service._flush_batch_to_disk = fake_flush  # type: ignore

    async def fake_wait(_timeout_seconds: int = 30) -> bool:
        return True

    service._wait_for_resources = fake_wait  # type: ignore

    async def fake_process(zip_file: str, _codes: set[str]):
        if zip_file == "error.zip":
            return Exception("expected failure")
        if zip_file == "raised.zip":
            raise RuntimeError("boom")
        return [{"zip": zip_file}]

    service._process_single_zip = fake_process  # type: ignore

    result = await service.extract_from_zip_files(
        ["good.zip", "error.zip", "raised.zip"],
        {"010"},
        tmp_path / "out.parquet",
    )

    assert result["success_count"] == 1
    assert result["error_count"] == 2
    assert result["total_records"] == 1
    assert result["batches_written"] == 1
    assert result["errors"] == {"error.zip": "expected failure"}
    assert flush_batches == [1]


def test_extraction_service_cleanup_graceful_shutdown(monkeypatch, process_pool_spy):
    """Test that ExtractionService properly cleans up process pool on deletion."""
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    # Verify process pool was created
    assert len(process_pool_spy) == 1
    pool = process_pool_spy[0]
    assert pool.shutdown_called is False

    # Trigger cleanup via __del__
    service.__del__()

    # Verify shutdown was called with correct parameters
    assert pool.shutdown_called is True


def test_extraction_service_cleanup_no_pool_in_slow_mode(monkeypatch, process_pool_spy):
    """Test that SLOW mode doesn't create process pool, so cleanup is safe."""
    monitor = FakeResourceMonitor(safe_worker_cap=2)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.SLOW,
    )

    # Verify no process pool was created
    assert service.process_pool is None
    assert len(process_pool_spy) == 0

    # Cleanup should not raise any error
    service.__del__()

    # No pools to verify
    assert len(process_pool_spy) == 0


def test_extraction_service_cleanup_handles_shutdown_errors(
    monkeypatch, process_pool_spy
):
    """Test that cleanup gracefully handles exceptions during shutdown."""
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        "src.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    # Make shutdown raise an error

    def shutdown_with_error(wait: bool = False, cancel_futures: bool = False):
        raise RuntimeError("Shutdown error during interpreter cleanup")

    process_pool_spy[0].shutdown = shutdown_with_error

    # Cleanup should not raise any error even if shutdown fails
    try:
        service.__del__()
    except Exception as e:
        pytest.fail(f"__del__ should handle shutdown errors gracefully: {e}")
