from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DownloadResult:
    """Result of a download operation.

    Attributes:
        successful_downloads: List of successfully downloaded files/document types.
        failed_downloads: Dictionary mapping document types to error messages.
        success_count: Number of successful downloads.
        error_count: Number of failed downloads.
    """

    successful_downloads: List[str] = field(default_factory=list)
    failed_downloads: Dict[str, str] = field(default_factory=dict)

    @property
    def success_count(self) -> int:
        """Get count of successful downloads."""
        return len(self.successful_downloads)

    @property
    def error_count(self) -> int:
        """Get count of failed downloads."""
        return len(self.failed_downloads)

    def add_success(self, item: str) -> None:
        """Add a successful download."""
        if item not in self.successful_downloads:
            self.successful_downloads.append(item)

    def add_error(self, item: str, error: str) -> None:
        """Add a failed download with error message."""
        self.failed_downloads[item] = error

    def __str__(self) -> str:
        """String representation of download result."""
        return (
            f"DownloadResult(success={self.success_count}, "
            f"errors={self.error_count})"
        )
