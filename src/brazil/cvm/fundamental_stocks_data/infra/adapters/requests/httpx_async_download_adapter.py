import asyncio
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from src.brazil.cvm.fundamental_stocks_data.application import (
    DownloadDocsCVMRepository,
    FileExtractorRepository,
)
from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
from src.core import RetryStrategy, SimpleProgressBar, get_logger, remove_file
from src.macro_exceptions import CorruptedZipError, DiskFullError, ExtractionError
from src.macro_infra import RequestsAdapter

logger = get_logger(__name__)


class HttpxAsyncDownloadAdapter(DownloadDocsCVMRepository):
    """Asynchronous download adapter using httpx."""

    def __init__(
        self,
        file_extractor_repository: FileExtractorRepository,
        max_concurrent: int = 10,
        chunk_size: int = 8192,
        timeout: float = 60.0,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
        http2: bool = True,
        automatic_extractor: bool = False,
    ):
        """
        Initializes the asynchronous download adapter.

        Args:
            file_extractor_repository: File extractor for extracting downloaded ZIPs.
            max_concurrent: Maximum number of concurrent downloads.
            chunk_size: Chunk size for streaming.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts on failure.
            initial_backoff: Initial backoff in seconds.
            max_backoff: Maximum backoff in seconds.
            backoff_multiplier: Exponential backoff multiplier.
            http2: Enable HTTP/2.
            automatic_extractor: Enable automatic extraction after download.
        """
        self.file_extractor_repository = file_extractor_repository
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.automatic_extractor = automatic_extractor

        self.requests_adapter = RequestsAdapter(
            timeout=timeout,
            http2=http2,
            verify=True,
            max_redirects=20,
        )

        self.retry_strategy = RetryStrategy(
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            multiplier=backoff_multiplier,
        )

        logger.debug(
            f"HttpxAsyncDownloadAdapter initialized with max_concurrent={max_concurrent}, "
            f"http2={http2}, timeout={timeout}"
        )

    def download_docs(
        self,
        tasks: List[Tuple[str, str, str, str]],
    ) -> DownloadResult:
        """
        Asynchronously downloads documents.

        Args:
            tasks: List of tuples (url, doc_name, year, destination_path) representing each download task.

        Returns:
            DownloadResult containing aggregated success/error information.
        """
        result = DownloadResult()
        total_files = len(tasks)

        if total_files == 0:
            logger.warning("No files to download")
            return result

        logger.info(
            f"Starting async download of {total_files} files "
            f"with {self.max_concurrent} concurrent downloads"
        )

        asyncio.run(self._execute_async_downloads(tasks, result))

        logger.info(
            f"Download completed: {result.success_count_downloads} successful, "
            f"{result.error_count_downloads} errors"
        )

        return result

    async def _execute_async_downloads(
        self,
        tasks: List[Tuple[str, str, str, str]],
        result: DownloadResult,
    ) -> None:
        """Execute async downloads with concurrency control."""
        progress_bar = SimpleProgressBar(total=len(tasks), desc="Downloading (async)")
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def download_with_semaphore(task):
            async with semaphore:
                url, doc_name, year, dest_path = task
                await self._download_and_extract(
                    url, dest_path, doc_name, year, result, progress_bar
                )

        try:
            download_tasks = [download_with_semaphore(task) for task in tasks]
            await asyncio.gather(*download_tasks)
        finally:
            progress_bar.close()

    async def _download_and_extract(
        self,
        url: str,
        dest_path: str,
        doc_name: str,
        year: str,
        result: DownloadResult,
        progress_bar: SimpleProgressBar,
    ) -> None:
        """Download a file and extract its contents."""
        filename = self._extract_filename(url)
        filepath = str(Path(dest_path) / filename)

        success, error_msg = await self._download_with_retry(
            url, filepath, doc_name, year
        )

        if success:
            # CRITICAL FIX: Get expected size for validation
            expected_size = await self._get_content_length(url)

            # CRITICAL FIX: Validate file integrity before extraction
            if not self._validate_downloaded_file(filepath, expected_size):
                logger.error(
                    f"Downloaded file validation failed for {doc_name}_{year}: {filepath}"
                )
                result.add_error_downloads(
                    f"{doc_name}_{year}",
                    "Downloaded file corrupted, incomplete, or invalid ZIP",
                )
                remove_file(filepath, log_on_error=True)
                progress_bar.update(1)
                return

            if self.automatic_extractor:
                try:
                    logger.info(f"Starting extraction for {doc_name}_{year}")
                    self.file_extractor_repository.extract(filepath, dest_path)

                    # CRITICAL FIX: Verify extraction with recursive glob
                    parquet_files = list(Path(dest_path).glob("**/*.parquet"))
                    if not parquet_files:
                        logger.warning(
                            f"Extraction completed but no .parquet files found in {dest_path} "
                            f"(including subdirectories). Keeping source ZIP: {filepath}"
                        )
                        result.add_error_downloads(
                            f"{doc_name}_{year}",
                            "No parquet files generated after extraction",
                        )
                        progress_bar.update(1)
                        return

                    result.add_success_downloads(f"{doc_name}_{year}")
                    logger.info(
                        f"✓ Extraction completed for {doc_name}_{year}: "
                        f"{len(parquet_files)} parquet files created"
                    )
                    remove_file(filepath, log_on_error=True)

                except DiskFullError as disk_err:
                    logger.error(
                        f"Disk full during extraction of {doc_name}_{year}: {disk_err}"
                    )
                    result.add_error_downloads(
                        f"{doc_name}_{year}", f"DiskFull: {disk_err}"
                    )
                    # Remove ZIP on disk full (non-recoverable)
                    remove_file(filepath, log_on_error=True)

                except CorruptedZipError as zip_err:
                    logger.error(
                        f"Corrupted ZIP detected during extraction of {doc_name}_{year}: {zip_err}"
                    )
                    result.add_error_downloads(
                        f"{doc_name}_{year}", f"CorruptedZIP: {zip_err}"
                    )
                    # Remove corrupted ZIP (non-recoverable)
                    remove_file(filepath, log_on_error=True)

                except ExtractionError as extract_err:
                    logger.error(
                        f"Extraction error for {doc_name}_{year}: {extract_err}"
                    )
                    result.add_error_downloads(
                        f"{doc_name}_{year}", f"ExtractionFailed: {extract_err}"
                    )
                    # CRITICAL FIX: Track failed extraction for later retry
                    self._track_failed_extraction(
                        filepath, doc_name, year, str(extract_err), dest_path
                    )
                    logger.info(f"Keeping ZIP for manual investigation: {filepath}")

                except Exception as unexpected_err:
                    logger.error(
                        f"Unexpected extraction error for {doc_name}_{year}: "
                        f"{type(unexpected_err).__name__}: {unexpected_err}",
                        exc_info=True,
                    )
                    result.add_error_downloads(
                        f"{doc_name}_{year}",
                        f"UnexpectedError: {type(unexpected_err).__name__}: {unexpected_err}",
                    )
                    # Track for retry
                    self._track_failed_extraction(
                        filepath,
                        doc_name,
                        year,
                        f"{type(unexpected_err).__name__}: {unexpected_err}",
                        dest_path,
                    )
                    # Keep ZIP for debugging
                    logger.info(f"Keeping ZIP for debugging: {filepath}")

            else:
                # Automatic extraction disabled
                result.add_success_downloads(f"{doc_name}_{year}")
                logger.info(f"✓ Downloaded {doc_name}_{year} (extraction disabled)")
        else:
            result.add_error_downloads(
                f"{doc_name}_{year}", error_msg or "Unknown download error"
            )

        progress_bar.update(1)

    async def _download_with_retry(
        self,
        url: str,
        filepath: str,
        doc_name: str,
        year: str,
    ) -> Tuple[bool, Optional[str]]:
        """Download a file with retry logic."""
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = self.retry_strategy.calculate_backoff(attempt - 1)
                    logger.info(
                        f"Retry {attempt}/{self.max_retries} for {doc_name}_{year} "
                        f"after {backoff:.1f}s"
                    )
                    await asyncio.sleep(backoff)

                logger.debug(f"Downloading {doc_name}_{year} (async)")

                await self._stream_download(url, filepath)
                logger.info(f"Successfully downloaded {doc_name}_{year}")
                return True, None

            except Exception as e:
                last_exception = e

                if (
                    not self.retry_strategy.is_retryable(e)
                    or attempt >= self.max_retries
                ):
                    logger.error(
                        f"Download failed for {doc_name}_{year}: "
                        f"{type(e).__name__}: {e}"
                    )
                    break

                logger.warning(
                    f"Download error for {doc_name}_{year} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                )

        remove_file(filepath, log_on_error=False)

        error_msg = (
            f"{type(last_exception).__name__}: {last_exception}"
            if last_exception
            else "Unknown error"
        )
        return False, error_msg

    async def _stream_download(self, url: str, filepath: str) -> None:
        """Perform asynchronous streaming download."""
        try:
            await self.requests_adapter.async_download_file(
                url=url,
                output_path=filepath,
                chunk_size=self.chunk_size,
            )
        except Exception as e:
            remove_file(filepath, log_on_error=False)
            raise e

    async def _get_content_length(self, url: str) -> Optional[int]:
        """Get Content-Length from HTTP headers before downloading.

        Args:
            url: URL to check

        Returns:
            Expected file size in bytes, or None if not available
        """
        try:
            response = await self.requests_adapter.async_head(url)
            content_length = response.headers.get("content-length")

            if content_length:
                size_bytes = int(content_length)
                logger.debug(
                    f"Content-Length for {url}: {size_bytes / 1024 / 1024:.2f} MB"
                )
                return size_bytes
            else:
                logger.debug(f"No Content-Length header for {url}")
                return None

        except Exception as e:
            logger.warning(f"Failed to get Content-Length for {url}: {e}")
            return None

    @staticmethod
    def _extract_filename(url: str) -> str:
        """Extract the filename from the URL."""
        try:
            return url.split("/")[-1].split("?")[0] or "download"
        except Exception:
            return "download"

    def _validate_downloaded_file(
        self, filepath: str, expected_size: Optional[int] = None
    ) -> bool:
        """Validate that downloaded file is complete and not corrupted.

        Args:
            filepath: Path to downloaded file
            expected_size: Optional expected file size in bytes from Content-Length

        Returns:
            True if file is valid, False otherwise
        """
        try:
            path = Path(filepath)

            # Check 1: File exists
            if not path.exists():
                logger.error(f"Downloaded file does not exist: {filepath}")
                return False

            file_size = path.stat().st_size

            # Check 2: Minimum size validation (very permissive - just ensure file is not empty/corrupted)
            # Some legitimate CVM files (e.g., VLMO for certain years) can be quite small (< 100KB)
            MIN_EXPECTED_SIZE = 1024  # 1KB - just ensure file has some content
            if file_size < MIN_EXPECTED_SIZE:
                logger.error(
                    f"Downloaded file too small ({file_size} bytes, expected > {MIN_EXPECTED_SIZE}): {filepath}"
                )
                return False

            # Check 3: Expected size validation (if Content-Length was available)
            if expected_size is not None and expected_size > 0:
                # Allow 1% tolerance for HTTP headers, compression, etc
                tolerance = max(1024, expected_size * 0.01)  # At least 1KB tolerance
                size_diff = abs(file_size - expected_size)

                if size_diff > tolerance:
                    logger.error(
                        f"File size mismatch: expected {expected_size} bytes, "
                        f"got {file_size} bytes (diff: {size_diff}): {filepath}"
                    )
                    return False
                elif size_diff > 0:
                    logger.debug(
                        f"File size within tolerance: expected {expected_size}, "
                        f"got {file_size} (diff: {size_diff} bytes)"
                    )

            # Check 4: ZIP validity and completeness
            try:
                with zipfile.ZipFile(filepath, "r") as z:
                    # Test ZIP integrity of ALL files
                    bad_file = z.testzip()
                    if bad_file:
                        logger.error(f"Corrupted file in ZIP: {bad_file} ({filepath})")
                        return False

                    # Check if ZIP has at least one file
                    namelist = z.namelist()
                    if not namelist:
                        logger.error(f"Empty ZIP file: {filepath}")
                        return False

                    # Check 5: Validate at least one CSV exists (CVM specific)
                    csv_files = [n for n in namelist if n.lower().endswith(".csv")]
                    if not csv_files:
                        logger.warning(
                            f"No CSV files in ZIP: {filepath}. "
                            f"Files found: {', '.join(namelist[:5])}"
                            f"{'...' if len(namelist) > 5 else ''}"
                        )
                        # Not a fatal error, but suspicious

            except zipfile.BadZipFile as e:
                logger.error(f"Invalid ZIP file: {filepath} - {e}")
                return False

            logger.debug(
                f"File validation passed: {filepath} "
                f"({file_size / 1024 / 1024:.2f} MB)"
            )
            return True

        except Exception as e:
            logger.error(f"Error validating file {filepath}: {e}")
            return False

    def _track_failed_extraction(
        self, filepath: str, doc_name: str, year: str, error: str, dest_path: str
    ) -> None:
        """Track ZIPs with failed extraction for later retry.

        Creates a JSON file with failed extraction info for manual retry.

        Args:
            filepath: Path to the ZIP file
            doc_name: Document name (e.g., "DFP", "ITR")
            year: Year of the document
            error: Error message
            dest_path: Destination directory
        """
        try:
            tracking_dir = Path(dest_path) / ".pending_extractions"
            tracking_dir.mkdir(exist_ok=True, parents=True)

            tracking_file = tracking_dir / "failed_extractions.json"

            # Load existing failures
            failed_list = []
            if tracking_file.exists():
                try:
                    failed_list = json.loads(tracking_file.read_text(encoding="utf-8"))
                except Exception as load_err:
                    logger.warning(f"Failed to load tracking file: {load_err}")
                    failed_list = []

            # Check if already tracked (avoid duplicates)
            file_path_str = str(filepath)
            already_tracked = any(
                entry.get("filepath") == file_path_str for entry in failed_list
            )

            if not already_tracked:
                # Add new failure record
                file_size_mb = 0.0
                try:
                    file_size_mb = Path(filepath).stat().st_size / 1024 / 1024
                except Exception:
                    pass

                failed_list.append(
                    {
                        "filepath": file_path_str,
                        "doc_name": doc_name,
                        "year": year,
                        "error": error,
                        "timestamp": datetime.now().isoformat(),
                        "file_size_mb": round(file_size_mb, 2),
                    }
                )

                # Save tracking file
                tracking_file.write_text(
                    json.dumps(failed_list, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

                logger.warning(
                    f"⚠️ Extraction failed for {doc_name}_{year}. "
                    f"ZIP kept at: {filepath}. "
                    f"Total failed extractions: {len(failed_list)}. "
                    f"Run retry_failed_extractions() to process again."
                )
            else:
                logger.debug(f"Extraction failure already tracked: {doc_name}_{year}")

        except Exception as track_err:
            logger.error(f"Failed to track extraction failure: {track_err}")

    def retry_failed_extractions(self, destination_path: str) -> DownloadResult:
        """Retry extraction of previously failed ZIPs.

        Reads the failed_extractions.json file and attempts to extract
        ZIPs that failed in previous runs.

        Args:
            destination_path: Base destination directory

        Returns:
            DownloadResult with retry results

        Example:
            >>> adapter = HttpxAsyncDownloadAdapter(...)
            >>> result = adapter.retry_failed_extractions("/tmp/cvm_data")
            >>> print(f"Retried: {result.success_count_downloads} succeeded, "
            ...       f"{result.error_count_downloads} failed")
        """
        tracking_file = (
            Path(destination_path) / ".pending_extractions" / "failed_extractions.json"
        )

        if not tracking_file.exists():
            logger.info("No failed extractions to retry")
            return DownloadResult()

        try:
            failed_list = json.loads(tracking_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to read tracking file: {e}")
            return DownloadResult()

        result = DownloadResult()
        successful_entries = []

        logger.info(f"Retrying {len(failed_list)} failed extractions...")

        for entry in failed_list:
            filepath = entry.get("filepath")
            doc_name = entry.get("doc_name", "Unknown")
            year = entry.get("year", "Unknown")

            if not filepath or not Path(filepath).exists():
                logger.warning(
                    f"ZIP not found (may have been manually deleted): {filepath}"
                )
                continue

            try:
                # Get the directory where the ZIP is located
                zip_dir = str(Path(filepath).parent)

                logger.info(f"Retrying extraction: {doc_name}_{year}")
                self.file_extractor_repository.extract(filepath, zip_dir)

                # Verify extraction succeeded (check for parquet files)
                parquet_files = list(Path(zip_dir).glob("**/*.parquet"))
                if parquet_files:
                    result.add_success_downloads(f"{doc_name}_{year}")
                    successful_entries.append(entry)

                    # Remove ZIP after successful extraction
                    remove_file(filepath, log_on_error=True)

                    logger.info(
                        f"✓ Retry successful for {doc_name}_{year}: "
                        f"{len(parquet_files)} parquet files created"
                    )
                else:
                    logger.warning(
                        f"Extraction completed but no parquet files found: {doc_name}_{year}"
                    )
                    result.add_error_downloads(
                        f"{doc_name}_{year}", "Retry: No parquet files generated"
                    )

            except Exception as e:
                logger.error(f"Retry failed for {doc_name}_{year}: {e}")
                result.add_error_downloads(
                    f"{doc_name}_{year}", f"Retry failed: {type(e).__name__}: {e}"
                )

        # Update tracking file - remove successful entries
        if successful_entries:
            remaining_failures = [
                entry for entry in failed_list if entry not in successful_entries
            ]

            if remaining_failures:
                tracking_file.write_text(
                    json.dumps(remaining_failures, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                logger.info(
                    f"Updated tracking file: {len(remaining_failures)} failures remaining"
                )
            else:
                # All retries succeeded - remove tracking file
                try:
                    tracking_file.unlink()
                    tracking_file.parent.rmdir()  # Remove directory if empty
                    logger.info("All retries succeeded! Tracking file removed.")
                except Exception:
                    pass

        logger.info(
            f"Retry complete: {result.success_count_downloads} succeeded, "
            f"{result.error_count_downloads} failed"
        )

        return result
