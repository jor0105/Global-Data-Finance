from abc import ABC, abstractmethod
from typing import Dict, List

from ...domain import DownloadResult


class DownloadDocsCVMRepository(ABC):
    """Abstract repository interface for downloading CVM documents.

    This interface defines the contract for any implementation that downloads
    CVM documents from the internet.
    """

    @abstractmethod
    def download_docs(
        self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
    ) -> DownloadResult:
        """Download CVM documents.

        Args:
            your_path: Destination directory path for downloaded files.
            dict_zip_to_download: Dictionary mapping document types to lists of URLs.

        Returns:
            DownloadResult containing successful downloads and any errors encountered.
        """
        pass
