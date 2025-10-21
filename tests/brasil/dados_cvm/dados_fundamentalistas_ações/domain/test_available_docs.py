import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.domain.available_docs import (
    AvailableDocs,
    UrlDocs,
)
from src.brasil.dados_cvm.dados_fundamentalistas_ações.exceptions.exceptions import (
    InvalidDocName,
    InvalidTypeDoc,
)


@pytest.mark.unit
class TestAvailableDocs:
    @pytest.fixture
    def available_docs(self):
        return AvailableDocs()

    def test_get_available_docs_returns_dict(self, available_docs):
        docs = available_docs.get_available_docs()
        assert isinstance(docs, dict)

    def test_get_available_docs_returns_all_expected_keys(self, available_docs):
        docs = available_docs.get_available_docs()
        expected_keys = ["CGVN", "FRE", "FCA", "DFP", "ITR", "IPE", "VLMO"]

        assert len(docs) == len(expected_keys)
        for key in expected_keys:
            assert key in docs

    def test_get_available_docs_returns_copy(self, available_docs):
        docs1 = available_docs.get_available_docs()
        docs2 = available_docs.get_available_docs()

        docs1["TEST"] = "Test value"
        assert "TEST" not in docs2

    def test_get_available_docs_values_are_strings(self, available_docs):
        docs = available_docs.get_available_docs()
        for value in docs.values():
            assert isinstance(value, str)
            assert len(value) > 0

    def test_get_available_docs_keys_are_uppercase(self, available_docs):
        docs = available_docs.get_available_docs()
        for key in docs.keys():
            assert key.isupper()

    def test_validate_docs_name_with_valid_doc_uppercase(self, available_docs):
        available_docs.validate_docs_name("DFP")
        available_docs.validate_docs_name("ITR")
        available_docs.validate_docs_name("FRE")

    def test_validate_docs_name_with_valid_doc_lowercase(self, available_docs):
        available_docs.validate_docs_name("dfp")
        available_docs.validate_docs_name("itr")
        available_docs.validate_docs_name("fre")

    def test_validate_docs_name_with_valid_doc_mixed_case(self, available_docs):
        available_docs.validate_docs_name("DfP")
        available_docs.validate_docs_name("ItR")
        available_docs.validate_docs_name("FrE")

    def test_validate_docs_name_with_spaces(self, available_docs):
        available_docs.validate_docs_name("  DFP  ")
        available_docs.validate_docs_name(" ITR ")
        available_docs.validate_docs_name("FRE   ")

    def test_validate_docs_name_with_invalid_doc_name(self, available_docs):
        with pytest.raises(InvalidDocName) as exc_info:
            available_docs.validate_docs_name("INVALID_DOC")

        assert "INVALID_DOC" in str(exc_info.value)

    def test_validate_docs_name_with_empty_string(self, available_docs):
        with pytest.raises(InvalidDocName):
            available_docs.validate_docs_name("")

    def test_validate_docs_name_with_non_string_type_integer(self, available_docs):
        with pytest.raises(InvalidTypeDoc) as exc_info:
            available_docs.validate_docs_name(123)

        assert "123" in str(exc_info.value)

    def test_validate_docs_name_with_non_string_type_list(self, available_docs):
        with pytest.raises(InvalidTypeDoc):
            available_docs.validate_docs_name(["DFP"])

    def test_validate_docs_name_with_non_string_type_dict(self, available_docs):
        with pytest.raises(InvalidTypeDoc):
            available_docs.validate_docs_name({"doc": "DFP"})

    def test_validate_docs_name_with_none(self, available_docs):
        with pytest.raises(InvalidTypeDoc):
            available_docs.validate_docs_name(None)

    def test_validate_docs_name_with_float(self, available_docs):
        with pytest.raises(InvalidTypeDoc):
            available_docs.validate_docs_name(3.14)

    def test_validate_docs_name_with_boolean(self, available_docs):
        with pytest.raises(InvalidTypeDoc):
            available_docs.validate_docs_name(True)

    def test_validate_all_available_docs(self, available_docs):
        docs = available_docs.get_available_docs()
        for doc_name in docs.keys():
            available_docs.validate_docs_name(doc_name)

    def test_doc_descriptions_not_empty(self, available_docs):
        docs = available_docs.get_available_docs()
        for description in docs.values():
            assert len(description.strip()) > 0


@pytest.mark.unit
class TestUrlDocs:
    @pytest.fixture
    def url_docs(self):
        return UrlDocs()

    def test_url_docs_initialization(self, url_docs):
        assert url_docs is not None
        assert hasattr(url_docs, "_available_docs")
        assert isinstance(url_docs._available_docs, AvailableDocs)

    def test_get_url_docs_without_parameters_returns_all_urls(self, url_docs):
        urls = url_docs.get_url_docs()

        assert isinstance(urls, list)
        assert len(urls) == 7

    def test_get_url_docs_returns_list_of_strings(self, url_docs):
        urls = url_docs.get_url_docs()

        for url in urls:
            assert isinstance(url, str)

    def test_get_url_docs_urls_start_with_https(self, url_docs):
        urls = url_docs.get_url_docs()

        for url in urls:
            assert url.startswith("https://")

    def test_get_url_docs_urls_contain_cvm_domain(self, url_docs):
        urls = url_docs.get_url_docs()

        for url in urls:
            assert "dados.cvm.gov.br" in url

    def test_get_url_docs_with_single_doc(self, url_docs):
        urls = url_docs.get_url_docs(["DFP"])

        assert len(urls) == 1
        assert "dfp_cia_aberta_" in urls[0]

    def test_get_url_docs_with_multiple_docs(self, url_docs):
        urls = url_docs.get_url_docs(["DFP", "ITR", "FRE"])

        assert len(urls) == 3
        assert any("dfp_cia_aberta_" in url for url in urls)
        assert any("itr_cia_aberta_" in url for url in urls)
        assert any("fre_cia_aberta_" in url for url in urls)

    def test_get_url_docs_with_lowercase_doc_name(self, url_docs):
        urls = url_docs.get_url_docs(["dfp"])

        assert len(urls) == 1
        assert "dfp_cia_aberta_" in urls[0]

    def test_get_url_docs_with_mixed_case_doc_name(self, url_docs):
        urls = url_docs.get_url_docs(["DfP"])

        assert len(urls) == 1
        assert "dfp_cia_aberta_" in urls[0]

    def test_get_url_docs_with_invalid_doc_name(self, url_docs):
        with pytest.raises(InvalidDocName):
            url_docs.get_url_docs(["INVALID_DOC"])

    def test_get_url_docs_with_non_list_parameter(self, url_docs):
        with pytest.raises(TypeError) as exc_info:
            url_docs.get_url_docs("DFP")

        assert "must be a built-in list" in str(exc_info.value)

    def test_get_url_docs_with_dict_parameter(self, url_docs):
        with pytest.raises(TypeError):
            url_docs.get_url_docs({"doc": "DFP"})

    def test_get_url_docs_with_integer_parameter(self, url_docs):
        with pytest.raises(TypeError):
            url_docs.get_url_docs(123)

    def test_get_url_docs_with_empty_list(self, url_docs):
        urls = url_docs.get_url_docs([])

        assert isinstance(urls, list)
        assert len(urls) == 7

    def test_get_url_docs_with_all_available_docs(self, url_docs):
        all_docs = ["CGVN", "FRE", "FCA", "DFP", "ITR", "IPE", "VLMO"]
        urls = url_docs.get_url_docs(all_docs)

        assert len(urls) == 7

    def test_get_url_docs_with_duplicate_docs(self, url_docs):
        urls = url_docs.get_url_docs(["DFP", "DFP"])

        assert len(urls) == 1
        assert "dfp_cia_aberta_" in urls[0]

    def test_get_url_docs_with_non_string_in_list(self, url_docs):
        with pytest.raises(InvalidTypeDoc):
            url_docs.get_url_docs([123])

    def test_get_url_docs_with_mixed_valid_invalid_docs(self, url_docs):
        with pytest.raises(InvalidDocName):
            url_docs.get_url_docs(["DFP", "INVALID"])

    def test_get_url_docs_specific_urls_for_each_doc(self, url_docs):
        urls_cgvn = url_docs.get_url_docs(["CGVN"])
        assert "cgvn_cia_aberta_" in urls_cgvn[0]

        urls_fre = url_docs.get_url_docs(["FRE"])
        assert "fre_cia_aberta_" in urls_fre[0]

        urls_fca = url_docs.get_url_docs(["FCA"])
        assert "fca_cia_aberta_" in urls_fca[0]

        urls_dfp = url_docs.get_url_docs(["DFP"])
        assert "dfp_cia_aberta_" in urls_dfp[0]

        urls_itr = url_docs.get_url_docs(["ITR"])
        assert "itr_cia_aberta_" in urls_itr[0]

        urls_ipe = url_docs.get_url_docs(["IPE"])
        assert "ipe_cia_aberta_" in urls_ipe[0]

        urls_vlmo = url_docs.get_url_docs(["VLMO"])
        assert "vlmo_cia_aberta_" in urls_vlmo[0]

    def test_get_url_docs_urls_end_correctly(self, url_docs):
        urls = url_docs.get_url_docs(["DFP"])

        assert urls[0].endswith("_")

    def test_get_url_docs_order_preserved(self, url_docs):
        docs_list = ["ITR", "DFP", "FRE"]
        urls = url_docs.get_url_docs(docs_list)

        assert "itr_cia_aberta_" in urls[0]
        assert "dfp_cia_aberta_" in urls[1]
        assert "fre_cia_aberta_" in urls[2]

    def test_get_url_docs_with_none_returns_all(self, url_docs):
        urls = url_docs.get_url_docs(None)

        assert len(urls) == 7
