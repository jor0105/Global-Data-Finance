"""ZIP → Parquet extractor for CVM regulatory document archives.

Implements direct and robust extraction of downloaded ZIP files into structured
Parquet datasets with automatic error handling and filesystem rollback support.
"""

import zipfile

from ....core import get_logger
from ....macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    SecurityError,
)
from ....macro_infra import ExtractorAdapter
from .transaction import CvmFailureAtomicBatchCommit

logger = get_logger(__name__)


class ParquetExtractorAdapterCVM:
    """Extracts ZIP files containing CSVs and converts to Parquet format."""

    def __init__(self) -> None:
        """Initialize the generic archive extraction adapter."""
        self.extractor_adapter = ExtractorAdapter()

    def extract(self, source_path: str, destination_path: str) -> None:
        """Extract ZIP to Parquet with a failure-atomic batch commit."""
        try:
            logger.info('Starting Parquet extraction from %s', source_path)

            with zipfile.ZipFile(source_path, 'r') as zip_file:
                transaction = CvmFailureAtomicBatchCommit(
                    source_path=source_path,
                    destination_path=destination_path,
                    extractor_adapter=self.extractor_adapter,
                )
                transaction.execute(zip_file)

            logger.info(
                'Parquet extraction completed successfully: %s', source_path
            )

        except zipfile.BadZipFile as error:
            raise CorruptedZipError(source_path, str(error)) from error

        except (
            ExtractionError,
            CorruptedZipError,
            DiskFullError,
            SecurityError,
        ):
            raise

        except Exception as e:
            logger.error(
                'Unexpected error during extraction of %s: %s',
                source_path,
                e,
                exc_info=True,
            )
            raise ExtractionError(
                source_path,
                f'Unexpected extraction error: {type(e).__name__}: {e}',
            ) from e
