"""Tests for ExtractHistoricalQuotesUseCase."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    ExtractHistoricalQuotesUseCase,
)
from src.brazil.dados_b3.historical_quotes.domain.entities import DocsToExtractor


class TestExtractHistoricalQuotesUseCaseInitialization:
    """Test suite for ExtractHistoricalQuotesUseCase initialization."""

    def test_initializes_with_dependencies(self):
        """Test that use case initializes with required dependencies."""
        # Act
        use_case = ExtractHistoricalQuotesUseCase()

        # Assert
        assert use_case.zip_reader is not None
        assert use_case.parser is not None
        assert use_case.data_writer is not None

    def test_initializes_zip_reader(self):
        """Test that zip_reader is initialized."""
        # Act
        use_case = ExtractHistoricalQuotesUseCase()

        # Assert
        assert hasattr(use_case, "zip_reader")

    def test_initializes_parser(self):
        """Test that parser is initialized."""
        # Act
        use_case = ExtractHistoricalQuotesUseCase()

        # Assert
        assert hasattr(use_case, "parser")

    def test_initializes_data_writer(self):
        """Test that data_writer is initialized."""
        # Act
        use_case = ExtractHistoricalQuotesUseCase()

        # Assert
        assert hasattr(use_case, "data_writer")


class TestExecuteAsyncMethod:
    """Test suite for execute async method."""

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_returns_dict(self, mock_assets_service, mock_factory):
        """Test that execute returns a dictionary."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {
            "total_files": 1,
            "success_count": 1,
            "error_count": 0,
            "total_records": 100,
            "errors": {},
            "output_file": "/path/output.parquet",
        }
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010", "020"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        result = await use_case.execute(docs)

        # Assert
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_calls_extraction_service_factory(
        self, mock_assets_service, mock_factory
    ):
        """Test that execute calls ExtractionServiceFactory."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {
            "total_files": 0,
            "success_count": 0,
            "error_count": 0,
            "total_records": 0,
            "errors": {},
            "output_file": "",
        }
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        await use_case.execute(docs, processing_mode="fast")

        # Assert
        mock_factory.create.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_calls_get_tpmerc_codes(
        self, mock_assets_service, mock_factory
    ):
        """Test that execute calls get_tpmerc_codes_for_assets."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010", "020"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações", "etf"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        await use_case.execute(docs)

        # Assert
        mock_assets_service.get_tpmerc_codes_for_assets.assert_called_once_with(
            {"ações", "etf"}
        )

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_returns_empty_result_for_no_files(
        self, mock_assets_service, mock_factory
    ):
        """Test that execute returns empty result when no files to download."""
        # Arrange
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download=set(),  # Empty set
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        result = await use_case.execute(docs)

        # Assert
        assert result["total_files"] == 0
        assert result["success_count"] == 0
        assert result["error_count"] == 0
        assert result["total_records"] == 0
        assert result["errors"] == {}
        assert result["output_file"] == ""

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_with_custom_output_filename(
        self, mock_assets_service, mock_factory
    ):
        """Test execute with custom output filename."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {
            "total_files": 1,
            "success_count": 1,
            "error_count": 0,
            "total_records": 100,
            "errors": {},
            "output_file": "/path/to/output/custom.parquet",
        }
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        await use_case.execute(docs, output_filename="custom.parquet")

        # Assert
        # Check that extract_from_zip_files was called with the right output path
        call_args = mock_service.extract_from_zip_files.call_args
        assert "output_path" in call_args.kwargs
        assert (
            call_args.kwargs["output_path"]
            == Path("/path/to/output") / "custom.parquet"
        )

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_with_slow_processing_mode(
        self, mock_assets_service, mock_factory
    ):
        """Test execute with slow processing mode."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        await use_case.execute(docs, processing_mode="slow")

        # Assert
        call_args = mock_factory.create.call_args
        assert call_args.kwargs["processing_mode"] == "slow"


class TestExecuteSyncMethod:
    """Test suite for execute_sync method."""

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    def test_execute_sync_returns_dict(self, mock_assets_service, mock_factory):
        """Test that execute_sync returns a dictionary."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {
            "total_files": 1,
            "success_count": 1,
            "error_count": 0,
            "total_records": 100,
            "errors": {},
            "output_file": "/path/output.parquet",
        }
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        result = use_case.execute_sync(docs)

        # Assert
        assert isinstance(result, dict)

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    def test_execute_sync_with_all_parameters(self, mock_assets_service, mock_factory):
        """Test execute_sync with all parameters."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        result = use_case.execute_sync(
            docs, processing_mode="slow", output_filename="custom.parquet"
        )

        # Assert
        assert isinstance(result, dict)

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    def test_execute_sync_handles_empty_files(self, mock_assets_service, mock_factory):
        """Test execute_sync handles empty files set."""
        # Arrange
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download=set(),
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        result = use_case.execute_sync(docs)

        # Assert
        assert result["total_files"] == 0
        assert result["output_file"] == ""


class TestOutputPathGeneration:
    """Test suite for output path generation."""

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_generates_correct_output_path(
        self, mock_assets_service, mock_factory
    ):
        """Test that correct output path is generated."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        await use_case.execute(docs, output_filename="test.parquet")

        # Assert
        call_args = mock_service.extract_from_zip_files.call_args
        expected_path = Path("/path/to/output") / "test.parquet"
        assert call_args.kwargs["output_path"] == expected_path

    @pytest.mark.asyncio
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_uses_default_filename(self, mock_assets_service, mock_factory):
        """Test that default filename is used when not specified."""
        # Arrange
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCase()

        # Act
        await use_case.execute(docs)

        # Assert
        call_args = mock_service.extract_from_zip_files.call_args
        expected_path = Path("/path/to/output") / "cotahist_extracted.parquet"
        assert call_args.kwargs["output_path"] == expected_path
