from contextlib import contextmanager
from pathlib import Path

import pytest

from datafinance.brazil.dados_b3.historical_quotes.domain import ProcessingModeEnum
from datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service import (
    ExtractionService,
    _parse_lines_batch,
)
from datafinance.core import ResourceState


class FakeResourceMonitor:
    def __init__(
        self,
        *,
        safe_worker_cap: int = 8,
        safe_batch_size: int | None = None,
        states: list[ResourceState] | None = None,
        wait_result: bool = True,
        process_memory_mb: float = 100.0,
    ) -> None:
        self.safe_worker_cap = safe_worker_cap
        self.safe_batch_size = safe_batch_size
        self.states = list(states or [ResourceState.HEALTHY])
        self.wait_result = wait_result
        self.process_memory_mb = process_memory_mb
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

    def get_process_memory_mb(self) -> float:
        return self.process_memory_mb


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
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.log_execution_time",
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
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ThreadPoolExecutor",
        factory,
    )
    return created


def test_extraction_service_initialization_fast_mode(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(safe_worker_cap=6)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
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
    assert monitor.worker_calls == [15, None]


def test_extraction_service_initialization_slow_mode(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.SLOW,
    )

    assert service.use_parallel_parsing is False
    assert service.max_concurrent_files == 3
    assert service.max_workers == 1
    assert service.executor_pool is None
    assert monitor.worker_calls == [3]


@pytest.mark.asyncio
async def test_extraction_service_wait_for_resources(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(wait_result=False)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
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
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.asyncio.get_event_loop",
        lambda: dummy_loop,
    )

    result = await service._wait_for_resources(timeout_seconds=7)

    assert result is False
    assert monitor.wait_calls == [(ResourceState.WARNING, 7)]
    assert dummy_loop.calls


@pytest.mark.asyncio
async def test_extraction_service_write_buffer_to_disk(
    monkeypatch, process_pool_spy, tmp_path
):
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
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

    await service._write_buffer_to_disk([{"row": 1}], output_path, "overwrite")
    await service._write_buffer_to_disk([{"row": 2}], output_path, "append")

    assert writer.calls[0]["mode"] == "overwrite"
    assert writer.calls[1]["mode"] == "append"
    assert writer.calls[0]["records"] == [{"row": 1}]
    assert writer.calls[1]["records"] == [{"row": 2}]


@pytest.mark.asyncio
async def test_process_and_write_zip_slow_mode(monkeypatch, tmp_path):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
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

    output_path = tmp_path / "data.parquet"
    result = await service._process_and_write_zip("sample.zip", {"010"}, output_path)

    assert result["records"] == 2
    assert zip_reader.calls == ["sample.zip"]
    assert parser.calls[0][0] == "keep-1"
    assert parser.calls[-1][0] == "keep-2"


@pytest.mark.asyncio
async def test_process_and_write_zip_fast_mode(monkeypatch, process_pool_spy, tmp_path):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY])
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
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

    output_path = tmp_path / "data.parquet"
    result = await service._process_and_write_zip("fast.zip", {"010"}, output_path)

    assert result["records"] == 2
    assert batch_calls[0] == ["keep-1", "drop"]
    assert batch_calls[1] == ["keep-2"]


@pytest.mark.asyncio
async def test_process_and_write_zip_propagates_errors(
    monkeypatch, process_pool_spy, tmp_path
):
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
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

    output_path = tmp_path / "data.parquet"
    with pytest.raises(RuntimeError):
        await service._process_and_write_zip("error.zip", {"010"}, output_path)


@pytest.mark.asyncio
async def test_parse_lines_batch_parallel_filters_none(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor()
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
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
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.asyncio.get_event_loop",
        lambda: dummy_loop,
    )

    records = await service._parse_lines_batch_parallel(["line"], {"010"})

    assert records == [{"value": "ok"}]
    assert dummy_loop.calls


def test_parse_lines_batch_filters_by_target():
    lines = [build_cotahist_line("010"), build_cotahist_line("020")]

    records = _parse_lines_batch(lines, {"010"})

    assert len(records) == 1
    assert records[0]["tipo_mercado"] == "010"


@pytest.mark.asyncio
async def test_extract_from_zip_files_success(monkeypatch, tmp_path, process_pool_spy):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 4)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    wait_calls: list[int] = []

    async def fake_wait(timeout_seconds: int = 30) -> bool:
        wait_calls.append(timeout_seconds)
        return True

    service._wait_for_resources = fake_wait  # type: ignore

    process_calls: list[tuple[str, set]] = []

    async def fake_process(
        zip_file: str, target_tpmerc_codes: set[str], output_path: Path
    ):
        process_calls.append((zip_file, target_tpmerc_codes))
        if zip_file == "file_a.zip":
            return {"records": 2, "temp_file": str(tmp_path / "temp_a.parquet")}
        return {"records": 1, "temp_file": str(tmp_path / "temp_b.parquet")}

    service._process_and_write_zip = fake_process  # type: ignore

    async def fake_merge(temp_files: list, final_output: Path) -> int:
        return 3

    service._merge_temp_files_streaming = fake_merge  # type: ignore

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
    assert len(process_calls) == 2
    assert wait_calls == [30, 30]
    assert result["output_file"] == str(output_path)


@pytest.mark.asyncio
async def test_extract_from_zip_files_handles_errors(
    monkeypatch, tmp_path, process_pool_spy
):
    monitor = FakeResourceMonitor(states=[ResourceState.HEALTHY] * 5)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    result = await service.extract_from_zip_files(
        set(),
        {"010"},
        tmp_path / "out.parquet",
    )

    assert result["total_files"] == 0
    assert result["success_count"] == 0
    assert result["error_count"] == 0


def test_extraction_service_cleanup_graceful_shutdown(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    assert len(process_pool_spy) == 1
    pool = process_pool_spy[0]
    assert pool.shutdown_called is False

    service.__del__()

    assert pool.shutdown_called is True


def test_extraction_service_cleanup_no_pool_in_slow_mode(monkeypatch, process_pool_spy):
    monitor = FakeResourceMonitor(safe_worker_cap=2)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.SLOW,
    )

    assert service.executor_pool is None
    assert len(process_pool_spy) == 0

    service.__del__()

    assert len(process_pool_spy) == 0


def test_extraction_service_cleanup_handles_shutdown_errors(
    monkeypatch, process_pool_spy
):
    monitor = FakeResourceMonitor(safe_worker_cap=4)
    monkeypatch.setattr(
        "datafinance.brazil.dados_b3.historical_quotes.infra.extraction_service.ResourceMonitor",
        lambda: monitor,
    )

    service = ExtractionService(
        zip_reader=FakeZipReader(),
        parser=FakeParser(),
        data_writer=FakeWriter(),
        processing_mode=ProcessingModeEnum.FAST,
    )

    def shutdown_with_error(wait: bool = False, cancel_futures: bool = False):
        raise RuntimeError("Shutdown error during interpreter cleanup")

    process_pool_spy[0].shutdown = shutdown_with_error

    try:
        service.__del__()
    except Exception as e:
        pytest.fail(f"__del__ should handle shutdown errors gracefully: {e}")
