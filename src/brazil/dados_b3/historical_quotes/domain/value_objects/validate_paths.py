from pathlib import Path
from typing import Set

from src.macro_exceptions import (
    EmptyDirectoryError,
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
)


class ValidatePaths:
    @staticmethod
    def __validate_path(path: str) -> None:
        """Validates a given path. Checks if it's a valid string/Path, exists, is a directory, and is not empty.

        Args:
            path: The path to validate (str).

        Returns:
            Path object if valid.

        Raises:
            InvalidPathError: If path is None (when not allowed), not a string, empty, or not a valid type.
            EmptyDirectoryError: If path is an empty directory.
        """
        if not isinstance(path, str):
            raise TypeError(
                f"Destination path must be a string, got {type(path).__name__}"
            )

        if not path or path.isspace():
            raise InvalidDestinationPathError("path cannot be empty or whitespace")

        normalized_path = Path(path).expanduser().resolve()

        if not normalized_path.exists():
            raise PathIsNotDirectoryError(path)

        if not normalized_path.is_dir():
            raise PathIsNotDirectoryError(path)

        if not any(normalized_path.iterdir()):
            raise EmptyDirectoryError(path)

    def create_set_document_to_download(
        self, range_years: range, path: str
    ) -> Set[str]:
        """Generates a set with all files in the 'path' directory whose name contains any of the years in 'range_years'."""
        self.__validate_path(path)
        p = Path(path).expanduser()
        document_set = set()
        for year in range_years:
            for file in p.iterdir():
                if file.is_file() and str(year) in file.name:
                    document_set.add(str(file))
        return document_set
