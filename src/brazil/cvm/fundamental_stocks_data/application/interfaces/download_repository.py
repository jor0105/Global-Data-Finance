from abc import ABC, abstractmethod
from typing import Dict, List

from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult


class DownloadDocsCVMRepository(ABC):
    """Abstract repository interface for downloading CVM documents.

    This interface defines the contract for any implementation that downloads
    CVM documents from the internet.
    """

    @abstractmethod
    def download_docs(
        self,
        dict_zip_to_download: Dict[str, List[str]],
        docs_paths: Dict[str, Dict[int, str]],
    ) -> DownloadResult:
        """Download CVM documents.

        Args:
            dict_zip_to_download: Dictionary mapping document types to lists of URLs.
            docs_paths: Dictionary with structure {doc: {year: path}} containing
                       the specific destination path for each document and year.

        Returns:
            DownloadResult containing successful downloads and any errors encountered.
        """
        pass
