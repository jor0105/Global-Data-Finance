from abc import ABC, abstractmethod


class FileExtractorRepositoryCVM(ABC):
    """Abstract interface for file extraction strategies."""

    @abstractmethod
    def extract(self, source_path: str, destination_path: str) -> None:
        """Extract files from source to destination.

        Args:
            source_path: Path to the source file (e.g., ZIP) to extract.
            destination_path: Path where the extracted files should be placed.

        Raises:
            ExtractionError: If extraction fails.
            DiskFullError: If insufficient disk space is available.
            CorruptedZipError: If ZIP file is corrupted or invalid.
        """
        pass
