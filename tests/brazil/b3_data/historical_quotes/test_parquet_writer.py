from pathlib import Path
from types import SimpleNamespace

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes import parquet_writer
from globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer import (
    disk as parquet_writer_disk,
)
from globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer import (
    writer as parquet_writer_impl,
)
from globaldatafinance.core import ResourceState
from globaldatafinance.macro_exceptions import DiskFullError

pytestmark = pytest.mark.unit

ParquetWriterB3 = parquet_writer.ParquetWriterB3


class FakeDataFrame:
    def __init__(self, rows: list[dict], schema_overrides=None):
        self.data = [dict(row) for row in rows]
        self.height = len(self.data)
        self.width = len(self.data[0]) if self.data else 0
        self.schema_overrides = schema_overrides

    def estimated_size(self) -> int:
        return max(1, self.height) * 64

    def write_parquet(self, path: str, **_kwargs) -> None:
        Path(path).write_text('parquet')

    def to_arrow(self):
        raise NotImplementedError


class FakePolarsModule:
    DataFrame = FakeDataFrame

    @staticmethod
    def Decimal(precision: int, scale: int):
        return f'Decimal({precision}, {scale})'

    @staticmethod
    def read_parquet(_path: str) -> FakeDataFrame:
        return FakeDataFrame([{'existing': True}])

    @staticmethod
    def concat(
        frames: list[FakeDataFrame], how: str = 'vertical'
    ) -> FakeDataFrame:
        combined: list[dict] = []
        for frame in frames:
            combined.extend(frame.data)
        return FakeDataFrame(combined)


class WriterResourceMonitor:
    def __init__(self, states: list[ResourceState]) -> None:
        self.states = list(states)
        self._index = 0
        self.check_history: list[ResourceState] = []

    def check_resources(self) -> ResourceState:
        if self._index < len(self.states):
            state = self.states[self._index]
            self._index += 1
        else:
            state = self.states[-1]
        self.check_history.append(state)
        return state


@pytest.fixture(autouse=True)
def fake_polars(monkeypatch):
    monkeypatch.setattr(parquet_writer_impl, 'pl', FakePolarsModule)


@pytest.mark.asyncio
async def test_parquet_writer_skips_empty_data(tmp_path):
    monitor = WriterResourceMonitor([ResourceState.HEALTHY])
    writer = ParquetWriterB3(resource_monitor=monitor)

    await writer.write_to_parquet([], tmp_path / 'out.parquet')

    assert monitor.check_history == []


@pytest.mark.asyncio
async def test_parquet_writer_raises_on_memory_exhaustion(
    monkeypatch, tmp_path
):
    monitor = WriterResourceMonitor([ResourceState.EXHAUSTED])
    writer = ParquetWriterB3(resource_monitor=monitor)

    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    with pytest.raises(MemoryError):
        await writer.write_to_parquet([{'value': 1}], tmp_path / 'out.parquet')


@pytest.mark.asyncio
async def test_parquet_writer_overwrite_mode(monkeypatch, tmp_path):
    monitor = WriterResourceMonitor([ResourceState.HEALTHY])
    writer = ParquetWriterB3(resource_monitor=monitor)

    calls: list[dict] = []

    def fake_write(df: FakeDataFrame, output_path: Path) -> None:
        calls.append({'rows': df.height, 'path': output_path})
        output_path.write_text('content')

    monkeypatch.setattr(
        writer,
        '_write_dataframe',
        fake_write,
    )
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    output_path = tmp_path / 'out.parquet'
    await writer.write_to_parquet([{'a': 1}, {'a': 2}], output_path)

    assert calls == [{'rows': 2, 'path': output_path}]
    assert output_path.exists()


@pytest.mark.asyncio
async def test_parquet_writer_append_uses_streaming(monkeypatch, tmp_path):
    monitor = WriterResourceMonitor(
        [ResourceState.HEALTHY, ResourceState.HEALTHY]
    )
    writer = ParquetWriterB3(resource_monitor=monitor)

    streaming_calls: list[int] = []

    async def fake_stream(df: FakeDataFrame, output_path: Path) -> None:
        streaming_calls.append(df.height)

    monkeypatch.setattr(writer, '_append_with_streaming', fake_stream)
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    output_path = tmp_path / 'out.parquet'
    output_path.write_text('existing')

    await writer.write_to_parquet([{'a': 1}], output_path, mode='append')

    assert streaming_calls == [1]


@pytest.mark.asyncio
async def test_parquet_writer_append_uses_streaming_when_low_memory(
    monkeypatch, tmp_path
):
    monitor = WriterResourceMonitor(
        [ResourceState.HEALTHY, ResourceState.CRITICAL]
    )
    writer = ParquetWriterB3(resource_monitor=monitor)

    streaming_calls: list[int] = []

    async def fake_stream(df: FakeDataFrame, output_path: Path) -> None:
        streaming_calls.append(df.height)
        output_path.write_text('stream')

    monkeypatch.setattr(writer, '_append_with_streaming', fake_stream)
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    output_path = tmp_path / 'out.parquet'
    output_path.write_text('existing')

    await writer.write_to_parquet([{'a': 1}], output_path, mode='append')

    assert streaming_calls == [1]


@pytest.mark.asyncio
async def test_parquet_writer_chunk_mode_merges_once(monkeypatch, tmp_path):
    monitor = WriterResourceMonitor([ResourceState.CRITICAL])
    writer = ParquetWriterB3(resource_monitor=monitor)

    write_calls: list[Path] = []
    merge_calls: list[list[Path]] = []

    def fake_write(_df: FakeDataFrame, output_path: Path) -> None:
        write_calls.append(output_path)
        output_path.write_text('chunk')

    async def fake_merge(source_paths: list[Path], output_path: Path) -> None:
        merge_calls.append(source_paths)
        output_path.write_text('merged')

    async def fail_stream(*_args, **_kwargs) -> None:
        raise AssertionError('chunk mode should not append each chunk')

    monkeypatch.setattr(writer, '_write_dataframe', fake_write)
    monkeypatch.setattr(writer, '_merge_parquet_files_streaming', fake_merge)
    monkeypatch.setattr(writer, '_append_with_streaming', fail_stream)
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    output_path = tmp_path / 'out.parquet'
    records = [{'a': index} for index in range(50_001)]

    await writer.write_to_parquet(records, output_path)

    assert len(write_calls) == 3
    assert len(merge_calls) == 1
    assert len(merge_calls[0]) == 3
    assert output_path.read_text() == 'merged'


@pytest.mark.asyncio
async def test_parquet_writer_chunk_append_includes_existing_output(
    monkeypatch, tmp_path
):
    monitor = WriterResourceMonitor([ResourceState.CRITICAL])
    writer = ParquetWriterB3(resource_monitor=monitor)

    merge_calls: list[list[Path]] = []

    def fake_write(_df: FakeDataFrame, output_path: Path) -> None:
        output_path.write_text('chunk')

    async def fake_merge(source_paths: list[Path], output_path: Path) -> None:
        merge_calls.append(source_paths)
        output_path.write_text('merged')

    monkeypatch.setattr(writer, '_write_dataframe', fake_write)
    monkeypatch.setattr(writer, '_merge_parquet_files_streaming', fake_merge)
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    output_path = tmp_path / 'out.parquet'
    output_path.write_text('existing')
    records = [{'a': index} for index in range(25_001)]

    await writer.write_to_parquet(records, output_path, mode='append')

    assert len(merge_calls) == 1
    assert merge_calls[0][0] == output_path
    assert len(merge_calls[0]) == 3
    assert output_path.read_text() == 'merged'


def test_parquet_writer_check_disk_space_raises(monkeypatch, tmp_path):
    free_space = (ParquetWriterB3.MIN_FREE_SPACE_MB - 10) * 1024 * 1024
    monkeypatch.setattr(
        parquet_writer_disk.shutil,
        'disk_usage',
        lambda _path: SimpleNamespace(free=free_space),
    )

    with pytest.raises(DiskFullError):
        ParquetWriterB3._check_disk_space(tmp_path / 'file.parquet')


@pytest.mark.asyncio
async def test_parquet_writer_translates_oserror_disk_full(
    monkeypatch, tmp_path
):
    monitor = WriterResourceMonitor([ResourceState.HEALTHY])
    writer = ParquetWriterB3(resource_monitor=monitor)

    def failing_write(*_args, **_kwargs):
        raise OSError('No space left on device')

    monkeypatch.setattr(writer, '_write_dataframe', failing_write)
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    with pytest.raises(DiskFullError):
        await writer.write_to_parquet([{'a': 1}], tmp_path / 'out.parquet')


@pytest.mark.asyncio
async def test_parquet_writer_raises_ioerror_for_other_oserror(
    monkeypatch, tmp_path
):
    monitor = WriterResourceMonitor([ResourceState.HEALTHY])
    writer = ParquetWriterB3(resource_monitor=monitor)

    def failing_write(*_args, **_kwargs):
        raise OSError('Permission denied')

    monkeypatch.setattr(writer, '_write_dataframe', failing_write)
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    with pytest.raises(IOError) as exc_info:
        await writer.write_to_parquet([{'a': 1}], tmp_path / 'out.parquet')

    assert 'Permission denied' in str(exc_info.value)


@pytest.mark.asyncio
async def test_parquet_writer_propagates_unexpected_exception(
    monkeypatch, tmp_path
):
    monitor = WriterResourceMonitor([ResourceState.HEALTHY])
    writer = ParquetWriterB3(resource_monitor=monitor)

    def failing_write(*_args, **_kwargs):
        raise RuntimeError('unexpected')

    monkeypatch.setattr(writer, '_write_dataframe', failing_write)
    monkeypatch.setattr(ParquetWriterB3, '_check_disk_space', lambda *_: None)

    with pytest.raises(RuntimeError):
        await writer.write_to_parquet([{'a': 1}], tmp_path / 'out.parquet')
