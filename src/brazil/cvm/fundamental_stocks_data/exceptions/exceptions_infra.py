from typing import Optional


class WgetLibraryError(Exception):
    def __init__(self, doc_name: str, message: Optional[str] = None):
        super().__init__(f"Wget library error for '{doc_name}'. {message or ''}")


class WgetValueError(Exception):
    def __init__(self, value):
        super().__init__(f"Value error: got invalid value '{value}'.")
