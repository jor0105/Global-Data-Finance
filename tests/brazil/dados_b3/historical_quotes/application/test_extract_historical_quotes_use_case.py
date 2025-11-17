from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from datafinc.brazil.dados_b3.historical_quotes.application.use_cases import (
    ExtractHistoricalQuotesUseCaseB3,
)
from datafinc.brazil.dados_b3.historical_quotes.domain import DocsToExtractorB3


class TestExtractHistoricalQuotesUseCaseInitialization:
    def test_initializes_with_dependencies(self):
        use_case = ExtractHistoricalQuotesUseCaseB3()
        assert use_case.zip_reader is not None
        assert use_case.parser is not None
        assert use_case.data_writer is not None

    def test_initializes_zip_reader(self):
        use_case = ExtractHistoricalQuotesUseCaseB3()
        assert hasattr(use_case, "zip_reader")

    def test_initializes_parser(self):
        use_case = ExtractHistoricalQuotesUseCaseB3()
        assert hasattr(use_case, "parser")

    def test_initializes_data_writer(self):
        use_case = ExtractHistoricalQuotesUseCaseB3()
        assert hasattr(use_case, "data_writer")


class TestExecuteAsyncMethod:
    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_returns_dict(self, mock_assets_service, mock_factory):
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

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        result = await use_case.execute(docs)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_calls_extraction_service_factory(
        self, mock_assets_service, mock_factory
    ):
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

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        await use_case.execute(docs, processing_mode="fast")
        mock_factory.create.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_calls_get_tpmerc_codes(
        self, mock_assets_service, mock_factory
    ):
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010", "020"}

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações", "etf"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        await use_case.execute(docs)
        mock_assets_service.get_tpmerc_codes_for_assets.assert_called_once_with(
            {"ações", "etf"}
        )

    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_returns_empty_result_for_no_files(
        self, mock_assets_service, mock_factory
    ):
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download=set(),
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        result = await use_case.execute(docs)
        assert result["total_files"] == 0
        assert result["success_count"] == 0
        assert result["error_count"] == 0
        assert result["total_records"] == 0
        assert result["errors"] == {}
        assert result["output_file"] == ""

    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_with_custom_output_filename(
        self, mock_assets_service, mock_factory
    ):
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

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        await use_case.execute(docs, output_filename="custom.parquet")
        call_args = mock_service.extract_from_zip_files.call_args
        assert "output_path" in call_args.kwargs
        assert (
            call_args.kwargs["output_path"]
            == Path("/path/to/output") / "custom.parquet"
        )

    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_execute_with_slow_processing_mode(
        self, mock_assets_service, mock_factory
    ):
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        await use_case.execute(docs, processing_mode="slow")
        call_args = mock_factory.create.call_args
        assert call_args.kwargs["processing_mode"] == "slow"


class TestExecuteSyncMethod:
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    def test_execute_sync_returns_dict(self, mock_assets_service, mock_factory):
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

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        result = use_case.execute_sync(docs)
        assert isinstance(result, dict)

    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    def test_execute_sync_with_all_parameters(self, mock_assets_service, mock_factory):
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        result = use_case.execute_sync(
            docs, processing_mode="slow", output_filename="custom.parquet"
        )
        assert isinstance(result, dict)

    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    def test_execute_sync_handles_empty_files(self, mock_assets_service, mock_factory):
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download=set(),
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        result = use_case.execute_sync(docs)
        assert result["total_files"] == 0
        assert result["output_file"] == ""


class TestOutputPathGeneration:
    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_generates_correct_output_path(
        self, mock_assets_service, mock_factory
    ):
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        await use_case.execute(docs, output_filename="test.parquet")
        call_args = mock_service.extract_from_zip_files.call_args
        expected_path = Path("/path/to/output") / "test.parquet"
        assert call_args.kwargs["output_path"] == expected_path

    @pytest.mark.asyncio
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.ExtractionServiceFactory"
    )
    @patch(
        "datafinc.brazil.dados_b3.historical_quotes.application.use_cases.extract_historical_quotes_use_case.AvailableAssetsService"
    )
    async def test_uses_default_filename(self, mock_assets_service, mock_factory):
        mock_service = AsyncMock()
        mock_service.extract_from_zip_files.return_value = {}
        mock_factory.create.return_value = mock_service
        mock_assets_service.get_tpmerc_codes_for_assets.return_value = {"010"}

        docs = DocsToExtractorB3(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2021),
            destination_path="/path/to/output",
            set_documents_to_download={"COTAHIST_A2020.ZIP"},
        )

        use_case = ExtractHistoricalQuotesUseCaseB3()
        await use_case.execute(docs)
        call_args = mock_service.extract_from_zip_files.call_args
        expected_path = Path("/path/to/output") / "cotahist_extracted.parquet"
        assert call_args.kwargs["output_path"] == expected_path
