"""Async HTTP download adapter for CVM ZIP files."""

import asyncio
from pathlib import Path

from ....core import (
    RetryStrategy,
    SimpleProgressBar,
    get_logger,
    remove_file,
)
from ....macro_infra import RequestsAdapter
from .core import DownloadResultCVM
from .download_extraction import extract_downloaded_file
from .download_validation import (
    find_parquet_files,
    validate_downloaded_file,
    validate_parquet_files,
)
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
        timeout: float = 60.0,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
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
            f'AsyncDownloadAdapterCVM initialized with max_concurrent={max_concurrent}, '
            f'http2={http2}, timeout={timeout}'
        )

    def download_docs(
        self,
        tasks: list[DownloadTaskCVM],
    ) -> DownloadResultCVM:
        """Asynchronously download documents."""
        result = DownloadResultCVM()
        total_files = len(tasks)

        if total_files == 0:
            logger.warning('No files to download')
            return result

        logger.info(
            f'Starting async download of {total_files} files '
            f'with {self.max_concurrent} concurrent downloads'
        )

        asyncio.run(self._execute_async_downloads(tasks, result))

        logger.info(
            f'Download completed: {result.success_count_downloads} successful, '
            f'{result.error_count_downloads} errors'
        )

        return result

    async def _execute_async_downloads(
        self,
        tasks: list[DownloadTaskCVM],
        result: DownloadResultCVM,
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
        result: DownloadResultCVM,
        progress_bar: SimpleProgressBar,
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
                f'Downloaded file validation failed for {document_key}: '
                f'{filepath}'
            )
            self._add_download_error(
                result,
                document_key,
                'Downloaded file corrupted, incomplete, or invalid ZIP',
            )
            remove_file(filepath, log_on_error=True)
            return

        if self.automatic_extractor:
            self._extract_downloaded_file(
                filepath=filepath,
                dest_path=dest_path,
                doc_name=doc_name,
                year=year,
                result=result,
            )
            return

        self._add_download_success(result, document_key)
        logger.info(f'✓ Downloaded {document_key} (extraction disabled)')

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
                        f'Retry {attempt}/{self.max_retries} for {doc_name}_{year} '
                        f'after {backoff:.1f}s'
                    )
                    await asyncio.sleep(backoff)

                logger.debug(f'Downloading {doc_name}_{year} (async)')

                await self._stream_download(url, filepath)
                logger.info(f'Successfully downloaded {doc_name}_{year}')
                return True, None

            except Exception as e:
                last_exception = e

                if (
                    not self.retry_strategy.is_retryable(e)
                    or attempt >= self.max_retries
                ):
                    logger.error(
                        f'Download failed for {doc_name}_{year}: '
                        f'{type(e).__name__}: {e}'
                    )
                    break

                logger.warning(
                    f'Download error for {doc_name}_{year} '
                    f'(attempt {attempt + 1}/{self.max_retries + 1}): {e}'
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
        except Exception as e:
            remove_file(filepath, log_on_error=False)
            raise e

    async def _get_content_length(self, url: str) -> int | None:
        """Get Content-Length from HTTP headers before downloading."""
        try:
            response = await self.requests_adapter.async_head(url)
            content_length = response.headers.get('content-length')

            if content_length:
                size_bytes = int(content_length)
                logger.debug(
                    f'Content-Length for {url}: {size_bytes / 1024 / 1024:.2f} MB'
                )
                return size_bytes
            else:
                logger.debug(f'No Content-Length header for {url}')
                return None

        except Exception as e:
            logger.warning(f'Failed to get Content-Length for {url}: {e}')
            return None

    def _validate_downloaded_file(
        self, filepath: str, expected_size: int | None = None
    ) -> bool:
        return validate_downloaded_file(filepath, expected_size)

    def _validate_parquet_files(
        self, parquet_files: list[Path], doc_name: str, year: str
    ) -> bool:
        return validate_parquet_files(parquet_files, doc_name, year)

    def _find_parquet_files(self, dest_path: str) -> list[Path]:
        return find_parquet_files(dest_path)

    def _add_download_success(
        self, result: DownloadResultCVM, document_key: str
    ) -> None:
        result.add_success_downloads(document_key)

    def _add_download_error(
        self,
        result: DownloadResultCVM,
        document_key: str,
        error_message: str,
    ) -> None:
        result.add_error_downloads(document_key, error_message)

    def _document_key(self, doc_name: str, year: str) -> str:
        return f'{doc_name}_{year}'
