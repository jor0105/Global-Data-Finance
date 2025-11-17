from abc import ABC, abstractmethod


class FileExtractorRepositoryCVM(ABC):
    """Abstract interface for file extraction strategies."""

    @abstractmethod
    def extract(self, source_path: str, destination_dir: str) -> None:
        """Extract files from source to destination.

        Args:
            source_path: Path to source file (ZIP, RAR, etc.)
            destination_dir: Directory where extracted files will be saved

        Raises:
            ExtractionError: If extraction fails.
            DiskFullError: If insufficient disk space is available.
            InvalidDestinationPathError: If destination path is invalid or not writable.
        """
        pass
