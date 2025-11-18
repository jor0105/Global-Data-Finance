from abc import ABC, abstractmethod


class FileExtractorRepositoryCVM(ABC):
    """Abstract interface for file extraction strategies."""

    @abstractmethod
    def extract(self, destination_path: str) -> None:
        """Extract files from source to destination.

        Args:
            destination_path: Directory where extracted files will be saved

        Raises:
            ExtractionError: If extraction fails.
            DiskFullError: If insufficient disk space is available.
            InvalidDestinationPathError: If destination path is invalid or not writable.
        """
        pass
