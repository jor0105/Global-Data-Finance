"""PyArrow streaming helpers for bounded B3 Parquet operations."""

import contextlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .....core import get_logger
from .....macro_exceptions import ParquetWriteError
from .constants import (
    APPEND_TEMP_SUFFIX,
    PARQUET_COMPRESSION,
    PARQUET_COMPRESSION_LEVEL,
    STREAM_BATCH_SIZE,
)

logger = get_logger(__name__)


def _cleanup_temp_file(temp_path: Path) -> None:
    if temp_path.exists():
        with contextlib.suppress(Exception):
            temp_path.unlink()


def create_pyarrow_writer(path: Path, schema: Any) -> Any:
    """Create a compressed PyArrow writer for one Parquet output path."""
    return pq.ParquetWriter(
        str(path),
        schema,
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
    )


def copy_parquet_batches(parquet_file: Any, writer: Any) -> int:
    """Copy bounded record batches and return the number of rows written."""
    total_rows = 0
    for batch in parquet_file.iter_batches(batch_size=STREAM_BATCH_SIZE):
        writer.write_batch(batch)
        total_rows += batch.num_rows
    return total_rows


def write_table_batches(table: Any, writer: Any) -> int:
    """Write bounded table batches and return the number of rows written."""
    total_rows = 0
    for batch in table.to_batches(max_chunksize=STREAM_BATCH_SIZE):
        writer.write_batch(batch)
        total_rows += batch.num_rows
    return total_rows


def cast_table_to_schema(table: Any, schema: Any) -> Any:
    """Cast a table to the existing output schema with column fallback."""
    try:
        return table.cast(schema)
    except (pa.ArrowException, TypeError, ValueError) as cast_error:
        logger.warning(
            'Schema cast failed, attempting column-by-column cast: %s',
            cast_error,
            exc_info=True,
        )
        arrays = []
        for index, field in enumerate(schema):
            try:
                arrays.append(table.column(index).cast(field.type))
            except (pa.ArrowException, TypeError, ValueError) as col_err:
                logger.error(
                    'Could not cast column %s to %s: %s',
                    field.name,
                    field.type,
                    col_err,
                    exc_info=True,
                )
                raise ParquetWriteError(
                    'schema_cast',
                    f"Could not cast column '{field.name}' to "
                    f"'{field.type}': {col_err}",
                ) from col_err
        return pa.table(arrays, schema=schema)


async def append_with_streaming(
    new_df: Any,
    output_path: Path,
    *,
    cast_table_to_schema_fn: Callable[[Any, Any], Any],
    create_pyarrow_writer_fn: Callable[[Path, Any], Any],
    copy_parquet_batches_fn: Callable[[Any, Any], int],
    write_table_batches_fn: Callable[[Any, Any], int],
) -> None:
    """Append a new table to an existing Parquet file through a temp file."""
    logger.debug(
        'Using streaming append for memory efficiency',
        extra={
            'new_rows': new_df.height,
            'existing_file': str(output_path),
        },
    )

    temp_path = output_path.with_suffix(APPEND_TEMP_SUFFIX)
    writer = None

    try:
        existing_parquet = pq.ParquetFile(str(output_path))
        schema = existing_parquet.schema_arrow
        new_table = cast_table_to_schema_fn(new_df.to_arrow(), schema)
        writer = create_pyarrow_writer_fn(temp_path, schema)

        total_rows_copied = copy_parquet_batches_fn(existing_parquet, writer)
        logger.debug('Copied %s existing rows', total_rows_copied)

        new_rows_written = write_table_batches_fn(new_table, writer)
        logger.debug('Appended %s new rows', new_rows_written)

        writer.close()
        writer = None
        temp_path.replace(output_path)

        logger.debug(
            'Streaming append completed successfully',
            extra={
                'total_rows': total_rows_copied + new_rows_written,
                'output_file': str(output_path),
            },
        )
    except Exception as exc:
        _cleanup_temp_file(temp_path)
        logger.error(
            'Streaming append failed: %s',
            exc,
            extra={'output_path': str(output_path)},
            exc_info=True,
        )
        raise ParquetWriteError(
            str(output_path), f'Streaming append failed: {exc}'
        ) from exc
    finally:
        if writer is not None:
            with contextlib.suppress(Exception):
                writer.close()
        _cleanup_temp_file(temp_path)


async def merge_parquet_files_streaming(
    source_paths: list[Path],
    output_path: Path,
    *,
    create_pyarrow_writer_fn: Callable[[Path, Any], Any],
    copy_parquet_batches_fn: Callable[[Any, Any], int],
) -> None:
    """Merge source Parquet files into one output using bounded batches."""
    if not source_paths:
        logger.warning('No parquet chunk files to merge')
        return

    temp_path = output_path.with_suffix(APPEND_TEMP_SUFFIX)
    writer = None

    try:
        first_file = pq.ParquetFile(str(source_paths[0]))
        schema = first_file.schema_arrow
        writer = create_pyarrow_writer_fn(temp_path, schema)

        total_rows = copy_parquet_batches_fn(first_file, writer)
        for source_path in source_paths[1:]:
            parquet_file = pq.ParquetFile(str(source_path))
            total_rows += copy_parquet_batches_fn(parquet_file, writer)

        writer.close()
        writer = None
        temp_path.replace(output_path)

        logger.debug(
            'Streaming merge completed successfully',
            extra={
                'source_files': len(source_paths),
                'total_rows': total_rows,
                'output_file': str(output_path),
            },
        )
    except Exception as exc:
        _cleanup_temp_file(temp_path)
        logger.error(
            'Streaming merge failed: %s',
            exc,
            extra={'output_path': str(output_path)},
            exc_info=True,
        )
        raise ParquetWriteError(
            str(output_path), f'Streaming merge failed: {exc}'
        ) from exc
    finally:
        if writer is not None:
            with contextlib.suppress(Exception):
                writer.close()
        _cleanup_temp_file(temp_path)
