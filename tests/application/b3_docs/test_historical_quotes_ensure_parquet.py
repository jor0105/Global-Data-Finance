from datafinance.application import HistoricalQuotesB3


class TestEnsureParquetExtension:
    def test_adds_parquet_extension_when_missing(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("my_file")
        assert result == "my_file.parquet"

    def test_does_not_duplicate_parquet_extension(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("my_file.parquet")
        assert result == "my_file.parquet"

    def test_handles_uppercase_parquet_extension(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("my_file.PARQUET")
        assert result == "my_file.PARQUET"

    def test_handles_mixed_case_parquet_extension(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("my_file.Parquet")
        assert result == "my_file.Parquet"

    def test_handles_filename_with_multiple_dots(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("my.file.v2")
        assert result == "my.file.v2.parquet"

    def test_handles_filename_with_dots_and_parquet(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("my.file.v2.parquet")
        assert result == "my.file.v2.parquet"

    def test_handles_empty_string(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("")
        assert result == ".parquet"

    def test_handles_whitespace(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("   ")
        assert result == "   .parquet"


class TestEnsureParquetExtensionRealWorldExamples:
    def test_example_simple_name(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("cotahist_extracted")
        assert result == "cotahist_extracted.parquet"

    def test_example_with_year_range(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("b3_stocks_2020_2023")
        assert result == "b3_stocks_2020_2023.parquet"

    def test_example_with_asset_types(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("acoes_etf_opcoes")
        assert result == "acoes_etf_opcoes.parquet"

    def test_example_user_already_provided_extension(self):
        hq = HistoricalQuotesB3()
        result = hq._ensure_parquet_extension("my_data.parquet")
        assert result == "my_data.parquet"
