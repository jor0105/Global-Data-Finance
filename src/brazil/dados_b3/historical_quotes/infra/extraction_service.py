import asyncio
import gc
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Set

from src.core import ResourceMonitor, ResourceState, get_logger, log_execution_time

from ..domain import ProcessingModeEnum
from .cotahist_parser import CotahistParser
from .parquet_writer import ParquetWriter
from .zip_reader import ZipFileReader

logger = get_logger(__name__)


class ExtractionService:
    """Service for extracting data from COTAHIST ZIP files with true chunk-based processing.

    This service implements TRUE STREAMING with incremental flush and memory monitoring:
    - Reads ZIP line by line (streaming)
    - Processes in small batches
    - Monitors RAM usage continuously
    - Writes to temp Parquet files when memory threshold reached OR buffer full
    - Each ZIP writes to unique temp file (prevents race conditions)
    - Final merge of all temp files using streaming
    - Memory usage controlled by batch sizes AND RAM thresholds

    Processing modes:
    - FAST: High concurrency (15 files parallel) + parallel parsing (threads)
           Memory target: ~4.5 GB total (flush at 3GB)
           Batch: 500k records per file
    - SLOW: Low concurrency (3 files parallel) + sequential parsing
           Memory target: ~1.5 GB total (flush at 1GB)
           Batch: 500k records per file (same as FAST for SSD optimization)

    Memory characteristics:
    - Flush triggers: buffer size (500k) OR RAM threshold (3GB/1GB)
    - Each ZIP writes to unique temp file (prevents race conditions)
    - Final streaming merge of temp files (200k batch size)
    - Never loads entire parquet in RAM

    SSD write optimization:
    - Large batches (500k) reduce write amplification on BOTH modes
    - ~12 appends per 6M records file
    - Streaming merge minimizes disk operations
    """

    # Batch sizes optimized for memory and SSD wear
    # Both modes use same flush size for consistent SSD write performance
    # FAST mode: 500k records × 15 files × 3KB/record ≈ 22.5 GB (high performance)
    # SLOW mode: 500k records × 3 files × 3KB/record ≈ 4.5 GB (low resource usage)
    FLUSH_BATCH_SIZE = (
        500_000  # Write every 500k records (both modes) - Minimize SSD writes
    )
    PARSE_BATCH_SIZE = 50_000  # Parse in batches of 50k lines (faster processing)

    # Minimum safe batch sizes
    MIN_FLUSH_BATCH = 50_000
    MIN_PARSE_BATCH = 10_000

    def __init__(
        self,
        zip_reader: ZipFileReader,
        parser: CotahistParser,
        data_writer: ParquetWriter,
        processing_mode: ProcessingModeEnum = ProcessingModeEnum.FAST,
    ):
        """Initialize extraction service with dependencies.

        Args:
            zip_reader: Service for reading ZIP files
            parser: Parser for COTAHIST format
            data_writer: Writer for output data
            processing_mode: Resource consumption strategy
        """
        self.zip_reader = zip_reader
        self.parser = parser
        self.data_writer = data_writer
        self.processing_mode = processing_mode
        self.resource_monitor = ResourceMonitor()

        # Configure concurrency based on mode and available resources
        if processing_mode == ProcessingModeEnum.FAST:
            desired_concurrent_files = (
                15  # Increased from 10 to 15 for better throughput
            )
            desired_workers = None  # Use default (CPU count)
            self.use_parallel_parsing = True
        else:  # SLOW
            desired_concurrent_files = 3  # Increased from 2 to 3
            desired_workers = 2  # Increased from 1 to 2
            self.use_parallel_parsing = False

        self.max_concurrent_files = min(
            desired_concurrent_files,
            self.resource_monitor.get_safe_worker_count(desired_concurrent_files),
        )

        # Determine safe worker count for parallel parsing
        if self.use_parallel_parsing:
            self.max_workers = self.resource_monitor.get_safe_worker_count(
                desired_workers
            )
        else:
            self.max_workers = 1

        # Set batch sizes - SAME for both modes to optimize SSD writes
        # Difference is only in concurrency and parsing strategy
        self.flush_batch_size = self.FLUSH_BATCH_SIZE
        self.parse_batch_size = self.PARSE_BATCH_SIZE

        # Initialize thread pool for parallel parsing (FAST mode only)
        self.executor_pool = None
        if self.use_parallel_parsing:
            self.executor_pool = ThreadPoolExecutor(max_workers=self.max_workers)

        logger.info(
            "ExtractionService initialized",
            extra={
                "processing_mode": str(processing_mode),
                "max_concurrent_files": self.max_concurrent_files,
                "use_parallel_parsing": self.use_parallel_parsing,
                "max_workers": self.max_workers,
                "flush_batch_size": self.flush_batch_size,
                "parse_batch_size": self.parse_batch_size,
                "estimated_memory_per_file_mb": self.flush_batch_size
                * 3
                // 1024,  # ~3KB per record
                "estimated_total_memory_mb": (self.flush_batch_size * 3 // 1024)
                * self.max_concurrent_files,
                "executor_type": (
                    "ThreadPoolExecutor" if self.use_parallel_parsing else "Sequential"
                ),
            },
        )

    def __del__(self):
        """Cleanup executor pool on deletion."""
        if self.executor_pool is not None:
            try:
                self.executor_pool.shutdown(wait=True, cancel_futures=False)
            except Exception:
                # Ignore errors during cleanup (interpreter might be shutting down)
                pass

    async def extract_from_zip_files(
        self, zip_files: Set[str], target_tpmerc_codes: Set[str], output_path: Path
    ) -> Dict[str, Any]:
        """Extract data from multiple ZIP files with true incremental processing.

        Each ZIP file is processed independently with immediate flush to disk.
        No data accumulation across files - constant memory usage.

        Args:
            zip_files: Set of paths to ZIP files
            target_tpmerc_codes: Set of TPMERC codes to filter
            output_path: Path where to save the extracted Parquet file

        Returns:
            Dictionary with extraction statistics (no data arrays)
        """
        self._adjust_batch_sizes()

        logger.info(
            "Starting extraction with incremental flush",
            extra={
                "total_files": len(zip_files),
                "target_codes_count": len(target_tpmerc_codes),
                "output_path": str(output_path),
                "processing_mode": str(self.processing_mode),
                "flush_batch_size": self.flush_batch_size,
                "parse_batch_size": self.parse_batch_size,
            },
        )

        with log_execution_time(
            logger, "Extract from all ZIP files", total_files=len(zip_files)
        ):
            # Statistics only (no data accumulation)
            total_records_written = 0
            success_count = 0
            error_count = 0
            errors = {}
            temp_files: List[Path] = []  # Collect temp files for merge

            semaphore = asyncio.Semaphore(self.max_concurrent_files)

            async def process_single_file(zip_file: str):
                """Process single ZIP file with direct write to temp file."""
                nonlocal success_count, error_count, errors

                # Check resources before processing
                if not await self._wait_for_resources(timeout_seconds=30):
                    error_msg = "Resources exhausted"
                    logger.error(f"Skipping {zip_file} - {error_msg}")
                    return (zip_file, Exception(error_msg))

                async with semaphore:
                    try:
                        # Process and write to temp file (returns dict with records and temp_file)
                        result_data = await self._process_and_write_zip(
                            zip_file=zip_file,
                            target_tpmerc_codes=target_tpmerc_codes,
                            output_path=output_path,
                        )

                        logger.info(
                            f"Completed {zip_file}",
                            extra={
                                "records_extracted": result_data["records"],
                                "temp_file": result_data["temp_file"],
                            },
                        )

                        return (zip_file, result_data)

                    except Exception as e:
                        logger.error(f"Error processing {zip_file}: {e}", exc_info=True)
                        return (zip_file, e)

            # Process all files with controlled concurrency
            results = await asyncio.gather(
                *[process_single_file(zip_file) for zip_file in zip_files],
                return_exceptions=True,
            )

            # Aggregate statistics and collect temp files
            for result in results:
                if isinstance(result, BaseException):
                    error_count += 1
                    continue

                try:
                    zip_file, result_data = result
                except (TypeError, ValueError):
                    error_count += 1
                    continue

                if isinstance(result_data, Exception):
                    error_count += 1
                    errors[zip_file] = str(result_data)
                elif isinstance(result_data, dict):
                    # Successful processing - collect temp file
                    success_count += 1
                    total_records_written += result_data["records"]
                    temp_file_path = Path(result_data["temp_file"])
                    if temp_file_path.exists():
                        temp_files.append(temp_file_path)
                    else:
                        logger.warning(f"Temp file not found: {temp_file_path}")

            # MERGE FINAL - combine all temp files into one
            if temp_files:
                logger.info(
                    f"Starting merge of {len(temp_files)} temporary files...",
                    extra={"temp_files": [f.name for f in temp_files]},
                )

                try:
                    final_record_count = await self._merge_temp_files_streaming(
                        temp_files=temp_files,
                        final_output=output_path,
                    )
                    total_records_written = final_record_count

                    logger.info(
                        "Final merge completed",
                        extra={
                            "total_records": f"{final_record_count:,}",
                            "output_file": str(output_path),
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to merge temporary files: {e}", exc_info=True)
                    # Don't set error_count here as files were processed successfully
                    # The error is in the merge step
                    errors["MERGE"] = str(e)

            result_summary = {
                "total_files": len(zip_files),
                "success_count": success_count,
                "error_count": error_count,
                "total_records": total_records_written,
                "errors": errors,
                "output_file": str(output_path),
            }

            logger.info("Extraction completed", extra=result_summary)

            return result_summary

    async def _process_and_write_zip(
        self,
        zip_file: str,
        target_tpmerc_codes: Set[str],
        output_path: Path,
    ) -> Dict[str, Any]:
        """Process a single ZIP file with incremental flush to disk.

        Each ZIP writes to its own temporary file to avoid race conditions
        in parallel processing. Returns info about temp file for later merge.

        Args:
            zip_file: Path to ZIP file
            target_tpmerc_codes: Set of TPMERC codes to filter
            output_path: Base path for output (used to generate temp file name)

        Returns:
            Dictionary with 'records' (int) and 'temp_file' (str) keys
        """
        # Generate unique temporary file name for this ZIP
        zip_basename = Path(zip_file).stem  # e.g., "COTAHIST_A2023"
        temp_output = (
            output_path.parent / f"{output_path.stem}_{zip_basename}_temp.parquet"
        )

        logger.debug(
            f"Processing ZIP: {zip_file}",
            extra={
                "target_codes": len(target_tpmerc_codes),
                "parallel_parsing": self.use_parallel_parsing,
                "temp_output": str(temp_output),
            },
        )

        buffer: List[Dict[str, Any]] = []
        total_written = 0
        is_first_write_to_temp = True  # Track first write to THIS temp file

        try:
            if self.use_parallel_parsing:
                # FAST mode: Parse in batches with threads
                line_buffer: List[str] = []

                async for line in self.zip_reader.read_lines_from_zip(zip_file):
                    line_buffer.append(line)

                    # Parse batch when threshold reached
                    if len(line_buffer) >= self.parse_batch_size:
                        batch_records = await self._parse_lines_batch_parallel(
                            line_buffer, target_tpmerc_codes
                        )
                        buffer.extend(batch_records)
                        line_buffer.clear()

                        # Check if should flush (by size OR by memory usage)
                        should_flush = (
                            len(buffer) >= self.flush_batch_size
                            or self._should_flush_by_memory()
                        )

                        # Flush to disk when buffer is full or memory threshold reached
                        if should_flush and buffer:
                            write_mode = (
                                "overwrite" if is_first_write_to_temp else "append"
                            )
                            await self._write_buffer_to_disk(
                                buffer, temp_output, write_mode
                            )
                            total_written += len(buffer)
                            is_first_write_to_temp = False
                            buffer.clear()
                            gc.collect()

                        # Check resources periodically (less frequently for performance)
                        if total_written % 250_000 == 0 and total_written > 0:
                            await self._check_and_wait_for_resources()

                # Process remaining lines
                if line_buffer:
                    batch_records = await self._parse_lines_batch_parallel(
                        line_buffer, target_tpmerc_codes
                    )
                    buffer.extend(batch_records)
                    line_buffer.clear()

            else:
                # SLOW mode: Sequential parsing
                line_count = 0

                async for line in self.zip_reader.read_lines_from_zip(zip_file):
                    parsed = self.parser.parse_line(line, target_tpmerc_codes)
                    if parsed:
                        buffer.append(parsed)

                    # Check if should flush (by size OR by memory usage)
                    should_flush = (
                        len(buffer) >= self.flush_batch_size
                        or self._should_flush_by_memory()
                    )

                    # Flush when buffer is full or memory threshold reached
                    if should_flush and buffer:
                        write_mode = "overwrite" if is_first_write_to_temp else "append"
                        await self._write_buffer_to_disk(
                            buffer, temp_output, write_mode
                        )
                        total_written += len(buffer)
                        is_first_write_to_temp = False
                        buffer.clear()
                        gc.collect()

                    # Check resources every 1000 lines
                    line_count += 1
                    if (
                        line_count % 5000 == 0
                    ):  # Reduced frequency (every 5k instead of 1k)
                        await self._check_and_wait_for_resources()

            # Final flush for remaining records
            if buffer:
                write_mode = "overwrite" if is_first_write_to_temp else "append"
                await self._write_buffer_to_disk(buffer, temp_output, write_mode)
                total_written += len(buffer)
                buffer.clear()

            logger.debug(
                f"Completed ZIP: {zip_file}",
                extra={
                    "records_extracted": total_written,
                    "temp_file": str(temp_output),
                },
            )

            return {"records": total_written, "temp_file": str(temp_output)}

        except Exception as e:
            logger.error(
                f"Error processing ZIP: {zip_file}",
                extra={"error": str(e), "records_written_so_far": total_written},
                exc_info=True,
            )

            # Try to save buffer to emergency file before clearing
            if buffer:
                emergency_file = temp_output.with_suffix(".emergency.json")
                try:
                    import json

                    with open(emergency_file, "w", encoding="utf-8") as f:
                        json.dump(buffer, f, ensure_ascii=False, indent=2)
                    logger.warning(
                        f"Buffer saved to emergency file: {emergency_file}",
                        extra={"records_saved": len(buffer)},
                    )
                except Exception as save_error:
                    logger.error(
                        f"Failed to save emergency buffer: {save_error}",
                        extra={"buffer_size": len(buffer)},
                    )

            # Clear buffer after attempting emergency save
            buffer.clear()
            gc.collect()

            # Clean up temp file on error
            if temp_output.exists():
                try:
                    temp_output.unlink()
                    logger.debug(f"Cleaned up temp file after error: {temp_output}")
                except Exception:
                    pass

            raise

    async def _parse_lines_batch_parallel(
        self, lines: List[str], target_tpmerc_codes: Set[str]
    ) -> List[Dict[str, Any]]:
        """Parse a batch of lines in parallel using ThreadPoolExecutor.

        Args:
            lines: List of lines to parse
            target_tpmerc_codes: Set of TPMERC codes to filter

        Returns:
            List of parsed records (excludes None values)
        """
        loop = asyncio.get_event_loop()
        parsed_batch = await loop.run_in_executor(
            self.executor_pool,
            _parse_lines_batch,
            lines,
            target_tpmerc_codes,
        )
        return [record for record in parsed_batch if record is not None]

    async def _write_buffer_to_disk(
        self, buffer: List[Dict[str, Any]], output_path: Path, mode: str
    ) -> None:
        """Write buffer to Parquet file with retry mechanism.

        Args:
            buffer: List of records to write
            output_path: Path to Parquet file
            mode: Write mode ('overwrite' or 'append')

        Raises:
            IOError: If all retry attempts fail
        """
        if not buffer:
            return

        logger.debug(
            f"Writing buffer to disk: {len(buffer)} records (mode: {mode})",
            extra={"output_path": str(output_path)},
        )

        # Retry mechanism to avoid data loss on temporary I/O errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.data_writer.write_to_parquet(
                    data=buffer,
                    output_path=output_path,
                    mode=mode,
                )
                return  # Success

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Write failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}",
                        extra={"output_path": str(output_path)},
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Write failed after {max_retries} attempts",
                        extra={
                            "output_path": str(output_path),
                            "buffer_size": len(buffer),
                            "error": str(e),
                        },
                        exc_info=True,
                    )
                    raise

    async def _check_and_wait_for_resources(self) -> None:
        """Check resource state and wait if necessary."""
        resource_state = self.resource_monitor.check_resources()

        if resource_state == ResourceState.CRITICAL:
            # Brief pause to allow recovery
            await asyncio.sleep(0.1)
            gc.collect()
        elif resource_state == ResourceState.EXHAUSTED:
            logger.warning("Resources exhausted, waiting for recovery...")
            if not await self._wait_for_resources(timeout_seconds=30):
                raise MemoryError("Unable to recover from resource exhaustion")

    def _adjust_batch_sizes(self) -> None:
        """Dynamically adjust batch sizes based on current memory state.

        Under memory pressure, reduces batch sizes to prevent OOM errors.
        Both modes use same base batch size for consistent SSD write performance.
        """
        memory_state = self.resource_monitor.check_resources()

        # Both modes use same base flush size for SSD optimization
        base_flush_size = self.FLUSH_BATCH_SIZE

        # Adjust flush batch size based on memory pressure
        new_flush_size = self.resource_monitor.get_safe_batch_size(base_flush_size)
        if new_flush_size != self.flush_batch_size:
            logger.info(
                f"Adjusted flush batch size: {self.flush_batch_size} -> {new_flush_size} "
                f"(memory state: {memory_state.value})"
            )
            self.flush_batch_size = max(new_flush_size, self.MIN_FLUSH_BATCH)

        # Adjust parse batch size proportionally (10% of flush size)
        ratio = self.PARSE_BATCH_SIZE / base_flush_size
        new_parse_size = int(self.flush_batch_size * ratio)
        if new_parse_size != self.parse_batch_size:
            self.parse_batch_size = max(new_parse_size, self.MIN_PARSE_BATCH)

    def _should_flush_by_memory(self) -> bool:
        """Check if should flush based on current RAM usage.

        Returns:
            True if process memory usage exceeds mode-specific threshold
        """
        process_memory_mb = self.resource_monitor.get_process_memory_mb()

        if self.processing_mode == ProcessingModeEnum.FAST:
            # Fast mode: flush at 2.5GB (leaves 500MB margin for 3GB target)
            threshold_mb = 3500
        else:  # SLOW
            # Slow mode: flush at 800MB (leaves 200MB margin for 1GB target)
            threshold_mb = 1000

        should_flush = process_memory_mb >= threshold_mb

        if should_flush:
            logger.info(
                "Memory threshold reached for flush",
                extra={
                    "process_memory_mb": f"{process_memory_mb:.2f}",
                    "threshold_mb": threshold_mb,
                    "mode": str(self.processing_mode),
                },
            )

        return should_flush

    async def _merge_temp_files_streaming(
        self,
        temp_files: List[Path],
        final_output: Path,
    ) -> int:
        """Merge multiple parquet files using PyArrow streaming.

        This method never loads entire files in RAM, processing in batches
        to maintain constant memory usage.

        Args:
            temp_files: List of temporary parquet files to merge
            final_output: Final output path for merged data

        Returns:
            Total number of records in final file

        Raises:
            IOError: If merge fails
        """
        import pyarrow.parquet as pq  # type: ignore

        if not temp_files:
            logger.warning("No temporary files to merge")
            return 0

        if len(temp_files) == 1:
            # Only one file - just rename it
            logger.info("Only one temp file, renaming to final output")
            temp_files[0].rename(final_output)
            return self._count_parquet_rows(final_output)

        logger.info(
            f"Merging {len(temp_files)} temporary files using streaming",
            extra={
                "temp_files": [f.name for f in temp_files],
                "final_output": str(final_output),
            },
        )

        temp_merge = final_output.with_suffix(".parquet.merge_tmp")

        try:
            # Get schema from first file
            first_file = pq.ParquetFile(str(temp_files[0]))
            schema = first_file.schema_arrow

            # Create writer for merged file
            writer = pq.ParquetWriter(
                str(temp_merge),
                schema,
                compression="zstd",
                compression_level=3,
            )

            total_rows = 0

            # Iterate over each temporary file
            for i, temp_file in enumerate(temp_files, 1):
                logger.debug(f"Merging file {i}/{len(temp_files)}: {temp_file.name}")

                parquet_file = pq.ParquetFile(str(temp_file))
                file_rows = 0

                # Copy in larger batches for better performance (200k rows)
                for batch in parquet_file.iter_batches(batch_size=200_000):
                    writer.write_batch(batch)
                    file_rows += batch.num_rows
                    total_rows += batch.num_rows

                logger.debug(
                    f"Merged {file_rows:,} rows from {temp_file.name}",
                    extra={"cumulative_rows": total_rows},
                )

                # Clean up temporary file
                try:
                    temp_file.unlink()
                    logger.debug(f"Deleted temporary file: {temp_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file.name}: {e}")

                # Check resources periodically (less frequently)
                if total_rows % 500_000 == 0 and total_rows > 0:
                    await self._check_and_wait_for_resources()

            # Close writer
            writer.close()

            # Move to final destination atomically
            temp_merge.replace(final_output)

            logger.info(
                "Merge completed successfully",
                extra={
                    "total_rows": f"{total_rows:,}",
                    "output_file": str(final_output),
                    "files_merged": len(temp_files),
                },
            )

            return total_rows

        except Exception as e:
            logger.error(
                f"Failed to merge temporary files: {e}",
                exc_info=True,
            )

            # Cleanup merge temp file
            if temp_merge.exists():
                try:
                    temp_merge.unlink()
                except Exception:
                    pass

            # Cleanup remaining temp files
            for temp_file in temp_files:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass

            raise IOError(f"Merge operation failed: {e}")

    def _count_parquet_rows(self, path: Path) -> int:
        """Count rows in parquet file without loading into RAM.

        Args:
            path: Path to parquet file

        Returns:
            Number of rows in file
        """
        import pyarrow.parquet as pq  # type: ignore

        try:
            parquet_file = pq.ParquetFile(str(path))
            return parquet_file.metadata.num_rows
        except Exception as e:
            logger.error(f"Error counting rows in {path}: {e}")
            return 0

    async def _wait_for_resources(self, timeout_seconds: int = 30) -> bool:
        """Wait for resources to become available.

        Args:
            timeout_seconds: Maximum time to wait

        Returns:
            True if resources became available, False if timeout
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.resource_monitor.wait_for_resources,
            ResourceState.WARNING,
            timeout_seconds,
        )


def _parse_lines_batch(
    lines: List[str], target_tpmerc_codes: Set[str]
) -> List[Dict[str, Any]]:
    """Parse a batch of lines using a fresh parser instance.

    Module-level function for use with ThreadPoolExecutor.

    Args:
        lines: List of lines to parse
        target_tpmerc_codes: Set of TPMERC codes to filter

    Returns:
        List of parsed records (may include None for non-matching lines)
    """
    parser = CotahistParser()
    parsed = [parser.parse_line(line, target_tpmerc_codes) for line in lines]
    return [record for record in parsed if record is not None]
