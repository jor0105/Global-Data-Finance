import logging
import os
from typing import List, Optional

from ...exceptions import (
    EmptyDocumentListError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)

logger = logging.getLogger(__name__)


class DownloadPathDTO:
    """Data Transfer Object for download path validation.

    This DTO validates and ensures the destination path exists:
    - Validates path is a string
    - Validates path is not empty
    - Creates directory if it doesn't exist
    - Validates write permissions
    - Stores optional parameters as provided (None if not provided)

    Attributes:
        destination_path: Directory path where files will be saved (validated and created if needed)
        doc_types: List of document type codes or None
        start_year: Starting year for downloads or None
        end_year: Ending year for downloads or None

    Example:
        >>> dto = DownloadPathDTO(
        ...     destination_path="/home/user/downloads",
        ...     doc_types=["DFP", "ITR"],
        ...     start_year=2020,
        ...     end_year=2023
        ... )
        >>> print(dto.destination_path)
        /home/user/downloads
    """

    destination_path: str
    doc_types: List[str]  # Will be filled by validator, never None after validation
    start_year: int  # Will be filled by validator, never None after validation
    end_year: int  # Will be filled by validator, never None after validation

    def __init__(
        self,
        destination_path: str,
        doc_types: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ):
        """Initialize and validate download path parameters.

        Args:
            destination_path: Directory path where files will be saved.
                             Will be created if it doesn't exist.
            doc_types: List of document type codes (if None, must be filled by caller)
            start_year: Starting year for downloads (if None, must be filled by caller)
            end_year: Ending year for downloads (if None, must be filled by caller)

        Raises:
            ValueError: If any validation fails (see _validate_and_create_path)
            TypeError: If parameter types are incorrect
            OSError: If directory cannot be created due to permissions
            EmptyDocumentListError: If doc_types is an empty list
            InvalidDocName: If doc_types contains invalid document names
            InvalidFirstYear: If start_year is invalid when end_year is provided
            InvalidLastYear: If end_year is invalid when start_year is provided

        Note:
            When using this DTO directly (not via ValidateDownloadRequestUseCase),
            ensure all optional parameters are provided with actual values, not None.
            The ValidateDownloadRequestUseCase fills None values with defaults.
        """
        from ...domain import AvailableDocs, AvailableYears

        self.destination_path = self._validate_and_create_path(destination_path)

        # Validate doc_types if provided and not None
        if doc_types is not None:
            # Validate empty list
            if not doc_types:
                raise EmptyDocumentListError()
            # Validate each doc type
            available_docs = AvailableDocs()
            for doc_type in doc_types:
                available_docs.validate_docs_name(doc_type)
            self.doc_types = doc_types
        else:
            # This should only happen when created with None explicitly
            # In normal flow, ValidateDownloadRequestUseCase fills defaults
            self.doc_types = []  # type: ignore[assignment]  # Temporary empty list

        # For years, we can use type ignore since validator fills them
        self.start_year = start_year if start_year is not None else 0  # type: ignore[assignment]
        self.end_year = end_year if end_year is not None else 0  # type: ignore[assignment]

        # Validate years range if both are provided
        if start_year is not None and end_year is not None:
            available_years = AvailableYears()
            available_years.return_range_years(start_year, end_year)

        logger.debug(
            f"DownloadPathDTO created: "
            f"path={self.destination_path}, "
            f"docs={self.doc_types}, "
            f"years={self.start_year}-{self.end_year}"
        )

    @staticmethod
    def _validate_and_create_path(path: str) -> str:
        """Validate path and create directory if it doesn't exist.

        Checks:
        - Type is string
        - Not empty or whitespace
        - Creates directory if needed
        - Validates write permissions on final/parent directory

        Args:
            path: Path to validate and create.

        Returns:
            Normalized absolute path.

        Raises:
            TypeError: If path is not a string.
            InvalidDestinationPathError: If path is empty or whitespace.
            PathIsNotDirectoryError: If a file exists at that path.
            PathPermissionError: If directory lacks write permissions.
            OSError: If directory cannot be created.
        """
        # Type validation
        if not isinstance(path, str):
            raise TypeError(
                f"Destination path must be a string, got {type(path).__name__}"
            )

        # Empty/whitespace validation
        if not path or path.isspace():
            raise InvalidDestinationPathError("path cannot be empty or whitespace")

        # Normalize path (expand user home and resolve relative paths)
        normalized_path = os.path.abspath(os.path.expanduser(path))

        # Check if path exists as a file (not directory)
        if os.path.exists(normalized_path):
            if not os.path.isdir(normalized_path):
                raise PathIsNotDirectoryError(normalized_path)

            # Check write permissions on existing directory
            if not os.access(normalized_path, os.W_OK):
                raise PathPermissionError(normalized_path)

            logger.debug(f"Destination directory already exists: {normalized_path}")
        else:
            # Directory doesn't exist - create it
            try:
                os.makedirs(normalized_path, exist_ok=True)
                logger.info(f"Created destination directory: {normalized_path}")
            except PermissionError as e:
                raise PathPermissionError(normalized_path) from e
            except OSError as e:
                raise OSError(
                    f"Failed to create directory {normalized_path}: {e}"
                ) from e

        logger.debug(f"Destination path validated and ready: {normalized_path}")
        return normalized_path

    def __repr__(self) -> str:
        """String representation of the DTO."""
        return (
            f"DownloadPathDTO("
            f"destination_path='{self.destination_path}', "
            f"doc_types={self.doc_types}, "
            f"start_year={self.start_year}, "
            f"end_year={self.end_year})"
        )
