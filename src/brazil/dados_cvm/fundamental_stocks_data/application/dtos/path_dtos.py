import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


class DownloadPathDTO:
    """Data Transfer Object for download path validation.

    This DTO validates and ensures the destination path exists:
    - Validates path is a string
    - Validates path is not empty
    - Creates directory if it doesn't exist
    - Validates write permissions

    Attributes:
        destination_path: Directory path where files will be saved (validated and created if needed)
        doc_types: List of document type codes (e.g., ["DFP", "ITR"])
        start_year: Starting year for downloads (inclusive, optional)
        end_year: Ending year for downloads (inclusive, optional)

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
            doc_types: List of document type codes (default: None, all types)
            start_year: Starting year for downloads (default: None)
            end_year: Ending year for downloads (default: None)

        Raises:
            ValueError: If any validation fails (see _validate_and_create_path)
            TypeError: If parameter types are incorrect
            OSError: If directory cannot be created due to permissions
        """
        self.destination_path = self._validate_and_create_path(destination_path)
        self.doc_types = doc_types
        self.start_year = start_year
        self.end_year = end_year

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
            ValueError: If path is empty, whitespace, or if a file exists at that path.
            OSError: If directory cannot be created due to permissions.
        """
        # Type validation
        if not isinstance(path, str):
            raise TypeError(
                f"destination_path must be a string, got {type(path).__name__}"
            )

        # Empty/whitespace validation
        if not path or path.isspace():
            raise ValueError("destination_path cannot be empty or whitespace")

        # Normalize path (expand user home and resolve relative paths)
        normalized_path = os.path.abspath(os.path.expanduser(path))

        # Check if path exists as a file (not directory)
        if os.path.exists(normalized_path):
            if not os.path.isdir(normalized_path):
                raise ValueError(
                    f"destination_path must be a directory, got file: {normalized_path}"
                )

            # Check write permissions on existing directory
            if not os.access(normalized_path, os.W_OK):
                raise ValueError(
                    f"destination_path has no write permission: {normalized_path}"
                )

            logger.debug(f"Destination directory already exists: {normalized_path}")
        else:
            # Directory doesn't exist - create it
            try:
                os.makedirs(normalized_path, exist_ok=True)
                logger.info(f"Created destination directory: {normalized_path}")
            except PermissionError as e:
                raise OSError(
                    f"Permission denied creating directory: {normalized_path}"
                ) from e
            except FileExistsError as e:
                # This shouldn't happen with exist_ok=True, but handle it anyway
                raise OSError(
                    f"Cannot create directory (file exists): {normalized_path}"
                ) from e
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
