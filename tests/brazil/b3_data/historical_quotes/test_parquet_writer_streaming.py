from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer import (
    constants,
    streaming,
)
from globaldatafinance.macro_exceptions import ParquetWriteError

pytestmark = pytest.mark.unit

APPEND_TEMP_SUFFIX = constants.APPEND_TEMP_SUFFIX


def test_require_pyarrow_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(streaming, 'pa', None)
    monkeypatch.setattr(streaming, 'pq', None)

    with pytest.raises(ImportError) as exc_info:
        streaming._require_pyarrow('test feature')

    assert 'pyarrow is required for test feature' in str(exc_info.value)


def test_cleanup_temp_file_handles_existing_and_missing(
    tmp_path: Path,
) -> None:
    temp_file = tmp_path / 'temp.parquet.append_tmp'
    temp_file.write_text('content')
    assert temp_file.exists()

    streaming._cleanup_temp_file(temp_file)
    assert not temp_file.exists()

    # Non-existent file should not raise
    streaming._cleanup_temp_file(temp_file)


def test_create_pyarrow_writer_creates_writer_with_schema(
    tmp_path: Path,
) -> None:
    schema = pa.schema([('col1', pa.int64()), ('col2', pa.string())])
    out_file = tmp_path / 'test_writer.parquet'

    writer = streaming.create_pyarrow_writer(out_file, schema)
    try:
        assert isinstance(writer, pq.ParquetWriter)
    finally:
        writer.close()


def test_copy_parquet_batches_and_write_table_batches(tmp_path: Path) -> None:
    schema = pa.schema([('id', pa.int64()), ('val', pa.string())])
    source_table = pa.table(
        {'id': [1, 2, 3], 'val': ['a', 'b', 'c']}, schema=schema
    )

    source_path = tmp_path / 'source.parquet'
    pq.write_table(source_table, str(source_path))

    dest_path = tmp_path / 'dest.parquet'
    writer = streaming.create_pyarrow_writer(dest_path, schema)

    source_parquet = pq.ParquetFile(str(source_path))
    copied_rows = streaming.copy_parquet_batches(source_parquet, writer)
    assert copied_rows == 3

    append_table = pa.table({'id': [4, 5], 'val': ['d', 'e']}, schema=schema)
    appended_rows = streaming.write_table_batches(append_table, writer)
    assert appended_rows == 2

    writer.close()

    result_parquet = pq.ParquetFile(str(dest_path))
    assert result_parquet.metadata.num_rows == 5


def test_cast_table_to_schema_direct_match() -> None:
    schema = pa.schema([('id', pa.int64()), ('val', pa.float64())])
    table = pa.table({'id': [1, 2], 'val': [1.5, 2.5]}, schema=schema)

    result = streaming.cast_table_to_schema(table, schema)
    assert result.schema == schema
    assert result.num_rows == 2


def test_cast_table_to_schema_fallback_column_by_column() -> None:
    target_schema = pa.schema([('id', pa.int64()), ('val', pa.float64())])
    table = pa.table({'id': [1, 2], 'val': [10, 20]})

    # Simulate table.cast failing so column-by-column fallback is exercised.
    mock_table = MagicMock()
    mock_table.cast.side_effect = pa.ArrowException('Direct cast failed')
    mock_table.column.side_effect = lambda idx: table.column(idx)

    result = streaming.cast_table_to_schema(mock_table, target_schema)
    assert result.schema == target_schema
    assert result.num_rows == 2


def test_cast_table_to_schema_incompatible_column_raises() -> None:
    target_schema = pa.schema([('id', pa.int64()), ('val', pa.int64())])
    # Non-numeric string cannot be cast to int64
    table = pa.table({'id': [1, 2], 'val': ['invalid_number', 'another_bad']})

    with pytest.raises(ParquetWriteError) as exc_info:
        streaming.cast_table_to_schema(table, target_schema)

    assert 'schema_cast' in str(exc_info.value)
    assert 'Could not cast column' in str(exc_info.value)


@pytest.mark.asyncio
async def test_append_with_streaming_success(tmp_path: Path) -> None:
    output_path = tmp_path / 'quotes.parquet'
    initial_table = pa.table({'id': [1, 2], 'name': ['PETR4', 'VALE3']})
    pq.write_table(initial_table, str(output_path))

    new_df = pl.DataFrame({'id': [3, 4], 'name': ['ITUB4', 'BBDC4']})

    await streaming.append_with_streaming(
        new_df,
        output_path,
        cast_table_to_schema_fn=streaming.cast_table_to_schema,
        create_pyarrow_writer_fn=streaming.create_pyarrow_writer,
        copy_parquet_batches_fn=streaming.copy_parquet_batches,
        write_table_batches_fn=streaming.write_table_batches,
    )

    result_parquet = pq.ParquetFile(str(output_path))
    assert result_parquet.metadata.num_rows == 4
    temp_path = output_path.with_suffix(APPEND_TEMP_SUFFIX)
    assert not temp_path.exists()


@pytest.mark.asyncio
async def test_append_with_streaming_failure_cleans_up_and_raises(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / 'quotes_fail.parquet'
    initial_table = pa.table({'id': [1, 2], 'name': ['PETR4', 'VALE3']})
    pq.write_table(initial_table, str(output_path))

    new_df = pl.DataFrame({'id': [3, 4], 'name': ['ITUB4', 'BBDC4']})

    def failing_writer(*_args, **_kwargs):
        raise RuntimeError('Disk write simulated failure')

    with pytest.raises(ParquetWriteError) as exc_info:
        await streaming.append_with_streaming(
            new_df,
            output_path,
            cast_table_to_schema_fn=streaming.cast_table_to_schema,
            create_pyarrow_writer_fn=failing_writer,
            copy_parquet_batches_fn=streaming.copy_parquet_batches,
            write_table_batches_fn=streaming.write_table_batches,
        )

    assert 'Streaming append failed' in str(exc_info.value)
    temp_path = output_path.with_suffix(APPEND_TEMP_SUFFIX)
    assert not temp_path.exists()


@pytest.mark.asyncio
async def test_merge_parquet_files_streaming_empty_sources(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / 'merged_empty.parquet'

    await streaming.merge_parquet_files_streaming(
        [],
        output_path,
        create_pyarrow_writer_fn=streaming.create_pyarrow_writer,
        copy_parquet_batches_fn=streaming.copy_parquet_batches,
    )

    assert not output_path.exists()


@pytest.mark.asyncio
async def test_merge_parquet_files_streaming_multiple_sources(
    tmp_path: Path,
) -> None:
    schema = pa.schema([('id', pa.int64()), ('symbol', pa.string())])

    file1 = tmp_path / 'chunk_1.parquet'
    file2 = tmp_path / 'chunk_2.parquet'
    file3 = tmp_path / 'chunk_3.parquet'

    pq.write_table(
        pa.table({'id': [1, 2], 'symbol': ['A', 'B']}, schema=schema),
        str(file1),
    )
    pq.write_table(
        pa.table({'id': [3], 'symbol': ['C']}, schema=schema), str(file2)
    )
    pq.write_table(
        pa.table({'id': [4, 5, 6], 'symbol': ['D', 'E', 'F']}, schema=schema),
        str(file3),
    )

    output_path = tmp_path / 'final_merged.parquet'

    await streaming.merge_parquet_files_streaming(
        [file1, file2, file3],
        output_path,
        create_pyarrow_writer_fn=streaming.create_pyarrow_writer,
        copy_parquet_batches_fn=streaming.copy_parquet_batches,
    )

    assert output_path.exists()
    result_parquet = pq.ParquetFile(str(output_path))
    assert result_parquet.metadata.num_rows == 6
    temp_path = output_path.with_suffix(APPEND_TEMP_SUFFIX)
    assert not temp_path.exists()


@pytest.mark.asyncio
async def test_merge_parquet_files_streaming_failure_cleans_up_and_raises(
    tmp_path: Path,
) -> None:
    schema = pa.schema([('id', pa.int64())])
    file1 = tmp_path / 'chunk_1.parquet'
    pq.write_table(pa.table({'id': [1, 2]}, schema=schema), str(file1))

    output_path = tmp_path / 'final_merged_fail.parquet'

    def failing_copy(*_args, **_kwargs):
        raise RuntimeError('Simulated read failure during batch copy')

    with pytest.raises(ParquetWriteError) as exc_info:
        await streaming.merge_parquet_files_streaming(
            [file1],
            output_path,
            create_pyarrow_writer_fn=streaming.create_pyarrow_writer,
            copy_parquet_batches_fn=failing_copy,
        )

    assert 'Streaming merge failed' in str(exc_info.value)
    temp_path = output_path.with_suffix(APPEND_TEMP_SUFFIX)
    assert not temp_path.exists()
