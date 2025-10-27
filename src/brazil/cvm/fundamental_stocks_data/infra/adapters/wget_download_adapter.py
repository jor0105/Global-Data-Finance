import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

import wget  # type: ignore

from src.brazil.cvm.fundamental_stocks_data.application import (
    DownloadDocsCVMRepository,
    FileExtractor,
)
from src.brazil.cvm.fundamental_stocks_data.application.extractors import (
    ParquetExtractor,
)
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
from src.macro_exceptions.macro_exceptions import DiskFullError, ExtractionError

logger = logging.getLogger(__name__)


class WgetDownloadAdapter(DownloadDocsCVMRepository):
    """Sequential document downloader using wget with retry logic.

    This adapter implements sequential download+extraction pipeline where
    each file is downloaded, extracted, and cleaned up one at a time.
    """

    def __init__(
        self,
        file_extractor: Optional[FileExtractor] = None,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
    ):
        """Initialize the adapter with injected dependencies.

        Args:
            file_extractor: FileExtractor implementation to use for post-download extraction.
                          Defaults to ParquetExtractor if not provided.
            max_retries: Maximum number of retry attempts for failed downloads
            initial_backoff: Initial backoff delay in seconds
            max_backoff: Maximum backoff delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
        """
        self.file_extractor = file_extractor or ParquetExtractor()
        self.retry_strategy = RetryStrategy(
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            multiplier=backoff_multiplier,
        )
        self.max_retries = max_retries
        logger.debug(
            f"WgetDownloadAdapter initialized with max_retries={max_retries} "
            f"and {file_extractor.__class__.__name__}"
        )

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
        """Download with retry logic and post-download extraction."""
        filename = self._extract_filename(url)
        filepath = str(Path(dest_path) / filename)
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = self.retry_strategy.calculate_backoff(attempt - 1)
                    logger.info(
                        f"Retry {attempt}/{self.max_retries} for {doc_name}_{year} "
                        f"after {backoff:.1f}s"
                    )
                    time.sleep(backoff)

                logger.debug(f"Downloading {doc_name}_{year}")
                wget.download(url, out=filepath)
                logger.info(f"Successfully downloaded {doc_name}_{year}")

                # Extract after successful download
                try:
                    logger.info(f"Starting extraction for {doc_name}_{year}")
                    self.file_extractor.extract(filepath, dest_path)

                    # Mark as success only after extraction completes
                    result.add_success(f"{doc_name}_{year}")
                    logger.info(f"Extraction completed for {doc_name}_{year}")

                    # Clean up ZIP file after successful extraction
                    self._cleanup_zip_file(filepath)

                except DiskFullError as disk_err:
                    logger.error(f"Disk full during extraction {filepath}: {disk_err}")
                    result.add_error(f"{doc_name}_{year}", f"DiskFull: {disk_err}")
                    self._cleanup_zip_file(filepath)

                except ExtractionError as extract_exc:
                    logger.error(f"Extraction error for {filepath}: {extract_exc}")
                    result.add_error(
                        f"{doc_name}_{year}", f"Extraction failed: {extract_exc}"
                    )

                except Exception as extract_exc:
                    logger.error(
                        f"Unexpected extraction error for {filepath}: "
                        f"{type(extract_exc).__name__}: {extract_exc}"
                    )
                    result.add_error(
                        f"{doc_name}_{year}",
                        f"Unexpected extraction error: {extract_exc}",
                    )

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
            path_obj = Path(filepath)
            if path_obj.exists():
                path_obj.unlink()
        except Exception:
            pass

    @staticmethod
    def _cleanup_zip_file(zip_path: str) -> None:
        """Attempt to delete ZIP file after extraction.

        Args:
            zip_path: Path to ZIP file to delete
        """
        try:
            Path(zip_path).unlink()
            logger.debug(f"Deleted ZIP file: {zip_path}")
        except Exception as cleanup_err:
            logger.warning(f"Failed to delete ZIP file {zip_path}: {cleanup_err}")
