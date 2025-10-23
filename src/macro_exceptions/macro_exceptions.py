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


class DiskFullError(Exception):
    def __init__(self, path: str):
        super().__init__(f"Insufficient disk space for saving '{path}'.")
