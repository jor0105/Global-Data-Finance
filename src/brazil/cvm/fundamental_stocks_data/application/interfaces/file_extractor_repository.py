from abc import ABC, abstractmethod


class FileExtractorRepository(ABC):
    """Abstract interface for file extraction strategies.

    This interface allows different extraction implementations to be injected
    into download adapters, maintaining the Single Responsibility Principle
    while enabling asynchronous download+extraction pipelines.

    The extractor is called after each file is downloaded, allowing parallel
    processing of multiple files (download + extract + cleanup) simultaneously.

    Example:
        >>> extractor = ParquetExtractor(chunk_size=50000)
        >>> extractor.extract("/path/to/file.zip", "/path/to/output")
    """

    @abstractmethod
    def extract(self, source_path: str, destination_dir: str) -> None:
        """Extract files from source to destination.

        This method is called after a file is successfully downloaded.
        It should handle extraction, conversion, and any necessary cleanup
        of partial files in case of errors.

        Args:
            source_path: Path to source file (ZIP, RAR, etc.)
            destination_dir: Directory where extracted files will be saved

        Raises:
            ExtractionError: If extraction fails (corrupted file, conversion error, etc.)
            DiskFullError: If insufficient disk space is available
            InvalidDestinationPathError: If destination path is invalid or not writable

        Note:
            Implementations should clean up partial files on error to avoid
            leaving the filesystem in an inconsistent state.
        """
        pass
