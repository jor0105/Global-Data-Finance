"""Async HTTP download adapter for CVM ZIP files."""

import asyncio
from pathlib import Path

import httpx

from ....core import (
    RetryStrategy,
    SimpleProgressBar,
    get_logger,
    remove_file,
)
from ....macro_exceptions import NetworkError
from ....macro_exceptions import TimeoutError as MacroTimeoutError
from ....macro_infra import RequestsAdapter
from .core import DownloadResultCVM
from .download_extraction import extract_downloaded_file
from .download_validation import validate_downloaded_file
from .extract import ParquetExtractorAdapterCVM

logger = get_logger(__name__)

DownloadTaskCVM = tuple[str, str, str, str]
DownloadAttemptResultCVM = tuple[bool, str | None]


class AsyncDownloadAdapterCVM:
    """Download CVM ZIP files with retry, integrity checks, and extraction."""

    def __init__(
        self,
        file_extractor_repository: ParquetExtractorAdapterCVM,
        max_concurrent: int = 10,
        chunk_size: int = 8192,
        timeout: float = 180.0,
        max_retries: int = 5,
        initial_backoff: float = 1.0,
        max_backoff: float = 120.0,
        backoff_multiplier: float = 2.0,
        http2: bool = True,
        automatic_extractor: bool = False,
    ):
        """Initialize the asynchronous download adapter."""
        self.file_extractor_repository = file_extractor_repository
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.automatic_extractor = automatic_extractor

        self.requests_adapter = RequestsAdapter(
            timeout=timeout,
            http2=http2,
            verify=True,
            max_redirects=5,
        )

        self.retry_strategy = RetryStrategy(
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            multiplier=backoff_multiplier,
        )

        logger.debug(
            'AsyncDownloadAdapterCVM initialized with max_concurrent=%d, http2=%s, timeout=%s',
            max_concurrent,
            http2,
            timeout,
        )

    def download_docs(
        self,
        tasks: list[DownloadTaskCVM],
        *,
        automatic_extractor: bool | None = None,
    ) -> DownloadResultCVM:
        """Synchronously download documents.

        Thin wrapper that owns the event loop via ``asyncio.run``. Call
        :meth:`async_download_docs` directly to compose downloads into
        already-async code.

        Args:
            tasks: List of download tasks to execute.
            automatic_extractor: If ``True``, extract downloaded ZIPs
                to Parquet after download.  When ``None`` (the default),
                falls back to ``self.automatic_extractor``.
        """
        return asyncio.run(
            self.async_download_docs(
                tasks,
                automatic_extractor=automatic_extractor,
            )
        )

    async def async_download_docs(
        self,
        tasks: list[DownloadTaskCVM],
        *,
        automatic_extractor: bool | None = None,
    ) -> DownloadResultCVM:
        """Asynchronously download documents in the current event loop.

        Args:
            tasks: List of download tasks to execute.
            automatic_extractor: If ``True``, extract downloaded ZIPs
                to Parquet after download.  When ``None`` (the default),
                falls back to ``self.automatic_extractor``.
        """
        effective_extractor = (
            automatic_extractor
            if automatic_extractor is not None
            else self.automatic_extractor
        )

        result = DownloadResultCVM()
        total_files = len(tasks)

        if total_files == 0:
            logger.warning('No files to download')
            return result

        logger.info(
            'Starting async download of %d files with %d concurrent downloads',
            total_files,
            self.max_concurrent,
        )

        await self._run_downloads(
            tasks,
            result,
            automatic_extractor=effective_extractor,
        )

        logger.info(
            'Download completed: %d successful, %d errors',
            result.success_count_downloads,
            result.error_count_downloads,
        )

        return result

    async def _run_downloads(
        self,
        tasks: list[DownloadTaskCVM],
        result: DownloadResultCVM,
        *,
        automatic_extractor: bool = False,
    ) -> None:
        """Execute async downloads with concurrency control."""
        progress_bar = SimpleProgressBar(
            total=len(tasks), desc='Downloading (async)'
        )
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def download_with_semaphore(task: DownloadTaskCVM) -> None:
            async with semaphore:
                url, doc_name, year, dest_path = task
                await self._download_and_extract(
                    url,
                    dest_path,
                    doc_name,
                    year,
                    result,
                    progress_bar,
                    automatic_extractor=automatic_extractor,
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
        result: DownloadResultCVM,
        progress_bar: SimpleProgressBar,
        *,
        automatic_extractor: bool = False,
    ) -> None:
        """Download a file and extract its contents."""
        filename = url.split('/')[-1].split('?')[0] or 'download'
        filepath = str(Path(dest_path) / filename)

        try:
            await self._process_downloaded_file(
                url=url,
                filepath=filepath,
                dest_path=dest_path,
                doc_name=doc_name,
                year=year,
                result=result,
                automatic_extractor=automatic_extractor,
            )
        finally:
            progress_bar.update(1)

    async def _process_downloaded_file(
        self,
        url: str,
        filepath: str,
        dest_path: str,
        doc_name: str,
        year: str,
        result: DownloadResultCVM,
        *,
        automatic_extractor: bool = False,
    ) -> None:
        success, error_msg = await self._download_with_retry(
            url, filepath, doc_name, year
        )
        document_key = self._document_key(doc_name, year)

        if not success:
            self._add_download_error(
                result, document_key, error_msg or 'Unknown download error'
            )
            return

        expected_size = await self._get_content_length(url)
        if not self._validate_downloaded_file(filepath, expected_size):
            logger.error(
                'Downloaded file validation failed for %s: %s',
                document_key,
                filepath,
            )
            self._add_download_error(
                result,
                document_key,
                'Downloaded file corrupted, incomplete, or invalid ZIP',
            )
            remove_file(filepath, log_on_error=True)
            return

        if automatic_extractor:
            self._extract_downloaded_file(
                filepath=filepath,
                dest_path=dest_path,
                doc_name=doc_name,
                year=year,
                result=result,
            )
            return

        self._add_download_success(result, document_key)
        logger.info('✓ Downloaded %s (extraction disabled)', document_key)

    def _extract_downloaded_file(
        self,
        filepath: str,
        dest_path: str,
        doc_name: str,
        year: str,
        result: DownloadResultCVM,
    ) -> None:
        extract_downloaded_file(
            file_extractor_repository=self.file_extractor_repository,
            filepath=filepath,
            dest_path=dest_path,
            doc_name=doc_name,
            year=year,
            result=result,
            cleanup_file=lambda path: remove_file(path, log_on_error=True),
        )

    async def _download_with_retry(
        self,
        url: str,
        filepath: str,
        doc_name: str,
        year: str,
    ) -> DownloadAttemptResultCVM:
        """Download a file with retry logic."""
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    backoff = self.retry_strategy.calculate_backoff(
                        attempt - 1
                    )
                    logger.info(
                        'Retry %d/%d for %s_%s after %.1fs',
                        attempt,
                        self.max_retries,
                        doc_name,
                        year,
                        backoff,
                    )
                    await asyncio.sleep(backoff)

                logger.debug('Downloading %s_%s (async)', doc_name, year)

                await self._stream_download(url, filepath)
                logger.info('Successfully downloaded %s_%s', doc_name, year)
                return True, None

            except Exception as e:
                timeouts = (
                    httpx.TimeoutException,
                    TimeoutError,
                    asyncio.TimeoutError,
                )
                net_errs = (
                    httpx.RequestError,
                    httpx.HTTPStatusError,
                    ConnectionError,
                )
                key = f'{doc_name}_{year}'
                if isinstance(e, timeouts):
                    e = MacroTimeoutError(key, self.requests_adapter.timeout)
                elif isinstance(e, net_errs):
                    e = NetworkError(key, f'{type(e).__name__}: {e}')

                last_exception = e

                retryable = self.retry_strategy.is_retryable(e)
                if not retryable or attempt >= self.max_retries:
                    logger.error(
                        'Download failed for %s: %s: %s',
                        key,
                        type(e).__name__,
                        e,
                        exc_info=True,
                    )
                    break

                logger.warning(
                    'Download error for %s (attempt %d/%d): %s',
                    key,
                    attempt + 1,
                    self.max_retries + 1,
                    e,
                )

        remove_file(filepath, log_on_error=False)

        error_msg = (
            f'{type(last_exception).__name__}: {last_exception}'
            if last_exception
            else 'Unknown error'
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
        except Exception:
            remove_file(filepath, log_on_error=False)
            raise

    async def _get_content_length(self, url: str) -> int | None:
        """Get Content-Length from HTTP headers before downloading."""
        try:
            response = await self.requests_adapter.async_head(url)
            content_length = response.headers.get('content-length')

            if content_length:
                size_bytes = int(content_length)
                logger.debug(
                    'Content-Length for %s: %.2f MB',
                    url,
                    size_bytes / 1024 / 1024,
                )
                return size_bytes
            else:
                logger.debug('No Content-Length header for %s', url)
                return None

        except Exception as e:
            logger.warning('Failed to get Content-Length for %s: %s', url, e)
            return None

    def _validate_downloaded_file(
        self, filepath: str, expected_size: int | None = None
    ) -> bool:
        return validate_downloaded_file(filepath, expected_size)

    def _add_download_success(self, res: DownloadResultCVM, key: str) -> None:
        res.add_success_downloads(key)

    def _add_download_error(
        self, res: DownloadResultCVM, key: str, msg: str
    ) -> None:
        res.add_error_downloads(key, msg)

    def _document_key(self, doc_name: str, year: str) -> str:
        return f'{doc_name}_{year}'
