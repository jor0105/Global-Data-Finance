"""High-level Parquet writer for B3 historical quote records."""

import gc
import tempfile
from pathlib import Path
from typing import Any

try:
    import polars as pl
except ImportError:
    pl = None  # type: ignore[assignment]

from .....core import ResourceMonitor, ResourceState, get_logger
from .....macro_exceptions import DiskFullError, ParquetWriteError
from .constants import (
    CHUNK_RECORD_COUNT,
    MEMORY_SPLIT_RECORD_THRESHOLD,
    PARQUET_COMPRESSION,
    PARQUET_COMPRESSION_LEVEL,
)
from .disk import check_disk_space
from .schema import get_schema_overrides
from .streaming import (
    append_with_streaming,
    cast_table_to_schema,
    copy_parquet_batches,
    create_pyarrow_writer,
    merge_parquet_files_streaming,
    write_table_batches,
)

logger = get_logger(__name__)


class ParquetWriterB3:
    """Writer for saving B3 historical quotes in Parquet format."""

    MIN_FREE_SPACE_MB = 100

    def __init__(self, resource_monitor: ResourceMonitor | None = None):
        """Initialize the writer with an optional resource monitor."""
        if pl is None:
            raise ImportError(
                'polars is required for ParquetWriterB3. '
                'Install it with: pip install polars'
            )

        self.resource_monitor = resource_monitor or ResourceMonitor()
        logger.debug(
            'ParquetWriterB3 initialized with memory-safe optimizations'
        )

    @staticmethod
    def _get_schema_overrides() -> dict[str, Any]:
        return get_schema_overrides(pl)

    @staticmethod
    def _check_disk_space(path: Path, estimated_size_mb: float = 0) -> None:
        check_disk_space(
            path=path,
            estimated_size_mb=estimated_size_mb,
            min_free_space_mb=ParquetWriterB3.MIN_FREE_SPACE_MB,
        )

    async def write_to_parquet(
        self,
        data: list[dict[str, Any]],
        output_path: Path,
        mode: str = 'overwrite',
    ) -> None:
        """Write records using overwrite or append semantics as requested."""
        if not data:
            logger.warning('No data to write to Parquet')
            return

        logger.info(
            'Writing data to Parquet',
            extra={
                'record_count': len(data),
                'output_path': str(output_path),
                'mode': mode,
            },
        )

        try:
            memory_state = self.resource_monitor.check_resources()
            if (
                memory_state
                in (ResourceState.CRITICAL, ResourceState.EXHAUSTED)
                and len(data) > MEMORY_SPLIT_RECORD_THRESHOLD
            ):
                logger.warning(
                    'Memory %s with %s records - splitting write',
                    memory_state.value,
                    len(data),
                )
                await self._write_in_chunks(data, output_path, mode)
                return

            memory_state = self.resource_monitor.check_resources()
            if memory_state == ResourceState.EXHAUSTED:
                logger.warning(
                    'Memory exhausted before DataFrame creation; '
                    'attempting recovery'
                )
                gc.collect()

                memory_state = self.resource_monitor.check_resources()
                if memory_state == ResourceState.EXHAUSTED:
                    estimated_memory_needed_mb = (
                        self._estimate_memory_needed_mb(len(data))
                    )
                    logger.error(
                        'Insufficient memory after cleanup attempt',
                        extra={
                            'records': len(data),
                            'estimated_memory_mb': (
                                f'{estimated_memory_needed_mb:.2f}'
                            ),
                            'memory_state': memory_state.value,
                        },
                    )
                    raise MemoryError(
                        'Insufficient memory to create DataFrame with '
                        f'{len(data)} records. Estimated memory needed: '
                        f'{estimated_memory_needed_mb:.2f}MB'
                    )

            df = self._create_dataframe(data)
            await self._persist_dataframe(df, output_path, mode)

            file_size_mb = output_path.stat().st_size / 1024 / 1024
            logger.info(
                'Successfully wrote Parquet file',
                extra={
                    'output_path': str(output_path),
                    'file_size_mb': f'{file_size_mb:.2f}',
                    'records': df.height,
                    'mode': mode,
                },
            )
        except OSError as exc:
            if 'No space left on device' in str(exc):
                logger.error(
                    'Insufficient disk space',
                    extra={'output_path': str(output_path)},
                    exc_info=True,
                )
                raise DiskFullError(str(output_path)) from exc

            logger.error(
                'Failed to write Parquet file',
                extra={
                    'output_path': str(output_path),
                    'error': str(exc),
                },
                exc_info=True,
            )
            raise ParquetWriteError(str(output_path), str(exc)) from exc
        except MemoryError:
            raise
        except Exception as exc:
            logger.error(
                'Unexpected error writing Parquet file',
                extra={
                    'output_path': str(output_path),
                    'error': str(exc),
                },
                exc_info=True,
            )
            raise

    def _write_dataframe(self, df: 'pl.DataFrame', output_path: Path) -> None:
        df.write_parquet(
            str(output_path),
            compression=PARQUET_COMPRESSION,
            compression_level=PARQUET_COMPRESSION_LEVEL,
            statistics=True,
            use_pyarrow=False,
        )

    async def _write_in_chunks(
        self,
        data: list[dict[str, Any]],
        output_path: Path,
        mode: str = 'overwrite',
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        total_chunks = (
            len(data) + CHUNK_RECORD_COUNT - 1
        ) // CHUNK_RECORD_COUNT

        logger.info(
            'Writing %s records in %s chunks of %s',
            len(data),
            total_chunks,
            CHUNK_RECORD_COUNT,
        )

        with tempfile.TemporaryDirectory(
            prefix=f'{output_path.stem}_',
            suffix='_chunks',
            dir=output_path.parent,
        ) as temp_dir:
            temp_paths: list[Path] = []

            for start in range(0, len(data), CHUNK_RECORD_COUNT):
                chunk = data[start : start + CHUNK_RECORD_COUNT]
                chunk_num = (start // CHUNK_RECORD_COUNT) + 1
                chunk_path = Path(temp_dir) / f'part-{chunk_num:05d}.parquet'

                logger.debug('Writing chunk %s/%s', chunk_num, total_chunks)

                try:
                    df = self._create_dataframe(chunk)
                    await self._persist_dataframe(
                        df, chunk_path, mode='overwrite'
                    )
                    temp_paths.append(chunk_path)

                    del df
                    del chunk
                    gc.collect()
                except Exception as exc:
                    logger.error(
                        'Failed to write chunk %s/%s: %s',
                        chunk_num,
                        total_chunks,
                        exc,
                        exc_info=True,
                    )
                    raise

            if mode == 'append' and output_path.exists():
                sources = [output_path, *temp_paths]
                await self._merge_parquet_files_streaming(sources, output_path)
            elif len(temp_paths) == 1:
                temp_paths[0].replace(output_path)
            else:
                await self._merge_parquet_files_streaming(
                    temp_paths, output_path
                )

        logger.info('Successfully wrote all %s chunks', total_chunks)

    def _create_dataframe(self, data: list[dict[str, Any]]) -> 'pl.DataFrame':
        df = pl.DataFrame(data, schema_overrides=self._get_schema_overrides())
        estimated_size_mb = df.estimated_size() / 1024 / 1024

        logger.debug(
            'Created Polars DataFrame',
            extra={
                'rows': df.height,
                'columns': df.width,
                'memory_mb': f'{estimated_size_mb:.2f}',
            },
        )
        return df

    async def _persist_dataframe(
        self,
        df: 'pl.DataFrame',
        output_path: Path,
        mode: str,
    ) -> None:
        estimated_size_mb = df.estimated_size() / 1024 / 1024
        self._check_disk_space(output_path, estimated_size_mb)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if mode == 'append' and output_path.exists():
            logger.debug('Appending to existing Parquet file: %s', output_path)
            await self._append_with_streaming(df, output_path)
            return

        self._write_dataframe(df, output_path)

    @staticmethod
    def _estimate_memory_needed_mb(record_count: int) -> float:
        return record_count * 0.001

    async def _append_with_streaming(
        self, new_df: 'pl.DataFrame', output_path: Path
    ) -> None:
        await append_with_streaming(
            new_df,
            output_path,
            cast_table_to_schema_fn=self._cast_table_to_schema,
            create_pyarrow_writer_fn=self._create_pyarrow_writer,
            copy_parquet_batches_fn=self._copy_parquet_batches,
            write_table_batches_fn=self._write_table_batches,
        )

    async def _merge_parquet_files_streaming(
        self, source_paths: list[Path], output_path: Path
    ) -> None:
        await merge_parquet_files_streaming(
            source_paths,
            output_path,
            create_pyarrow_writer_fn=self._create_pyarrow_writer,
            copy_parquet_batches_fn=self._copy_parquet_batches,
        )

    @staticmethod
    def _create_pyarrow_writer(path: Path, schema: Any) -> Any:
        return create_pyarrow_writer(path, schema)

    @staticmethod
    def _copy_parquet_batches(parquet_file: Any, writer: Any) -> int:
        return copy_parquet_batches(parquet_file, writer)

    @staticmethod
    def _write_table_batches(table: Any, writer: Any) -> int:
        return write_table_batches(table, writer)

    @staticmethod
    def _cast_table_to_schema(table: Any, schema: Any) -> Any:
        return cast_table_to_schema(table, schema)
