import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.brazil.cvm.fundamental_stocks_data import (
    DownloadResult,
    HttpxAsyncDownloadAdapter,
)
from src.macro_exceptions import (
    DiskFullError,
    ExtractionError,
    NetworkError,
    TimeoutError,
)


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterInitialization:
    def test_init_with_default_values(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        assert adapter.max_concurrent == 10
        assert adapter.chunk_size == 8192
        assert adapter.max_retries == 3
        assert adapter.automatic_extractor is False
        assert adapter.file_extractor_repository is mock_extractor

    def test_init_with_custom_values(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor,
            max_concurrent=20,
            chunk_size=16384,
            timeout=120.0,
            max_retries=5,
            initial_backoff=2.0,
            max_backoff=120.0,
            backoff_multiplier=3.0,
            http2=False,
            automatic_extractor=True,
        )

        assert adapter.max_concurrent == 20
        assert adapter.chunk_size == 16384
        assert adapter.max_retries == 5
        assert adapter.automatic_extractor is True
        assert adapter.retry_strategy.initial_backoff == 2.0
        assert adapter.retry_strategy.max_backoff == 120.0
        assert adapter.retry_strategy.multiplier == 3.0

    def test_init_creates_requests_adapter(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        assert adapter.requests_adapter is not None
        assert hasattr(adapter.requests_adapter, "async_download_file")

    def test_init_creates_retry_strategy(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        assert adapter.retry_strategy is not None
        assert hasattr(adapter.retry_strategy, "is_retryable")
        assert hasattr(adapter.retry_strategy, "calculate_backoff")

    def test_init_with_zero_max_concurrent(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_concurrent=0
        )

        assert adapter.max_concurrent == 0

    def test_init_with_very_high_concurrency(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_concurrent=1000
        )

        assert adapter.max_concurrent == 1000


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterHelpers:
    def test_extract_filename_normal_url(self):
        url = "https://example.com/path/to/document.zip"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "document.zip"

    def test_extract_filename_with_query_params(self):
        url = "https://example.com/document.zip?param=value&other=123"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "document.zip"

    def test_extract_filename_with_no_extension(self):
        url = "https://example.com/path/to/document"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "document"

    def test_extract_filename_from_empty_url(self):
        url = ""
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "download"

    def test_extract_filename_from_malformed_url(self):
        url = "not-a-url"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "not-a-url"

    def test_extract_filename_with_trailing_slash(self):
        url = "https://example.com/path/"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "download"

    def test_extract_filename_with_special_characters(self):
        url = "https://example.com/açúcar_café_2023.zip"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "açúcar_café_2023.zip"


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterDownloadDocs:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.asyncio.run"
    )
    def test_download_docs_with_empty_tasks(self, mock_asyncio_run):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        result = adapter.download_docs([])

        assert isinstance(result, DownloadResult)
        assert result.success_count_downloads == 0
        assert result.error_count_downloads == 0
        mock_asyncio_run.assert_not_called()

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.asyncio.run"
    )
    def test_download_docs_calls_async_execution(self, mock_asyncio_run):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        tasks = [
            ("https://example.com/file1.zip", "DRE", "2023", "/tmp/output"),
            ("https://example.com/file2.zip", "BPARMS", "2023", "/tmp/output"),
        ]

        mock_asyncio_run.return_value = None

        result = adapter.download_docs(tasks)

        mock_asyncio_run.assert_called_once()
        assert isinstance(result, DownloadResult)

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.asyncio.run"
    )
    def test_download_docs_with_single_task(self, mock_asyncio_run):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        tasks = [("https://example.com/file.zip", "DRE", "2023", "/tmp/output")]

        adapter.download_docs(tasks)

        mock_asyncio_run.assert_called_once()

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.asyncio.run"
    )
    def test_download_docs_with_many_tasks(self, mock_asyncio_run):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        tasks = [
            (f"https://example.com/file{i}.zip", f"DOC{i}", "2023", "/tmp/output")
            for i in range(100)
        ]

        adapter.download_docs(tasks)

        mock_asyncio_run.assert_called_once()


@pytest.mark.asyncio
class TestHttpxAsyncDownloadAdapterAsyncMethods:
    async def test_download_with_retry_success_first_attempt(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        async def mock_stream_download(url, filepath):
            pass

        adapter._stream_download = mock_stream_download

        success, error_msg = await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        assert success is True
        assert error_msg is None

    async def test_download_with_retry_failure_after_retries(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_retries=2
        )

        async def mock_stream_download(url, filepath):
            raise NetworkError("DRE", "Connection refused")

        adapter._stream_download = mock_stream_download

        success, error_msg = await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        assert success is False
        assert error_msg is not None
        assert "NetworkError" in error_msg

    async def test_download_with_retry_success_on_second_attempt(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_retries=3
        )

        call_count = 0

        async def mock_stream_download(url, filepath):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NetworkError("DRE", "Temporary error")

        adapter._stream_download = mock_stream_download

        success, error_msg = await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        assert success is True
        assert error_msg is None
        assert call_count == 2

    async def test_download_with_retry_non_retryable_error(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_retries=5
        )

        call_count = 0

        async def mock_stream_download(url, filepath):
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid URL format")

        adapter._stream_download = mock_stream_download

        success, error_msg = await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        assert success is False
        assert error_msg is not None
        assert call_count == 1

    async def test_download_with_retry_timeout_error(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_retries=2
        )

        async def mock_stream_download(url, filepath):
            raise TimeoutError("DRE", 30.0)

        adapter._stream_download = mock_stream_download

        success, error_msg = await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        assert success is False
        assert "TimeoutError" in error_msg

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_download_with_retry_cleans_up_on_failure(self, mock_remove):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_retries=1
        )

        async def mock_stream_download(url, filepath):
            raise NetworkError("DRE", "Error")

        adapter._stream_download = mock_stream_download

        await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        mock_remove.assert_called_once_with("/tmp/file.zip", log_on_error=False)

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.asyncio.sleep"
    )
    async def test_download_with_retry_backoff(self, mock_sleep):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor,
            max_retries=3,
            initial_backoff=1.0,
        )

        call_count = 0

        async def mock_stream_download(url, filepath):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("DRE", "Temporary")

        adapter._stream_download = mock_stream_download

        await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        assert mock_sleep.call_count >= 1


@pytest.mark.asyncio
class TestHttpxAsyncDownloadAdapterStreamDownload:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_stream_download_cleans_up_on_error(self, mock_remove):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        adapter.requests_adapter = MagicMock()
        adapter.requests_adapter.async_download_file = AsyncMock(
            side_effect=NetworkError("DRE", "Error")
        )

        with pytest.raises(NetworkError):
            await adapter._stream_download(
                "https://example.com/file.zip", "/tmp/file.zip"
            )

        mock_remove.assert_called_once_with("/tmp/file.zip", log_on_error=False)

    async def test_stream_download_calls_requests_adapter(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        adapter.requests_adapter = MagicMock()
        adapter.requests_adapter.async_download_file = AsyncMock()

        await adapter._stream_download("https://example.com/file.zip", "/tmp/file.zip")

        adapter.requests_adapter.async_download_file.assert_called_once_with(
            url="https://example.com/file.zip",
            output_path="/tmp/file.zip",
            chunk_size=8192,
        )

    async def test_stream_download_uses_custom_chunk_size(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, chunk_size=16384
        )

        adapter.requests_adapter = MagicMock()
        adapter.requests_adapter.async_download_file = AsyncMock()

        await adapter._stream_download("https://example.com/file.zip", "/tmp/file.zip")

        adapter.requests_adapter.async_download_file.assert_called_once_with(
            url="https://example.com/file.zip",
            output_path="/tmp/file.zip",
            chunk_size=16384,
        )


@pytest.mark.asyncio
class TestHttpxAsyncDownloadAdapterDownloadAndExtract:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_download_and_extract_without_automatic_extractor(
        self, mock_remove, tmp_path
    ):
        import random
        import string
        import zipfile

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        zip_path = output_dir / "file.zip"

        # CRITICAL FIX: Create larger file to pass validation (> 100KB)
        # Generate 150KB of random data to ensure it passes size validation
        random_data = "".join(
            random.choices(string.ascii_letters + string.digits, k=150_000)
        )
        csv_data = "col1,col2,col3,col4\n" + "\n".join(
            [
                f"{random.randint(1,1000)},{random.random():.4f},"
                f"{random.choice(['A','B','C','D'])},{random.randint(100,999)}"
                for _ in range(200)
            ]
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("test.txt", random_data)
            zf.writestr("data.csv", csv_data)

        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=False
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return True, None

        async def mock_get_content_length(url):
            return None  # No Content-Length available

        adapter._download_with_retry = mock_download_with_retry
        adapter._get_content_length = mock_get_content_length

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            str(output_dir),
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        assert result.success_count_downloads == 1
        assert "DRE_2023" in result.successful_downloads

        mock_extractor.extract.assert_not_called()

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_download_and_extract_with_automatic_extractor(
        self, mock_remove, tmp_path
    ):
        import random
        import string
        import zipfile

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        zip_path = output_dir / "file.zip"
        # CRITICAL FIX: Create larger file to pass validation (> 100KB)
        random_data = "".join(
            random.choices(string.ascii_letters + string.digits, k=150_000)
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("test.txt", random_data)
            zf.writestr("data.csv", "col1,col2\n1,2\n")

        (output_dir / "file1.parquet").touch()
        (output_dir / "file2.parquet").touch()

        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=True
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return True, None

        async def mock_get_content_length(url):
            return None

        adapter._download_with_retry = mock_download_with_retry
        adapter._get_content_length = mock_get_content_length

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            str(output_dir),
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        mock_extractor.extract.assert_called_once()
        assert (
            mock_remove.called
        ), "ZIP source should be removed after successful extraction with parquet files"
        assert result.success_count_downloads == 1

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_download_and_extract_no_parquet_files_keeps_zip(
        self, mock_remove, tmp_path
    ):
        import random
        import string
        import zipfile

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        zip_path = output_dir / "file.zip"
        # CRITICAL FIX: Create larger file to pass validation (> 100KB)
        random_data = "".join(
            random.choices(string.ascii_letters + string.digits, k=150_000)
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("test.txt", random_data)
            zf.writestr("data.csv", "col1,col2\n1,2\n")

        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=True
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return True, None

        async def mock_get_content_length(url):
            return None

        adapter._download_with_retry = mock_download_with_retry
        adapter._get_content_length = mock_get_content_length

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            str(output_dir),
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        mock_extractor.extract.assert_called_once()
        assert (
            not mock_remove.called
        ), "ZIP source should NOT be removed if no parquet files were created"
        assert result.error_count_downloads == 1
        assert "No parquet files generated" in result.failed_downloads["DRE_2023"]

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_download_and_extract_extraction_error(self, mock_remove, tmp_path):
        import random
        import string
        import zipfile

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        zip_path = output_dir / "file.zip"
        # CRITICAL FIX: Create larger file to pass validation (> 100KB)
        random_data = "".join(
            random.choices(string.ascii_letters + string.digits, k=150_000)
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("test.txt", random_data)
            zf.writestr("data.csv", "col1,col2\n1,2\n")

        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = ExtractionError("/tmp/file.zip", "Bad CSV")

        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=True
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return True, None

        async def mock_get_content_length(url):
            return None

        adapter._download_with_retry = mock_download_with_retry
        adapter._get_content_length = mock_get_content_length

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            str(output_dir),
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        assert result.error_count_downloads == 1
        assert "DRE_2023" in result.failed_downloads
        assert "ExtractionFailed" in result.failed_downloads["DRE_2023"]

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_download_and_extract_disk_full_error(self, mock_remove, tmp_path):
        import random
        import string
        import zipfile

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        zip_path = output_dir / "file.zip"
        # CRITICAL FIX: Create larger file to pass validation (> 100KB)
        random_data = "".join(
            random.choices(string.ascii_letters + string.digits, k=150_000)
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("test.txt", random_data)
            zf.writestr("data.csv", "col1,col2\n1,2\n")

        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = DiskFullError("/tmp/output")

        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=True
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return True, None

        async def mock_get_content_length(url):
            return None

        adapter._download_with_retry = mock_download_with_retry
        adapter._get_content_length = mock_get_content_length

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            str(output_dir),
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        assert result.error_count_downloads == 1
        assert "DiskFull" in result.failed_downloads["DRE_2023"]
        assert mock_remove.called

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.remove_file"
    )
    async def test_download_and_extract_unexpected_extraction_error(
        self, mock_remove, tmp_path
    ):
        import random
        import string
        import zipfile

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        zip_path = output_dir / "file.zip"
        # CRITICAL FIX: Create larger file to pass validation (> 100KB)
        random_data = "".join(
            random.choices(string.ascii_letters + string.digits, k=150_000)
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("test.txt", random_data)
            zf.writestr("data.csv", "col1,col2\n1,2\n")

        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = RuntimeError("Unexpected error")

        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=True
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return True, None

        async def mock_get_content_length(url):
            return None

        adapter._download_with_retry = mock_download_with_retry
        adapter._get_content_length = mock_get_content_length

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            str(output_dir),
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        assert result.error_count_downloads == 1
        assert "UnexpectedError" in result.failed_downloads["DRE_2023"]

    async def test_download_and_extract_download_failure(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=True
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return False, "NetworkError: Connection refused"

        adapter._download_with_retry = mock_download_with_retry

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            "/tmp/output",
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        assert result.error_count_downloads == 1
        assert "DRE_2023" in result.failed_downloads
        mock_extractor.extract.assert_not_called()

    async def test_download_and_extract_updates_progress(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, automatic_extractor=False
        )

        async def mock_download_with_retry(url, filepath, doc_name, year):
            return True, None

        adapter._download_with_retry = mock_download_with_retry

        mock_progress = MagicMock()
        result = DownloadResult()

        await adapter._download_and_extract(
            "https://example.com/file.zip",
            "/tmp/output",
            "DRE",
            "2023",
            result,
            mock_progress,
        )

        mock_progress.update.assert_called_once_with(1)


@pytest.mark.asyncio
class TestHttpxAsyncDownloadAdapterConcurrency:
    async def test_execute_async_downloads_respects_semaphore(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor, max_concurrent=2
        )

        concurrent_count = 0
        max_concurrent = 0
        lock = asyncio.Lock()

        async def mock_download_and_extract(*args):
            nonlocal concurrent_count, max_concurrent
            async with lock:
                concurrent_count += 1
                if concurrent_count > max_concurrent:
                    max_concurrent = concurrent_count

            await asyncio.sleep(0.01)

            async with lock:
                concurrent_count -= 1

        adapter._download_and_extract = mock_download_and_extract

        tasks = [
            (f"https://example.com/file{i}.zip", "DRE", "2023", "/tmp/output")
            for i in range(10)
        ]

        result = DownloadResult()

        await adapter._execute_async_downloads(tasks, result)

        assert max_concurrent <= 2

    async def test_execute_async_downloads_with_empty_tasks(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        result = DownloadResult()

        await adapter._execute_async_downloads([], result)

        assert result.success_count_downloads == 0
        assert result.error_count_downloads == 0


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterEdgeCases:
    def test_adapter_with_none_extractor(self):
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=None)
        assert adapter.file_extractor_repository is None

    def test_extract_filename_edge_cases(self):
        test_cases = [
            ("", "download"),
            ("/", "download"),
            ("https://", "download"),
            ("file.zip", "file.zip"),
            ("path/to/file.zip?", "file.zip"),
            ("https://example.com/", "download"),
        ]

        for url, expected in test_cases:
            result = HttpxAsyncDownloadAdapter._extract_filename(url)
            assert result == expected, f"Failed for URL: {url}"

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests.httpx_async_download_adapter.asyncio.run"
    )
    def test_download_docs_with_malformed_tasks(self, mock_asyncio_run):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        tasks = [("https://example.com/file.zip", "DRE", "2023", "/tmp/output")]

        result = adapter.download_docs(tasks)

        assert isinstance(result, DownloadResult)


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterDownloadDocsRepository:
    def test_implements_download_docs_method(self):
        mock_extractor = MagicMock()
        adapter = HttpxAsyncDownloadAdapter(file_extractor_repository=mock_extractor)

        assert hasattr(adapter, "download_docs")
        assert callable(adapter.download_docs)

    def test_can_be_used_as_download_repository(self):
        from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
            DownloadDocsCVMRepository,
        )

        mock_extractor = MagicMock()
        adapter: DownloadDocsCVMRepository = HttpxAsyncDownloadAdapter(
            file_extractor_repository=mock_extractor
        )

        assert isinstance(adapter, HttpxAsyncDownloadAdapter)
