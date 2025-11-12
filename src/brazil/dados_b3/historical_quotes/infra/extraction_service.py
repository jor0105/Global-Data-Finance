import asyncio
import gc
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Set

from src.core import ResourceMonitor, ResourceState, get_logger, log_execution_time

from ..domain import ProcessingModeEnum
from .cotahist_parser import CotahistParser
from .parquet_writer import ParquetWriter
from .zip_reader import ZipFileReader

logger = get_logger(__name__)


class ExtractionService:
    """Service for extracting data from COTAHIST ZIP files asynchronously.

    This service controls resource consumption through processing modes:
    - FAST: High concurrency, more CPU/RAM usage, with parallel parsing
    - SLOW: Low concurrency, minimal CPU/RAM usage, sequential parsing

    Features:
    - Parallel CPU-bound parsing using ProcessPoolExecutor (FAST mode)
    - Async I/O for reading ZIP files
    - Dynamic batch writing based on available memory
    - Real-time resource monitoring with circuit breaker
    - Automatic garbage collection on memory pressure
    """

    # Default batch sizes (will be adjusted dynamically based on RAM)
    DEFAULT_BATCH_SIZE = 100_000
    DEFAULT_PARSE_BATCH_SIZE = 10_000

    # Minimum safe batch sizes
    MIN_BATCH_SIZE = 1_000
    MIN_PARSE_BATCH_SIZE = 500

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
            desired_concurrent_files = 10
            desired_workers = None  # Use default (CPU count)
            self.use_parallel_parsing = True
        else:  # SLOW
            desired_concurrent_files = 2
            desired_workers = 1
            self.use_parallel_parsing = False

        self.max_concurrent_files = min(
            desired_concurrent_files,
            self.resource_monitor.get_safe_worker_count(desired_concurrent_files),
        )

        # Determine safe worker count for ProcessPoolExecutor
        if self.use_parallel_parsing:
            self.max_workers = self.resource_monitor.get_safe_worker_count(
                desired_workers
            )
        else:
            self.max_workers = 1

        # Dynamic batch sizes (will be adjusted during execution)
        self.batch_size = self.DEFAULT_BATCH_SIZE
        self.parse_batch_size = self.DEFAULT_PARSE_BATCH_SIZE

        # Initialize process pool for CPU-bound parsing if in FAST mode
        self.process_pool = None
        if self.use_parallel_parsing:
            self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)

        logger.info(
            "ExtractionService initialized",
            extra={
                "processing_mode": str(processing_mode),
                "max_concurrent_files": self.max_concurrent_files,
                "use_parallel_parsing": self.use_parallel_parsing,
                "max_workers": self.max_workers,
                "batch_size": self.batch_size,
                "resource_monitoring": "enabled",
            },
        )

    def __del__(self):
        """Cleanup process pool on deletion."""
        if self.process_pool is not None:
            try:
                self.process_pool.shutdown(wait=True, cancel_futures=False)
            except Exception:
                # Ignore errors during cleanup (interpreter might be shutting down)
                pass

    async def extract_from_zip_files(
        self, zip_files: Set[str], target_tpmerc_codes: Set[str], output_path: Path
    ) -> Dict[str, Any]:
        """Extract data from multiple ZIP files asynchronously with adaptive batch writing.

        Args:
            zip_files: Set of paths to ZIP files
            target_tpmerc_codes: Set of TPMERC codes to filter (e.g., {'010', '020'})
            output_path: Path where to save the extracted data

        Returns:
            Dictionary with extraction statistics
        """
        self._adjust_batch_sizes()

        logger.info(
            "Starting extraction from ZIP files",
            extra={
                "total_files": len(zip_files),
                "target_codes_count": len(target_tpmerc_codes),
                "output_path": str(output_path),
                "processing_mode": str(self.processing_mode),
                "batch_size": self.batch_size,
                "parse_batch_size": self.parse_batch_size,
            },
        )

        with log_execution_time(
            logger,
            "Extract from all ZIP files",
            total_files=len(zip_files),
        ):
            semaphore = asyncio.Semaphore(self.max_concurrent_files)

            async def process_with_semaphore(zip_file: str):
                # Check resources before processing each file
                if not await self._wait_for_resources():
                    logger.error(f"Skipping {zip_file} - resources exhausted")
                    return (zip_file, Exception("Resources exhausted"))

                async with semaphore:
                    result = await self._process_single_zip(
                        zip_file, target_tpmerc_codes
                    )
                    return (zip_file, result)

            # Process all files with controlled concurrency
            results = await asyncio.gather(
                *[process_with_semaphore(zip_file) for zip_file in zip_files],
                return_exceptions=True,
            )

            # Consolidate results with adaptive batch writing
            all_records: List[Dict[str, Any]] = []
            success_count = 0
            error_count = 0
            errors = {}
            total_records_written = 0
            batch_number = 0

            for result in results:
                if isinstance(result, BaseException):
                    error_count += 1
                    logger.error(
                        "Unexpected error processing ZIP files",
                        extra={"error": str(result)},
                        exc_info=result,
                    )
                    continue

                try:
                    zip_file, result_data = result
                except (TypeError, ValueError) as e:
                    error_count += 1
                    logger.error(
                        "Failed to unpack result from ZIP processing",
                        extra={"error": str(e), "result": str(result)},
                        exc_info=True,
                    )
                    continue

                if isinstance(result_data, Exception):
                    error_count += 1
                    errors[zip_file] = str(result_data)
                    logger.error(
                        "Failed to process ZIP file",
                        extra={
                            "zip_file": zip_file,
                            "error": str(result_data),
                        },
                        exc_info=result_data,
                    )
                elif isinstance(result_data, list):
                    success_count += 1
                    all_records.extend(result_data)
                    logger.debug(
                        "Successfully processed ZIP file",
                        extra={
                            "zip_file": zip_file,
                            "records_extracted": len(result_data),
                        },
                    )

                    # Adjust batch size dynamically and flush if needed
                    self._adjust_batch_sizes()

                    if len(all_records) >= self.batch_size:
                        batch_number += 1
                        await self._flush_batch_to_disk(
                            all_records,
                            output_path,
                            batch_number,
                        )
                        total_records_written += len(all_records)
                        all_records.clear()

                        # Force garbage collection after flush
                        gc.collect()

            # Write remaining records
            if all_records:
                batch_number += 1
                await self._flush_batch_to_disk(
                    all_records,
                    output_path,
                    batch_number,
                )
                total_records_written += len(all_records)
                all_records.clear()
                gc.collect()

            if total_records_written == 0:
                logger.warning("No records extracted from any ZIP file")

            result_summary = {
                "total_files": len(zip_files),
                "success_count": success_count,
                "error_count": error_count,
                "total_records": total_records_written,
                "batches_written": batch_number,
                "errors": errors,
                "output_file": str(output_path),
            }

            logger.info(
                "Extraction completed",
                extra=result_summary,
            )

            return result_summary

    async def _process_single_zip(
        self, zip_file: str, target_tpmerc_codes: Set[str]
    ) -> List[Dict[str, Any]]:
        """Process a single ZIP file and extract matching records.

        Args:
            zip_file: Path to ZIP file
            target_tpmerc_codes: Set of TPMERC codes to filter

        Returns:
            List of parsed records
        """
        logger.debug(
            "Processing ZIP file",
            extra={
                "zip_file": zip_file,
                "target_codes": list(target_tpmerc_codes),
                "parallel_parsing": self.use_parallel_parsing,
            },
        )

        records = []

        try:
            if self.use_parallel_parsing:
                # Collect lines in batches for parallel processing
                line_buffer: List[str] = []

                async for line in self.zip_reader.read_lines_from_zip(zip_file):
                    # Check resources periodically
                    if len(line_buffer) % 5000 == 0 and len(line_buffer) > 0:
                        resource_state = self.resource_monitor.check_resources()
                        if resource_state == ResourceState.EXHAUSTED:
                            logger.warning(
                                f"Resource exhaustion detected while processing {zip_file}"
                            )
                            # Wait for resources to recover
                            if not await self._wait_for_resources():
                                raise MemoryError(
                                    "Unable to recover from resource exhaustion"
                                )

                    line_buffer.append(line)

                    # Process batch when threshold reached (dynamic size)
                    if len(line_buffer) >= self.parse_batch_size:
                        batch_records = await self._parse_lines_batch_parallel(
                            line_buffer, target_tpmerc_codes
                        )
                        records.extend(batch_records)
                        line_buffer.clear()

                        # Opportunistic garbage collection on large batches
                        if len(records) % 50000 == 0:
                            gc.collect()

                # Process remaining lines
                if line_buffer:
                    batch_records = await self._parse_lines_batch_parallel(
                        line_buffer, target_tpmerc_codes
                    )
                    records.extend(batch_records)
                    line_buffer.clear()
            else:
                # Sequential parsing for SLOW mode
                line_count = 0
                async for line in self.zip_reader.read_lines_from_zip(zip_file):
                    # Check resources every 1000 lines
                    if line_count % 1000 == 0 and line_count > 0:
                        resource_state = self.resource_monitor.check_resources()
                        if resource_state == ResourceState.CRITICAL:
                            # Pause briefly to allow memory recovery
                            await asyncio.sleep(0.1)
                        elif resource_state == ResourceState.EXHAUSTED:
                            if not await self._wait_for_resources():
                                raise MemoryError(
                                    "Unable to recover from resource exhaustion"
                                )

                    parsed = self.parser.parse_line(line, target_tpmerc_codes)
                    if parsed:
                        records.append(parsed)

                    line_count += 1

            logger.debug(
                "Completed processing ZIP file",
                extra={
                    "zip_file": zip_file,
                    "records_extracted": len(records),
                },
            )

        except Exception as e:
            logger.error(
                "Error processing ZIP file",
                extra={
                    "zip_file": zip_file,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

        return records

    async def _parse_lines_batch_parallel(
        self, lines: List[str], target_tpmerc_codes: Set[str]
    ) -> List[Dict[str, Any]]:
        """Parse a batch of lines in parallel using ProcessPoolExecutor.

        This offloads CPU-intensive parsing to separate processes, allowing
        better utilization of multi-core CPUs.

        Args:
            lines: List of lines to parse
            target_tpmerc_codes: Set of TPMERC codes to filter

        Returns:
            List of parsed records (excludes None values)
        """
        loop = asyncio.get_event_loop()

        # Execute parsing in process pool
        parsed_batch = await loop.run_in_executor(
            self.process_pool,
            _parse_lines_batch,  # Static function for pickling
            lines,
            target_tpmerc_codes,
        )

        return [record for record in parsed_batch if record is not None]

    async def _flush_batch_to_disk(
        self,
        records: List[Dict[str, Any]],
        output_path: Path,
        batch_number: int,
    ) -> None:
        """Flush a batch of records to disk.

        Uses append mode for batches after the first one to prevent overwriting.

        Args:
            records: List of records to write
            output_path: Path where to save the data
            batch_number: Current batch number (1-indexed)
        """
        if not records:
            return

        # First batch overwrites, subsequent batches append
        write_mode = "overwrite" if batch_number == 1 else "append"

        logger.info(
            f"Flushing batch {batch_number} to disk",
            extra={
                "batch_number": batch_number,
                "records_in_batch": len(records),
                "write_mode": write_mode,
                "output_path": str(output_path),
            },
        )

        await self.data_writer.write_to_parquet(
            data=records,
            output_path=output_path,
            mode=write_mode,
        )

    def _adjust_batch_sizes(self) -> None:
        """Dynamically adjust batch sizes based on current memory state."""
        memory_state = self.resource_monitor.check_resources()

        new_batch_size = self.resource_monitor.get_safe_batch_size(
            self.DEFAULT_BATCH_SIZE
        )
        if new_batch_size != self.batch_size:
            logger.info(
                f"Adjusted write batch size: {self.batch_size} -> {new_batch_size} "
                f"(memory state: {memory_state.value})"
            )
            self.batch_size = max(new_batch_size, self.MIN_BATCH_SIZE)

        ratio = self.DEFAULT_PARSE_BATCH_SIZE / self.DEFAULT_BATCH_SIZE
        new_parse_batch_size = int(self.batch_size * ratio)
        if new_parse_batch_size != self.parse_batch_size:
            self.parse_batch_size = max(new_parse_batch_size, self.MIN_PARSE_BATCH_SIZE)

    async def _wait_for_resources(self, timeout_seconds: int = 30) -> bool:
        """Wait for resources to become available.

        Args:
            timeout_seconds: Maximum time to wait

        Returns:
            True if resources became available, False if timeout
        """
        # Run blocking wait in executor to avoid blocking event loop
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

    This function is defined at module level so it can be pickled
    and sent to worker processes.

    Args:
        lines: List of lines to parse
        target_tpmerc_codes: Set of TPMERC codes to filter

    Returns:
        List of parsed records (may include None for non-matching lines)
    """
    parser = CotahistParser()
    parsed = [parser.parse_line(line, target_tpmerc_codes) for line in lines]
    return [record for record in parsed if record is not None]
