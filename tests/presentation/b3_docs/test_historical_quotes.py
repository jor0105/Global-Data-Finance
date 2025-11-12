"""Tests for HistoricalQuotes presentation layer."""

from unittest.mock import Mock, patch

from src.presentation.b3_docs import HistoricalQuotes


class TestHistoricalQuotes:
    """Test suite for HistoricalQuotes class."""

    def test_initialization(self):
        """Test that HistoricalQuotes can be initialized."""
        b3 = HistoricalQuotes()
        assert b3 is not None
        assert repr(b3) == "HistoricalQuotes()"

    def test_get_available_assets(self):
        """Test retrieving available asset classes."""
        b3 = HistoricalQuotes()
        assets = b3.get_available_assets()

        assert isinstance(assets, list)
        assert len(assets) > 0
        assert "ações" in assets
        assert "etf" in assets
        assert "opções" in assets

    def test_get_available_years(self):
        """Test retrieving available year range."""
        b3 = HistoricalQuotes()
        years = b3.get_available_years()

        assert isinstance(years, dict)
        assert "minimal_year" in years
        assert "current_year" in years
        assert years["minimal_year"] == 1986
        assert years["current_year"] >= 2025

    @patch("src.presentation.b3_docs.historical_quotes.CreateDocsToExtractUseCase")
    @patch("src.presentation.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCase")
    def test_extract_with_all_parameters(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        """Test extract method with all parameters specified."""
        # Setup mocks
        mock_docs = Mock()
        mock_docs.set_documents_to_download = {"file1.zip", "file2.zip"}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            "success": True,
            "message": "Success",
            "total_files": 2,
            "success_count": 2,
            "error_count": 0,
            "total_records": 1000,
            "output_file": "/output/test.parquet",
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute_sync.return_value = mock_result
        mock_extract_use_case.return_value = mock_extract_instance

        # Execute
        b3 = HistoricalQuotes()
        result = b3.extract(
            path_of_docs="/data/cotahist",
            destination_path="/output",
            assets_list=["ações", "etf"],
            initial_year=2020,
            last_year=2023,
            output_filename="test.parquet",
            processing_mode="fast",
        )

        # Assertions
        assert result == mock_result
        assert result["success"] is True
        assert result["total_records"] == 1000

    @patch("src.presentation.b3_docs.historical_quotes.CreateDocsToExtractUseCase")
    @patch("src.presentation.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCase")
    def test_extract_with_minimal_parameters(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        """Test extract method with only required parameters."""
        # Setup mocks
        mock_docs = Mock()
        mock_docs.set_documents_to_download = {"file1.zip"}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            "success": True,
            "message": "Success",
            "total_files": 1,
            "success_count": 1,
            "error_count": 0,
            "total_records": 500,
            "output_file": "/data/cotahist/cotahist_extracted.parquet",
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute_sync.return_value = mock_result
        mock_extract_use_case.return_value = mock_extract_instance

        # Execute
        b3 = HistoricalQuotes()
        result = b3.extract(
            path_of_docs="/data/cotahist", assets_list=["ações"], initial_year=2023
        )

        # Assertions
        assert result["success"] is True
        mock_create_docs_use_case.assert_called_once()

    @patch("src.presentation.b3_docs.historical_quotes.CreateDocsToExtractUseCase")
    @patch("src.presentation.b3_docs.historical_quotes.ExtractHistoricalQuotesUseCase")
    def test_extract_with_errors(
        self, mock_extract_use_case, mock_create_docs_use_case
    ):
        """Test extract method when errors occur."""
        # Setup mocks
        mock_docs = Mock()
        mock_docs.set_documents_to_download = {"file1.zip", "file2.zip"}
        mock_create_docs_use_case.return_value.execute.return_value = mock_docs

        mock_result = {
            "success": False,
            "message": "Some errors occurred",
            "total_files": 2,
            "success_count": 1,
            "error_count": 1,
            "total_records": 500,
            "output_file": "/output/test.parquet",
            "errors": ["Error processing file2.zip"],
        }
        mock_extract_instance = Mock()
        mock_extract_instance.execute_sync.return_value = mock_result
        mock_extract_use_case.return_value = mock_extract_instance

        # Execute
        b3 = HistoricalQuotes()
        result = b3.extract(
            path_of_docs="/data/cotahist", assets_list=["ações"], initial_year=2023
        )

        # Assertions
        assert result["success"] is False
        assert result["error_count"] == 1
        assert "errors" in result
