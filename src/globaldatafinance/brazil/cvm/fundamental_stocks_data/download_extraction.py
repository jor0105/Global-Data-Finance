"""Automatic extraction handling for CVM downloads."""

from collections.abc import Callable

from ....core import get_logger, remove_file
from ....macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
)
from .core import DownloadResultCVM
from .download_validation import find_parquet_files, validate_parquet_files
from .extract import ParquetExtractorAdapterCVM

logger = get_logger(__name__)


def extract_downloaded_file(
    file_extractor_repository: ParquetExtractorAdapterCVM,
    filepath: str,
    dest_path: str,
    doc_name: str,
    year: str,
    result: DownloadResultCVM,
    cleanup_file: Callable[[str], None] = remove_file,
) -> None:
    document_key = f'{doc_name}_{year}'

    try:
        logger.info(f'Starting extraction for {document_key}')
        file_extractor_repository.extract(filepath, dest_path)

        parquet_files = find_parquet_files(dest_path)
        if not parquet_files:
            logger.warning(
                f'Extraction completed but no .parquet files found in '
                f'{dest_path} (including subdirectories). Keeping source '
                f'ZIP: {filepath}'
            )
            result.add_error_downloads(
                document_key,
                'No parquet files generated after extraction',
            )
            return

        if not validate_parquet_files(parquet_files, doc_name, year):
            result.add_error_downloads(
                document_key,
                'Parquet validation failed: corrupted or empty files',
            )
            return

        result.add_success_downloads(document_key)
        logger.info(
            f'Extraction completed for {document_key}: '
            f'{len(parquet_files)} parquet files created'
        )
        cleanup_file(filepath)

    except DiskFullError as disk_err:
        logger.error(
            f'Disk full during extraction of {document_key}: {disk_err}'
        )
        result.add_error_downloads(document_key, f'DiskFull: {disk_err}')
        cleanup_file(filepath)

    except CorruptedZipError as zip_err:
        logger.error(
            f'Corrupted ZIP detected during extraction of {document_key}: '
            f'{zip_err}'
        )
        result.add_error_downloads(document_key, f'CorruptedZIP: {zip_err}')
        cleanup_file(filepath)

    except ExtractionError as extract_err:
        logger.error(f'Extraction error for {document_key}: {extract_err}')
        result.add_error_downloads(
            document_key, f'ExtractionFailed: {extract_err}'
        )
        logger.info(f'Keeping ZIP for manual investigation: {filepath}')

    except Exception as unexpected_err:
        logger.error(
            f'Unexpected extraction error for {document_key}: '
            f'{type(unexpected_err).__name__}: {unexpected_err}',
            exc_info=True,
        )
        result.add_error_downloads(
            document_key,
            f'UnexpectedError: {type(unexpected_err).__name__}: '
            f'{unexpected_err}',
        )
        logger.info(f'Keeping ZIP for debugging: {filepath}')
