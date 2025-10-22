"""Threaded parallel download adapter using requests and ThreadPoolExecutor.

This adapter provides faster downloads by parallelizing requests across
multiple threads, with automatic retry, exponential backoff, and streaming
to disk for memory efficiency. Includes a simple progress bar (no external deps).
"""

import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import requests

from src.brazil.dados_cvm.fundamental_stocks_data.application.interfaces import (
    DownloadDocsCVMRepository,
)
from src.brazil.dados_cvm.fundamental_stocks_data.domain.download_result import (
    DownloadResult,
)
from src.macro_exceptions.exception_network_errors import (
    DiskFullError,
    NetworkError,
    PermissionError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class SimpleProgressBar:
    """Simple progress bar without external dependencies (uses only sys/time).

    Thread-safe progress tracking for terminal output.
    """

    def __init__(self, total: int, desc: str = "", width: int = 40):
        """Initialize progress bar.

        Args:
            total: Total number of items
            desc: Description prefix
            width: Width of progress bar in characters
        """
        self.total = total
        self.desc = desc
        self.width = width
        self.current = 0
        self.start_time = time.time()
        self.last_print_time = 0

        # Print initial message
        if total > 0:
            print(f"\n{desc}: Starting download of {total} files...")
            sys.stdout.flush()

    def update(self, amount: int = 1):
        """Update progress by amount."""
        self.current += amount

        # Rate limit printing (max once per 0.1 seconds to avoid flickering)
        current_time = time.time()
        if current_time - self.last_print_time >= 0.1 or self.current == self.total:
            self._print()
            self.last_print_time = current_time

    def _print(self):
        """Print progress bar to terminal."""
        if self.total == 0:
            return

        percent = self.current / self.total
        filled = int(self.width * percent)
        bar = "█" * filled + "░" * (self.width - filled)

        # Clear line and print progress
        sys.stdout.write(
            f"\r{self.desc} [{bar}] {self.current}/{self.total} ({percent*100:.0f}%)"
        )
        sys.stdout.flush()

    def close(self):
        """Finalize progress bar."""
        if self.total > 0:
            # Ensure final state is printed
            self._print()
            sys.stdout.write("\n")
            sys.stdout.flush()


# Default configuration constants
DEFAULT_MAX_WORKERS = 8
DEFAULT_CHUNK_SIZE = 8192  # 8KB chunks for streaming to disk
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 1.0
DEFAULT_MAX_BACKOFF = 60.0
DEFAULT_BACKOFF_MULTIPLIER = 2.0


class ThreadPoolDownloadAdapter(DownloadDocsCVMRepository):
    """Parallel downloader using ThreadPoolExecutor with requests.

    Features:
    - Downloads multiple files concurrently using worker threads
    - Streams to disk to minimize memory usage
    - Automatic retry with exponential backoff on transient errors
    - Comprehensive error classification and reporting
    - Progress tracking and detailed logging

    Example:
        >>> adapter = ThreadPoolDownloadAdapter(max_workers=8)
        >>> result = adapter.download_docs(
        ...     "/path/to/dest",
        ...     {"DFP": ["url1", "url2"], "ITR": ["url3"]}
        ... )
        >>> print(f"Downloaded {result.success_count} files")
    """

    def __init__(
        self,
        max_workers: int = DEFAULT_MAX_WORKERS,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
        max_backoff: float = DEFAULT_MAX_BACKOFF,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
    ):
        """Initialize ThreadPool adapter with download configuration.

        Args:
            max_workers: Number of concurrent download threads. Default: 8.
            chunk_size: Size of chunks for streaming to disk (bytes). Default: 8KB.
            timeout: Request timeout in seconds. Default: 30.
            max_retries: Maximum retry attempts on failure. Default: 3.
            initial_backoff: Initial backoff in seconds. Default: 1.0.
            max_backoff: Maximum backoff in seconds. Default: 60.0.
            backoff_multiplier: Exponential backoff multiplier. Default: 2.0.
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier

        logger.debug(
            f"ThreadPoolDownloadAdapter initialized: "
            f"workers={max_workers}, chunk_size={chunk_size}, "
            f"timeout={timeout}s, max_retries={max_retries}"
        )

    def _is_retryable_error(self, exception: Exception) -> bool:
        """Determine if an error is retryable.

        Retryable: Network timeouts, connection errors, temporary issues
        Non-retryable: Permission denied, disk full, invalid URLs
        """
        non_retryable = (PermissionError, DiskFullError, ValueError)
        if isinstance(exception, non_retryable):
            return False

        retryable = (
            NetworkError,
            TimeoutError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        )
        if isinstance(exception, retryable):
            return True

        # Check error message for retryable keywords
        error_msg = str(exception).lower()
        retryable_keywords = [
            "timeout",
            "connection refused",
            "connection reset",
            "connection aborted",
            "temporarily",
            "unavailable",
            "try again",
        ]
        return any(kw in error_msg for kw in retryable_keywords)

    def _calculate_backoff(self, retry_count: int) -> float:
        """Calculate exponential backoff: initial * (multiplier ^ count)."""
        backoff = self.initial_backoff * (self.backoff_multiplier**retry_count)
        return min(backoff, self.max_backoff)

    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL.

        Falls back to a generic name if URL has no filename component.
        """
        try:
            return url.split("/")[-1].split("?")[0] or "download"
        except Exception:
            return "download"

    def _download_single_file(
        self, url: str, destination_path: str, doc_name: str, year: str
    ) -> Tuple[bool, Optional[str]]:
        """Download a single file with retry logic.

        Returns:
            (success: bool, error_message: Optional[str])
        """
        last_exception: Optional[Exception] = None
        filename = self._extract_filename_from_url(url)
        filepath = os.path.join(destination_path, filename)

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = self._calculate_backoff(attempt - 1)
                    logger.info(
                        f"Retry {attempt}/{self.max_retries} for "
                        f"{doc_name}_{year} after {backoff:.1f}s"
                    )
                    time.sleep(backoff)

                logger.debug(f"Downloading {doc_name}_{year} from {url}")

                # Stream download to disk in chunks
                response = requests.get(
                    url, stream=True, timeout=self.timeout, allow_redirects=True
                )
                response.raise_for_status()

                # Write to file in chunks to minimize memory usage
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)

                logger.info(
                    f"Successfully downloaded {doc_name}_{year} "
                    f"({response.headers.get('content-length', 'unknown')} bytes)"
                )
                return True, None

            except requests.exceptions.HTTPError as e:
                last_exception = e
                if 400 <= e.response.status_code < 500:
                    # Client errors (4xx) are not retryable
                    logger.error(
                        f"HTTP {e.response.status_code} for {doc_name}_{year}: "
                        f"not retrying"
                    )
                    return False, f"HTTP {e.response.status_code}: {url}"
                # 5xx errors are retryable
                if attempt < self.max_retries:
                    logger.warning(
                        f"HTTP {e.response.status_code} for {doc_name}_{year}, "
                        f"retrying..."
                    )
                    continue
            except requests.exceptions.RequestException as e:
                last_exception = e
                is_retryable = self._is_retryable_error(e)
                if attempt < self.max_retries and is_retryable:
                    logger.warning(
                        f"Request failed for {doc_name}_{year} "
                        f"({type(e).__name__}), retrying..."
                    )
                    continue
            except (OSError, IOError) as e:
                last_exception = e
                if "disk" in str(e).lower():
                    return False, f"DiskError: {destination_path} - {e}"
                if "permission" in str(e).lower():
                    return False, f"PermissionError: {destination_path} - {e}"
                if attempt < self.max_retries:
                    logger.warning(f"IO error for {doc_name}_{year}, retrying...")
                    continue
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error for {doc_name}_{year}: {e}")
                if attempt < self.max_retries:
                    continue

        # Failed after all retries
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

        if last_exception:
            error_type = (
                "retryable"
                if self._is_retryable_error(last_exception)
                else "non-retryable"
            )
            error_msg = f"{type(last_exception).__name__} ({error_type}): {doc_name}_{year} - {last_exception}"
        else:
            error_msg = f"Unknown error: {doc_name}_{year}"

        logger.error(f"Download failed: {error_msg}")
        return False, error_msg

    def download_docs(
        self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
    ) -> DownloadResult:
        """Download documents in parallel using ThreadPoolExecutor.

        Args:
            your_path: Destination directory path
            dict_zip_to_download: Dict mapping doc types to URL lists

        Returns:
            DownloadResult with success/error counts
        """
        result = DownloadResult()
        total_files = sum(len(urls) for urls in dict_zip_to_download.values())

        logger.info(
            f"Starting parallel download of {total_files} files "
            f"using {self.max_workers} workers to {your_path}"
        )

        # Initialize progress bar (simple, no external deps)
        progress_bar = SimpleProgressBar(
            total=total_files, desc="Downloading", width=30
        )

        # Prepare list of download tasks: (url, doc_name, year, filepath)
        tasks = []
        for doc_name, url_list in dict_zip_to_download.items():
            for url in url_list:
                # Extract year from URL (assuming format like "..._YYYY.zip")
                try:
                    year = url.split("_")[-1].split(".")[0]
                except Exception:
                    year = "unknown"
                tasks.append((url, doc_name, year))

        # Execute downloads in parallel
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self._download_single_file, url, your_path, doc_name, year
                    ): (doc_name, year, url)
                    for url, doc_name, year in tasks
                }

                for future in as_completed(futures):
                    doc_name, year, url = futures[future]
                    try:
                        success, error_msg = future.result()
                        if success:
                            result.add_success(doc_name, year)
                        else:
                            assert error_msg is not None
                            result.add_error(error_msg)
                    except Exception as e:
                        logger.error(f"Task failed for {doc_name}_{year}: {e}")
                        result.add_error(f"TaskError: {doc_name}_{year} - {e}")
                    finally:
                        progress_bar.update(1)
        finally:
            progress_bar.close()

        logger.info(
            f"Download completed: {result.success_count} successful, "
            f"{result.error_count} errors"
        )

        return result
