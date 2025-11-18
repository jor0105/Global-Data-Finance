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

from .....core import ResourceMonitor, ResourceState, get_logger
from .....macro_exceptions import DiskFullError

logger = get_logger(__name__)


class ParquetWriterB3:
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

    # Minimum free space required (in MB)
    MIN_FREE_SPACE_MB = 100

    def __init__(self, resource_monitor: Optional[ResourceMonitor] = None):
        if pl is None:
            raise ImportError(
                "polars is required for ParquetWriterB3. "
                "Install it with: pip install polars"
            )

        self.resource_monitor = resource_monitor or ResourceMonitor()
        logger.debug("ParquetWriterB3 initialized with memory-safe optimizations")

    @staticmethod
    def _get_schema_overrides() -> Dict[str, Any]:
        """Get explicit schema overrides to ensure consistency.

        This prevents Polars from inferring different decimal precisions
        between different batches of data.

        Returns:
            Dictionary with column name -> type mappings
        """
        return {
            # Decimal fields - explicitly set to 2 decimal places
            "preco_abertura": pl.Decimal(precision=38, scale=2),
            "preco_maximo": pl.Decimal(precision=38, scale=2),
            "preco_minimo": pl.Decimal(precision=38, scale=2),
            "preco_medio": pl.Decimal(precision=38, scale=2),
            "preco_fechamento": pl.Decimal(precision=38, scale=2),
            "melhor_oferta_compra": pl.Decimal(precision=38, scale=2),
            "melhor_oferta_venda": pl.Decimal(precision=38, scale=2),
            "volume_total": pl.Decimal(
                precision=38, scale=2
            ),  # ✅ Force 2 decimal places
        }

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
        required_space_mb = estimated_size_mb + ParquetWriterB3.MIN_FREE_SPACE_MB

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
        mode: str = "overwrite",
    ) -> None:
        """Write data to Parquet format with memory safety.

        Args:
            data: List of dictionaries containing parsed quote data
            output_path: Path where to save the Parquet file(s)
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
                "mode": mode,
            },
        )

        # If data is very large and memory is tight, split into smaller chunks
        memory_state = self.resource_monitor.check_resources()
        if (
            memory_state in (ResourceState.CRITICAL, ResourceState.EXHAUSTED)
            and len(data) > 10000
        ):
            logger.warning(
                f"Memory {memory_state.value} with {len(data)} records - splitting write"
            )
            await self._write_in_chunks(data, output_path, mode)
            return

        try:
            # Check memory state before creating DataFrame
            memory_state = self.resource_monitor.check_resources()
            if memory_state == ResourceState.EXHAUSTED:
                logger.warning(
                    "Memory exhausted before DataFrame creation - attempting recovery"
                )
                # Try aggressive cleanup
                import gc

                gc.collect()

                # Re-check after cleanup
                memory_state = self.resource_monitor.check_resources()
                if memory_state == ResourceState.EXHAUSTED:
                    # Before raising, try to estimate how much memory we need
                    estimated_memory_needed_mb = (
                        len(data) * 0.001
                    )  # Very rough estimate: 1KB per record
                    logger.error(
                        "Insufficient memory after cleanup attempt",
                        extra={
                            "records": len(data),
                            "estimated_memory_mb": f"{estimated_memory_needed_mb:.2f}",
                            "memory_state": memory_state.value,
                        },
                    )
                    raise MemoryError(
                        f"Insufficient memory to create DataFrame with {len(data)} records. "
                        f"Estimated memory needed: {estimated_memory_needed_mb:.2f}MB"
                    )

            # Create DataFrame with explicit schema to ensure consistency
            df = pl.DataFrame(data, schema_overrides=self._get_schema_overrides())

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

            # Handle append mode with ALWAYS streaming (never load full parquet in RAM)
            if mode == "append" and output_path.exists():
                logger.debug(f"Appending to existing Parquet file: {output_path}")
                # ALWAYS use streaming to avoid loading entire parquet in memory
                await self._append_with_streaming(df, output_path)
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

    async def _write_in_chunks(
        self, data: List[Dict[str, Any]], output_path: Path, mode: str = "overwrite"
    ) -> None:
        """Write data in smaller chunks to avoid memory issues.

        Args:
            data: List of records to write
            output_path: Output file path
            mode: Write mode ('overwrite' or 'append')
        """
        import gc

        chunk_size = 25000  # Write 25000 records at a time (optimized for performance)
        total_chunks = (len(data) + chunk_size - 1) // chunk_size

        logger.info(
            f"Writing {len(data)} records in {total_chunks} chunks of {chunk_size}"
        )

        current_mode = mode
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            chunk_num = (i // chunk_size) + 1

            logger.debug(f"Writing chunk {chunk_num}/{total_chunks}")

            try:
                df = pl.DataFrame(chunk, schema_overrides=self._get_schema_overrides())

                self._check_disk_space(output_path, df.estimated_size() / 1024 / 1024)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if current_mode == "append" and output_path.exists():
                    await self._append_with_streaming(df, output_path)
                else:
                    await self._write_dataframe(df, output_path)

                # After first chunk is written, switch to append mode
                current_mode = "append"

                # Clean up
                del df
                del chunk
                gc.collect()

            except Exception as e:
                logger.error(
                    f"Failed to write chunk {chunk_num}/{total_chunks}: {e}",
                    exc_info=True,
                )
                raise

        logger.info(f"Successfully wrote all {total_chunks} chunks")

    async def _append_with_streaming(
        self, new_df: "pl.DataFrame", output_path: Path
    ) -> None:
        """Append data using PyArrow streaming (NEVER loads full parquet in RAM).

        This approach reads existing file in batches and writes incrementally,
        ensuring constant memory usage regardless of file size.

        Args:
            new_df: New DataFrame to append
            output_path: Path to existing Parquet file
        """
        if pa is None or pq is None:
            raise ImportError(
                "pyarrow is required for streaming append. "
                "Install it with: pip install pyarrow"
            )

        logger.debug(
            "Using streaming append for memory efficiency",
            extra={
                "new_rows": new_df.height,
                "existing_file": str(output_path),
            },
        )

        # Create temporary file for atomic write
        temp_path = output_path.with_suffix(".parquet.tmp")

        try:
            # Open existing file for streaming read
            existing_parquet = pq.ParquetFile(str(output_path))

            # Get schema from existing file
            schema = existing_parquet.schema_arrow

            # Convert new DataFrame to Arrow table and CAST to existing schema
            new_table = new_df.to_arrow()

            # Cast new table to match existing schema (handles decimal precision differences)
            try:
                new_table = new_table.cast(schema)
            except Exception as cast_error:
                logger.warning(
                    f"Schema cast failed, attempting column-by-column cast: {cast_error}"
                )
                # Fallback: cast each column individually
                arrays = []
                for i, field in enumerate(schema):
                    try:
                        arrays.append(new_table.column(i).cast(field.type))
                    except Exception:
                        # If cast fails, keep original column
                        logger.warning(
                            f"Could not cast column {field.name}, keeping original"
                        )
                        arrays.append(new_table.column(i))
                new_table = pa.table(arrays, schema=schema)

            # Create writer for temp file with existing schema
            writer = pq.ParquetWriterB3(
                str(temp_path),
                schema,
                compression="zstd",
                compression_level=3,
            )

            # Stream existing data in larger batches (200k rows at a time for performance)
            total_rows_copied = 0
            for batch in existing_parquet.iter_batches(batch_size=200_000):
                writer.write_batch(batch)
                total_rows_copied += batch.num_rows

            logger.debug(f"Copied {total_rows_copied} existing rows")

            # Write new data in larger batches
            new_rows_written = 0
            for batch in new_table.to_batches(max_chunksize=200_000):
                writer.write_batch(batch)
                new_rows_written += batch.num_rows

            logger.debug(f"Appended {new_rows_written} new rows")

            # Close writer
            writer.close()

            # Replace original file atomically
            temp_path.replace(output_path)

            logger.debug(
                "Streaming append completed successfully",
                extra={
                    "total_rows": total_rows_copied + new_rows_written,
                    "output_file": str(output_path),
                },
            )

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

            logger.error(
                f"Streaming append failed: {e}",
                extra={"output_path": str(output_path)},
                exc_info=True,
            )
            raise IOError(f"Streaming append failed: {e}")
        finally:
            # Ensure temp file is cleaned up
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
