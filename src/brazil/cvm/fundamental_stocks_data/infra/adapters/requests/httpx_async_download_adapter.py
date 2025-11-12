import asyncio
from pathlib import Path
from typing import List, Optional, Tuple

from src.brazil.cvm.fundamental_stocks_data.application import (
    DownloadDocsCVMRepository,
    FileExtractorRepository,
)
from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
from src.core import RetryStrategy, SimpleProgressBar, get_logger, remove_file
from src.macro_exceptions import DiskFullError, ExtractionError
from src.macro_infra import RequestsAdapter

logger = get_logger(__name__)


class HttpxAsyncDownloadAdapter(DownloadDocsCVMRepository):
    """
    Asynchronous download adapter using httpx.

    This adapter performs downloads asynchronously and in parallel,
    offering superior performance compared to traditional synchronous downloads.
    Uses RequestsAdapter as an interface for the httpx library.
    """

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
            file_extractor_repository: File extractor for extracting downloaded ZIPs
            max_concurrent: Maximum number of concurrent downloads
            chunk_size: Chunk size for streaming
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts on failure
            initial_backoff: Initial backoff in seconds
            max_backoff: Maximum backoff in seconds
            backoff_multiplier: Exponential backoff multiplier
            http2: Enable HTTP/2
        """
        self.file_extractor_repository = file_extractor_repository
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.automatic_extractor = automatic_extractor

        # Configure requests adapter to download
        self.requests_adapter = RequestsAdapter(
            timeout=timeout,
            http2=http2,
            verify=True,
            max_redirects=20,
        )

        # Configure retry strategy
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
        """
        Executes downloads asynchronously with concurrency control.

        Args:
            tasks: List of download tasks
            result: Object to accumulate results
        """
        progress_bar = SimpleProgressBar(total=len(tasks), desc="Downloading (async)")
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def download_with_semaphore(task):
            async with semaphore:
                url, doc_name, year, dest_path = task
                await self._download_and_extract(
                    url, dest_path, doc_name, year, result, progress_bar
                )

        try:
            # Create all asynchronous tasks
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
        """
        Downloads a file and extracts its contents.

        Args:
            url: File URL
            dest_path: Destination path
            doc_name: Document name
            year: Document year
            result: Object to accumulate results
            progress_bar: Progress bar
        """
        filename = self._extract_filename(url)
        filepath = str(Path(dest_path) / filename)

        success, error_msg = await self._download_with_retry(
            url, filepath, doc_name, year
        )

        if success and self.automatic_extractor:
            # Extract file after successful download
            try:
                logger.info(f"Starting extraction for {doc_name}_{year}")
                self.file_extractor_repository.extract(filepath, dest_path)
                result.add_success_downloads(f"{doc_name}_{year}")
                logger.info(f"Extraction completed for {doc_name}_{year}")
                remove_file(filepath, log_on_error=True)

            except DiskFullError as disk_err:
                logger.error(f"Disk full during extraction {filepath}: {disk_err}")
                result.add_error_downloads(
                    f"{doc_name}_{year}", f"DiskFull: {disk_err}"
                )
                remove_file(filepath, log_on_error=True)

            except ExtractionError as extract_exc:
                logger.error(f"Extraction error for {filepath}: {extract_exc}")
                result.add_error_downloads(
                    f"{doc_name}_{year}", f"Extraction failed: {extract_exc}"
                )

            except Exception as extract_exc:
                logger.error(
                    f"Unexpected extraction error for {filepath}: "
                    f"{type(extract_exc).__name__}: {extract_exc}"
                )
                result.add_error_downloads(
                    f"{doc_name}_{year}",
                    f"Unexpected extraction error: {extract_exc}",
                )
        elif success:
            result.add_success_downloads(f"{doc_name}_{year}")
        else:
            result.add_error_downloads(
                f"{doc_name}_{year}", error_msg or "Unknown error"
            )

        progress_bar.update(1)

    async def _download_with_retry(
        self,
        url: str,
        filepath: str,
        doc_name: str,
        year: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Downloads a file with retry logic.

        Returns:
            Tuple (success, error_message)
        """
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

                # Check if should retry
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

        # Clean up file in case of failure
        remove_file(filepath, log_on_error=False)

        error_msg = (
            f"{type(last_exception).__name__}: {last_exception}"
            if last_exception
            else "Unknown error"
        )
        return False, error_msg

    async def _stream_download(self, url: str, filepath: str) -> None:
        """
        Performs asynchronous streaming download.

        Args:
            url: File URL
            filepath: Path to save the file

        Raises:
            Exception: In case of download error
        """
        try:
            await self.requests_adapter.async_download_file(
                url=url,
                output_path=filepath,
                chunk_size=self.chunk_size,
            )
        except Exception as e:
            # Clean up partially downloaded file
            remove_file(filepath, log_on_error=False)
            raise e

    @staticmethod
    def _extract_filename(url: str) -> str:
        """
        Extracts the filename from the URL.

        Args:
            url: File URL

        Returns:
            Filename extracted from URL or 'download' as fallback
        """
        try:
            return url.split("/")[-1].split("?")[0] or "download"
        except Exception:
            return "download"
