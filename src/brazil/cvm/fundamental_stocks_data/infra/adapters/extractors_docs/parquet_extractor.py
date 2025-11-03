import logging

from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
    FileExtractorRepository,
)
from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
)
from src.macro_infra import Extractor

logger = logging.getLogger(__name__)


class ParquetExtractor(FileExtractorRepository):
    """Extracts ZIP files containing CSVs and converts to Parquet format."""

    def __init__(self, chunk_size: int = 50000):
        """Initialize ParquetExtractor with optional chunk size."""
        self.chunk_size = chunk_size
        logger.debug(f"ParquetExtractor initialized with chunk_size={chunk_size}")

    def extract(self, source_path: str, destination_dir: str) -> None:
        """Extract ZIP to Parquet files.

        Args:
            source_path: Path to ZIP file containing CSV files.
            destination_dir: Directory where Parquet files will be saved.
        """
        try:
            logger.info(f"Starting Parquet extraction from {source_path}")

            Extractor.extract_zip_to_parquet(
                self.chunk_size, source_path, destination_dir
            )

            logger.info(f"Parquet extraction completed successfully: {source_path}")

        except (
            ExtractionError,
            CorruptedZipError,
            DiskFullError,
            InvalidDestinationPathError,
        ):
            raise

        except Exception as e:
            logger.error(f"Unexpected error during extraction of {source_path}: {e}")
            raise ExtractionError(
                source_path, f"Unexpected extraction error: {type(e).__name__}: {e}"
            )
