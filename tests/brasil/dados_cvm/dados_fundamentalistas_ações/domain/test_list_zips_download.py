from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.domain.list_zips_download import (
    ListZipsToDownload,
)
from src.brasil.dados_cvm.dados_fundamentalistas_ações.exceptions.exceptions import (
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidTypeDoc,
)


@pytest.mark.unit
class TestListZipsToDownload:
    @pytest.fixture
    def list_zips(self):
        return ListZipsToDownload()

    def test_initialization(self, list_zips):
        assert list_zips is not None
        assert hasattr(list_zips, "_url_docs")
        assert hasattr(list_zips, "_available_years")

    def test_get_list_zips_to_download_returns_list(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)
        assert isinstance(result, list)

    def test_get_list_zips_to_download_returns_strings(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)
        for item in result:
            assert isinstance(item, str)

    def test_get_list_zips_to_download_single_doc_single_year(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)

        assert len(result) == 1
        assert "dfp_cia_aberta_2020.zip" in result[0]
        assert result[0].startswith("https://")

    def test_get_list_zips_to_download_single_doc_multiple_years(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2022)

        assert len(result) == 3
        assert any("2020.zip" in url for url in result)
        assert any("2021.zip" in url for url in result)
        assert any("2022.zip" in url for url in result)

    def test_get_list_zips_to_download_multiple_docs_single_year(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP", "ITR"], 2020, 2020)

        assert len(result) == 2
        assert any("dfp_cia_aberta_2020.zip" in url for url in result)
        assert any("itr_cia_aberta_2020.zip" in url for url in result)

    def test_get_list_zips_to_download_multiple_docs_multiple_years(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP", "ITR"], 2020, 2021)

        assert len(result) == 4
        assert any("dfp_cia_aberta_2020.zip" in url for url in result)
        assert any("dfp_cia_aberta_2021.zip" in url for url in result)
        assert any("itr_cia_aberta_2020.zip" in url for url in result)
        assert any("itr_cia_aberta_2021.zip" in url for url in result)

    def test_get_list_zips_to_download_with_default_parameters(self, list_zips):
        result = list_zips.get_list_zips_to_download()

        expected_count = 7 * (date.today().year - 2010 + 1)

        assert len(result) == expected_count
        assert all(".zip" in url for url in result)

    def test_get_list_zips_to_download_all_urls_end_with_zip(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2022)

        for url in result:
            assert url.endswith(".zip")

    def test_get_list_zips_to_download_all_urls_start_with_https(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2022)

        for url in result:
            assert url.startswith("https://")

    def test_get_list_zips_to_download_urls_contain_cvm_domain(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)

        for url in result:
            assert "dados.cvm.gov.br" in url

    def test_get_list_zips_to_download_with_only_list_docs(self, list_zips):
        result = list_zips.get_list_zips_to_download(list_docs=["DFP"])

        current_year = date.today().year
        expected_count = current_year - 2010 + 1

        assert len(result) == expected_count

    def test_get_list_zips_to_download_with_only_initial_year(self, list_zips):
        result = list_zips.get_list_zips_to_download(initial_year=2020)

        current_year = date.today().year
        expected_count = 7 * (current_year - 2020 + 1)

        assert len(result) == expected_count

    def test_get_list_zips_to_download_with_only_last_year(self, list_zips):
        result = list_zips.get_list_zips_to_download(last_year=2020)

        expected_count = 7 * (2020 - 2010 + 1)

        assert len(result) == expected_count

    def test_get_list_zips_to_download_with_lowercase_doc_name(self, list_zips):
        result = list_zips.get_list_zips_to_download(["dfp"], 2020, 2020)

        assert len(result) == 1
        assert "dfp_cia_aberta_2020.zip" in result[0]

    def test_get_list_zips_to_download_with_mixed_case_doc_name(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DfP"], 2020, 2020)

        assert len(result) == 1
        assert "dfp_cia_aberta_2020.zip" in result[0]

    def test_get_list_zips_to_download_with_invalid_doc_raises_error(self, list_zips):
        with pytest.raises(InvalidDocName):
            list_zips.get_list_zips_to_download(["INVALID_DOC"], 2020, 2020)

    def test_get_list_zips_to_download_with_non_string_doc_raises_error(
        self, list_zips
    ):
        with pytest.raises(InvalidTypeDoc):
            list_zips.get_list_zips_to_download([123], 2020, 2020)

    def test_get_list_zips_to_download_with_invalid_first_year_raises_error(
        self, list_zips
    ):
        with pytest.raises(InvalidFirstYear):
            list_zips.get_list_zips_to_download(["DFP"], 2009, 2020)

    def test_get_list_zips_to_download_with_invalid_last_year_raises_error(
        self, list_zips
    ):
        with pytest.raises(InvalidLastYear):
            list_zips.get_list_zips_to_download(["DFP"], 2020, 2019)

    def test_get_list_zips_to_download_with_future_year_raises_error(self, list_zips):
        future_year = date.today().year + 10
        with pytest.raises(InvalidLastYear):
            list_zips.get_list_zips_to_download(["DFP"], 2020, future_year)

    def test_get_list_zips_to_download_with_year_before_minimum_raises_error(
        self, list_zips
    ):
        with pytest.raises(InvalidFirstYear):
            list_zips.get_list_zips_to_download(["DFP"], 2000, 2020)

    def test_get_list_zips_to_download_order_years_then_docs(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP", "ITR"], 2020, 2021)

        assert "2020" in result[0]
        assert "2020" in result[1]
        assert "2021" in result[2]

    def test_get_list_zips_to_download_all_seven_docs(self, list_zips):
        all_docs = ["CGVN", "FRE", "FCA", "DFP", "ITR", "IPE", "VLMO"]
        result = list_zips.get_list_zips_to_download(all_docs, 2020, 2020)

        assert len(result) == 7
        for doc in all_docs:
            assert any(doc.lower() in url.lower() for url in result)

    def test_get_list_zips_to_download_with_empty_list_docs(self, list_zips):
        result = list_zips.get_list_zips_to_download([], 2020, 2020)

        expected_count = 7 * 1

        assert len(result) == expected_count

    def test_get_list_zips_to_download_url_format_is_correct(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)

        url = result[0]
        assert url.startswith("https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/")
        assert "dfp_cia_aberta_2020.zip" in url

    def test_get_list_zips_to_download_with_duplicate_docs(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP", "DFP"], 2020, 2020)

        assert len(result) == 1
        assert "dfp_cia_aberta_2020.zip" in result[0]

    def test_get_list_zips_to_download_range_includes_boundaries(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2018, 2020)

        assert any("2018.zip" in url for url in result)
        assert any("2019.zip" in url for url in result)
        assert any("2020.zip" in url for url in result)
        assert len(result) == 3

    def test_get_list_zips_to_download_with_minimum_year_2010(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2010, 2010)

        assert len(result) == 1
        assert "2010.zip" in result[0]

    def test_get_list_zips_to_download_with_current_year(self, list_zips):
        current_year = date.today().year
        result = list_zips.get_list_zips_to_download(
            ["DFP"], current_year, current_year
        )

        assert len(result) == 1
        assert f"{current_year}.zip" in result[0]

    def test_get_list_zips_to_download_no_duplicate_urls(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)

        assert len(result) == 1

    def test_get_list_zips_to_download_large_year_range(self, list_zips):
        result = list_zips.get_list_zips_to_download(["DFP"], 2010, 2024)

        assert len(result) == 15

    def test_get_list_zips_to_download_specific_url_structure_for_each_doc(
        self, list_zips
    ):
        result_dfp = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)
        assert "/DFP/DADOS/dfp_cia_aberta_2020.zip" in result_dfp[0]

        result_itr = list_zips.get_list_zips_to_download(["ITR"], 2020, 2020)
        assert "/ITR/DADOS/itr_cia_aberta_2020.zip" in result_itr[0]

        result_fre = list_zips.get_list_zips_to_download(["FRE"], 2020, 2020)
        assert "/FRE/DADOS/fre_cia_aberta_2020.zip" in result_fre[0]

    def test_get_list_zips_to_download_with_non_list_docs_type_raises_error(
        self, list_zips
    ):
        with pytest.raises(TypeError):
            list_zips.get_list_zips_to_download("DFP", 2020, 2020)

    def test_get_list_zips_to_download_with_string_years_raises_error(self, list_zips):
        with pytest.raises(InvalidFirstYear):
            list_zips.get_list_zips_to_download(["DFP"], "2020", 2021)

    def test_get_list_zips_to_download_with_float_years_raises_error(self, list_zips):
        with pytest.raises(InvalidFirstYear):
            list_zips.get_list_zips_to_download(["DFP"], 2020.5, 2021)

    def test_get_list_zips_to_download_combinations(self, list_zips):
        result1 = list_zips.get_list_zips_to_download(["DFP", "ITR", "FRE"], 2020, 2021)
        assert len(result1) == 6

        result2 = list_zips.get_list_zips_to_download(["DFP"], 2018, 2022)
        assert len(result2) == 5

        result3 = list_zips.get_list_zips_to_download(["DFP", "ITR"], 2020, 2020)
        assert len(result3) == 2

    @patch(
        "src.brasil.dados_cvm.dados_fundamentalistas_ações.domain.list_zips_download.UrlDocs"
    )
    @patch(
        "src.brasil.dados_cvm.dados_fundamentalistas_ações.domain.list_zips_download.AvailableYears"
    )
    def test_get_list_zips_to_download_uses_dependencies_correctly(
        self, mock_available_years, mock_url_docs
    ):
        mock_years_instance = MagicMock()
        mock_years_instance.return_range_years.return_value = range(2020, 2022)
        mock_available_years.return_value = mock_years_instance

        mock_url_instance = MagicMock()
        mock_url_instance.get_url_docs.return_value = [
            "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_"
        ]
        mock_url_docs.return_value = mock_url_instance

        list_zips_test = ListZipsToDownload()
        result = list_zips_test.get_list_zips_to_download(["DFP"], 2020, 2021)

        mock_years_instance.return_range_years.assert_called_once_with(2020, 2021)
        mock_url_instance.get_url_docs.assert_called_once_with(["DFP"])

        assert len(result) == 2

    def test_get_list_zips_to_download_result_is_new_list(self, list_zips):
        result1 = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)
        result2 = list_zips.get_list_zips_to_download(["DFP"], 2020, 2020)

        result1.append("test")
        assert len(result2) == 1
