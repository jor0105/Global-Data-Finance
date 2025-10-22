from typing import Optional


class WgetLibraryError(Exception):
    """Raised when wget library encounters an error.

    This exception wraps errors that occur when using the wget library
    for file downloads.
    """

    def __init__(self, doc_name: str, message: Optional[str] = None):
        """Initialize the exception with document name and error details.

        Args:
            doc_name: Name of the document being downloaded.
            message: Optional detailed error message from wget.
        """
        super().__init__(f"Wget library error for '{doc_name}'. {message or ''}")


class WgetValueError(Exception):
    """Raised when wget receives invalid parameter values.

    This exception indicates that an invalid value was passed to wget.
    """

    def __init__(self, value):
        """Initialize the exception with the invalid value.

        Args:
            value: The invalid value that was provided.
        """
        super().__init__(f"Value error: got invalid value '{value}'.")
