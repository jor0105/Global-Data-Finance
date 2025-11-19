from pathlib import Path
from unittest.mock import MagicMock, patch

from datafinance.brazil.b3_data.historical_quotes.application.use_cases import (
    CreateSetToDownloadUseCaseB3,
)


class TestCreateSetToDownloadUseCaseB3:
    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_returns_set(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = {"COTAHIST_A2020.ZIP"}
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(2020, 2021), "/path/to/docs")

        assert isinstance(result, set)

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_calls_validate_directory_path(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = set()
        mock_file_system.return_value = mock_instance

        CreateSetToDownloadUseCaseB3.execute(range(2020, 2021), "/path/to/docs")

        mock_instance.validate_directory_path.assert_called_once_with("/path/to/docs")

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_calls_find_files_by_years(self, mock_file_system):
        mock_instance = MagicMock()
        validated_path = Path("/path/to/docs")
        mock_instance.validate_directory_path.return_value = validated_path
        mock_instance.find_files_by_years.return_value = set()
        mock_file_system.return_value = mock_instance
        year_range = range(2020, 2021)

        CreateSetToDownloadUseCaseB3.execute(year_range, "/path/to/docs")

        mock_instance.find_files_by_years.assert_called_once_with(
            validated_path, year_range
        )

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_with_single_year(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = {"COTAHIST_A2020.ZIP"}
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(2020, 2021), "/path/to/docs")

        assert "COTAHIST_A2020.ZIP" in result

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_with_multiple_years(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = {
            "COTAHIST_A2020.ZIP",
            "COTAHIST_A2021.ZIP",
            "COTAHIST_A2022.ZIP",
        }
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(2020, 2023), "/path/to/docs")

        assert len(result) == 3
        assert "COTAHIST_A2020.ZIP" in result
        assert "COTAHIST_A2021.ZIP" in result
        assert "COTAHIST_A2022.ZIP" in result

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_returns_empty_set_when_no_files_found(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = set()
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(2020, 2021), "/path/to/docs")

        assert result == set()

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_with_long_year_range(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        files = {f"COTAHIST_A{year}.ZIP" for year in range(1986, 2025)}
        mock_instance.find_files_by_years.return_value = files
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(1986, 2025), "/path/to/docs")

        assert len(result) == 39

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_is_static_method(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = set()
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(2020, 2021), "/path/to/docs")
        assert result is not None

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_with_path_containing_spaces(self, mock_file_system):
        mock_instance = MagicMock()
        path_with_spaces = "/path/with spaces/to/docs"
        mock_instance.validate_directory_path.return_value = Path(path_with_spaces)
        mock_instance.find_files_by_years.return_value = {"COTAHIST_A2020.ZIP"}
        mock_file_system.return_value = mock_instance

        CreateSetToDownloadUseCaseB3.execute(range(2020, 2021), path_with_spaces)

        mock_instance.validate_directory_path.assert_called_once_with(path_with_spaces)

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_with_empty_range(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = set()
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(2020, 2020), "/path/to/docs")

        assert result == set()

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_creates_file_system_service(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        mock_instance.find_files_by_years.return_value = set()
        mock_file_system.return_value = mock_instance

        CreateSetToDownloadUseCaseB3.execute(range(2020, 2021), "/path/to/docs")

        mock_file_system.assert_called_once()

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_passes_validated_path_to_find_files(self, mock_file_system):
        mock_instance = MagicMock()
        validated_path = Path("/validated/path")
        mock_instance.validate_directory_path.return_value = validated_path
        mock_instance.find_files_by_years.return_value = set()
        mock_file_system.return_value = mock_instance
        year_range = range(2020, 2021)

        CreateSetToDownloadUseCaseB3.execute(year_range, "/original/path")

        mock_instance.find_files_by_years.assert_called_once_with(
            validated_path, year_range
        )

    @patch(
        "datafinance.brazil.b3_data.historical_quotes.application.use_cases.set_docs_to_download_use_case.FileSystemServiceB3"
    )
    def test_execute_returns_result_from_find_files(self, mock_file_system):
        mock_instance = MagicMock()
        mock_instance.validate_directory_path.return_value = Path("/path/to/docs")
        expected_files = {"COTAHIST_A2020.ZIP", "COTAHIST_A2021.ZIP"}
        mock_instance.find_files_by_years.return_value = expected_files
        mock_file_system.return_value = mock_instance

        result = CreateSetToDownloadUseCaseB3.execute(range(2020, 2022), "/path/to/docs")

        assert result == expected_files
