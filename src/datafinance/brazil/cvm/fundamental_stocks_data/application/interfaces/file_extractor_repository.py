from abc import ABC, abstractmethod


class FileExtractorRepositoryCVM(ABC):
    """Abstract interface for file extraction strategies."""

    @abstractmethod
    def extract(self, zip_file_path: str) -> None:
        """Extract files from ZIP to destination.

        Args:
            zip_file_path: Path to the ZIP file to extract

        Raises:
            ExtractionError: If extraction fails.
            DiskFullError: If insufficient disk space is available.
            CorruptedZipError: If ZIP file is corrupted or invalid.
        """
        pass
