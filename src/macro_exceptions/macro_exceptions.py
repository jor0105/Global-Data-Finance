from typing import Optional


class InvalidDestinationPathError(ValueError):
    def __init__(self, reason: str):
        super().__init__(f"Invalid destination path: {reason}")


class PathIsNotDirectoryError(ValueError):
    def __init__(self, path: str):
        super().__init__(
            f"Destination path must be a directory, but '{path}' is a file."
        )


class PathPermissionError(OSError):
    def __init__(self, path: str):
        super().__init__(
            f"Permission denied: No write permission for destination path '{path}'"
        )


class NetworkError(Exception):
    def __init__(self, doc_name: str, message: Optional[str] = None):
        super().__init__(
            f"Network error while downloading '{doc_name}'. {message or ''}"
        )


class TimeoutError(Exception):
    def __init__(self, doc_name: str, timeout: Optional[float] = None):
        msg = f"Timeout while downloading '{doc_name}'."
        if timeout:
            msg += f" Timeout: {timeout}s."
        super().__init__(msg)


class ExtractionError(Exception):
    def __init__(self, path: str, message: str):
        super().__init__(f"Extraction error for '{path}': {message}")


class CorruptedZipError(ExtractionError):
    def __init__(self, zip_path: str, message: str):
        super().__init__(zip_path, f"Corrupted ZIP: {message}")


class DownloadExtractionError(Exception):
    def __init__(self, doc_name: str, year: str, zip_path: str, message: str):
        self.doc_name = doc_name
        self.year = year
        self.zip_path = zip_path
        self.message = message
        super().__init__(
            f"Download/Extraction failed for '{doc_name}_{year}' ({zip_path}): {message}"
        )


class DiskFullError(OSError):
    def __init__(self, path: str):
        super().__init__(f"Insufficient disk space for saving '{path}'.")
