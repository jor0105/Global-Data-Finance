import os
from pathlib import Path
from typing import Set

from src.core import get_logger
from src.macro_exceptions import (
    EmptyDirectoryError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
    SecurityError,
)

logger = get_logger(__name__)


class FileSystemService:
    """Service for file system operations.

    Uses centralized exceptions from macro_exceptions.
    Implements path traversal protection for security.
    """

    @staticmethod
    def _validate_path_safety(path: Path) -> None:
        """Validate that resolved path doesn't traverse to sensitive system directories.

        This prevents path traversal attacks where malicious paths like
        '../../../etc/passwd' could access sensitive system files.

        Args:
            path: Path to validate (should be resolved)

        Raises:
            SecurityError: If path traversal to sensitive directories is detected
        """
        resolved = path.resolve()

        # Block access to sensitive system directories
        sensitive_dirs = [
            Path("/etc"),
            Path("/root"),
            Path("/sys"),
            Path("/proc"),
            Path("/dev"),
            Path("/boot"),
        ]

        for sensitive_dir in sensitive_dirs:
            try:
                # Check if the path is inside a sensitive directory
                resolved.relative_to(sensitive_dir)
                raise SecurityError(
                    f"Access to sensitive system directory denied: '{resolved}' "
                    f"is within protected path '{sensitive_dir}'",
                    path=str(path),
                )
            except ValueError:
                # Path is not relative to this sensitive dir - that's good
                continue

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
            SecurityError: If path traversal detected
        """
        logger.debug("Validating directory path", extra={"path": path})

        if not isinstance(path, str):
            raise TypeError(f"Path must be a string, got {type(path).__name__}")

        if not path or path.isspace():
            raise InvalidDestinationPathError("Path cannot be empty or whitespace")

        normalized_path = Path(path).expanduser().resolve()

        self._validate_path_safety(normalized_path)

        if not normalized_path.exists():
            raise PathIsNotDirectoryError(str(normalized_path))

        if not normalized_path.is_dir():
            raise PathIsNotDirectoryError(str(normalized_path))

        if not any(normalized_path.iterdir()):
            raise EmptyDirectoryError(str(normalized_path))

        logger.debug(
            "Directory path validated successfully",
            extra={"normalized_path": str(normalized_path)},
        )

        return normalized_path

    def create_directory_if_not_exists(self, path: str) -> Path:
        """Create directory if it doesn't exist.

        Args:
            path: Path to create

        Returns:
            Normalized Path object

        Raises:
            PathPermissionError: If no write permission
            SecurityError: If path traversal detected
        """
        logger.debug("Creating directory if not exists", extra={"path": path})

        if not isinstance(path, str):
            raise TypeError(f"Path must be a string, got {type(path).__name__}")

        if not path or path.isspace():
            raise InvalidDestinationPathError("Path cannot be empty or whitespace")

        normalized_path = Path(path).expanduser().resolve()

        self._validate_path_safety(normalized_path)

        if normalized_path.exists():
            if not normalized_path.is_dir():
                raise PathIsNotDirectoryError(str(normalized_path))

            if not os.access(str(normalized_path), os.W_OK):
                raise PathPermissionError(str(normalized_path))

            logger.debug(
                "Directory already exists",
                extra={"path": str(normalized_path)},
            )
        else:
            try:
                normalized_path.mkdir(parents=True, exist_ok=True)
                logger.info(
                    "Created directory",
                    extra={"path": str(normalized_path)},
                )
            except PermissionError as e:
                logger.error(
                    "Permission denied creating directory",
                    extra={"path": str(normalized_path)},
                    exc_info=True,
                )
                raise PathPermissionError(str(normalized_path)) from e
            except OSError as e:
                logger.error(
                    "Failed to create directory",
                    extra={"path": str(normalized_path), "error": str(e)},
                    exc_info=True,
                )
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
