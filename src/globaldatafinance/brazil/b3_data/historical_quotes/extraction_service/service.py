import asyncio
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


class ExtractionServiceB3:
    """Extract COTAHIST ZIP data using bounded concurrency and incremental flush."""

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

    def __del__(self):
        """Fallback cleanup when callers forget to close the service."""
        self.close()

    async def extract_from_zip_files(
        self,
        zip_files: set[str],
        target_tpmerc_codes: set[str],
        output_path: Path,
    ) -> dict[str, Any]:
        """Extract ZIP files into one final parquet file and return statistics."""
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
            logger, 'Extract from all ZIP files', total_files=len(zip_files)
        ):
            total_records_written = 0
            success_count = 0
            error_count = 0
            errors: dict[str, str] = {}
            temp_files: list[Path] = []

            progress_bar = SimpleProgressBar(
                total=len(zip_files), desc='Extracting (async)'
            )
            semaphore = asyncio.Semaphore(
                self.resource_policy.max_concurrent_files
            )

            async def process_single_file(
                zip_file: str,
            ) -> ProcessSingleFileResult:
                if not await self.resource_policy.wait_for_resources(
                    timeout_seconds=30
                ):
                    error_msg = 'Resources exhausted'
                    logger.error(f'Skipping {zip_file} - {error_msg}')
                    progress_bar.update(1)
                    return (zip_file, Exception(error_msg))

                async with semaphore:
                    try:
                        result_data = await self.zip_processor.process(
                            zip_file=zip_file,
                            target_tpmerc_codes=target_tpmerc_codes,
                            output_path=output_path,
                        )

                        logger.info(
                            f'Completed {zip_file}',
                            extra={
                                'records_extracted': result_data['records'],
                                'temp_file': result_data['temp_file'],
                            },
                        )
                        progress_bar.update(1)
                        return (zip_file, result_data)

                    except Exception as e:
                        logger.error(
                            f'Error processing {zip_file}: {e}', exc_info=True
                        )
                        progress_bar.update(1)
                        return (zip_file, e)

            try:
                results = await asyncio.gather(
                    *[process_single_file(zip_file) for zip_file in zip_files],
                    return_exceptions=True,
                )
            finally:
                progress_bar.close()

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
                    success_count += 1
                    total_records_written += result_data['records']
                    temp_file_path = Path(result_data['temp_file'])
                    if temp_file_path.exists():
                        temp_files.append(temp_file_path)
                    else:
                        logger.warning(
                            f'Temp file not found: {temp_file_path}'
                        )

            if temp_files:
                logger.info(
                    f'Starting merge of {len(temp_files)} temporary files...',
                    extra={'temp_files': [f.name for f in temp_files]},
                )

                try:
                    final_record_count = await merge_temp_files_streaming(
                        temp_files=temp_files,
                        final_output=output_path,
                        check_resources=self.resource_policy.check_and_wait_for_resources,
                    )
                    total_records_written = final_record_count

                    logger.info(
                        'Final merge completed',
                        extra={
                            'total_records': f'{final_record_count:,}',
                            'output_file': str(output_path),
                        },
                    )
                except Exception as e:
                    logger.error(
                        f'Failed to merge temporary files: {e}', exc_info=True
                    )
                    error_count += 1
                    errors['MERGE'] = str(e)

            output_file = str(output_path) if output_path.exists() else ''
            result_summary: ExtractionSummary = {
                'total_files': len(zip_files),
                'success_count': success_count,
                'error_count': error_count,
                'total_records': total_records_written,
                'errors': errors,
                'output_file': output_file,
            }

            logger.info('Extraction completed', extra=result_summary)

            return dict(result_summary)
