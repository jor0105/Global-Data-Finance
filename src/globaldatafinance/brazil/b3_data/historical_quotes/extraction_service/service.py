"""Orchestrate incremental parsing and writing of B3 COTAHIST inputs."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .....core import SimpleProgressBar, get_logger, log_execution_time
from ..cotahist_parser import CotahistParserB3
from ..parquet_writer import ParquetWriterB3
from ..processing import ProcessingModeEnumB3
from ..zip_reader import ZipFileReaderB3
from .buffered_writer import BufferedParquetWriterB3
from .resource_policy import ResourcePolicyB3
from .temp_parquet_merge import merge_temp_files_streaming
from .types import ExtractionSummary, ProcessSingleFileResult
from .zip_processor import ZipProcessorB3

logger = get_logger(__name__)


@dataclass
class _ExtractionState:
    """Accumulate observable results across one extraction request."""

    total_records: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: dict[str, str] = field(default_factory=dict)
    temp_files: list[Path] = field(default_factory=list)


class ExtractionServiceB3:
    """Extract COTAHIST ZIP or TXT data with bounded incremental flushing."""

    def __init__(
        self,
        zip_reader: ZipFileReaderB3,
        parser: CotahistParserB3,
        data_writer: ParquetWriterB3,
        processing_mode: ProcessingModeEnumB3,
    ):
        """Initialize collaborators and extraction policy."""
        self.zip_reader = zip_reader
        self.parser = parser
        self.data_writer = data_writer
        self.processing_mode = processing_mode

        self.resource_policy = ResourcePolicyB3(processing_mode)
        self.buffered_writer = BufferedParquetWriterB3(
            data_writer=data_writer,
            resource_policy=self.resource_policy,
        )
        self.zip_processor = ZipProcessorB3(
            zip_reader=zip_reader,
            parser=parser,
            buffered_writer=self.buffered_writer,
            resource_policy=self.resource_policy,
        )
        self._closed = False

        self._log_initialization()

    def _log_initialization(self) -> None:
        rp = self.resource_policy
        estimated_memory_per_file_mb = rp.flush_batch_size * 3 // 1024
        logger.info(
            'ExtractionServiceB3 initialized',
            extra={
                'processing_mode': str(self.processing_mode),
                'max_concurrent_files': rp.max_concurrent_files,
                'use_parallel_parsing': rp.use_parallel_parsing,
                'max_workers': rp.max_workers,
                'flush_batch_size': rp.flush_batch_size,
                'parse_batch_size': rp.parse_batch_size,
                'estimated_memory_per_file_mb': estimated_memory_per_file_mb,
                'estimated_total_memory_mb': (
                    estimated_memory_per_file_mb * rp.max_concurrent_files
                ),
                'executor_type': (
                    'ThreadPoolExecutor'
                    if rp.use_parallel_parsing
                    else 'Sequential'
                ),
            },
        )

    def close(self) -> None:
        """Release parser workers owned by this extraction service."""
        if getattr(self, '_closed', False):
            return

        zip_processor = getattr(self, 'zip_processor', None)
        if zip_processor is not None:
            zip_processor.close()
        self._closed = True

    def __del__(self) -> None:
        """Fallback cleanup when callers forget to close the service."""
        self.close()

    async def _run_single_file(
        self,
        zip_file: str,
        target_tpmerc_codes: set[str],
        output_path: Path,
    ) -> ProcessSingleFileResult:
        """Process one input and translate failures into a partial result."""
        try:
            result_data = await self.zip_processor.process(
                zip_file=zip_file,
                target_tpmerc_codes=target_tpmerc_codes,
                output_path=output_path,
            )
        except Exception as error:
            logger.exception('Error processing %s', zip_file)
            return zip_file, error

        logger.info(
            f'Completed {zip_file}',
            extra={
                'records_extracted': result_data['records'],
                'temp_file': result_data['temp_file'],
            },
        )
        return zip_file, result_data

    async def _process_single_file(
        self,
        zip_file: str,
        target_tpmerc_codes: set[str],
        output_path: Path,
        semaphore: asyncio.Semaphore,
        progress_bar: SimpleProgressBar,
    ) -> ProcessSingleFileResult:
        """Wait for capacity and update progress once for one input."""
        try:
            resources_available = (
                await self.resource_policy.wait_for_resources(
                    timeout_seconds=30
                )
            )
            if not resources_available:
                error_message = 'Resources exhausted'
                logger.error('Skipping %s - %s', zip_file, error_message)
                return zip_file, Exception(error_message)

            async with semaphore:
                return await self._run_single_file(
                    zip_file, target_tpmerc_codes, output_path
                )
        finally:
            progress_bar.update(1)

    @staticmethod
    def _accumulate_result(
        result: ProcessSingleFileResult | BaseException,
        state: _ExtractionState,
    ) -> None:
        """Fold one gathered input result into the extraction state."""
        if isinstance(result, BaseException):
            state.error_count += 1
            return
        try:
            zip_file, result_data = result
        except (TypeError, ValueError):
            state.error_count += 1
            return

        if isinstance(result_data, Exception):
            state.error_count += 1
            state.errors[zip_file] = str(result_data)
            return

        state.success_count += 1
        state.total_records += result_data['records']
        temp_file = Path(result_data['temp_file'])
        if temp_file.exists():
            state.temp_files.append(temp_file)
        else:
            logger.warning(f'Temp file not found: {temp_file}')

    async def _merge_temp_files(
        self, state: _ExtractionState, output_path: Path
    ) -> None:
        """Merge successful temporary outputs into the final artifact."""
        if not state.temp_files:
            return
        logger.info(
            f'Starting merge of {len(state.temp_files)} temporary files...',
            extra={'temp_files': [path.name for path in state.temp_files]},
        )
        try:
            final_record_count = await merge_temp_files_streaming(
                temp_files=state.temp_files,
                final_output=output_path,
                check_resources=self.resource_policy.check_and_wait_for_resources,
            )
        except Exception as error:
            logger.exception('Failed to merge temporary files')
            state.error_count += 1
            state.errors['MERGE'] = str(error)
            return

        state.total_records = final_record_count
        logger.info(
            'Final merge completed',
            extra={
                'total_records': f'{final_record_count:,}',
                'output_file': str(output_path),
            },
        )

    @staticmethod
    def _build_summary(
        zip_files: set[str],
        output_path: Path,
        state: _ExtractionState,
    ) -> ExtractionSummary:
        """Build the stable aggregate result mapping for callers."""
        return {
            'total_files': len(zip_files),
            'success_count': state.success_count,
            'error_count': state.error_count,
            'total_records': state.total_records,
            'errors': state.errors,
            'output_file': str(output_path) if output_path.exists() else '',
        }

    async def extract_from_zip_files(
        self,
        zip_files: set[str],
        target_tpmerc_codes: set[str],
        output_path: Path,
    ) -> dict[str, Any]:
        """Extract COTAHIST input files into Parquet and return statistics."""
        self.resource_policy.adjust_batch_sizes()

        logger.info(
            'Starting extraction with incremental flush',
            extra={
                'total_files': len(zip_files),
                'target_codes_count': len(target_tpmerc_codes),
                'output_path': str(output_path),
                'processing_mode': str(self.processing_mode),
                'flush_batch_size': self.resource_policy.flush_batch_size,
                'parse_batch_size': self.resource_policy.parse_batch_size,
            },
        )

        with log_execution_time(
            logger,
            'Extract from all COTAHIST input files',
            total_files=len(zip_files),
        ):
            state = _ExtractionState()
            progress_bar = SimpleProgressBar(
                total=len(zip_files), desc='Extracting (async)'
            )
            semaphore = asyncio.Semaphore(
                self.resource_policy.max_concurrent_files
            )

            try:
                results = await asyncio.gather(
                    *[
                        self._process_single_file(
                            zip_file,
                            target_tpmerc_codes,
                            output_path,
                            semaphore,
                            progress_bar,
                        )
                        for zip_file in zip_files
                    ],
                    return_exceptions=True,
                )
            finally:
                progress_bar.close()

            for result in results:
                self._accumulate_result(result, state)

            await self._merge_temp_files(state, output_path)
            result_summary = self._build_summary(zip_files, output_path, state)
            logger.info('Extraction completed', extra=result_summary)

            return dict(result_summary)
