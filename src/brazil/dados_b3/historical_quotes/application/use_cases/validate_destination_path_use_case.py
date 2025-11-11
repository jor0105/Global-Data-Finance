import os
from pathlib import Path

from src.macro_exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)


class VerifyDestinationPathsUseCase:
    @staticmethod
    def execute(destination_path: str) -> None:
        """Create and verify directory structure for documents and years."""
        if not isinstance(destination_path, str):
            raise TypeError(
                f"Destination path must be a string, got {type(destination_path).__name__}"
            )

        if not destination_path or destination_path.isspace():
            raise InvalidDestinationPathError("path cannot be empty or whitespace")

        normalized_path = Path(destination_path).expanduser().resolve()

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
