import logging
import time
from typing import Dict, List, Optional, Tuple

import wget

from src.brasil.dados_cvm.dados_fundamentalistas_ações.application import (
    DownloadDocsCVMRepository,
)
from src.brasil.dados_cvm.dados_fundamentalistas_ações.domain import DownloadResult
from src.brasil.dados_cvm.dados_fundamentalistas_ações.exceptions import (
    WgetLibraryError,
    WgetValueError,
)
from src.macro_exceptions.exception_network_errors import (
    DiskFullError,
    NetworkError,
    PermissionError,
    TimeoutError,
)

logger = logging.getLogger(__name__)

# Retry configuration constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 1
DEFAULT_MAX_BACKOFF = 60
DEFAULT_BACKOFF_MULTIPLIER = 2.0


class WgetDownloadAdapter(DownloadDocsCVMRepository):
    """Adapter for downloading CVM documents using wget with retry logic.

    Implements DownloadDocsCVMRepository interface with:
    - Automatic retry for transient network errors
    - Exponential backoff between retries
    - Comprehensive error classification
    - Detailed operation logging
    """

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
        max_backoff: float = DEFAULT_MAX_BACKOFF,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
    ):
        """Initialize adapter with retry configuration.

        Args:
            max_retries: Maximum retry attempts (default: 3)
            initial_backoff: Initial backoff in seconds (default: 1)
            max_backoff: Maximum backoff in seconds (default: 60)
            backoff_multiplier: Exponential backoff multiplier (default: 2.0)
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier
        logger.debug(
            f"WgetDownloadAdapter initialized: max_retries={max_retries}, "
            f"initial_backoff={initial_backoff}s, max_backoff={max_backoff}s"
        )

    def _is_retryable_error(self, exception: Exception) -> bool:
        """Classify if an error is retryable or not.

        Retryable: Network timeouts, connection errors, temporary unavailability
        Non-retryable: Permission denied, disk full, invalid parameters
        """
        # Explicitly non-retryable exceptions
        non_retryable = (PermissionError, DiskFullError, WgetValueError)
        if isinstance(exception, non_retryable):
            return False

        # Explicitly retryable exceptions
        retryable = (NetworkError, TimeoutError)
        if isinstance(exception, retryable):
            return True

        # Check error message for retryable keywords
        error_msg = str(exception).lower()
        retryable_keywords = [
            "timeout",
            "connection refused",
            "network",
            "temporarily",
            "unavailable",
            "connection reset",
            "connection aborted",
            "try again",
        ]
        return any(kw in error_msg for kw in retryable_keywords)

    def _calculate_backoff(self, retry_count: int) -> float:
        """Calculate exponential backoff: init_backoff * (multiplier ^ count)."""
        backoff = self.initial_backoff * (self.backoff_multiplier**retry_count)
        backoff = min(backoff, self.max_backoff)
        logger.debug(f"Calculated backoff for retry {retry_count}: {backoff}s")
        return backoff

    def _download_with_retry(
        self, url: str, destination: str, doc_name: str, year: str
    ) -> Tuple[bool, Optional[str]]:
        """Download with automatic retry and exponential backoff.

        Returns:
            (success: bool, error_message: Optional[str]) - error_message is None on success
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = self._calculate_backoff(attempt - 1)
                    logger.info(
                        f"Retry {attempt + 1}/{self.max_retries + 1} for "
                        f"{doc_name}_{year} after {backoff}s backoff"
                    )
                    time.sleep(backoff)

                logger.debug(f"Downloading {doc_name}_{year} from {url}")
                wget.download(url, out=destination)
                logger.info(f"Successfully downloaded {doc_name}_{year}")
                return True, None

            except Exception as e:
                last_exception = e
                is_retryable = self._is_retryable_error(e)

                if attempt < self.max_retries and is_retryable:
                    logger.warning(
                        f"Attempt {attempt + 1} for {doc_name}_{year} failed "
                        f"({type(e).__name__}). Retrying..."
                    )
                    continue
                else:
                    error_type = "retryable" if is_retryable else "non-retryable"
                    logger.error(
                        f"Download of {doc_name}_{year} failed ({error_type}): "
                        f"{type(e).__name__}: {e}"
                    )
                    break

        # If we exhausted all retries, format error message
        if last_exception is not None:
            error_msg = self._format_error_message(
                last_exception, doc_name, year, destination
            )
        else:
            # Should not happen - exception must be set if we reach here
            error_msg = "Unknown error: Download failed"
        return False, error_msg

    def _format_error_message(
        self, exception: Exception, doc_name: str, year: str, destination: str
    ) -> str:
        """Format standardized error message based on exception type."""
        if isinstance(exception, NetworkError):
            return f"NetworkError: {doc_name}_{year} - Network connectivity issue"
        elif isinstance(exception, TimeoutError):
            return f"TimeoutError: {doc_name}_{year} - Request timed out"
        elif isinstance(exception, PermissionError):
            return f"PermissionError: {destination} - Access denied"
        elif isinstance(exception, DiskFullError):
            return f"DiskFullError: {destination} - Insufficient disk space"
        elif isinstance(exception, WgetLibraryError):
            return f"WgetLibraryError: {doc_name}_{year} - {exception}"
        elif isinstance(exception, WgetValueError):
            return f"WgetValueError: {exception}"
        else:
            return f"DownloadError: {doc_name}_{year} - {type(exception).__name__}"

    def download_docs(
        self, your_path: str, dict_zip_to_download: Dict[str, List[str]]
    ) -> DownloadResult:
        """Download documents with automatic retry on transient errors.

        Args:
            your_path: Destination directory path
            dict_zip_to_download: Document types mapped to URL lists

        Returns:
            DownloadResult with success/error counts
        """
        result = DownloadResult()

        total_files = sum(len(urls) for urls in dict_zip_to_download.values())
        logger.info(
            f"Starting download of {total_files} files to {your_path} "
            f"(max retries: {self.max_retries})"
        )
        logger.debug(f"Documents: {list(dict_zip_to_download.keys())}")

        for doc_name, doc_list in dict_zip_to_download.items():
            for doc_zip in doc_list:
                year = doc_zip.split("_")[-1].split(".")[0]

                success, error_msg = self._download_with_retry(
                    doc_zip, your_path, doc_name, year
                )

                if success:
                    result.add_success(doc_name, year)
                else:
                    assert (
                        error_msg is not None
                    ), "error_msg should not be None when success is False"
                    result.add_error(error_msg)

        logger.info(
            f"Download completed: {result.success_count} successful, "
            f"{result.error_count} errors"
        )

        return result
