"""Tests for WgetDownloadAdapter infrastructure component."""

from unittest.mock import patch

from src.brasil.dados_cvm.dados_fundamentalistas_ações.application.interfaces import (
    DownloadDocsCVMRepository,
)
from src.brasil.dados_cvm.dados_fundamentalistas_ações.domain import DownloadResult
from src.brasil.dados_cvm.dados_fundamentalistas_ações.infra.adapters.wget_download_adapter import (
    WgetDownloadAdapter,
)


class TestWgetDownloadAdapterInit:
    """Tests for WgetDownloadAdapter initialization."""

    def test_init_creates_instance(self):
        """Should create an instance of the adapter."""
        adapter = WgetDownloadAdapter()
        assert isinstance(adapter, WgetDownloadAdapter)

    def test_adapter_implements_repository_interface(self):
        """Should implement the DownloadDocsCVMRepository interface."""
        adapter = WgetDownloadAdapter()
        assert isinstance(adapter, DownloadDocsCVMRepository)

    def test_adapter_has_download_docs_method(self):
        """Should have the download_docs method."""
        adapter = WgetDownloadAdapter()
        assert hasattr(adapter, "download_docs")
        assert callable(adapter.download_docs)


class TestWgetDownloadAdapterSuccessfulDownloads:
    """Tests for successful download scenarios."""

    @patch(
        "src.brasil.dados_cvm.dados_fundamentalistas_ações.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_single_document_single_year(self, mock_wget):
        """Should successfully download a single document and year."""
        adapter = WgetDownloadAdapter()

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        your_path = "/path/to/save"

        result = adapter.download_docs(your_path, dict_zip)

        assert isinstance(result, DownloadResult)
        mock_wget.assert_called_once_with(
            "https://example.com/DRE_2020.zip", out=your_path
        )

    @patch(
        "src.brasil.dados_cvm.dados_fundamentalistas_ações.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_single_document_multiple_years(self, mock_wget):
        """Should successfully download a single document with multiple years."""
        adapter = WgetDownloadAdapter()

        dict_zip = {
            "DRE": [
                "https://example.com/DRE_2020.zip",
                "https://example.com/DRE_2021.zip",
                "https://example.com/DRE_2022.zip",
            ]
        }
        your_path = "/path/to/save"

        result = adapter.download_docs(your_path, dict_zip)

        assert isinstance(result, DownloadResult)
        assert mock_wget.call_count == 3

    @patch(
        "src.brasil.dados_cvm.dados_fundamentalistas_ações.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_multiple_documents_single_year(self, mock_wget):
        """Should successfully download multiple documents for a single year."""
        adapter = WgetDownloadAdapter()

        dict_zip = {
            "DRE": ["https://example.com/DRE_2020.zip"],
            "ITR": ["https://example.com/ITR_2020.zip"],
            "FRE": ["https://example.com/FRE_2020.zip"],
        }
        your_path = "/path/to/save"

        result = adapter.download_docs(your_path, dict_zip)

        assert isinstance(result, DownloadResult)
        assert mock_wget.call_count == 3


class TestWgetDownloadAdapterFailedDownloads:
    """Tests for failed download scenarios."""

    @patch(
        "src.brasil.dados_cvm.dados_fundamentalistas_ações.infra.adapters.wget_download_adapter.wget.download"
    )
    def test_download_with_wget_error(self, mock_wget):
        """Should handle wget download errors gracefully."""
        adapter = WgetDownloadAdapter()

        dict_zip = {"DRE": ["https://example.com/DRE_2020.zip"]}
        your_path = "/path/to/save"

        mock_wget.side_effect = Exception("wget download failed")

        result = adapter.download_docs(your_path, dict_zip)

        assert isinstance(result, DownloadResult)
        assert result.has_errors
        assert result.error_count > 0
