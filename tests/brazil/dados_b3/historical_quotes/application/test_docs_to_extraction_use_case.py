"""Tests for CreateDocsToExtractUseCase."""

from unittest.mock import MagicMock, patch

import pytest

from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    CreateDocsToExtractUseCase,
)
from src.brazil.dados_b3.historical_quotes.domain.entities import DocsToExtractor
from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
    InvalidFirstYear,
    InvalidLastYear,
)


class TestCreateDocsToExtractUseCaseInitialization:
    """Test suite for CreateDocsToExtractUseCase initialization."""

    def test_initializes_with_all_parameters(self):
        """Test initialization with all parameters."""
        # Arrange & Act
        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações", "etf"],
            initial_year=2020,
            last_year=2024,
            destination_path="/path/to/output",
        )

        # Assert
        assert use_case.path_of_docs == "/path/to/docs"
        assert use_case.assets_list == ["ações", "etf"]
        assert use_case.initial_year == 2020
        assert use_case.last_year == 2024
        assert use_case.destination_path == "/path/to/output"

    def test_initializes_without_destination_path(self):
        """Test initialization without destination_path (defaults to path_of_docs)."""
        # Arrange & Act
        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2024,
        )

        # Assert
        assert use_case.destination_path == "/path/to/docs"

    def test_initializes_with_none_destination_path(self):
        """Test initialization with None destination_path (defaults to path_of_docs)."""
        # Arrange & Act
        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2024,
            destination_path=None,
        )

        # Assert
        assert use_case.destination_path == "/path/to/docs"

    def test_stores_all_parameters_correctly(self):
        """Test that all parameters are stored correctly."""
        # Arrange
        path = "/test/path"
        assets = ["ações", "etf", "opções"]
        initial = 2015
        last = 2020
        dest = "/test/output"

        # Act
        use_case = CreateDocsToExtractUseCase(
            path_of_docs=path,
            assets_list=assets,
            initial_year=initial,
            last_year=last,
            destination_path=dest,
        )

        # Assert
        assert use_case.path_of_docs == path
        assert use_case.assets_list == assets
        assert use_case.initial_year == initial
        assert use_case.last_year == last
        assert use_case.destination_path == dest


class TestCreateDocsToExtractUseCaseExecute:
    """Test suite for execute method."""

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_returns_docs_to_extractor(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test that execute returns a DocsToExtractor entity."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações", "etf"}
        mock_range_years.execute.return_value = range(2020, 2025)
        mock_verify_path.return_value.execute.return_value = None
        mock_set_download.execute.return_value = {"COTAHIST_A2020.ZIP"}

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações", "etf"],
            initial_year=2020,
            last_year=2024,
            destination_path="/path/to/output",
        )

        # Act
        result = use_case.execute()

        # Assert
        assert isinstance(result, DocsToExtractor)

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_calls_set_assets_use_case(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test that execute calls CreateSetAssetsUseCase."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações"}
        mock_range_years.execute.return_value = range(2020, 2025)
        mock_verify_path.return_value.execute.return_value = None
        mock_set_download.execute.return_value = set()

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2024,
        )

        # Act
        use_case.execute()

        # Assert
        mock_set_assets.execute.assert_called_once_with(["ações"])

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_calls_range_years_use_case(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test that execute calls CreateRangeYearsUseCase."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações"}
        mock_range_years.execute.return_value = range(2020, 2025)
        mock_verify_path.return_value.execute.return_value = None
        mock_set_download.execute.return_value = set()

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2024,
        )

        # Act
        use_case.execute()

        # Assert
        mock_range_years.execute.assert_called_once_with(2020, 2024)

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_calls_verify_destination_path_use_case(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test that execute calls VerifyDestinationPathsUseCase."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações"}
        mock_range_years.execute.return_value = range(2020, 2025)
        mock_verify_instance = MagicMock()
        mock_verify_path.return_value = mock_verify_instance
        mock_set_download.execute.return_value = set()

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2024,
            destination_path="/output",
        )

        # Act
        use_case.execute()

        # Assert
        mock_verify_instance.execute.assert_called_once_with("/output")

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_calls_set_to_download_use_case(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test that execute calls CreateSetToDownloadUseCase."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações"}
        year_range = range(2020, 2025)
        mock_range_years.execute.return_value = year_range
        mock_verify_path.return_value.execute.return_value = None
        mock_set_download.execute.return_value = set()

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2024,
        )

        # Act
        use_case.execute()

        # Assert
        mock_set_download.execute.assert_called_once_with(year_range, "/path/to/docs")

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_builds_entity_with_correct_data(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test that execute builds entity with correct data."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações", "etf"}
        mock_range_years.execute.return_value = range(2020, 2025)
        mock_verify_path.return_value.execute.return_value = None
        mock_set_download.execute.return_value = {
            "COTAHIST_A2020.ZIP",
            "COTAHIST_A2021.ZIP",
        }

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações", "etf"],
            initial_year=2020,
            last_year=2024,
            destination_path="/output",
        )

        # Act
        result = use_case.execute()

        # Assert
        assert result.path_of_docs == "/path/to/docs"
        assert result.set_assets == {"ações", "etf"}
        assert result.range_years == range(2020, 2025)
        assert result.destination_path == "/output"
        assert result.set_documents_to_download == {
            "COTAHIST_A2020.ZIP",
            "COTAHIST_A2021.ZIP",
        }

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    def test_execute_raises_empty_asset_list_error(self, mock_set_assets):
        """Test that execute raises EmptyAssetListError for empty assets."""
        # Arrange
        mock_set_assets.execute.side_effect = EmptyAssetListError()

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=[],
            initial_year=2020,
            last_year=2024,
        )

        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            use_case.execute()

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    def test_execute_raises_invalid_assets_name(self, mock_set_assets):
        """Test that execute raises InvalidAssetsName for invalid assets."""
        # Arrange
        mock_set_assets.execute.side_effect = InvalidAssetsName(
            ["invalid"], ["ações", "etf"]
        )

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["invalid"],
            initial_year=2020,
            last_year=2024,
        )

        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            use_case.execute()

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    def test_execute_raises_invalid_first_year(self, mock_range_years, mock_set_assets):
        """Test that execute raises InvalidFirstYear for invalid initial year."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações"}
        mock_range_years.execute.side_effect = InvalidFirstYear(1986, 2024)

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=1900,
            last_year=2024,
        )

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            use_case.execute()

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    def test_execute_raises_invalid_last_year(self, mock_range_years, mock_set_assets):
        """Test that execute raises InvalidLastYear for invalid last year."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações"}
        mock_range_years.execute.side_effect = InvalidLastYear(2020, 2024)

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2030,
        )

        # Act & Assert
        with pytest.raises(InvalidLastYear):
            use_case.execute()

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_with_single_asset(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test execute with single asset."""
        # Arrange
        mock_set_assets.execute.return_value = {"ações"}
        mock_range_years.execute.return_value = range(2020, 2021)
        mock_verify_path.return_value.execute.return_value = None
        mock_set_download.execute.return_value = {"COTAHIST_A2020.ZIP"}

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=["ações"],
            initial_year=2020,
            last_year=2020,
        )

        # Act
        result = use_case.execute()

        # Assert
        assert len(result.set_assets) == 1
        assert "ações" in result.set_assets

    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetAssetsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateRangeYearsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.VerifyDestinationPathsUseCase"
    )
    @patch(
        "src.brazil.dados_b3.historical_quotes.application.use_cases.docs_to_extraction_use_case.CreateSetToDownloadUseCase"
    )
    def test_execute_with_all_assets(
        self,
        mock_set_download,
        mock_verify_path,
        mock_range_years,
        mock_set_assets,
    ):
        """Test execute with all available assets."""
        # Arrange
        all_assets = {
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        }
        mock_set_assets.execute.return_value = all_assets
        mock_range_years.execute.return_value = range(2020, 2025)
        mock_verify_path.return_value.execute.return_value = None
        mock_set_download.execute.return_value = set()

        use_case = CreateDocsToExtractUseCase(
            path_of_docs="/path/to/docs",
            assets_list=list(all_assets),
            initial_year=2020,
            last_year=2024,
        )

        # Act
        result = use_case.execute()

        # Assert
        assert len(result.set_assets) == 7
