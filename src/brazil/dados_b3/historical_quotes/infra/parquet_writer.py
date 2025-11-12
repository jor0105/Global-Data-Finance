import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import polars as pl
except ImportError:
    pl = None  # type: ignore

try:
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore
except ImportError:
    pa = None  # type: ignore
    pq = None  # type: ignore

from src.core import ResourceMonitor, ResourceState, get_logger
from src.macro_exceptions import DiskFullError

logger = get_logger(__name__)


class ParquetWriter:
    """Writer for saving data to Parquet format using Polars with memory safety.

    Features:
    - ZSTD compression for optimal file size
    - Statistics for query optimization
    - Disk space validation before writing
    - Memory-aware append mode with streaming for large datasets
    - Automatic memory check before concatenation
    - Resource monitoring integration

    Raises:
        ImportError: If polars is not installed
    """

    # Minimum free space required (in bytes) - 100MB
    MIN_FREE_SPACE_MB = 100
    MIN_FREE_SPACE_BYTES = MIN_FREE_SPACE_MB * 1024 * 1024

    # Maximum rows to hold in memory before forcing streaming write
    MAX_ROWS_IN_MEMORY = 500_000

    def __init__(self, resource_monitor: Optional[ResourceMonitor] = None):
        if pl is None:
            raise ImportError(
                "polars is required for ParquetWriter. "
                "Install it with: pip install polars"
            )

        self.resource_monitor = resource_monitor or ResourceMonitor()
        logger.debug("ParquetWriter initialized with memory-safe optimizations")

    @staticmethod
    def _check_disk_space(path: Path, estimated_size_mb: float = 0) -> None:
        """Check if sufficient disk space is available.

        Args:
            path: Path where file will be written
            estimated_size_mb: Estimated size of data to write in MB

        Raises:
            DiskFullError: If insufficient disk space
        """
        # Get disk usage statistics
        stat = shutil.disk_usage(path.parent)
        free_space_mb = stat.free / 1024 / 1024

        # Calculate required space (estimated + minimum buffer)
        required_space_mb = estimated_size_mb + ParquetWriter.MIN_FREE_SPACE_MB

        if free_space_mb < required_space_mb:
            logger.error(
                "Insufficient disk space",
                extra={
                    "free_space_mb": f"{free_space_mb:.2f}",
                    "required_space_mb": f"{required_space_mb:.2f}",
                    "path": str(path),
                },
            )
            raise DiskFullError(str(path))

        logger.debug(
            "Disk space check passed",
            extra={
                "free_space_mb": f"{free_space_mb:.2f}",
                "required_space_mb": f"{required_space_mb:.2f}",
            },
        )

    async def write_to_parquet(
        self,
        data: List[Dict[str, Any]],
        output_path: Path,
        partition_cols: Optional[List[str]] = None,
        mode: str = "overwrite",
    ) -> None:
        """Write data to Parquet format with memory safety.

        Args:
            data: List of dictionaries containing parsed quote data
            output_path: Path where to save the Parquet file(s)
            partition_cols: Optional list of columns to partition by
            mode: Write mode - 'overwrite' or 'append'. Default is 'overwrite'

        Raises:
            IOError: If unable to write to disk
            DiskFullError: If insufficient disk space
            MemoryError: If insufficient memory for operation
        """
        if not data:
            logger.warning("No data to write to Parquet")
            return

        logger.info(
            "Writing data to Parquet",
            extra={
                "record_count": len(data),
                "output_path": str(output_path),
                "partition_cols": partition_cols,
                "mode": mode,
            },
        )

        try:
            # Check memory state before creating DataFrame
            memory_state = self.resource_monitor.check_resources()
            if memory_state == ResourceState.EXHAUSTED:
                raise MemoryError("Insufficient memory to create DataFrame")

            df = pl.DataFrame(data)

            estimated_size_mb = df.estimated_size() / 1024 / 1024

            logger.debug(
                "Created Polars DataFrame",
                extra={
                    "rows": df.height,
                    "columns": df.width,
                    "memory_mb": f"{estimated_size_mb:.2f}",
                },
            )

            self._check_disk_space(output_path, estimated_size_mb)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Handle append mode with memory-safe concatenation
            if mode == "append" and output_path.exists():
                logger.debug(f"Appending to existing Parquet file: {output_path}")

                # Check memory before reading existing file
                memory_state = self.resource_monitor.check_resources()
                if memory_state in (ResourceState.CRITICAL, ResourceState.EXHAUSTED):
                    # Use streaming approach for low memory
                    await self._append_with_streaming(df, output_path)
                else:
                    # Standard concatenation for adequate memory
                    await self._append_with_concat(df, output_path)
            else:
                # Direct write for overwrite mode
                await self._write_dataframe(df, output_path)

            # Get file size
            file_size_mb = output_path.stat().st_size / 1024 / 1024

            logger.info(
                "Successfully wrote Parquet file",
                extra={
                    "output_path": str(output_path),
                    "file_size_mb": f"{file_size_mb:.2f}",
                    "records": df.height,
                    "mode": mode,
                },
            )

        except OSError as e:
            if "No space left on device" in str(e):
                logger.error(
                    "Insufficient disk space",
                    extra={"output_path": str(output_path)},
                    exc_info=True,
                )
                raise DiskFullError(str(output_path))

            logger.error(
                "Failed to write Parquet file",
                extra={
                    "output_path": str(output_path),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise IOError(f"Failed to write Parquet file: {e}")
        except MemoryError:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error writing Parquet file",
                extra={
                    "output_path": str(output_path),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def _write_dataframe(self, df: "pl.DataFrame", output_path: Path) -> None:
        """Write DataFrame to Parquet with optimal settings.

        Args:
            df: Polars DataFrame to write
            output_path: Output file path
        """
        df.write_parquet(
            str(output_path),
            compression="zstd",
            compression_level=3,
            statistics=True,
            use_pyarrow=False,
        )

    async def _append_with_concat(
        self, new_df: "pl.DataFrame", output_path: Path
    ) -> None:
        """Append data using concatenation (for adequate memory).

        Args:
            new_df: New DataFrame to append
            output_path: Path to existing Parquet file
        """
        try:
            existing_df = pl.read_parquet(str(output_path))

            logger.debug(
                "Concatenating with existing data",
                extra={
                    "previous_rows": existing_df.height,
                    "new_rows": new_df.height,
                },
            )

            combined_df = pl.concat([existing_df, new_df], how="vertical")

            logger.debug(f"Combined DataFrame has {combined_df.height} rows")

            await self._write_dataframe(combined_df, output_path)

        except Exception as e:
            logger.error(f"Error in concat-based append: {e}")
            logger.info("Falling back to streaming append")
            await self._append_with_streaming(new_df, output_path)

    async def _append_with_streaming(
        self, new_df: "pl.DataFrame", output_path: Path
    ) -> None:
        """Append data using PyArrow streaming (for low memory).

        This approach reads existing file in batches and writes incrementally.

        Args:
            new_df: New DataFrame to append
            output_path: Path to existing Parquet file
        """
        if pa is None or pq is None:
            raise ImportError(
                "pyarrow is required for streaming append. "
                "Install it with: pip install pyarrow"
            )

        logger.debug("Using streaming append for memory efficiency")

        # Create temporary file for atomic write
        temp_path = output_path.with_suffix(".parquet.tmp")

        try:
            # Convert new DataFrame to Arrow table
            new_table = new_df.to_arrow()

            # Open existing file
            existing_parquet = pq.ParquetFile(str(output_path))

            # Create writer for temp file
            writer = None

            # Stream existing data in batches
            for batch in existing_parquet.iter_batches(batch_size=50_000):
                if writer is None:
                    # Initialize writer with schema from first batch
                    writer = pq.ParquetWriter(
                        str(temp_path),
                        batch.schema,
                        compression="zstd",
                        compression_level=3,
                    )
                writer.write_batch(batch)

            # Write new data
            if writer is not None:
                for batch in new_table.to_batches(max_chunksize=50_000):
                    writer.write_batch(batch)
                writer.close()
            else:
                # No existing data, just write new data
                pq.write_table(
                    new_table,
                    str(temp_path),
                    compression="zstd",
                    compression_level=3,
                )

            temp_path.replace(output_path)

            logger.debug("Streaming append completed successfully")

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Streaming append failed: {e}")
        finally:
            # Ensure temp file is cleaned up
            if temp_path.exists():
                temp_path.unlink()
