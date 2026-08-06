class EmptyDirectoryError(Exception):
    def __init__(self, path):
        super().__init__(f'Directory is empty: {path!r}')


class InvalidDestinationPathError(ValueError):
    def __init__(self, reason: str):
        super().__init__(f'Invalid destination path: {reason}')


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
    def __init__(self, doc_name: str, message: str | None = None):
        super().__init__(
            f"Network error while downloading '{doc_name}'. {message or ''}"
        )


class TimeoutError(Exception):
    def __init__(self, doc_name: str, timeout: float | None = None):
        msg = f"Timeout while downloading '{doc_name}'."
        if timeout:
            msg += f' Timeout: {timeout}s.'
        super().__init__(msg)


class ExtractionError(Exception):
    def __init__(self, path: str, message: str):
        super().__init__(f"Extraction error for '{path}': {message}")


class CorruptedZipError(ExtractionError):
    def __init__(self, zip_path: str, message: str):
        super().__init__(zip_path, f'Corrupted ZIP: {message}')


class DiskFullError(OSError):
    def __init__(self, path: str):
        super().__init__(f"Insufficient disk space for saving '{path}'.")


class SecurityError(Exception):
    def __init__(self, message: str, path: str | None = None):
        if path:
            super().__init__(f"Security violation: {message} (path: '{path}')")
        else:
            super().__init__(f'Security violation: {message}')


class PathCreationError(OSError):
    def __init__(self, path: str, reason: str | None = None):
        msg = f"Failed to create directory '{path}'"
        if reason:
            msg += f': {reason}'
        super().__init__(msg)


class FileWriteError(OSError):
    def __init__(self, path: str, reason: str | None = None):
        msg = f"Failed to write chunk to '{path}'"
        if reason:
            msg += f': {reason}'
        super().__init__(msg)


class ParquetWriteError(OSError):
    def __init__(self, path: str, reason: str | None = None):
        msg = f"Failed to write Parquet file '{path}'"
        if reason:
            msg += f': {reason}'
        super().__init__(msg)
