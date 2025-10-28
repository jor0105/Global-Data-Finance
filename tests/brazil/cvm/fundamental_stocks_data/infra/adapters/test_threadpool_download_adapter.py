import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.brazil.cvm.fundamental_stocks_data import DownloadResult
from src.brazil.cvm.fundamental_stocks_data.infra.adapters.threadpool_download_adapter import (
    SingleFileDownloader,
    ThreadPoolDownloadAdapter,
)
from src.brazil.cvm.fundamental_stocks_data.utils.retry_strategy import RetryStrategy


@pytest.mark.unit
class TestSingleFileDownloaderInit:
    def test_init_with_default_values(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)
        assert downloader.chunk_size == 8192
        assert downloader.timeout == 30
        assert downloader.max_retries == 3

    def test_init_with_custom_values(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(
            retry_strategy,
            chunk_size=16384,
            timeout=60,
            max_retries=5,
        )
        assert downloader.chunk_size == 16384
        assert downloader.timeout == 60
        assert downloader.max_retries == 5

    def test_retry_strategy_stored(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)
        assert downloader.retry_strategy is retry_strategy


@pytest.mark.unit
class TestSingleFileDownloaderGetFilename:
    def test_get_filename_normal_url(self):
        url = "https://example.com/path/to/document.zip"
        filename = SingleFileDownloader._get_filename(url)
        assert filename == "document.zip"

    def test_get_filename_with_query_params(self):
        url = "https://example.com/document.zip?param=value&other=123"
        filename = SingleFileDownloader._get_filename(url)
        assert filename == "document.zip"

    def test_get_filename_malformed_url(self):
        url = "not_a_url"
        filename = SingleFileDownloader._get_filename(url)
        assert filename == "not_a_url"

    def test_get_filename_empty_string(self):
        url = ""
        filename = SingleFileDownloader._get_filename(url)
        assert filename == "download"

    def test_get_filename_only_slash(self):
        url = "https://example.com/"
        filename = SingleFileDownloader._get_filename(url)
        assert filename == "download"


@pytest.mark.unit
class TestSingleFileDownloaderGetYear:
    def test_get_year_standard_format(self):
        url = "https://example.com/dre_2023.zip"
        year = SingleFileDownloader._get_year(url)
        assert year == "2023"

    def test_get_year_with_full_path(self):
        url = "https://cvm.gov.br/data/DRE_2024.zip"
        year = SingleFileDownloader._get_year(url)
        assert year == "2024"

    def test_get_year_multiple_underscores(self):
        url = "https://example.com/document_2022_final.zip"
        year = SingleFileDownloader._get_year(url)
        assert year == "final"

    def test_get_year_no_underscore(self):
        url = "https://example.com/document.zip"
        year = SingleFileDownloader._get_year(url)
        assert year == "https://example"

    def test_get_year_invalid_format(self):
        url = "invalid_url"
        year = SingleFileDownloader._get_year(url)
        assert year == "url"


@pytest.mark.unit
class TestSingleFileDownloaderSuccess:
    def test_download_success_first_attempt(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://example.com/document_2023.zip"
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"chunk1", b"chunk2"])

            with patch("requests.get", return_value=mock_response):
                success, error_msg = downloader.download(
                    url,
                    tmpdir,
                    doc_name="DRE",
                    year="2023",
                )

            assert success is True
            assert error_msg is None

    def test_download_creates_file(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://example.com/document.zip"
            mock_response = MagicMock()
            mock_response.iter_content = Mock(
                return_value=[b"content", b"data", b"here"]
            )

            with patch("requests.get", return_value=mock_response):
                downloader.download(
                    url,
                    tmpdir,
                    doc_name="DRE",
                    year="2023",
                )

            files = os.listdir(tmpdir)
            assert "document.zip" in files

    def test_download_writes_correct_content(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://example.com/test.zip"
            test_content = b"test_data_content"
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[test_content])

            with patch("requests.get", return_value=mock_response):
                downloader.download(
                    url,
                    tmpdir,
                    doc_name="TEST",
                    year="2023",
                )

            filepath = os.path.join(tmpdir, "test.zip")
            with open(filepath, "rb") as f:
                content = f.read()
            assert content == test_content

    def test_download_with_multiple_chunks(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, chunk_size=4096)

        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://example.com/large.zip"
            chunks = [b"chunk1", b"chunk2", b"chunk3", b"chunk4"]
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=chunks)

            with patch("requests.get", return_value=mock_response):
                downloader.download(
                    url,
                    tmpdir,
                    doc_name="LARGE",
                    year="2023",
                )

            filepath = os.path.join(tmpdir, "large.zip")
            with open(filepath, "rb") as f:
                content = f.read()
            assert content == b"chunk1chunk2chunk3chunk4"


@pytest.mark.unit
class TestSingleFileDownloaderHTTPErrors:
    def test_download_http_400_not_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=3)

        url = "https://example.com/document.zip"
        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 400

        with patch("requests.get", side_effect=http_error):
            success, error_msg = downloader.download(
                url,
                "/tmp",
                doc_name="DRE",
                year="2023",
            )

        assert success is False
        assert "HTTP 400" in error_msg

    def test_download_http_404_not_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=3)

        url = "https://example.com/notfound.zip"
        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 404

        with patch("requests.get", side_effect=http_error):
            success, error_msg = downloader.download(
                url,
                "/tmp",
                doc_name="DRE",
                year="2023",
            )

        assert success is False
        assert "HTTP 404" in error_msg

    def test_download_http_500_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        url = "https://example.com/document.zip"
        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 500

        with patch("requests.get", side_effect=http_error):
            with patch.object(downloader, "_apply_backoff"):
                success, error_msg = downloader.download(
                    url,
                    "/tmp",
                    doc_name="DRE",
                    year="2023",
                )

        assert success is False

    def test_download_http_503_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        url = "https://example.com/document.zip"
        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 503

        with patch("requests.get", side_effect=http_error):
            with patch.object(downloader, "_apply_backoff"):
                success, error_msg = downloader.download(
                    url,
                    "/tmp",
                    doc_name="DRE",
                    year="2023",
                )

        assert success is False


@pytest.mark.unit
class TestSingleFileDownloaderNetworkErrors:
    def test_download_connection_error_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        connection_error = requests.exceptions.ConnectionError("Connection refused")

        with patch("requests.get", side_effect=connection_error):
            with patch.object(downloader, "_apply_backoff"):
                success, error_msg = downloader.download(
                    "https://example.com/doc.zip",
                    "/tmp",
                    doc_name="DRE",
                    year="2023",
                )

        assert success is False

    def test_download_timeout_error_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        timeout_error = requests.exceptions.Timeout("Request timed out")

        with patch("requests.get", side_effect=timeout_error):
            with patch.object(downloader, "_apply_backoff"):
                success, error_msg = downloader.download(
                    "https://example.com/doc.zip",
                    "/tmp",
                    doc_name="BPARMS",
                    year="2024",
                )

        assert success is False

    def test_download_request_exception_generic(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        generic_error = requests.exceptions.RequestException("Generic error")

        with patch("requests.get", side_effect=generic_error):
            success, error_msg = downloader.download(
                "https://example.com/doc.zip",
                "/tmp",
                doc_name="DRE",
                year="2023",
            )

        assert success is False


@pytest.mark.unit
class TestSingleFileDownloaderIOErrors:
    def test_download_permission_denied(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            perm_error = PermissionError("Permission denied")

            with patch("requests.get", return_value=mock_response):
                with patch("builtins.open", side_effect=perm_error):
                    success, error_msg = downloader.download(
                        "https://example.com/doc.zip",
                        tmpdir,
                        doc_name="DRE",
                        year="2023",
                    )

            assert success is False
            assert "PermissionError" in error_msg

    def test_download_disk_full(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        disk_error = OSError("disk quota exceeded")

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                with patch("builtins.open", side_effect=disk_error):
                    success, error_msg = downloader.download(
                        "https://example.com/doc.zip",
                        tmpdir,
                        doc_name="DRE",
                        year="2023",
                    )

            assert success is False
            assert "DiskError" in error_msg

    def test_download_file_not_found_in_path(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_path = os.path.join(tmpdir, "nonexistent", "file.zip")
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                success, error_msg = downloader.download(
                    "https://example.com/doc.zip",
                    invalid_path,
                    doc_name="DRE",
                    year="2023",
                )

            assert success is False


@pytest.mark.unit
class TestSingleFileDownloaderRetryLogic:
    def test_download_succeeds_after_retry(self):
        retry_strategy = RetryStrategy(0.01, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            timeout_error = requests.exceptions.Timeout("Timeout")
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", side_effect=[timeout_error, mock_response]):
                with patch.object(downloader, "_apply_backoff"):
                    success, error_msg = downloader.download(
                        "https://example.com/doc.zip",
                        tmpdir,
                        doc_name="DRE",
                        year="2023",
                    )

            assert success is True
            assert error_msg is None

    def test_download_retries_on_connection_error(self):
        retry_strategy = RetryStrategy(0.01, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=3)

        connection_error = requests.exceptions.ConnectionError("Connection refused")
        attempts = [0]

        def side_effect(*args, **kwargs):
            attempts[0] += 1
            if attempts[0] < 3:
                raise connection_error
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"success"])
            return mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("requests.get", side_effect=side_effect):
                with patch.object(downloader, "_apply_backoff"):
                    success, error_msg = downloader.download(
                        "https://example.com/doc.zip",
                        tmpdir,
                        doc_name="DRE",
                        year="2023",
                    )

            assert success is True
            assert attempts[0] == 3

    def test_download_max_retries_exceeded(self):
        retry_strategy = RetryStrategy(0.01, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        timeout_error = requests.exceptions.Timeout("Timeout")

        with patch("requests.get", side_effect=timeout_error):
            with patch.object(downloader, "_apply_backoff"):
                success, error_msg = downloader.download(
                    "https://example.com/doc.zip",
                    "/tmp",
                    doc_name="DRE",
                    year="2023",
                )

        assert success is False


@pytest.mark.unit
class TestSingleFileDownloaderCleanup:
    def test_failed_file_cleanup(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.zip")
            Path(filepath).touch()

            assert os.path.exists(filepath)

            downloader._cleanup_failed_file(filepath)

            assert not os.path.exists(filepath)

    def test_cleanup_nonexistent_file(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        downloader._cleanup_failed_file("/nonexistent/path/file.zip")

    def test_cleanup_on_failed_download(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=1)

        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://example.com/doc.zip"
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            write_error = OSError("Write failed")

            with patch("requests.get", return_value=mock_response):
                with patch("builtins.open", side_effect=write_error):
                    downloader.download(
                        url,
                        tmpdir,
                        doc_name="DRE",
                        year="2023",
                    )

            files = os.listdir(tmpdir)
            assert len(files) == 0


@pytest.mark.unit
class TestSingleFileDownloaderFormatters:
    def test_format_io_error_disk_full(self):
        error = OSError("disk quota exceeded")
        formatted = SingleFileDownloader._format_io_error(error, "/path")
        assert "DiskError" in formatted
        assert "/path" in formatted

    def test_format_io_error_permission(self):
        error = PermissionError("Permission denied")
        formatted = SingleFileDownloader._format_io_error(error, "/restricted")
        assert "PermissionError" in formatted
        assert "/restricted" in formatted

    def test_format_io_error_generic(self):
        error = OSError("Generic OS error")
        formatted = SingleFileDownloader._format_io_error(error, "/path")
        assert "IOError" in formatted

    def test_format_final_error_none_exception(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        result = downloader._format_final_error(None, "DRE", "2023")
        assert "Unknown error" in result
        assert "DRE" in result
        assert "2023" in result

    def test_format_final_error_with_exception(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        error = requests.exceptions.Timeout("Timeout")
        result = downloader._format_final_error(error, "DRE", "2023")
        assert "Timeout" in result or "error" in result.lower()


@pytest.mark.unit
class TestThreadPoolDownloadAdapterInit:
    def test_init_with_default_values(self):
        adapter = ThreadPoolDownloadAdapter()
        assert adapter.max_workers == 8
        assert isinstance(adapter.file_downloader, SingleFileDownloader)
        assert isinstance(adapter.retry_strategy, RetryStrategy)

    def test_init_with_custom_values(self):
        adapter = ThreadPoolDownloadAdapter(
            max_workers=16,
            chunk_size=16384,
            timeout=60,
            max_retries=5,
            initial_backoff=2.0,
            max_backoff=120.0,
            backoff_multiplier=3.0,
        )
        assert adapter.max_workers == 16
        assert adapter.file_downloader.chunk_size == 16384
        assert adapter.file_downloader.timeout == 60
        assert adapter.file_downloader.max_retries == 5


@pytest.mark.unit
class TestThreadPoolDownloadAdapterPrepare:
    def test_prepare_tasks_single_doc(self):
        adapter = ThreadPoolDownloadAdapter()
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
        adapter = ThreadPoolDownloadAdapter()
        dict_zip = {
            "DRE": ["https://example.com/dre_2023.zip"],
            "ITR": ["https://example.com/itr_2023.zip"],
            "BPARMS": ["https://example.com/bparms_2023.zip"],
        }
        docs_paths = {
            "DRE": {2023: "/tmp/DRE/2023"},
            "ITR": {2023: "/tmp/ITR/2023"},
            "BPARMS": {2023: "/tmp/BPARMS/2023"},
        }

        tasks = adapter._prepare_download_tasks(dict_zip, docs_paths)

        assert len(tasks) == 3

    def test_prepare_tasks_empty_dict(self):
        adapter = ThreadPoolDownloadAdapter()
        dict_zip = {}
        docs_paths = {}

        tasks = adapter._prepare_download_tasks(dict_zip, docs_paths)

        assert len(tasks) == 0

    def test_prepare_tasks_extracts_year(self):
        adapter = ThreadPoolDownloadAdapter()
        dict_zip = {"DRE": ["https://example.com/dre_2024.zip"]}
        docs_paths = {"DRE": {2024: "/tmp/DRE/2024"}}

        tasks = adapter._prepare_download_tasks(dict_zip, docs_paths)

        url, doc_name, year, destination_path = tasks[0]
        assert year == "2024"
        assert doc_name == "DRE"
        assert destination_path == "/tmp/DRE/2024"


@pytest.mark.unit
class TestThreadPoolDownloadAdapterDownloadDocs:
    def test_download_docs_empty_dict(self):
        adapter = ThreadPoolDownloadAdapter()
        docs_paths = {}
        result = adapter.download_docs({}, docs_paths)

        assert isinstance(result, DownloadResult)
        assert result.success_count == 0
        assert result.error_count == 0

    def test_download_docs_all_success(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=2, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": [
                    "https://example.com/dre_2023.zip",
                    "https://example.com/dre_2022.zip",
                ]
            }
            docs_paths = {
                "DRE": {
                    2023: os.path.join(tmpdir, "DRE", "2023"),
                    2022: os.path.join(tmpdir, "DRE", "2022"),
                }
            }
            # Create directories
            os.makedirs(docs_paths["DRE"][2023], exist_ok=True)
            os.makedirs(docs_paths["DRE"][2022], exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 2
            assert result.error_count == 0

    def test_download_docs_partial_failure(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=2, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": [
                    "https://example.com/dre_2023.zip",
                    "https://example.com/dre_2022.zip",
                ]
            }
            docs_paths = {
                "DRE": {
                    2023: os.path.join(tmpdir, "DRE", "2023"),
                    2022: os.path.join(tmpdir, "DRE", "2022"),
                }
            }
            os.makedirs(docs_paths["DRE"][2023], exist_ok=True)
            os.makedirs(docs_paths["DRE"][2022], exist_ok=True)

            success_response = MagicMock()
            success_response.iter_content = Mock(return_value=[b"data"])
            error = requests.exceptions.ConnectionError("Failed")

            with patch("requests.get", side_effect=[success_response, error]):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 1
            assert result.error_count == 1

    def test_download_docs_all_failure(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=2, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": [
                    "https://example.com/dre_2023.zip",
                    "https://example.com/dre_2022.zip",
                ]
            }
            docs_paths = {
                "DRE": {
                    2023: os.path.join(tmpdir, "DRE", "2023"),
                    2022: os.path.join(tmpdir, "DRE", "2022"),
                }
            }
            os.makedirs(docs_paths["DRE"][2023], exist_ok=True)
            os.makedirs(docs_paths["DRE"][2022], exist_ok=True)

            error = requests.exceptions.ConnectionError("Failed")

            with patch("requests.get", side_effect=error):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 0
            assert result.error_count == 2

    def test_download_docs_multiple_documents(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=4, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": ["https://example.com/dre_2023.zip"],
                "ITR": ["https://example.com/itr_2023.zip"],
                "BPARMS": ["https://example.com/bparms_2023.zip"],
            }
            docs_paths = {
                "DRE": {2023: os.path.join(tmpdir, "DRE", "2023")},
                "ITR": {2023: os.path.join(tmpdir, "ITR", "2023")},
                "BPARMS": {2023: os.path.join(tmpdir, "BPARMS", "2023")},
            }
            for doc in docs_paths:
                for year_path in docs_paths[doc].values():
                    os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 3
            assert result.error_count == 0

    def test_download_docs_with_many_files(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=4, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            years = list(range(2010, 2025))
            dict_zip = {
                "DRE": [f"https://example.com/dre_{year}.zip" for year in years]
            }
            docs_paths = {
                "DRE": {year: os.path.join(tmpdir, "DRE", str(year)) for year in years}
            }
            for year_path in docs_paths["DRE"].values():
                os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 15
            assert result.error_count == 0

    def test_download_docs_result_accumulation(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=2, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": ["https://example.com/dre_2023.zip"],
                "ITR": ["https://example.com/itr_2023.zip"],
            }
            docs_paths = {
                "DRE": {2023: os.path.join(tmpdir, "DRE", "2023")},
                "ITR": {2023: os.path.join(tmpdir, "ITR", "2023")},
            }
            for doc in docs_paths:
                for year_path in docs_paths[doc].values():
                    os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert len(result.successful_downloads) == 2
            assert "DRE_2023" in result.successful_downloads
            assert "ITR_2023" in result.successful_downloads


@pytest.mark.unit
class TestThreadPoolDownloadAdapterParallelism:
    def test_download_uses_thread_pool_executor(self):
        _ = ThreadPoolDownloadAdapter(max_workers=4)

        with tempfile.TemporaryDirectory():
            _ = {
                "DRE": [
                    "https://example.com/dre_2023.zip",
                    "https://example.com/dre_2022.zip",
                ]
            }
            _ = {
                "DRE": {
                    2023: "/tmp/DRE/2023",
                    2022: "/tmp/DRE/2022",
                }
            }

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
                    mock_executor.return_value.__enter__ = Mock(
                        return_value=mock_executor.return_value
                    )
                    mock_executor.return_value.__exit__ = Mock(return_value=False)
                    mock_executor.return_value.submit = Mock(return_value=MagicMock())
                    mock_executor.return_value.__enter__.return_value.submit = Mock(
                        return_value=MagicMock()
                    )

    def test_parallel_download_different_worker_counts(self):
        for worker_count in [1, 2, 4, 8]:
            adapter = ThreadPoolDownloadAdapter(max_workers=worker_count)
            assert adapter.max_workers == worker_count


@pytest.mark.unit
class TestThreadPoolDownloadAdapterExceptionHandling:
    def test_download_docs_http_errors(self):
        adapter = ThreadPoolDownloadAdapter(max_workers=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": ["https://example.com/dre_2023.zip"],
            }
            docs_paths = {"DRE": {2023: os.path.join(tmpdir, "DRE", "2023")}}
            os.makedirs(docs_paths["DRE"][2023], exist_ok=True)

            http_error = requests.exceptions.HTTPError()
            http_error.response = MagicMock()
            http_error.response.status_code = 404

            with patch("requests.get", side_effect=http_error):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.error_count == 1
            assert "DRE_2023" in result.failed_downloads

    def test_download_docs_network_errors(self):
        adapter = ThreadPoolDownloadAdapter(max_workers=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "BPARMS": ["https://example.com/bparms_2023.zip"],
            }
            docs_paths = {"BPARMS": {2023: os.path.join(tmpdir, "BPARMS", "2023")}}
            os.makedirs(docs_paths["BPARMS"][2023], exist_ok=True)

            network_error = requests.exceptions.ConnectionError("Connection failed")

            with patch("requests.get", side_effect=network_error):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.error_count == 1

    def test_download_docs_timeout_errors(self):
        adapter = ThreadPoolDownloadAdapter(max_workers=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "ITR": ["https://example.com/itr_2023.zip"],
            }
            docs_paths = {"ITR": {2023: os.path.join(tmpdir, "ITR", "2023")}}
            os.makedirs(docs_paths["ITR"][2023], exist_ok=True)

            timeout_error = requests.exceptions.Timeout("Request timed out")

            with patch("requests.get", side_effect=timeout_error):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.error_count == 1

    def test_download_docs_unexpected_exception(self):
        adapter = ThreadPoolDownloadAdapter(max_workers=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": ["https://example.com/dre_2023.zip"],
            }
            docs_paths = {"DRE": {2023: os.path.join(tmpdir, "DRE", "2023")}}
            os.makedirs(docs_paths["DRE"][2023], exist_ok=True)

            with patch("requests.get", side_effect=ValueError("Unexpected error")):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.error_count == 1

    def test_download_docs_mixed_errors_and_success(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=4, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": [
                    "https://example.com/dre_2023.zip",
                    "https://example.com/dre_2022.zip",
                    "https://example.com/dre_2021.zip",
                    "https://example.com/dre_2020.zip",
                ],
            }
            docs_paths = {
                "DRE": {
                    2023: os.path.join(tmpdir, "DRE", "2023"),
                    2022: os.path.join(tmpdir, "DRE", "2022"),
                    2021: os.path.join(tmpdir, "DRE", "2021"),
                    2020: os.path.join(tmpdir, "DRE", "2020"),
                }
            }
            for year_path in docs_paths["DRE"].values():
                os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])
            error = requests.exceptions.ConnectionError("Failed")

            responses = [mock_response, error, mock_response, error]

            with patch("requests.get", side_effect=responses):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 2
            assert result.error_count == 2


@pytest.mark.unit
class TestThreadPoolDownloadAdapterProgressBar:
    def test_progress_bar_initialization(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(file_extractor=mock_extractor)

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {"DRE": ["https://example.com/dre_2023.zip"]}
            docs_paths = {"DRE": {2023: os.path.join(tmpdir, "DRE", "2023")}}
            os.makedirs(docs_paths["DRE"][2023], exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                with patch(
                    "src.brazil.cvm.fundamental_stocks_data.infra.adapters.threadpool_download_adapter.SimpleProgressBar"
                ) as mock_progress:
                    adapter.download_docs(dict_zip, docs_paths)
                    mock_progress.assert_called_once()

    def test_progress_bar_update_called(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=1, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": [
                    "https://example.com/dre_2023.zip",
                    "https://example.com/dre_2022.zip",
                ]
            }
            docs_paths = {
                "DRE": {
                    2023: os.path.join(tmpdir, "DRE", "2023"),
                    2022: os.path.join(tmpdir, "DRE", "2022"),
                }
            }
            for year_path in docs_paths["DRE"].values():
                os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                mock_progress = MagicMock()
                with patch(
                    "src.brazil.cvm.fundamental_stocks_data.infra.adapters.threadpool_download_adapter.SimpleProgressBar",
                    return_value=mock_progress,
                ):
                    adapter.download_docs(dict_zip, docs_paths)
                    assert mock_progress.update.call_count == 2


@pytest.mark.unit
class TestThreadPoolDownloadAdapterIntegration:
    def test_full_download_workflow_success(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=2, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": [
                    "https://example.com/dre_2023.zip",
                    "https://example.com/dre_2022.zip",
                ],
                "ITR": ["https://example.com/itr_2023.zip"],
            }
            docs_paths = {
                "DRE": {
                    2023: os.path.join(tmpdir, "DRE", "2023"),
                    2022: os.path.join(tmpdir, "DRE", "2022"),
                },
                "ITR": {2023: os.path.join(tmpdir, "ITR", "2023")},
            }
            for doc in docs_paths:
                for year_path in docs_paths[doc].values():
                    os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"test_data"])

            with patch("requests.get", return_value=mock_response):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 3
            assert result.error_count == 0
            assert len(result.successful_downloads) == 3

    def test_full_download_workflow_with_retries(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=1, max_retries=2, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {"DRE": ["https://example.com/dre_2023.zip"]}
            docs_paths = {"DRE": {2023: os.path.join(tmpdir, "DRE", "2023")}}
            os.makedirs(docs_paths["DRE"][2023], exist_ok=True)

            timeout_error = requests.exceptions.Timeout("Timeout")
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", side_effect=[timeout_error, mock_response]):
                with patch.object(adapter.file_downloader, "_apply_backoff"):
                    result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 1

    def test_large_batch_download(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=4, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            years_dre = list(range(2010, 2025))
            years_itr = list(range(2015, 2025))
            dict_zip = {
                "DRE": [f"https://example.com/dre_{year}.zip" for year in years_dre],
                "ITR": [f"https://example.com/itr_{year}.zip" for year in years_itr],
            }
            docs_paths = {
                "DRE": {
                    year: os.path.join(tmpdir, "DRE", str(year)) for year in years_dre
                },
                "ITR": {
                    year: os.path.join(tmpdir, "ITR", str(year)) for year in years_itr
                },
            }
            for doc in docs_paths:
                for year_path in docs_paths[doc].values():
                    os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 25
            assert result.error_count == 0

    def test_result_accumulation_over_time(self):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = Mock(return_value=None)

        adapter = ThreadPoolDownloadAdapter(
            max_workers=1, file_extractor=mock_extractor
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dict_zip = {
                "DRE": ["https://example.com/dre_2023.zip"],
                "ITR": ["https://example.com/itr_2023.zip"],
                "BPARMS": ["https://example.com/bparms_2023.zip"],
            }
            docs_paths = {
                "DRE": {2023: os.path.join(tmpdir, "DRE", "2023")},
                "ITR": {2023: os.path.join(tmpdir, "ITR", "2023")},
                "BPARMS": {2023: os.path.join(tmpdir, "BPARMS", "2023")},
            }
            for doc in docs_paths:
                for year_path in docs_paths[doc].values():
                    os.makedirs(year_path, exist_ok=True)

            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                result = adapter.download_docs(dict_zip, docs_paths)

            assert result.success_count == 3
            assert result.error_count == 0
            assert len(result.failed_downloads) == 0


@pytest.mark.unit
class TestApplyBackoff:
    def test_apply_backoff_calculation(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        with patch("time.sleep") as mock_sleep:
            downloader._apply_backoff(1, "DRE", "2023")
            mock_sleep.assert_called_once()

    def test_apply_backoff_exponential_growth(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        _ = SingleFileDownloader(retry_strategy)

        backoff_1 = retry_strategy.calculate_backoff(0)
        backoff_2 = retry_strategy.calculate_backoff(1)
        backoff_3 = retry_strategy.calculate_backoff(2)

        assert backoff_1 < backoff_2 < backoff_3


@pytest.mark.unit
class TestStreamDownload:
    def test_stream_download_with_raise_for_status(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.zip")
            mock_response = MagicMock()
            mock_response.iter_content = Mock(return_value=[b"data"])

            with patch("requests.get", return_value=mock_response):
                downloader._stream_download("https://example.com/file.zip", filepath)
                mock_response.raise_for_status.assert_called_once()

    def test_stream_download_http_error(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                downloader._stream_download(
                    "https://example.com/file.zip", "/tmp/file.zip"
                )


@pytest.mark.unit
class TestShouldRetryMethods:
    def test_should_retry_http_400_client_error(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy)

        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 400

        should_retry = downloader._should_retry_http(http_error, 0, "DRE", "2023")
        assert should_retry is False

    def test_should_retry_http_500_server_error(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=3)

        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 500

        should_retry = downloader._should_retry_http(http_error, 0, "DRE", "2023")
        assert should_retry is True

    def test_should_retry_http_max_retries_exceeded(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        http_error = requests.exceptions.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 502

        should_retry = downloader._should_retry_http(http_error, 2, "DRE", "2023")
        assert should_retry is False

    def test_should_retry_request_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=3)

        error = requests.exceptions.Timeout("Timeout")

        should_retry = downloader._should_retry_request(error, 0, "DRE", "2023")
        assert should_retry is True

    def test_should_retry_request_non_retryable(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=3)

        error = ValueError("Invalid value")

        should_retry = downloader._should_retry_request(error, 0, "DRE", "2023")
        assert should_retry is False

    def test_should_retry_io_first_attempt(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=3)

        error = OSError("IO error")

        should_retry = downloader._should_retry_io(error, 0, "DRE", "2023")
        assert should_retry is True

    def test_should_retry_io_max_retries(self):
        retry_strategy = RetryStrategy(1.0, 60.0, 2.0)
        downloader = SingleFileDownloader(retry_strategy, max_retries=2)

        error = OSError("IO error")

        should_retry = downloader._should_retry_io(error, 2, "DRE", "2023")
        assert should_retry is False
