"""Process individual B3 COTAHIST inputs with resource-aware parsing."""

import asyncio
import contextlib
import gc
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

from .....core import get_logger
from .batch_parser import parse_lines_batch
from .buffered_writer import BufferedParquetWriterB3
from .resource_policy import ResourcePolicyB3
from .types import ParsedRecord, ZipProcessingResult

logger = get_logger(__name__)


class _LineReader(Protocol):
    def read_lines_from_zip(self, zip_path: str) -> AsyncIterator[str]: ...


class _LineParser(Protocol):
    def parse_line(
        self, line: str, target_codes: set[str]
    ) -> ParsedRecord | None: ...


class ZipProcessorB3:
    """Process one COTAHIST ZIP or TXT input into temporary Parquet."""

    SEQUENTIAL_FLUSH_CHECK_INTERVAL = 10_000
    SEQUENTIAL_RESOURCE_CHECK_INTERVAL = 5_000

    def __init__(
        self,
        zip_reader: _LineReader,
        parser: _LineParser,
        buffered_writer: BufferedParquetWriterB3,
        resource_policy: ResourcePolicyB3,
    ) -> None:
        """Initialize processing collaborators and the optional worker pool."""
        self.zip_reader = zip_reader
        self.parser = parser
        self.buffered_writer = buffered_writer
        self.resource_policy = resource_policy

        self.executor_pool = None
        if self.resource_policy.use_parallel_parsing:
            self.executor_pool = ThreadPoolExecutor(
                max_workers=self.resource_policy.max_workers
            )

    def close(self) -> None:
        """Shutdown the parser worker pool if parallel parsing is enabled."""
        if self.executor_pool is not None:
            executor_pool = self.executor_pool
            self.executor_pool = None
            with contextlib.suppress(Exception):
                executor_pool.shutdown(wait=True, cancel_futures=False)

    async def process(
        self,
        zip_file: str,
        target_tpmerc_codes: set[str],
        output_path: Path,
    ) -> ZipProcessingResult:
        """Process one COTAHIST input into a unique temporary Parquet file."""
        input_name = Path(zip_file).name
        temp_output = (
            output_path.parent
            / f'{output_path.stem}_{input_name}_temp.parquet'
        )

        logger.debug(
            f'Processing COTAHIST input: {zip_file}',
            extra={
                'target_codes': len(target_tpmerc_codes),
                'parallel_parsing': self.resource_policy.use_parallel_parsing,
                'temp_output': str(temp_output),
            },
        )

        buffer: list[ParsedRecord] = []
        total_written = 0
        is_first_write_to_temp = True

        try:
            if self.resource_policy.use_parallel_parsing:
                (
                    records_written,
                    is_first_write_to_temp,
                ) = await self._process_parallel(
                    zip_file,
                    target_tpmerc_codes,
                    temp_output,
                    buffer,
                    is_first_write_to_temp,
                )
                total_written += records_written
            else:
                (
                    records_written,
                    is_first_write_to_temp,
                ) = await self._process_sequential(
                    zip_file,
                    target_tpmerc_codes,
                    temp_output,
                    buffer,
                    is_first_write_to_temp,
                )
                total_written += records_written

            if buffer:
                (
                    records_written,
                    is_first_write_to_temp,
                ) = await self.buffered_writer.flush_to_disk(
                    buffer,
                    temp_output,
                    is_first_write=is_first_write_to_temp,
                    collect_garbage=False,
                )
                total_written += records_written

            logger.debug(
                f'Completed COTAHIST input: {zip_file}',
                extra={
                    'records_extracted': total_written,
                    'temp_file': str(temp_output),
                },
            )

            return {'records': total_written, 'temp_file': str(temp_output)}

        except Exception as e:
            logger.error(
                f'Error processing COTAHIST input: {zip_file}',
                extra={
                    'error': str(e),
                    'records_written_so_far': total_written,
                },
                exc_info=True,
            )

            buffer.clear()
            gc.collect()

            if temp_output.exists():
                with contextlib.suppress(Exception):
                    temp_output.unlink()
                    logger.debug(
                        f'Cleaned up temp file after error: {temp_output}'
                    )

            raise

    async def _process_parallel(
        self,
        zip_file: str,
        target_tpmerc_codes: set[str],
        temp_output: Path,
        buffer: list[ParsedRecord],
        is_first_write_to_temp: bool,
    ) -> tuple[int, bool]:
        line_buffer: list[str] = []
        total_written = 0

        async for line in self.zip_reader.read_lines_from_zip(zip_file):
            line_buffer.append(line)

            if len(line_buffer) >= self.resource_policy.parse_batch_size:
                batch_records = await self._parse_lines_batch_parallel(
                    line_buffer, target_tpmerc_codes
                )
                buffer.extend(batch_records)
                line_buffer.clear()

                (
                    records_written,
                    is_first_write_to_temp,
                ) = await self.buffered_writer.flush_if_needed(
                    buffer,
                    temp_output,
                    is_first_write=is_first_write_to_temp,
                )
                total_written += records_written

                if total_written % 250_000 == 0 and total_written > 0:
                    await self.resource_policy.check_and_wait_for_resources()

        if line_buffer:
            batch_records = await self._parse_lines_batch_parallel(
                line_buffer, target_tpmerc_codes
            )
            buffer.extend(batch_records)
            line_buffer.clear()

        return total_written, is_first_write_to_temp

    async def _process_sequential(
        self,
        zip_file: str,
        target_tpmerc_codes: set[str],
        temp_output: Path,
        buffer: list[ParsedRecord],
        is_first_write_to_temp: bool,
    ) -> tuple[int, bool]:
        line_count = 0
        total_written = 0

        async for line in self.zip_reader.read_lines_from_zip(zip_file):
            parsed = self.parser.parse_line(line, target_tpmerc_codes)
            if parsed:
                buffer.append(parsed)

            line_count += 1
            if line_count % self.SEQUENTIAL_FLUSH_CHECK_INTERVAL == 0:
                (
                    records_written,
                    is_first_write_to_temp,
                ) = await self.buffered_writer.flush_if_needed(
                    buffer,
                    temp_output,
                    is_first_write=is_first_write_to_temp,
                )
                total_written += records_written

            if line_count % self.SEQUENTIAL_RESOURCE_CHECK_INTERVAL == 0:
                await self.resource_policy.check_and_wait_for_resources()

        return total_written, is_first_write_to_temp

    async def _parse_lines_batch_parallel(
        self, lines: list[str], target_tpmerc_codes: set[str]
    ) -> list[ParsedRecord]:
        """Parse a batch of lines in parallel using ThreadPoolExecutor."""
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(
            self.executor_pool,
            parse_lines_batch,
            lines,
            target_tpmerc_codes,
        )
        parsed_batch = await future
        return [record for record in parsed_batch if record is not None]
