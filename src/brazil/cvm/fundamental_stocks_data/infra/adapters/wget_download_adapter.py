import logging
import os
import time
from typing import Dict, List, Optional

import wget  # type: ignore

from src.brazil.cvm.fundamental_stocks_data.application import DownloadDocsCVMRepository
from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    WgetLibraryError,
    WgetValueError,
)
from src.brazil.cvm.fundamental_stocks_data.utils import (
    RetryStrategy,
    SimpleProgressBar,
)
from src.macro_exceptions import PathPermissionError

logger = logging.getLogger(__name__)


class WgetDownloadAdapter(DownloadDocsCVMRepository):
    """Sequential document downloader using wget with retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
    ):
        self.retry_strategy = RetryStrategy(
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            multiplier=backoff_multiplier,
        )
        self.max_retries = max_retries
        logger.debug(f"WgetDownloadAdapter: max_retries={max_retries}")

    def download_docs(
        self,
        dict_zip_to_download: Dict[str, List[str]],
        docs_paths: Dict[str, Dict[int, str]],
    ) -> DownloadResult:
        """Download documents sequentially with retry logic.

        Args:
            dict_zip_to_download: Dict mapping doc types to URL lists
            docs_paths: Dict with structure {doc: {year: path}} containing
                       the specific destination path for each document and year

        Returns:
            DownloadResult with aggregated success/error information
        """
        result = DownloadResult()
        total_files = sum(len(urls) for urls in dict_zip_to_download.values())

        if total_files == 0:
            logger.warning("No files to download")
            return result

        logger.info(f"Starting sequential download of {total_files} files")
        progress_bar = SimpleProgressBar(total=total_files, desc="Downloading")

        try:
            for doc_name, url_list in dict_zip_to_download.items():
                for url in url_list:
                    year_str = self._extract_year(url)
                    year_int = int(year_str)

                    # Get the specific path for this document and year
                    dest_path = docs_paths[doc_name][year_int]

                    self._download_with_retry(
                        url, dest_path, doc_name, year_str, result
                    )
                    progress_bar.update(1)
        finally:
            progress_bar.close()

        logger.info(
            f"Download completed: {result.success_count} successful, "
            f"{result.error_count} errors"
        )
        return result

    def _download_with_retry(
        self, url: str, dest_path: str, doc_name: str, year: str, result: DownloadResult
    ) -> None:
        """Download with retry logic."""
        filename = self._extract_filename(url)
        filepath = os.path.join(dest_path, filename)
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = self.retry_strategy.calculate_backoff(attempt - 1)
                    logger.info(
                        f"Retry {attempt}/{self.max_retries} after {backoff:.1f}s"
                    )
                    time.sleep(backoff)

                logger.debug(f"Downloading {doc_name}_{year}")
                wget.download(url, out=filepath)
                logger.info(f"Successfully downloaded {doc_name}_{year}")
                result.add_success(f"{doc_name}_{year}")
                return

            except WgetValueError as e:
                result.add_error(f"{doc_name}_{year}", str(e))
                return

            except (WgetLibraryError, TypeError, ValueError) as e:
                last_error = e

            except PermissionError:
                error_msg = f"PathPermissionError: {dest_path}"
                if attempt >= self.max_retries:
                    result.add_error(f"{doc_name}_{year}", error_msg)
                    return
                last_error = PathPermissionError(dest_path)

            except OSError as e:
                if "disk" in str(e).lower() or "no space" in str(e).lower():
                    error_msg = f"DiskFullError: {dest_path}"
                    result.add_error(f"{doc_name}_{year}", error_msg)
                    return

                if attempt >= self.max_retries:
                    result.add_error(f"{doc_name}_{year}", str(e))
                    return
                last_error = e

            except Exception as e:
                if (
                    not self.retry_strategy.is_retryable(e)
                    or attempt >= self.max_retries
                ):
                    result.add_error(f"{doc_name}_{year}", str(e))
                    return
                last_error = e

        self._cleanup_file(filepath)
        error_msg = (
            f"{type(last_error).__name__}: {last_error}"
            if last_error
            else "Unknown error"
        )
        result.add_error(f"{doc_name}_{year}", error_msg)

    @staticmethod
    def _extract_filename(url: str) -> str:
        """Extract filename from URL."""
        try:
            return url.split("/")[-1].split("?")[0] or "download"
        except Exception:
            return "download"

    @staticmethod
    def _extract_year(url: str) -> str:
        """Extract year from URL."""
        try:
            return url.split("_")[-1].split(".")[0]
        except Exception:
            return "unknown"

    @staticmethod
    def _cleanup_file(filepath: str) -> None:
        """Remove file on failure."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
