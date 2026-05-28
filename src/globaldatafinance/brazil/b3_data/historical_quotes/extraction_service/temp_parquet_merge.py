import contextlib
from collections.abc import Awaitable, Callable
from pathlib import Path

import pyarrow.parquet as pq  # type: ignore

from .....core import get_logger

logger = get_logger(__name__)


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
            logger.debug(
                f'Merging file {index}/{len(temp_files)}: {temp_file.name}'
            )

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

            try:
                temp_file.unlink()
                logger.debug(f'Deleted temporary file: {temp_file.name}')
            except Exception as e:
                logger.warning(
                    f'Failed to delete temp file {temp_file.name}: {e}'
                )

            if total_rows % 500_000 == 0 and total_rows > 0:
                await check_resources()

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

    except Exception as e:
        logger.error(
            f'Failed to merge temporary files: {e}',
            exc_info=True,
        )

        if temp_merge.exists():
            with contextlib.suppress(Exception):
                temp_merge.unlink()

        for temp_file in temp_files:
            if temp_file.exists():
                with contextlib.suppress(Exception):
                    temp_file.unlink()

        raise OSError(f'Merge operation failed: {e}') from e


def count_parquet_rows(path: Path) -> int:
    """Count rows in parquet file without loading rows into memory."""
    try:
        parquet_file = pq.ParquetFile(str(path))
        result: int = parquet_file.metadata.num_rows
        return result
    except Exception as e:
        logger.error(f'Error counting rows in {path}: {e}')
        return 0
