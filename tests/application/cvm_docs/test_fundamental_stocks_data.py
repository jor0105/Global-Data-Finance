from unittest.mock import Mock, patch

from datafinc.application import FundamentalStocksData


class TestFundamentalStocksData:
    def test_initialization(self):
        cvm = FundamentalStocksData()
        assert cvm is not None
        assert repr(cvm) == "FundamentalStocksData()"

    def test_initialization_sets_download_adapter(self):
        cvm = FundamentalStocksData()
        assert cvm.download_adapter is not None
        assert hasattr(cvm.download_adapter, "automatic_extractor")

    def test_get_available_docs(self):
        cvm = FundamentalStocksData()
        docs = cvm.get_available_docs()
        assert isinstance(docs, dict)
        assert len(docs) > 0
        assert "DFP" in docs or "ITR" in docs

    def test_get_available_years(self):
        cvm = FundamentalStocksData()
        years = cvm.get_available_years()
        assert isinstance(years, dict)
        assert len(years) > 0

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_with_all_parameters(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 5
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = ["DFP_2023.zip"]
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(
            destination_path="/data/cvm",
            list_docs=["DFP", "ITR"],
            initial_year=2020,
            last_year=2023,
            automatic_extractor=True,
        )

        mock_download_instance.execute.assert_called_once()
        call_args = mock_download_instance.execute.call_args
        assert call_args[1]["destination_path"] == "/data/cvm"
        assert call_args[1]["list_docs"] == ["DFP", "ITR"]
        assert call_args[1]["initial_year"] == 2020
        assert call_args[1]["last_year"] == 2023

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_with_minimal_parameters(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 3
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = ["DFP_2023.zip"]
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(destination_path="/data/cvm")

        mock_download_instance.execute.assert_called_once()

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_enables_automatic_extractor_when_true(
        self, mock_download_use_case
    ):
        mock_result = Mock()
        mock_result.success_count_downloads = 2
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = []
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()

        cvm.download(destination_path="/data/cvm", automatic_extractor=True)

        assert cvm.download_adapter.automatic_extractor is True

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_with_specific_docs(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 2
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = ["DFP_2023.zip", "DFP_2022.zip"]
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(destination_path="/data/cvm", list_docs=["DFP"])

        call_args = mock_download_instance.execute.call_args
        assert call_args[1]["list_docs"] == ["DFP"]

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_with_year_range(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 4
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = []
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(destination_path="/data/cvm", initial_year=2020, last_year=2023)

        call_args = mock_download_instance.execute.call_args
        assert call_args[1]["initial_year"] == 2020
        assert call_args[1]["last_year"] == 2023

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_with_errors(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 2
        mock_result.error_count_downloads = 1
        mock_result.successful_downloads = ["DFP_2023.zip", "DFP_2022.zip"]
        mock_result.failed_downloads = {"ITR_2023.zip": "Network error"}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(destination_path="/data/cvm", list_docs=["DFP", "ITR"])

        assert mock_result.error_count_downloads == 1

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_without_automatic_extractor(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 3
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = []
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(destination_path="/data/cvm", automatic_extractor=False)

        mock_download_instance.execute.assert_called_once()

    def test_repr_returns_correct_string(self):
        cvm = FundamentalStocksData()
        assert repr(cvm) == "FundamentalStocksData()"

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_calls_result_formatter(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 1
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = ["DFP_2023.zip"]
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        with patch.object(
            cvm, "_FundamentalStocksData__result_formatter"
        ) as mock_formatter:
            cvm.download(destination_path="/data/cvm")
            mock_formatter.print_result.assert_called_once_with(mock_result)

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_with_none_list_docs(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 5
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = []
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(destination_path="/data/cvm", list_docs=None)

        call_args = mock_download_instance.execute.call_args
        assert call_args[1]["list_docs"] is None

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_with_none_years(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 3
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = []
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        cvm.download(destination_path="/data/cvm", initial_year=None, last_year=None)

        call_args = mock_download_instance.execute.call_args
        assert call_args[1]["initial_year"] is None
        assert call_args[1]["last_year"] is None

    def test_get_available_docs_returns_dict(self):
        cvm = FundamentalStocksData()
        docs = cvm.get_available_docs()
        assert isinstance(docs, dict)

    def test_get_available_years_returns_dict(self):
        cvm = FundamentalStocksData()
        years = cvm.get_available_years()
        assert isinstance(years, dict)

    def test_initialization_creates_use_cases(self):
        cvm = FundamentalStocksData()
        assert hasattr(cvm, "_FundamentalStocksData__download_use_case")
        assert hasattr(cvm, "_FundamentalStocksData__available_docs_use_case")
        assert hasattr(cvm, "_FundamentalStocksData__available_years_use_case")
        assert hasattr(cvm, "_FundamentalStocksData__result_formatter")

    @patch(
        "datafinc.application.cvm_docs.fundamental_stocks_data.DownloadDocumentsUseCaseCVM"
    )
    def test_download_returns_none(self, mock_download_use_case):
        mock_result = Mock()
        mock_result.success_count_downloads = 1
        mock_result.error_count_downloads = 0
        mock_result.successful_downloads = []
        mock_result.failed_downloads = {}
        mock_download_instance = Mock()
        mock_download_instance.execute.return_value = mock_result
        mock_download_use_case.return_value = mock_download_instance

        cvm = FundamentalStocksData()
        result = cvm.download(destination_path="/data/cvm")
        assert result is None
