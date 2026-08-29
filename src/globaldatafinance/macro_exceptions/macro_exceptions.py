"""Shared exception types for filesystem, network, and extraction failures."""


class EmptyDirectoryError(Exception):
    """Indicate that a required directory contains no usable files."""

    def __init__(self, path: str):
        """Create an error for the empty directory path."""
        super().__init__(f'Directory is empty: {path!r}')


class InvalidDestinationPathError(ValueError):
    """Indicate that a destination path failed validation."""

    def __init__(self, reason: str):
        """Create an error with the path validation reason."""
        super().__init__(f'Invalid destination path: {reason}')


class PathIsNotDirectoryError(ValueError):
    """Indicate that a destination path points to a regular file."""

    def __init__(self, path: str):
        """Create an error for the invalid destination path."""
        super().__init__(
            f"Destination path must be a directory, but '{path}' is a file."
        )


class PathPermissionError(OSError):
    """Indicate that a destination path is not writable."""

    def __init__(self, path: str):
        """Create an error for the unwritable destination path."""
        super().__init__(
            f'Permission denied: No write permission for destination path '
            f"'{path}'"
        )


class NetworkError(Exception):
    """Indicate a network failure while downloading a document."""

    def __init__(self, doc_name: str, message: str | None = None):
        """Create an error with the document and optional detail."""
        super().__init__(
            f"Network error while downloading '{doc_name}'. {message or ''}"
        )


class TimeoutError(Exception):
    """Indicate that a document download exceeded its timeout."""

    def __init__(self, doc_name: str, timeout: float | None = None):
        """Create an error with the document and optional timeout value."""
        msg = f"Timeout while downloading '{doc_name}'."
        if timeout:
            msg += f' Timeout: {timeout}s.'
        super().__init__(msg)


class ExtractionError(Exception):
    """Indicate a failure while extracting an input archive."""

    def __init__(self, path: str, message: str):
        """Create an error with the source path and failure detail."""
        super().__init__(f"Extraction error for '{path}': {message}")


class CorruptedZipError(ExtractionError):
    """Indicate that a ZIP input is malformed or corrupted."""

    def __init__(self, zip_path: str, message: str):
        """Create an error with the ZIP path and corruption detail."""
        super().__init__(zip_path, f'Corrupted ZIP: {message}')


class DiskFullError(OSError):
    """Indicate that an output write cannot fit on the target filesystem."""

    def __init__(self, path: str):
        """Create an error for the output path that could not be written."""
        super().__init__(f"Insufficient disk space for saving '{path}'.")


class SecurityError(Exception):
    """Indicate that a path or operation violated a security boundary."""

    def __init__(self, message: str, path: str | None = None):
        """Create an error with a message and optional offending path."""
        if path:
            super().__init__(f"Security violation: {message} (path: '{path}')")
        else:
            super().__init__(f'Security violation: {message}')


class PathCreationError(OSError):
    """Indicate that a destination directory could not be created."""

    def __init__(self, path: str, reason: str | None = None):
        """Create an error with the path and optional OS reason."""
        msg = f"Failed to create directory '{path}'"
        if reason:
            msg += f': {reason}'
        super().__init__(msg)


class FileWriteError(OSError):
    """Indicate that writing a file chunk failed."""

    def __init__(self, path: str, reason: str | None = None):
        """Create an error with the path and optional OS reason."""
        msg = f"Failed to write chunk to '{path}'"
        if reason:
            msg += f': {reason}'
        super().__init__(msg)


class ParquetWriteError(OSError):
    """Indicate that writing a Parquet output failed."""

    def __init__(self, path: str, reason: str | None = None):
        """Create an error with the path and optional OS reason."""
        msg = f"Failed to write Parquet file '{path}'"
        if reason:
            msg += f': {reason}'
        super().__init__(msg)
