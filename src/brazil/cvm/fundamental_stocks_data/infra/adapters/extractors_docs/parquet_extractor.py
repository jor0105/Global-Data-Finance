from src.brazil.cvm.fundamental_stocks_data.application import (
    FileExtractorRepository,
)
from src.core import get_logger
from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
)
from src.macro_infra import Extractor

logger = get_logger(__name__)


class ParquetExtractor(FileExtractorRepository):
    """Extracts ZIP files containing CSVs and converts to Parquet format.

    This implementation uses the core Extractor utility to handle the actual
    conversion while providing a clean interface that can be injected into
    download adapters.

    The extractor processes CSV files in chunks to optimize memory usage,
    making it suitable for large datasets.

    Attributes:
        chunk_size: Number of rows per chunk for memory optimization during conversion

    Example:
        >>> extractor = ParquetExtractor(chunk_size=50000)
        >>> extractor.extract("/tmp/data.zip", "/tmp/output")
    """

    def __init__(self, chunk_size: int = 50000):
        """Initialize ParquetExtractor."""
        self.chunk_size = chunk_size
        logger.debug(f"ParquetExtractor initialized with chunk_size={chunk_size}")

    def extract(self, source_path: str, destination_dir: str) -> None:
        """Extract ZIP to Parquet files.

        Processes all CSV files found in the ZIP archive and converts them
        to Parquet format for efficient storage and querying.

        Args:
            source_path: Path to ZIP file containing CSV files
            destination_dir: Directory where Parquet files will be saved

        Raises:
            ExtractionError: If ZIP is invalid or CSV conversion fails
            CorruptedZipError: If ZIP file is corrupted or cannot be read
            DiskFullError: If insufficient disk space is available
            InvalidDestinationPathError: If destination path is invalid or not writable

        Note:
            - Automatically creates destination directory if it doesn't exist
            - Cleans up partial Parquet files if extraction fails
            - Deletes the source ZIP file after successful extraction

        Example:
            >>> extractor = ParquetExtractor()
            >>> extractor.extract("/data/dfp_2023.zip", "/data/output")
            # Creates /data/output/file1.parquet, /data/output/file2.parquet, etc.
        """
        try:
            logger.info(f"Starting Parquet extraction from {source_path}")

            # Delegate to core Extractor which handles all the heavy lifting
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
            # Re-raise known extraction errors as-is
            raise

        except Exception as e:
            # Wrap unexpected errors in ExtractionError
            logger.error(f"Unexpected error during extraction of {source_path}: {e}")
            raise ExtractionError(
                source_path, f"Unexpected extraction error: {type(e).__name__}: {e}"
            )
