from src.brazil.dados_b3.historical_quotes.domain import DocsToExtractor


class TestDocsToExtractor:
    def test_create_docs_to_extractor_with_all_fields(self):
        path_of_docs = "/path/to/docs"
        set_assets = {"ações", "etf"}
        range_years = range(2020, 2024)
        destination_path = "/path/to/output"
        set_documents = {"COTAHIST_A2020.ZIP", "COTAHIST_A2021.ZIP"}
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
            set_documents_to_download=set_documents,
        )
        assert docs.path_of_docs == path_of_docs
        assert docs.set_assets == set_assets
        assert docs.range_years == range_years
        assert docs.destination_path == destination_path
        assert docs.set_documents_to_download == set_documents

    def test_create_docs_to_extractor_with_default_documents(self):
        path_of_docs = "/path/to/docs"
        set_assets = {"ações"}
        range_years = range(2020, 2021)
        destination_path = "/path/to/output"
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
        )
        assert docs.set_documents_to_download == set()

    def test_docs_to_extractor_with_empty_set_assets(self):
        path_of_docs = "/path/to/docs"
        set_assets = set()
        range_years = range(2020, 2024)
        destination_path = "/path/to/output"
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
        )
        assert docs.set_assets == set()

    def test_docs_to_extractor_with_single_year_range(self):
        path_of_docs = "/path/to/docs"
        set_assets = {"ações"}
        range_years = range(2020, 2021)
        destination_path = "/path/to/output"
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
        )
        assert list(docs.range_years) == [2020]

    def test_docs_to_extractor_with_empty_range(self):
        path_of_docs = "/path/to/docs"
        set_assets = {"ações"}
        range_years = range(2020, 2020)
        destination_path = "/path/to/output"
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
        )
        assert list(docs.range_years) == []

    def test_docs_to_extractor_is_dataclass(self):
        path_of_docs = "/path/to/docs"
        set_assets = {"ações"}
        range_years = range(2020, 2024)
        destination_path = "/path/to/output"
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
        )
        assert "DocsToExtractor" in repr(docs)
        assert path_of_docs in repr(docs)

    def test_docs_to_extractor_fields_are_mutable(self):
        docs = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2024),
            destination_path="/path/to/output",
        )
        docs.path_of_docs = "/new/path"
        docs.set_assets = {"etf", "opções"}
        docs.range_years = range(2021, 2023)
        docs.destination_path = "/new/output"
        docs.set_documents_to_download = {"new_doc.ZIP"}
        assert docs.path_of_docs == "/new/path"
        assert docs.set_assets == {"etf", "opções"}
        assert docs.range_years == range(2021, 2023)
        assert docs.destination_path == "/new/output"
        assert docs.set_documents_to_download == {"new_doc.ZIP"}

    def test_docs_to_extractor_with_special_characters_in_paths(self):
        path_of_docs = "/path/with spaces/and-dashes_underscores"
        destination_path = "/output/path/with.dots/and@symbols"
        set_assets = {"ações"}
        range_years = range(2020, 2021)
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
        )
        assert docs.path_of_docs == path_of_docs
        assert docs.destination_path == destination_path

    def test_docs_to_extractor_with_multiple_asset_classes(self):
        path_of_docs = "/path/to/docs"
        set_assets = {
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        }
        range_years = range(2020, 2024)
        destination_path = "/path/to/output"
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
        )
        assert docs.set_assets == set_assets
        assert len(docs.set_assets) == 7

    def test_docs_to_extractor_with_large_document_set(self):
        path_of_docs = "/path/to/docs"
        set_assets = {"ações"}
        range_years = range(1986, 2025)
        destination_path = "/path/to/output"
        set_documents = {f"COTAHIST_A{year}.ZIP" for year in range(1986, 2025)}
        docs = DocsToExtractor(
            path_of_docs=path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
            set_documents_to_download=set_documents,
        )
        assert len(docs.set_documents_to_download) == 39
        assert "COTAHIST_A1986.ZIP" in docs.set_documents_to_download
        assert "COTAHIST_A2024.ZIP" in docs.set_documents_to_download

    def test_docs_to_extractor_equality(self):
        docs1 = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2024),
            destination_path="/path/to/output",
        )
        docs2 = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2024),
            destination_path="/path/to/output",
        )
        assert docs1 == docs2

    def test_docs_to_extractor_inequality(self):
        docs1 = DocsToExtractor(
            path_of_docs="/path/to/docs",
            set_assets={"ações"},
            range_years=range(2020, 2024),
            destination_path="/path/to/output",
        )
        docs2 = DocsToExtractor(
            path_of_docs="/different/path",
            set_assets={"etf"},
            range_years=range(2021, 2023),
            destination_path="/different/output",
        )
        assert docs1 != docs2
