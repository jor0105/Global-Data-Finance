"""Filesystem validation helpers for B3 historical quotes."""

import os
import re
from pathlib import Path

from ....core import get_logger
from ....core.utils import assert_path_not_sensitive
from ....macro_exceptions import (
    EmptyDirectoryError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)

logger = get_logger(__name__)

_COTAHIST_YEAR_PATTERN = re.compile(
    r'^COTAHIST_A(\d{4})\.(?:ZIP|TXT)$',
    re.IGNORECASE,
)


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

        normalized_path = self._normalize_path(
            path,
            type_label='Path',
            empty_message='Path cannot be empty or whitespace',
        )

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

    def prepare_destination_path(self, path: str) -> Path:
        """Validate or create a writable extraction destination directory."""
        normalized_path = self._normalize_path(
            path,
            type_label='Destination path',
            empty_message='path cannot be empty or whitespace',
        )

        if normalized_path.exists():
            if not normalized_path.is_dir():
                raise PathIsNotDirectoryError(str(normalized_path))
            if not os.access(str(normalized_path), os.W_OK):
                raise PathPermissionError(str(normalized_path))
            return normalized_path

        try:
            normalized_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise PathPermissionError(str(normalized_path)) from exc
        except OSError as exc:
            raise OSError(
                f'Failed to create directory {normalized_path}: {exc}'
            ) from exc

        return normalized_path

    @staticmethod
    def _normalize_path(
        path: str,
        *,
        type_label: str,
        empty_message: str,
    ) -> Path:
        if not isinstance(path, str):
            raise TypeError(
                f'{type_label} must be a string, got {type(path).__name__}'
            )

        if not path or path.isspace():
            raise InvalidDestinationPathError(empty_message)

        normalized_path = Path(path).expanduser().resolve()
        assert_path_not_sensitive(normalized_path, raw_input=path)
        return normalized_path

    def find_files_by_years(self, directory: Path, years: range) -> set[str]:
        """Find official COTAHIST files whose year is in the given range.

        Only files matching the official annual B3 naming contract
        ``COTAHIST_A{YYYY}.(ZIP|TXT)`` are considered. The four-digit year
        is extracted from the name and compared against the requested year
        set, so files like ``data_12020.zip`` no longer match ``2020`` and
        non-COTAHIST files in the directory are ignored.

        Args:
            directory: Directory to scan for COTAHIST files.
            years: Range of years to match against.

        Returns:
            Set of absolute file paths whose extracted year is in ``years``.
        """
        requested_years = set(years)
        if not requested_years:
            return set()

        matching_files: set[str] = set()
        for file in directory.iterdir():
            if not file.is_file():
                continue
            match = _COTAHIST_YEAR_PATTERN.match(file.name)
            if match is None:
                continue
            if int(match.group(1)) in requested_years:
                matching_files.add(str(file))

        return matching_files
