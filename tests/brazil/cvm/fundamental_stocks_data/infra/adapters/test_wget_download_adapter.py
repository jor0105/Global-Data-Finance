from unittest.mock import MagicMock, patch

from src.brazil.cvm.fundamental_stocks_data import (
    DownloadDocsCVMRepository,
    DownloadResult,
    WgetDownloadAdapter,
    WgetLibraryError,
    WgetValueError,
)


class TestWgetDownloadAdapterInit:
    def test_init_creates_instance(self):
        adapter = WgetDownloadAdapter()
        assert isinstance(adapter, WgetDownloadAdapter)

    def test_adapter_implements_repository_interface(self):
        adapter = WgetDownloadAdapter()
        assert isinstance(adapter, DownloadDocsCVMRepository)

    def test_adapter_has_download_docs_method(self):
        adapter = WgetDownloadAdapter()
        assert hasattr(adapter, "download_docs")
        assert callable(adapter.download_docs)

    def test_init_with_custom_retry_parameters(self):
        adapter = WgetDownloadAdapter(
            max_retries=5,
            initial_backoff=2.0,
            max_backoff=120.0,
            backoff_multiplier=3.0,
        )
        assert adapter.max_retries == 5


class TestWgetDownloadAdapterSuccessfulDownloads:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_single_document_single_year(self, mock_wget, mock_progress):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = MagicMock(return_value=None)

        adapter = WgetDownloadAdapter(file_extractor=mock_extractor)
        mock_progress.return_value = MagicMock()

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        docs_paths = {"DRE": {2020: "/path/to/save/DRE/2020"}}

        result = adapter.download_docs(dict_zip, docs_paths)

        assert isinstance(result, DownloadResult)
        assert result.success_count == 1
        assert result.error_count == 0
        mock_wget.assert_called_once()

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_single_document_multiple_years(self, mock_wget, mock_progress):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = MagicMock(return_value=None)

        adapter = WgetDownloadAdapter(file_extractor=mock_extractor)
        mock_progress.return_value = MagicMock()

        dict_zip = {
            "DRE": [
                "https://example.com/DRE_2020.zip",
                "https://example.com/DRE_2021.zip",
                "https://example.com/DRE_2022.zip",
            ]
        }
        docs_paths = {
            "DRE": {
                2020: "/path/to/save/DRE/2020",
                2021: "/path/to/save/DRE/2021",
                2022: "/path/to/save/DRE/2022",
            }
        }

        result = adapter.download_docs(dict_zip, docs_paths)

        assert isinstance(result, DownloadResult)
        assert result.success_count == 3
        assert result.error_count == 0
        assert mock_wget.call_count == 3

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_multiple_documents_single_year(self, mock_wget, mock_progress):
        # Create a mock extractor that does nothing (no extraction)
        mock_extractor = MagicMock()
        mock_extractor.extract = MagicMock(return_value=None)

        adapter = WgetDownloadAdapter(file_extractor=mock_extractor)
        mock_progress.return_value = MagicMock()

        dict_zip = {
            "DRE": ["https://example.com/DRE_2020.zip"],
            "ITR": ["https://example.com/ITR_2020.zip"],
            "FRE": ["https://example.com/FRE_2020.zip"],
        }
        docs_paths = {
            "DRE": {2020: "/path/to/save/DRE/2020"},
            "ITR": {2020: "/path/to/save/ITR/2020"},
            "FRE": {2020: "/path/to/save/FRE/2020"},
        }

        result = adapter.download_docs(dict_zip, docs_paths)

        assert isinstance(result, DownloadResult)
        assert result.success_count == 3
        assert result.error_count == 0
        assert mock_wget.call_count == 3


class TestWgetDownloadAdapterEmptyDownloads:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    def test_download_empty_dict(self, mock_progress):
        adapter = WgetDownloadAdapter()
        mock_progress.return_value = MagicMock()

        dict_zip = {}
        docs_paths = {}

        result = adapter.download_docs(dict_zip, docs_paths)

        assert isinstance(result, DownloadResult)
        assert result.success_count == 0
        assert result.error_count == 0


class TestWgetDownloadAdapterFailedDownloads:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_with_generic_exception(self, mock_wget, mock_progress):
        adapter = WgetDownloadAdapter()
        mock_progress.return_value = MagicMock()
        mock_wget.side_effect = Exception("wget download failed")

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        docs_paths = {"DRE": {2020: "/path/to/save/DRE/2020"}}

        result = adapter.download_docs(dict_zip, docs_paths)

        assert isinstance(result, DownloadResult)
        assert result.error_count > 0

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_with_wget_value_error(self, mock_wget, mock_progress):
        adapter = WgetDownloadAdapter()
        mock_progress.return_value = MagicMock()
        mock_wget.side_effect = WgetValueError("Invalid URL")

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        docs_paths = {"DRE": {2020: "/path/to/save/DRE/2020"}}

        result = adapter.download_docs(dict_zip, docs_paths)

        assert result.error_count == 1
        assert "DRE_2020" in result.failed_downloads

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_with_wget_library_error(self, mock_wget, mock_progress):
        adapter = WgetDownloadAdapter()
        mock_progress.return_value = MagicMock()
        mock_wget.side_effect = WgetLibraryError("wget error")

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        docs_paths = {"DRE": {2020: "/path/to/save/DRE/2020"}}

        result = adapter.download_docs(dict_zip, docs_paths)

        assert result.error_count > 0

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_with_permission_error(self, mock_wget, mock_progress):
        adapter = WgetDownloadAdapter()
        mock_progress.return_value = MagicMock()
        mock_wget.side_effect = PermissionError("Permission denied")

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        docs_paths = {"DRE": {2020: "/path/to/save/DRE/2020"}}

        result = adapter.download_docs(dict_zip, docs_paths)

        assert result.error_count > 0
        assert "DRE_2020" in result.failed_downloads

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.SimpleProgressBar"
    )
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_with_disk_full_error(self, mock_wget, mock_progress):
        adapter = WgetDownloadAdapter()
        mock_progress.return_value = MagicMock()
        mock_wget.side_effect = OSError("No space left on device")

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        docs_paths = {"DRE": {2020: "/path/to/save/DRE/2020"}}

        result = adapter.download_docs(dict_zip, docs_paths)

        assert result.error_count == 1
        assert "DRE_2020" in result.failed_downloads
