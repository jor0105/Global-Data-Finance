from typing import Dict, List, Optional


class DownloadResult:
    """Represents the result of a download operation.

    This class encapsulates successful downloads and errors that occurred
    during the download process, providing a clean interface to access results.

    Attributes:
        successful_downloads: Dictionary mapping document names to lists of successfully downloaded years.
        errors: List of error messages that occurred during download.
    """

    def __init__(
        self,
        successful_downloads: Optional[Dict[str, List[str]]] = None,
        errors: Optional[List[str]] = None,
    ) -> None:
        """Initialize download result.

        Args:
            successful_downloads: Dictionary of successful downloads. Defaults to empty dict.
            errors: List of error messages. Defaults to empty list.
        """
        self._successful_downloads = successful_downloads or {}
        self._errors = errors or []

    @property
    def successful_downloads(self) -> Dict[str, List[str]]:
        """Get dictionary of successful downloads."""
        return self._successful_downloads

    @property
    def errors(self) -> List[str]:
        """Get list of error messages."""
        return self._errors

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self._errors) > 0

    @property
    def success_count(self) -> int:
        """Get total count of successful downloads."""
        return sum(len(years) for years in self._successful_downloads.values())

    @property
    def error_count(self) -> int:
        """Get total count of errors."""
        return len(self._errors)

    def add_success(self, doc_name: str, year: str) -> None:
        """Add a successful download.

        Args:
            doc_name: Name of the document type.
            year: Year that was successfully downloaded.
        """
        if doc_name not in self._successful_downloads:
            self._successful_downloads[doc_name] = []
        if year not in self._successful_downloads[doc_name]:
            self._successful_downloads[doc_name].append(year)

    def add_error(self, error_message: str) -> None:
        """Add an error message.

        Args:
            error_message: Error message to add.
        """
        self._errors.append(error_message)

    def clear(self) -> None:
        """Clear all results and errors."""
        self._successful_downloads.clear()
        self._errors.clear()

    def __repr__(self) -> str:
        """String representation of download result."""
        return (
            f"DownloadResult(success_count={self.success_count}, "
            f"error_count={self.error_count})"
        )
