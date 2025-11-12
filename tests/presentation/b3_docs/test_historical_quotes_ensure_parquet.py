"""Tests for HistoricalQuotes _ensure_parquet_extension method."""

from src.presentation.b3_docs.historical_quotes import HistoricalQuotes


class TestEnsureParquetExtension:
    """Tests for the _ensure_parquet_extension helper method."""

    def test_adds_parquet_extension_when_missing(self):
        """Test that .parquet extension is added when not present."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("my_file")
        assert result == "my_file.parquet"

    def test_does_not_duplicate_parquet_extension(self):
        """Test that .parquet extension is not duplicated."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("my_file.parquet")
        assert result == "my_file.parquet"

    def test_handles_uppercase_parquet_extension(self):
        """Test that uppercase .PARQUET is recognized."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("my_file.PARQUET")
        assert result == "my_file.PARQUET"

    def test_handles_mixed_case_parquet_extension(self):
        """Test that mixed case .Parquet is recognized."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("my_file.Parquet")
        assert result == "my_file.Parquet"

    def test_handles_filename_with_multiple_dots(self):
        """Test filename with multiple dots."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("my.file.v2")
        assert result == "my.file.v2.parquet"

    def test_handles_filename_with_dots_and_parquet(self):
        """Test filename with dots that already has .parquet."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("my.file.v2.parquet")
        assert result == "my.file.v2.parquet"

    def test_handles_empty_string(self):
        """Test with empty string - should add .parquet."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("")
        assert result == ".parquet"

    def test_handles_whitespace(self):
        """Test with whitespace - should add .parquet."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("   ")
        assert result == "   .parquet"


class TestEnsureParquetExtensionRealWorldExamples:
    """Test real-world usage examples."""

    def test_example_simple_name(self):
        """Test simple filename without extension."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("cotahist_extracted")
        assert result == "cotahist_extracted.parquet"

    def test_example_with_year_range(self):
        """Test filename with year range."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("b3_stocks_2020_2023")
        assert result == "b3_stocks_2020_2023.parquet"

    def test_example_with_asset_types(self):
        """Test filename with asset type information."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("acoes_etf_opcoes")
        assert result == "acoes_etf_opcoes.parquet"

    def test_example_user_already_provided_extension(self):
        """Test when user explicitly provides .parquet extension."""
        hq = HistoricalQuotes()
        result = hq._ensure_parquet_extension("my_data.parquet")
        assert result == "my_data.parquet"
        # Important: should NOT become "my_data.parquet.parquet"
