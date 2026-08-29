"""Merge temporary B3 Parquet artifacts while limiting memory use."""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq  # type: ignore

from .....core import get_logger
from .....macro_exceptions import ExtractionError, ParquetWriteError

logger = get_logger(__name__)


def _remove_temp_file(temp_file: Path) -> None:
    """Remove one merged temporary file without aborting a valid merge."""
    try:
        temp_file.unlink()
        logger.debug(f'Deleted temporary file: {temp_file.name}')
    except OSError:
        logger.warning(
            'Failed to delete temp file %s', temp_file.name, exc_info=True
        )


async def _check_merge_resources(
    total_rows: int,
    check_resources: Callable[[], Awaitable[None]],
) -> None:
    """Check resources at the established cumulative row boundary."""
    if total_rows > 0 and total_rows % 500_000 == 0:
        await check_resources()


async def _write_temp_parquet(
    writer: Any,
    temp_file: Path,
    *,
    index: int,
    file_count: int,
    total_rows: int,
    check_resources: Callable[[], Awaitable[None]],
) -> int:
    """Stream one temporary Parquet into the merge writer."""
    logger.debug(f'Merging file {index}/{file_count}: {temp_file.name}')
    parquet_file = pq.ParquetFile(str(temp_file))
    file_rows = 0
    for batch in parquet_file.iter_batches(batch_size=200_000):
        writer.write_batch(batch)
        file_rows += batch.num_rows
        total_rows += batch.num_rows

    logger.debug(
        f'Merged {file_rows:,} rows from {temp_file.name}',
        extra={'cumulative_rows': total_rows},
    )
    _remove_temp_file(temp_file)
    await _check_merge_resources(total_rows, check_resources)
    return total_rows


def _cleanup_path(path: Path) -> None:
    """Best-effort cleanup one merge artifact with observable failures."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning(
            'Failed to clean up merge artifact %s', path, exc_info=True
        )


def _cleanup_failed_merge(temp_merge: Path, temp_files: list[Path]) -> None:
    """Remove the intermediate output and all remaining temporary inputs."""
    _cleanup_path(temp_merge)
    for temp_file in temp_files:
        _cleanup_path(temp_file)


async def merge_temp_files_streaming(
    temp_files: list[Path],
    final_output: Path,
    *,
    check_resources: Callable[[], Awaitable[None]],
) -> int:
    """Merge temporary parquet files without loading all rows into memory."""
    if not temp_files:
        logger.warning('No temporary files to merge')
        return 0

    if len(temp_files) == 1:
        logger.info('Only one temp file, replacing final output')
        temp_files[0].replace(final_output)
        return count_parquet_rows(final_output)

    logger.info(
        f'Merging {len(temp_files)} temporary files using streaming',
        extra={
            'temp_files': [f.name for f in temp_files],
            'final_output': str(final_output),
        },
    )

    temp_merge = final_output.with_suffix('.parquet.merge_tmp')

    try:
        first_file = pq.ParquetFile(str(temp_files[0]))
        schema = first_file.schema_arrow

        writer = pq.ParquetWriter(
            str(temp_merge),
            schema,
            compression='zstd',
            compression_level=3,
        )

        total_rows = 0

        for index, temp_file in enumerate(temp_files, 1):
            total_rows = await _write_temp_parquet(
                writer,
                temp_file,
                index=index,
                file_count=len(temp_files),
                total_rows=total_rows,
                check_resources=check_resources,
            )

        writer.close()

        temp_merge.replace(final_output)

        logger.info(
            'Merge completed successfully',
            extra={
                'total_rows': f'{total_rows:,}',
                'output_file': str(final_output),
                'files_merged': len(temp_files),
            },
        )

        return total_rows

    except Exception as error:
        logger.exception('Failed to merge temporary files')
        _cleanup_failed_merge(temp_merge, temp_files)
        raise ParquetWriteError(
            str(final_output), f'Merge operation failed: {error}'
        ) from error


def count_parquet_rows(path: Path) -> int:
    """Count rows in parquet file without loading rows into memory."""
    try:
        parquet_file = pq.ParquetFile(str(path))
        result: int = parquet_file.metadata.num_rows
        return result
    except Exception as error:
        logger.exception('Error counting rows in %s', path)
        raise ExtractionError(
            str(path), f'Failed to read rows count: {error}'
        ) from error
