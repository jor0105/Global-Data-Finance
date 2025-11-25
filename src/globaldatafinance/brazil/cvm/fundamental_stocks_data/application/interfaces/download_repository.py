from abc import ABC, abstractmethod
from typing import List, Tuple

from ...domain import DownloadResultCVM


# Abstract base class for CVM document download repository
class DownloadDocsCVMRepositoryCVM(ABC):
    """Abstract repository interface for downloading CVM documents."""

    @abstractmethod
    def download_docs(
        self,
        tasks: List[Tuple[str, str, str, str]],
    ) -> DownloadResultCVM:
        """
        Download CVM documents.

        Args:
            tasks: List of tuples (url, doc_name, year, destination_path) representing each download task.

        Returns:
            DownloadResultCVM containing aggregated information about the success and error of downloads.
        """
        pass
