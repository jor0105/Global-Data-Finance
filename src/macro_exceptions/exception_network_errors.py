from typing import Optional


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


class PermissionError(Exception):
    def __init__(self, path: str):
        super().__init__(f"Permission denied when saving to '{path}'.")


class FileNotFoundError(Exception):
    def __init__(self, path: str):
        super().__init__(f"Destination path not found: '{path}'.")


class DiskFullError(Exception):
    def __init__(self, path: str):
        super().__init__(f"Insufficient disk space for saving '{path}'.")
