import logging
from unittest.mock import patch

import pytest

from src.brazil.cvm.fundamental_stocks_data import (
    DownloadDocumentsUseCase,
    DownloadResult,
    GetAvailableDocsUseCase,
    GetAvailableYearsUseCase,
    HttpxAsyncDownloadAdapter,
)
from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
)
from src.presentation.cvm_docs import FundamentalStocksData
from src.presentation.cvm_docs.download_result_formatter import DownloadResultFormatter


class TestFundamentalStocksDataInitialization:
    def test_initialization_creates_all_dependencies(self):
        cvm = FundamentalStocksData()

        assert cvm is not None
        assert isinstance(cvm.download_adapter, HttpxAsyncDownloadAdapter)
        assert hasattr(cvm, "_FundamentalStocksData__available_docs_use_case")
        assert hasattr(cvm, "_FundamentalStocksData__available_years_use_case")
        assert hasattr(cvm, "_FundamentalStocksData__download_use_case")
        assert hasattr(cvm, "_FundamentalStocksData__result_formatter")

    def test_initialization_creates_correct_types(self):
        cvm = FundamentalStocksData()

        assert isinstance(
            cvm._FundamentalStocksData__available_docs_use_case,
            GetAvailableDocsUseCase,
        )
        assert isinstance(
            cvm._FundamentalStocksData__available_years_use_case,
            GetAvailableYearsUseCase,
        )
        assert isinstance(
            cvm._FundamentalStocksData__download_use_case, DownloadDocumentsUseCase
        )
        assert isinstance(
            cvm._FundamentalStocksData__result_formatter, DownloadResultFormatter
        )

    def test_repr_returns_correct_string(self):
        cvm = FundamentalStocksData()
        assert repr(cvm) == "FundamentalStocksData()"
        assert str(cvm) == "FundamentalStocksData()"


class TestGetAvailableDocs:
    @patch.object(GetAvailableDocsUseCase, "execute")
    def test_get_available_docs_returns_dict(self, mock_execute):
        mock_execute.return_value = {
            "DFP": "Demonstrações Financeiras Padronizadas",
            "ITR": "Informações Trimestrais",
        }
        cvm = FundamentalStocksData()
        result = cvm.get_available_docs()
        assert isinstance(result, dict)
        assert "DFP" in result
        assert "ITR" in result
        mock_execute.assert_called_once()

    @patch.object(GetAvailableDocsUseCase, "execute")
    def test_get_available_docs_returns_correct_data(self, mock_execute):
        expected_docs = {
            "DFP": "Demonstrações Financeiras Padronizadas",
            "ITR": "Informações Trimestrais",
            "FCA": "Formulário Cadastral",
            "FRE": "Formulário de Referência",
        }
        mock_execute.return_value = expected_docs
        cvm = FundamentalStocksData()
        result = cvm.get_available_docs()
        assert result == expected_docs
        assert len(result) == 4

    @patch.object(GetAvailableDocsUseCase, "execute")
    def test_get_available_docs_empty_dict(self, mock_execute):
        mock_execute.return_value = {}
        cvm = FundamentalStocksData()
        result = cvm.get_available_docs()
        assert result == {}
        assert isinstance(result, dict)
        assert len(result) == 0

    @patch.object(GetAvailableDocsUseCase, "execute")
    def test_get_available_docs_logs_debug_message(self, mock_execute, caplog):
        mock_execute.return_value = {"DFP": "Test"}
        cvm = FundamentalStocksData()
        with caplog.at_level(logging.DEBUG):
            cvm.get_available_docs()
        assert "Retrieving available document types" in caplog.text

    @patch.object(GetAvailableDocsUseCase, "execute")
    def test_get_available_docs_called_multiple_times(self, mock_execute):
        mock_execute.return_value = {"DFP": "Test"}
        cvm = FundamentalStocksData()
        result1 = cvm.get_available_docs()
        result2 = cvm.get_available_docs()
        assert result1 == result2
        assert mock_execute.call_count == 2


class TestGetAvailableYears:
    @patch.object(GetAvailableYearsUseCase, "execute")
    def test_get_available_years_returns_dict(self, mock_execute):
        mock_execute.return_value = {
            "General Docs": 1998,
            "ITR Documents": 2011,
            "CGVN and VLMO Documents": 2017,
            "Current Year": 2025,
        }
        cvm = FundamentalStocksData()
        result = cvm.get_available_years()
        assert isinstance(result, dict)
        assert "General Docs" in result
        assert "ITR Documents" in result
        assert "CGVN and VLMO Documents" in result
        assert "Current Year" in result
        mock_execute.assert_called_once()

    @patch.object(GetAvailableYearsUseCase, "execute")
    def test_get_available_years_returns_correct_data(self, mock_execute):
        expected_years = {
            "General Docs": 1998,
            "ITR Documents": 2011,
            "CGVN and VLMO Documents": 2017,
            "Current Year": 2025,
        }
        mock_execute.return_value = expected_years
        cvm = FundamentalStocksData()
        result = cvm.get_available_years()
        assert result == expected_years
        assert result["General Docs"] == 1998
        assert result["ITR Documents"] == 2011
        assert result["Current Year"] == 2025

    @patch.object(GetAvailableYearsUseCase, "execute")
    def test_get_available_years_all_values_are_integers(self, mock_execute):
        mock_execute.return_value = {
            "General Docs": 1998,
            "ITR Documents": 2011,
            "CGVN and VLMO Documents": 2017,
            "Current Year": 2025,
        }
        cvm = FundamentalStocksData()
        result = cvm.get_available_years()
        for key, value in result.items():
            assert isinstance(value, int), f"{key} should be an integer"

    @patch.object(GetAvailableYearsUseCase, "execute")
    def test_get_available_years_logs_debug_message(self, mock_execute, caplog):
        mock_execute.return_value = {"Current Year": 2025}
        cvm = FundamentalStocksData()
        with caplog.at_level(logging.DEBUG):
            cvm.get_available_years()
        assert "Retrieving available years information" in caplog.text

    @patch.object(GetAvailableYearsUseCase, "execute")
    def test_get_available_years_called_multiple_times(self, mock_execute):
        mock_execute.return_value = {"Current Year": 2025}
        cvm = FundamentalStocksData()
        result1 = cvm.get_available_years()
        result2 = cvm.get_available_years()
        assert result1 == result2
        assert mock_execute.call_count == 2


class TestDownloadBasicFunctionality:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_all_parameters(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(
            destination_path="/tmp/test",
            list_docs=["DFP", "ITR"],
            initial_year=2020,
            last_year=2023,
            automatic_extractor=True,
        )
        mock_execute.assert_called_once_with(
            destination_path="/tmp/test",
            list_docs=["DFP", "ITR"],
            initial_year=2020,
            last_year=2023,
        )
        mock_print.assert_called_once_with(mock_result)

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_minimal_parameters(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test")
        mock_execute.assert_called_once_with(
            destination_path="/tmp/test",
            list_docs=None,
            initial_year=None,
            last_year=None,
        )
        mock_print.assert_called_once()

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_automatic_extractor_enabled(
        self, mock_execute, mock_print, caplog
    ):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        with caplog.at_level(logging.DEBUG):
            cvm.download(destination_path="/tmp/test", automatic_extractor=True)
        assert "Automatic extractor enabled for this download" in caplog.text
        assert cvm.download_adapter.automatic_extractor is True

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_automatic_extractor_disabled(
        self, mock_execute, mock_print, caplog
    ):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        with caplog.at_level(logging.DEBUG):
            cvm.download(destination_path="/tmp/test", automatic_extractor=False)
        assert "Automatic extractor disabled for this download" in caplog.text

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_returns_none(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        result = cvm.download(destination_path="/tmp/test")
        assert result is None


class TestDownloadLogging:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_logs_info_on_start(self, mock_execute, mock_print, caplog):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        with caplog.at_level(logging.INFO):
            cvm.download(
                destination_path="/tmp/test",
                list_docs=["DFP"],
                initial_year=2020,
                last_year=2023,
            )
        assert "Download requested" in caplog.text
        assert "path=/tmp/test" in caplog.text
        assert "docs=['DFP']" in caplog.text
        assert "years=2020-2023" in caplog.text

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_logs_info_on_completion(self, mock_execute, mock_print, caplog):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_result.add_success_downloads("DFP_2022.zip")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        with caplog.at_level(logging.INFO):
            cvm.download(destination_path="/tmp/test")
        assert "Download completed" in caplog.text
        assert "2 successful" in caplog.text
        assert "0 errors" in caplog.text

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_logs_errors_count(self, mock_execute, mock_print, caplog):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_result.add_error_downloads("ITR_2023.zip", "Network error")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        with caplog.at_level(logging.INFO):
            cvm.download(destination_path="/tmp/test")
        assert "1 successful" in caplog.text
        assert "1 errors" in caplog.text


class TestDownloadWithSuccessfulResults:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_successful_single_file(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test", list_docs=["DFP"])
        assert mock_result.success_count_downloads == 1
        assert mock_result.error_count_downloads == 0
        mock_print.assert_called_once_with(mock_result)

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_successful_multiple_files(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_result.add_success_downloads("DFP_2022.zip")
        mock_result.add_success_downloads("ITR_2023.zip")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(
            destination_path="/tmp/test",
            list_docs=["DFP", "ITR"],
            initial_year=2022,
            last_year=2023,
        )
        assert mock_result.success_count_downloads == 3
        assert mock_result.error_count_downloads == 0
        mock_print.assert_called_once()


class TestDownloadWithErrors:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_partial_failures(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_result.add_error_downloads("ITR_2023.zip", "Network timeout")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test", list_docs=["DFP", "ITR"])
        assert mock_result.success_count_downloads == 1
        assert mock_result.error_count_downloads == 1
        mock_print.assert_called_once_with(mock_result)

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_all_failures(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_error_downloads("DFP_2023.zip", "Connection refused")
        mock_result.add_error_downloads("ITR_2023.zip", "File not found")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test")
        assert mock_result.success_count_downloads == 0
        assert mock_result.error_count_downloads == 2
        mock_print.assert_called_once()

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_propagates_invalid_doc_name_exception(
        self, mock_execute, mock_print
    ):
        mock_execute.side_effect = InvalidDocName("INVALID", ["DFP", "ITR"])
        cvm = FundamentalStocksData()
        with pytest.raises(InvalidDocName):
            cvm.download(destination_path="/tmp/test", list_docs=["INVALID"])

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_propagates_invalid_first_year_exception(
        self, mock_execute, mock_print
    ):
        mock_execute.side_effect = InvalidFirstYear(1998, 2025)
        cvm = FundamentalStocksData()
        with pytest.raises(InvalidFirstYear):
            cvm.download(destination_path="/tmp/test", initial_year=1900)

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_propagates_invalid_last_year_exception(
        self, mock_execute, mock_print
    ):
        mock_execute.side_effect = InvalidLastYear(2020, 2025)
        cvm = FundamentalStocksData()
        with pytest.raises(InvalidLastYear):
            cvm.download(
                destination_path="/tmp/test", initial_year=2020, last_year=2030
            )


class TestDownloadWithEmptyResults:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_empty_result(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test")
        assert mock_result.success_count_downloads == 0
        assert mock_result.error_count_downloads == 0
        mock_print.assert_called_once_with(mock_result)


class TestDownloadFormatterIntegration:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_formatter_is_called_with_result(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0]
        assert isinstance(call_args[0], DownloadResult)
        assert call_args[0].success_count_downloads == 1

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_formatter_receives_correct_result_object(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_result.add_error_downloads("ITR_2023.zip", "Error")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test")
        mock_print.assert_called_once_with(mock_result)


class TestDownloadEdgeCases:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_empty_list_docs(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test", list_docs=[])
        mock_execute.assert_called_once_with(
            destination_path="/tmp/test",
            list_docs=[],
            initial_year=None,
            last_year=None,
        )

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_same_initial_and_last_year(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test", initial_year=2023, last_year=2023)
        mock_execute.assert_called_once_with(
            destination_path="/tmp/test",
            list_docs=None,
            initial_year=2023,
            last_year=2023,
        )

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_single_doc_type(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_result.add_success_downloads("DFP_2023.zip")
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test", list_docs=["DFP"])
        mock_execute.assert_called_once_with(
            destination_path="/tmp/test",
            list_docs=["DFP"],
            initial_year=None,
            last_year=None,
        )

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_download_with_special_characters_in_path(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test-data_123/cvm docs")
        mock_execute.assert_called_once()
        assert (
            mock_execute.call_args[1]["destination_path"]
            == "/tmp/test-data_123/cvm docs"
        )


class TestDownloadAutomaticExtractorBehavior:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_automatic_extractor_true_sets_adapter_flag(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test", automatic_extractor=True)
        assert cvm.download_adapter.automatic_extractor is True

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_automatic_extractor_false_does_not_set_adapter_flag(
        self, mock_execute, mock_print
    ):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download_adapter.automatic_extractor = False
        cvm.download(destination_path="/tmp/test", automatic_extractor=False)
        assert cvm.download_adapter.automatic_extractor is False

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_automatic_extractor_default_behavior(self, mock_execute, mock_print):
        mock_result = DownloadResult()
        mock_execute.return_value = mock_result
        cvm = FundamentalStocksData()
        cvm.download_adapter.automatic_extractor = False
        cvm.download(destination_path="/tmp/test")
        assert cvm.download_adapter.automatic_extractor is False


class TestMultipleOperations:
    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    @patch.object(GetAvailableDocsUseCase, "execute")
    @patch.object(GetAvailableYearsUseCase, "execute")
    def test_multiple_method_calls_on_same_instance(
        self, mock_years, mock_docs, mock_download, mock_print
    ):
        mock_docs.return_value = {"DFP": "Test"}
        mock_years.return_value = {"Current Year": 2025}
        mock_result = DownloadResult()
        mock_download.return_value = mock_result
        cvm = FundamentalStocksData()
        docs = cvm.get_available_docs()
        years = cvm.get_available_years()
        cvm.download(destination_path="/tmp/test")
        assert docs == {"DFP": "Test"}
        assert years == {"Current Year": 2025}
        mock_docs.assert_called_once()
        mock_years.assert_called_once()
        mock_download.assert_called_once()

    @patch.object(DownloadResultFormatter, "print_result")
    @patch.object(DownloadDocumentsUseCase, "execute")
    def test_multiple_downloads_on_same_instance(self, mock_execute, mock_print):
        mock_result1 = DownloadResult()
        mock_result1.add_success_downloads("DFP_2023.zip")
        mock_result2 = DownloadResult()
        mock_result2.add_success_downloads("ITR_2023.zip")
        mock_execute.side_effect = [mock_result1, mock_result2]
        cvm = FundamentalStocksData()
        cvm.download(destination_path="/tmp/test1", list_docs=["DFP"])
        cvm.download(destination_path="/tmp/test2", list_docs=["ITR"])
        assert mock_execute.call_count == 2
        assert mock_print.call_count == 2
