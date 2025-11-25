from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DownloadResultCVM:
    """
    Represents the result of a download operation.

    Attributes:
        successful_downloads: A list of successfully downloaded files/document types.
        failed_downloads: A dictionary that maps document types to error messages.
        success_count_downloads: The number of successful downloads.
        error_count_downloads: The number of failed downloads.
    """

    successful_downloads: List[str] = field(default_factory=list)
    failed_downloads: Dict[str, str] = field(default_factory=dict)

    @property
    def success_count_downloads(self) -> int:
        return len(self.successful_downloads)

    @property
    def error_count_downloads(self) -> int:
        return len(self.failed_downloads)

    def add_success_downloads(self, item: str) -> None:
        if item not in self.successful_downloads:
            self.successful_downloads.append(item)

    def add_error_downloads(self, item: str, error: str) -> None:
        self.failed_downloads[item] = error

    def __str__(self) -> str:
        return (
            f"DownloadResultCVM(success={self.success_count_downloads}, "
            f"errors={self.error_count_downloads})"
        )
