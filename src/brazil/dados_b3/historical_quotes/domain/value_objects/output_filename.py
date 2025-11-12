import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputFilename:
    """Value object representing a valid output filename.

    Ensures filename meets basic validation criteria:
    - Non-empty string
    - Not a path (only filename, no directory separators)
    - Reasonable length (max 255 chars)
    - Valid filesystem characters only

    Note: Extension handling (e.g., .parquet) is responsibility of the caller.

    Example:
        >>> filename = OutputFilename("my_quotes.parquet")
        >>> str(filename)
        "my_quotes.parquet"

        >>> filename = OutputFilename("my_quotes")
        >>> str(filename)
        "my_quotes"
    """

    value: str

    def __post_init__(self):
        """Validate filename on creation."""
        self._validate()

    def _validate(self) -> None:
        """Validate the filename.

        Raises:
            ValueError: If filename is invalid
        """
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("output_filename must be a non-empty string")

        value = self.value.strip()

        # Ensure it's just a filename, not a path
        if os.path.basename(value) != value:
            raise ValueError("output_filename must be a filename, not a path")

        # Check length
        if len(value) > 255:
            raise ValueError("output_filename is too long (max 255 characters)")

        # Allow letters, numbers, underscore, dash and dot
        if not re.match(r"^[\w\-.]+$", value):
            raise ValueError(
                "output_filename contains invalid characters; "
                "allowed: letters, numbers, underscore, dash and dot"
            )

    def __str__(self) -> str:
        """Return the filename as string."""
        return self.value
