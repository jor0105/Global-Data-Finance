from pathlib import Path
from typing import Protocol, Set


class IFileSystemService(Protocol):
    """Interface for file system operations."""

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
        ...

    def create_directory_if_not_exists(self, path: str) -> Path:
        """Create directory if it doesn't exist.

        Args:
            path: Path to create

        Returns:
            Normalized Path object

        Raises:
            PathPermissionError: If no write permission
        """
        ...

    def find_files_by_years(self, directory: Path, years: range) -> Set[str]:
        """Find all files in directory that contain any year from the range.

        Args:
            directory: Directory to search in
            years: Range of years to look for

        Returns:
            Set of file paths as strings
        """
        ...
