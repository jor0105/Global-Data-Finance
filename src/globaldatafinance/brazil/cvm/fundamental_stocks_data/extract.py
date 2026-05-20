"""ZIP → Parquet extractor for CVM data.

Moved from `infra/adapters/extractors_docs_adapter/`. ABC inheritance dropped
(`FileExtractorRepositoryCVM`) — the single-impl interface added no runtime
value (per design.md R2 / tasks 3.2.x).
"""

import zipfile
from pathlib import Path
from typing import List, cast

from ....core import get_logger
from ....macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
)
from ....macro_infra import ExtractorAdapter

logger = get_logger(__name__)


class ParquetExtractorAdapterCVM:
    """Extracts ZIP files containing CSVs and converts to Parquet format."""

    MAX_FALLBACK_SIZE_MB = 500

    def __init__(self) -> None:
        self.extractor_adapter = ExtractorAdapter()

    def extract(self, source_path: str, destination_path: str) -> None:
        """Extract ZIP to Parquet files with atomic transaction guarantee."""
        try:
            logger.info(f'Starting Parquet extraction from {source_path}')

            self.__extract_with_transaction(source_path, destination_path)

            logger.info(
                f'Parquet extraction completed successfully: {source_path}'
            )

        except (
            ExtractionError,
            CorruptedZipError,
            DiskFullError,
        ):
            raise

        except Exception as e:
            logger.error(
                f'Unexpected error during extraction of {source_path}: {e}'
            )
            raise ExtractionError(
                source_path,
                f'Unexpected extraction error: {type(e).__name__}: {e}',
            )

    def __extract_with_transaction(
        self, zip_path: str, destination_path: str
    ) -> None:
        """Extract with atomic transaction (all-or-nothing)."""
        extracted_count = 0
        failed_files = []
        created_files = []

        output_dir = Path(destination_path)

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                csv_files = self.extractor_adapter.list_files_in_zip(
                    zip_path, '.csv'
                )

                for csv_filename in csv_files:
                    parquet_filename = Path(csv_filename).stem + '.parquet'
                    parquet_path = output_dir / parquet_filename

                    try:
                        self.extractor_adapter.extract_csv_from_zip_to_parquet(
                            z, parquet_path, parquet_filename, csv_filename
                        )

                        if parquet_path.exists():
                            created_files.append(parquet_path)
                            logger.debug(
                                f'Registered created file: {parquet_filename}'
                            )

                        extracted_count += 1

                    except DiskFullError:
                        raise
                    except Exception as e:
                        logger.error(f'Failed to extract {csv_filename}: {e}')
                        failed_files.append((csv_filename, str(e)))
                        continue

                if failed_files:
                    self.__rollback_extraction(
                        created_files, failed_files, zip_path
                    )

        except zipfile.BadZipFile as e:
            self.__cleanup_files(created_files, 'ZIP corruption')
            raise CorruptedZipError(
                zip_path, f'Invalid or corrupted ZIP file: {e}'
            )

        except ExtractionError:
            self.__cleanup_files(created_files, 'extraction error')
            raise

        except DiskFullError:
            self.__cleanup_files(created_files, 'disk full')
            raise

        except Exception as e:
            self.__cleanup_files(created_files, 'unexpected error')
            raise ExtractionError(
                zip_path, f'Unexpected error during extraction: {e}'
            )

        logger.info(
            f'Successfully extracted {extracted_count} CSV files from {zip_path}'
        )

    def __rollback_extraction(
        self,
        created_files: list[Path],
        failed_files: list[tuple[str, str]],
        zip_path: str,
    ) -> None:
        """Rollback partial extraction (atomic behavior)."""
        failed_list = '; '.join([f'{f[0]}: {f[1]}' for f in failed_files])

        logger.warning(
            f'Partial extraction detected. Rolling back {len(created_files)} files...'
        )

        result = self.__cleanup_files(
            created_files, 'rollback', return_stats=True
        )
        cleanup_count, cleanup_errors = cast(tuple[int, List[str]], result)

        logger.info(
            f'Rollback complete: {cleanup_count} partial files removed'
        )

        if cleanup_errors:
            cleanup_msg = '; '.join(cleanup_errors)
            logger.error(
                f'WARNING: Some files could not be removed: {cleanup_msg}'
            )

        raise ExtractionError(
            zip_path,
            f'Atomic extraction failed: {len(failed_files)} files failed. '
            f'All partial data rolled back. Failures: {failed_list}',
        )

    def __cleanup_files(
        self,
        files: list[Path],
        reason: str,
        return_stats: bool = False,
    ) -> tuple[int, List[str]] | None:
        """Clean up files with error tracking."""
        cleanup_count = 0
        cleanup_errors: List[str] = []

        logger.info(f'Cleaning up {len(files)} files due to: {reason}')

        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    cleanup_count += 1
                    logger.debug(f'Cleaned up: {file_path.name}')
            except Exception as err:
                error_msg = f'{file_path.name}: {err}'
                cleanup_errors.append(error_msg)
                logger.error(f'Failed to cleanup {file_path.name}: {err}')

        if return_stats:
            return cleanup_count, cleanup_errors
        return None
