import os
from pathlib import Path
from typing import Set

from src.macro_exceptions import (
    EmptyDirectoryError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)


class FileSystemService:
    """Service for file system operations.

    Uses centralized exceptions from macro_exceptions.
    """

    def validate_directory_path(self, path: str) -> Path:
        """Validate that a path exists and is a directory.

        Args:
            path: Path to validate

        Returns:
            Normalized Path object

        Raises:
            InvalidDestinationPathError: If path is invalid
            PathIsNotDirectoryError: If path is not a directory
            EmptyDirectoryError: If directory is empty
        """
        if not isinstance(path, str):
            raise TypeError(f"Path must be a string, got {type(path).__name__}")

        if not path or path.isspace():
            raise InvalidDestinationPathError("Path cannot be empty or whitespace")

        normalized_path = Path(path).expanduser().resolve()

        if not normalized_path.exists():
            raise PathIsNotDirectoryError(str(normalized_path))

        if not normalized_path.is_dir():
            raise PathIsNotDirectoryError(str(normalized_path))

        if not any(normalized_path.iterdir()):
            raise EmptyDirectoryError(str(normalized_path))

        return normalized_path

    def create_directory_if_not_exists(self, path: str) -> Path:
        """Create directory if it doesn't exist.

        Args:
            path: Path to create

        Returns:
            Normalized Path object

        Raises:
            PathPermissionError: If no write permission
        """
        if not isinstance(path, str):
            raise TypeError(f"Path must be a string, got {type(path).__name__}")

        if not path or path.isspace():
            raise InvalidDestinationPathError("Path cannot be empty or whitespace")

        normalized_path = Path(path).expanduser().resolve()

        if normalized_path.exists():
            if not normalized_path.is_dir():
                raise PathIsNotDirectoryError(str(normalized_path))

            if not os.access(str(normalized_path), os.W_OK):
                raise PathPermissionError(str(normalized_path))
        else:
            try:
                normalized_path.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PathPermissionError(str(normalized_path)) from e
            except OSError as e:
                raise OSError(
                    f"Failed to create directory {normalized_path}: {e}"
                ) from e

        return normalized_path

    def find_files_by_years(self, directory: Path, years: range) -> Set[str]:
        """Find all files in directory that contain any year from the range.

        Args:
            directory: Directory to search in
            years: Range of years to look for

        Returns:
            Set of file paths as strings
        """
        document_set = set()
        for year in years:
            for file in directory.iterdir():
                if file.is_file() and str(year) in file.name:
                    document_set.add(str(file))
        return document_set
