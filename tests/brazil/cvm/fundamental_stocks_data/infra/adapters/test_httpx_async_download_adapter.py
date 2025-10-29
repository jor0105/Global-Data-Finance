"""
Testes para o HttpxAsyncDownloadAdapter.

Testes básicos para validar o funcionamento do adaptador de download
assíncrono usando httpx através do RequestsAdapter.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.brazil.cvm.fundamental_stocks_data import DownloadResult
from src.brazil.cvm.fundamental_stocks_data.infra.adapters.httpx_async_download_adapter import (
    HttpxAsyncDownloadAdapter,
)


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterInit:
    def test_init_with_default_values(self):
        adapter = HttpxAsyncDownloadAdapter()
        assert adapter.max_concurrent == 10
        assert adapter.chunk_size == 8192
        assert adapter.max_retries == 3

    def test_init_with_custom_values(self):
        adapter = HttpxAsyncDownloadAdapter(
            max_concurrent=20,
            chunk_size=16384,
            timeout=60.0,
            max_retries=5,
            http2=True,
        )
        assert adapter.max_concurrent == 20
        assert adapter.chunk_size == 16384
        assert adapter.max_retries == 5

    def test_init_creates_http_client(self):
        adapter = HttpxAsyncDownloadAdapter()
        assert adapter.http_client is not None


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterHelpers:
    def test_extract_filename_normal_url(self):
        url = "https://example.com/path/to/document.zip"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "document.zip"

    def test_extract_filename_with_query_params(self):
        url = "https://example.com/document.zip?param=value"
        filename = HttpxAsyncDownloadAdapter._extract_filename(url)
        assert filename == "document.zip"

    def test_extract_year_standard_format(self):
        url = "https://example.com/dre_2023.zip"
        year = HttpxAsyncDownloadAdapter._extract_year(url)
        assert year == "2023"

    def test_extract_year_with_full_path(self):
        url = "https://cvm.gov.br/data/DRE_2024.zip"
        year = HttpxAsyncDownloadAdapter._extract_year(url)
        assert year == "2024"


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterPrepare:
    def test_prepare_tasks_single_doc(self):
        adapter = HttpxAsyncDownloadAdapter()
        dict_zip = {
            "DRE": [
                "https://example.com/dre_2023.zip",
                "https://example.com/dre_2022.zip",
            ]
        }
        docs_paths = {
            "DRE": {
                2023: "/tmp/DRE/2023",
                2022: "/tmp/DRE/2022",
            }
        }

        tasks = adapter._prepare_download_tasks(dict_zip, docs_paths)

        assert len(tasks) == 2
        assert all(len(task) == 4 for task in tasks)

    def test_prepare_tasks_multiple_docs(self):
        adapter = HttpxAsyncDownloadAdapter()
        dict_zip = {
            "DRE": ["https://example.com/dre_2023.zip"],
            "ITR": ["https://example.com/itr_2023.zip"],
        }
        docs_paths = {
            "DRE": {2023: "/tmp/DRE/2023"},
            "ITR": {2023: "/tmp/ITR/2023"},
        }

        tasks = adapter._prepare_download_tasks(dict_zip, docs_paths)

        assert len(tasks) == 2

    def test_prepare_tasks_empty_dict(self):
        adapter = HttpxAsyncDownloadAdapter()
        dict_zip = {}
        docs_paths = {}

        tasks = adapter._prepare_download_tasks(dict_zip, docs_paths)

        assert len(tasks) == 0


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterDownloadDocs:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.httpx_async_download_adapter.SimpleProgressBar"
    )
    def test_download_docs_empty_dict(self, mock_progress):
        adapter = HttpxAsyncDownloadAdapter()
        mock_progress.return_value = MagicMock()

        result = adapter.download_docs({}, {})

        assert isinstance(result, DownloadResult)
        assert result.success_count == 0
        assert result.error_count == 0

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.httpx_async_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.httpx_async_download_adapter.asyncio.run"
    )
    def test_download_docs_calls_async_execution(self, mock_asyncio_run, mock_progress):
        # Create a mock extractor that does nothing
        mock_extractor = MagicMock()
        mock_extractor.extract = MagicMock(return_value=None)

        adapter = HttpxAsyncDownloadAdapter(file_extractor=mock_extractor)
        mock_progress.return_value = MagicMock()

        dict_zip = {"DRE": ["https://example.com/dre_2023.zip"]}
        docs_paths = {"DRE": {2023: "/tmp/DRE/2023"}}

        # Mock the async execution to not actually run
        mock_asyncio_run.return_value = None

        adapter.download_docs(dict_zip, docs_paths)

        # Verify that asyncio.run was called
        mock_asyncio_run.assert_called_once()


@pytest.mark.asyncio
class TestHttpxAsyncDownloadAdapterAsync:
    async def test_download_with_retry_success_first_attempt(self):
        adapter = HttpxAsyncDownloadAdapter()

        # Mock the _stream_download method
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
        adapter = HttpxAsyncDownloadAdapter(max_retries=2)

        # Mock the _stream_download method to always fail
        async def mock_stream_download(url, filepath):
            raise Exception("Download failed")

        adapter._stream_download = mock_stream_download

        success, error_msg = await adapter._download_with_retry(
            "https://example.com/file.zip",
            "/tmp/file.zip",
            "DRE",
            "2023",
        )

        assert success is False
        assert error_msg is not None
        assert "Download failed" in error_msg


@pytest.mark.unit
class TestHttpxAsyncDownloadAdapterCleanup:
    def test_cleanup_file_removes_existing_file(self, tmp_path):
        test_file = tmp_path / "test.zip"
        test_file.touch()

        assert test_file.exists()

        HttpxAsyncDownloadAdapter._cleanup_file(str(test_file))

        assert not test_file.exists()

    def test_cleanup_file_handles_nonexistent_file(self):
        # Should not raise exception
        HttpxAsyncDownloadAdapter._cleanup_file("/nonexistent/file.zip")

    def test_cleanup_zip_file_removes_existing_file(self, tmp_path):
        test_file = tmp_path / "test.zip"
        test_file.touch()

        assert test_file.exists()

        HttpxAsyncDownloadAdapter._cleanup_zip_file(str(test_file))

        assert not test_file.exists()
