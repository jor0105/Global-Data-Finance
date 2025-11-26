from unittest.mock import patch

import pytest

from globaldatafinance.application.cvm_docs import FundamentalStocksDataCVM
from globaldatafinance.brazil import DownloadResultCVM


@pytest.mark.integration
class TestFundamentalStocksDataCVM:
    def test_scenario_success_download_returns_result(self, tmp_path):
        cvm = FundamentalStocksDataCVM()
        mock_result = DownloadResultCVM()
        mock_result.add_success_downloads("DFP_2023")

        with patch.object(
            cvm, "_FundamentalStocksDataCVM__download_use_case"
        ) as mock_use_case:
            mock_use_case.execute.return_value = mock_result

            result = cvm.download(
                destination_path=str(tmp_path),
                list_docs=["DFP"],
                initial_year=2023,
                last_year=2023,
            )

            assert isinstance(result, DownloadResultCVM)
            assert result.success_count_downloads == 1
            assert "DFP_2023" in result.successful_downloads

    def test_scenario_success_download_with_errors(self, tmp_path):
        cvm = FundamentalStocksDataCVM()
        mock_result = DownloadResultCVM()
        mock_result.add_success_downloads("DFP_2023")
        mock_result.add_error_downloads("ITR_2023", "Network timeout")

        with patch.object(
            cvm, "_FundamentalStocksDataCVM__download_use_case"
        ) as mock_use_case:
            mock_use_case.execute.return_value = mock_result

            result = cvm.download(
                destination_path=str(tmp_path),
                list_docs=["DFP", "ITR"],
                initial_year=2023,
                last_year=2023,
            )

            assert result.success_count_downloads == 1
            assert result.error_count_downloads == 1
            assert "ITR_2023" in result.failed_downloads
            assert "Network timeout" in result.failed_downloads["ITR_2023"]

    def test_scenario_success_get_available_docs(self):
        cvm = FundamentalStocksDataCVM()
        docs = cvm.get_available_docs()

        assert isinstance(docs, dict)
        assert "DFP" in docs
        assert "ITR" in docs

    def test_scenario_success_get_available_years(self):
        cvm = FundamentalStocksDataCVM()
        years = cvm.get_available_years()

        assert isinstance(years, dict)
        assert "Current Year" in years
        assert isinstance(years["Current Year"], int)
