"""Filesystem validation helpers for B3 historical quotes."""

from pathlib import Path
from typing import Set

from ....core import get_logger
from ....core.utils import assert_path_not_sensitive
from ....macro_exceptions import (
    EmptyDirectoryError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
)

logger = get_logger(__name__)


class FileSystemServiceB3:
    """Service for file system operations.

    Uses centralized exceptions from macro_exceptions.
    Implements path traversal protection for security via the shared
    ``assert_path_not_sensitive`` helper.
    """

    @staticmethod
    def _validate_path_safety(path: Path) -> None:
        """Block writes into sensitive system or user-secret directories.

        Thin wrapper around
        :func:`globaldatafinance.core.utils.assert_path_not_sensitive`.
        Kept as a staticmethod on the service so existing callers and
        tests that depend on the method name continue to work.

        Args:
            path: A resolved ``Path`` to validate.

        Raises:
            SecurityError: If path falls inside any blocked directory.
        """
        assert_path_not_sensitive(path.resolve())

    def validate_directory_path(self, path: str) -> Path:
        """Validate that a path exists and is a directory."""
        logger.debug('Validating directory path', extra={'path': path})

        if not isinstance(path, str):
            raise TypeError(
                f'Path must be a string, got {type(path).__name__}'
            )

        if not path or path.isspace():
            raise InvalidDestinationPathError(
                'Path cannot be empty or whitespace'
            )

        normalized_path = Path(path).expanduser().resolve()

        assert_path_not_sensitive(normalized_path, raw_input=path)

        if not normalized_path.exists():
            raise PathIsNotDirectoryError(str(normalized_path))

        if not normalized_path.is_dir():
            raise PathIsNotDirectoryError(str(normalized_path))

        if not any(normalized_path.iterdir()):
            raise EmptyDirectoryError(str(normalized_path))

        logger.debug(
            'Directory path validated successfully',
            extra={'normalized_path': str(normalized_path)},
        )

        return normalized_path

    def find_files_by_years(self, directory: Path, years: range) -> Set[str]:
        """Find all files in directory that contain any year from the range."""
        year_strings = tuple(str(year) for year in years)
        if not year_strings:
            return set()

        matching_files = set()
        for file in directory.iterdir():
            if file.is_file() and any(
                year in file.name for year in year_strings
            ):
                matching_files.add(str(file))

        return matching_files
