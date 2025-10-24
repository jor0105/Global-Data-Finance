import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import requests

from src.brazil.cvm.fundamental_stocks_data.application import DownloadDocsCVMRepository
from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
from src.brazil.cvm.fundamental_stocks_data.utils import (
    RetryStrategy,
    SimpleProgressBar,
)

logger = logging.getLogger(__name__)


class ThreadPoolDownloadAdapter(DownloadDocsCVMRepository):
    """Parallel document downloader using thread pool executor."""

    def __init__(
        self,
        max_workers: int = 8,
        chunk_size: int = 8192,
        timeout: int = 30,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
    ):
        self.max_workers = max_workers
        self.retry_strategy = RetryStrategy(
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            multiplier=backoff_multiplier,
        )
        self.file_downloader = SingleFileDownloader(
            retry_strategy=self.retry_strategy,
            chunk_size=chunk_size,
            timeout=timeout,
            max_retries=max_retries,
        )

        logger.debug(
            f"ThreadPoolDownloadAdapter initialized with {max_workers} workers"
        )

    def download_docs(
        self,
        dict_zip_to_download: Dict[str, List[str]],
        docs_paths: Dict[str, Dict[int, str]],
    ) -> DownloadResult:
        """Download documents in parallel.

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

        logger.info(
            f"Starting parallel download of {total_files} files "
            f"using {self.max_workers} workers"
        )

        tasks = self._prepare_download_tasks(dict_zip_to_download, docs_paths)
        progress_bar = SimpleProgressBar(total=total_files, desc="Downloading")

        try:
            self._execute_parallel_downloads(tasks, result, progress_bar)
        finally:
            progress_bar.close()

        logger.info(
            f"Download completed: {result.success_count} successful, "
            f"{result.error_count} errors"
        )

        return result

    def _prepare_download_tasks(
        self,
        dict_zip_to_download: Dict[str, List[str]],
        docs_paths: Dict[str, Dict[int, str]],
    ) -> List[Tuple[str, str, str, str]]:
        """Prepare download tasks from input dictionary.

        Returns:
            List of (url, doc_name, year, destination_path) tuples
        """
        tasks = []
        for doc_name, url_list in dict_zip_to_download.items():
            for url in url_list:
                year_str = self.file_downloader._get_year(url)
                year_int = int(year_str)

                # Get the specific path for this document and year
                destination_path = docs_paths[doc_name][year_int]

                tasks.append((url, doc_name, year_str, destination_path))
        return tasks

    def _execute_parallel_downloads(
        self,
        tasks: List[Tuple[str, str, str, str]],
        result: DownloadResult,
        progress_bar: SimpleProgressBar,
    ) -> None:
        """Execute downloads concurrently using thread pool."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.file_downloader.download,
                    url,
                    destination_path,
                    doc_name,
                    year,
                ): (doc_name, year)
                for url, doc_name, year, destination_path in tasks
            }

            for future in as_completed(futures):
                doc_name, year = futures[future]
                try:
                    success, error_msg = future.result()
                    if success:
                        result.add_success(f"{doc_name}_{year}")
                    else:
                        assert error_msg is not None
                        result.add_error(f"{doc_name}_{year}", error_msg)
                except Exception as e:
                    logger.error(f"Task failed for {doc_name}_{year}: {e}")
                    result.add_error(f"{doc_name}_{year}", str(e))
                finally:
                    progress_bar.update(1)


class SingleFileDownloader:
    """Handles download of individual files with retry logic."""

    def __init__(
        self,
        retry_strategy: RetryStrategy,
        chunk_size: int = 8192,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.retry_strategy = retry_strategy
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retries = max_retries

    @staticmethod
    def _get_filename(url: str) -> str:
        """Extract filename from URL."""
        try:
            return url.split("/")[-1].split("?")[0] or "download"
        except Exception:
            return "download"

    @staticmethod
    def _get_year(url: str) -> str:
        """Extract year from URL (expects format: ..._YYYY.zip)."""
        try:
            return url.split("_")[-1].split(".")[0]
        except Exception:
            return "unknown"

    def download(
        self, url: str, destination_path: str, doc_name: str, year: str
    ) -> Tuple[bool, Optional[str]]:
        """Download file with retry logic.

        Returns:
            Tuple of (success, error_message)
        """
        filename = self._get_filename(url)
        filepath = os.path.join(destination_path, filename)
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self._apply_backoff(attempt, doc_name, year)

                logger.debug(f"Downloading {doc_name}_{year}")
                self._stream_download(url, filepath)
                logger.info(f"Successfully downloaded {doc_name}_{year}")
                return True, None

            except requests.exceptions.HTTPError as e:
                if not self._should_retry_http(e, attempt, doc_name, year):
                    return False, f"HTTP {e.response.status_code}: {url}"
                last_exception = e

            except requests.exceptions.RequestException as e:
                if not self._should_retry_request(e, attempt, doc_name, year):
                    last_exception = e
                    break
                last_exception = e

            except (OSError, IOError) as e:
                if not self._should_retry_io(e, attempt, doc_name, year):
                    return False, self._format_io_error(e, destination_path)
                last_exception = e

            except Exception as e:
                logger.error(f"Unexpected error for {doc_name}_{year}: {e}")
                last_exception = e
                if attempt < self.max_retries:
                    continue
                break

        self._cleanup_failed_file(filepath)
        return False, self._format_final_error(last_exception, doc_name, year)

    def _apply_backoff(self, attempt: int, doc_name: str, year: str) -> None:
        backoff = self.retry_strategy.calculate_backoff(attempt - 1)
        logger.info(
            f"Retry {attempt}/{self.max_retries} for {doc_name}_{year} "
            f"after {backoff:.1f}s"
        )
        time.sleep(backoff)

    def _stream_download(self, url: str, filepath: str) -> None:
        response = requests.get(
            url,
            stream=True,
            timeout=self.timeout,
            allow_redirects=True,
        )
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    f.write(chunk)

    def _should_retry_http(
        self,
        exception: requests.exceptions.HTTPError,
        attempt: int,
        doc_name: str,
        year: str,
    ) -> bool:
        status_code = exception.response.status_code
        if 400 <= status_code < 500:
            logger.error(f"HTTP {status_code} for {doc_name}_{year}: not retrying")
            return False

        if attempt < self.max_retries:
            logger.warning(f"HTTP {status_code} for {doc_name}_{year}, retrying...")
            return True
        return False

    def _should_retry_request(
        self,
        exception: requests.exceptions.RequestException,
        attempt: int,
        doc_name: str,
        year: str,
    ) -> bool:
        if attempt < self.max_retries and self.retry_strategy.is_retryable(exception):
            logger.warning(
                f"Request failed for {doc_name}_{year} ({type(exception).__name__}), retrying..."
            )
            return True
        return False

    def _should_retry_io(
        self, exception: Exception, attempt: int, doc_name: str, year: str
    ) -> bool:
        if attempt < self.max_retries:
            logger.warning(f"IO error for {doc_name}_{year}, retrying...")
            return True
        return False

    @staticmethod
    def _format_io_error(exception: Exception, destination_path: str) -> str:
        error_str = str(exception).lower()
        if "disk" in error_str:
            return f"DiskError: {destination_path} - {exception}"
        if "permission" in error_str:
            return f"PermissionError: {destination_path} - {exception}"
        return f"IOError: {exception}"

    def _format_final_error(
        self, exception: Optional[Exception], doc_name: str, year: str
    ) -> str:
        if not exception:
            return f"Unknown error: {doc_name}_{year}"

        error_type = (
            "retryable"
            if self.retry_strategy.is_retryable(exception)
            else "non-retryable"
        )
        return f"{type(exception).__name__} ({error_type}): {doc_name}_{year}"

    @staticmethod
    def _cleanup_failed_file(filepath: str) -> None:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
