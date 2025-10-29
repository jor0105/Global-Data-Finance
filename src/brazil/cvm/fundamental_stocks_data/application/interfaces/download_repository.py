from abc import ABC, abstractmethod
from typing import List, Tuple

from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult


# Abstract base class for CVM document download repository
class DownloadDocsCVMRepository(ABC):
    """
    Abstract repository interface for downloading CVM documents.

    This interface defines the contract for any implementation that downloads
    CVM documents from the internet.
    """

    @abstractmethod
    def download_docs(
        self,
        tasks: List[Tuple[str, str, str, str]],
    ) -> DownloadResult:
        """
        Download CVM documents.

        Args:
            tasks: List of tuples (url, doc_name, year, destination_path) representing each download task.

        Returns:
            DownloadResult containing aggregated information about the success and error of downloads.

        Note:
            Implementations should handle downloading files from the provided URLs and store them at the specified destination paths.
        """
        pass
