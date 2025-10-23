from typing import List


class InvalidFirstYear(Exception):
    """Raised when the first year is outside valid bounds.

    This exception indicates that the start year for data retrieval is either
    before the minimum available year or after the current year.
    """

    def __init__(self, minimal_first_year: int, atual_year: int):
        """Initialize the exception with year constraints.

        Args:
            minimal_first_year: Minimum acceptable year.
            atual_year: Maximum acceptable year (typically current year).
        """
        super().__init__(
            f"Invalid first year. You must provide an integer value greater than or equal to {minimal_first_year} year and less than or equal to {atual_year}."
        )


class InvalidLastYear(Exception):
    """Raised when the last year is outside valid bounds.

    This exception indicates that the end year is either before the start year
    or after the current year.
    """

    def __init__(self, first_year: int, atual_year: int):
        """Initialize the exception with year constraints.

        Args:
            first_year: Start year that must be less than or equal to this value.
            atual_year: Maximum acceptable year (typically current year).
        """
        super().__init__(
            f"Invalid last year. You must provide an integer value greater than or equal to the {first_year} year and less than or equal to {atual_year}."
        )


class InvalidDocName(Exception):
    """Raised when an invalid document name is provided.

    This exception indicates that the requested document type code is not
    recognized or supported by the system.
    """

    def __init__(self, doc_name: str, list_available_docs: List):
        """Initialize the exception with invalid document and available options.

        Args:
            doc_name: The invalid document name that was provided.
            list_available_docs: List of valid document names for reference.
        """
        super().__init__(
            f"Invalid document name: {doc_name}. Documents must be a string and one of: {list_available_docs}."
        )


class InvalidTypeDoc(Exception):
    """Raised when document parameter has incorrect type.

    This exception indicates that the document name was not provided as a string.
    """

    def __init__(self, doc_name: str):
        """Initialize the exception with the invalid value.

        Args:
            doc_name: The value that was not a string.
        """
        super().__init__(
            f"Invalid type document: {doc_name}. Documents must be a string."
        )


class EmptyDocumentListError(Exception):
    """Raised when an empty document list is provided.

    This exception indicates that a list of documents was provided but contains
    no elements, which is invalid for download operations.
    """

    def __init__(self):
        """Initialize the exception."""
        super().__init__(
            "Document list cannot be empty. Provide at least one document type or use None for all types."
        )


class InvalidDestinationPathError(ValueError):
    """Raised when destination path is invalid.

    This exception indicates that the provided destination path is invalid,
    such as being empty, whitespace-only, or not a string.
    """

    def __init__(self, reason: str):
        """Initialize the exception with the reason.

        Args:
            reason: Explanation of why the path is invalid.
        """
        super().__init__(f"Invalid destination path: {reason}")


class PathIsNotDirectoryError(ValueError):
    """Raised when path exists but is a file instead of directory.

    This exception indicates that the destination path points to a file
    when a directory is required.
    """

    def __init__(self, path: str):
        """Initialize the exception with the path.

        Args:
            path: The path that is a file instead of directory.
        """
        super().__init__(
            f"Destination path must be a directory, but '{path}' is a file."
        )


class PathPermissionError(OSError):
    """Raised when path lacks write permissions.

    This exception indicates that the destination directory exists but
    the current user lacks write permissions.
    """

    def __init__(self, path: str):
        """Initialize the exception with the path.

        Args:
            path: The path without write permissions.
        """
        super().__init__(
            f"Permission denied: No write permission for destination path '{path}'"
        )


class InvalidRepositoryTypeError(TypeError):
    """Raised when repository is not the correct type.

    This exception indicates that a repository instance does not implement
    the expected interface.
    """

    def __init__(self, expected_type: str, actual_type: str):
        """Initialize the exception with type information.

        Args:
            expected_type: The expected type/interface name.
            actual_type: The actual type that was provided.
        """
        super().__init__(
            f"Repository must be an instance of {expected_type}, got {actual_type}."
        )
