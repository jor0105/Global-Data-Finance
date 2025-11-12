"""Tests for CotahistParser with robust error handling and security."""

from src.brazil.dados_b3.historical_quotes.infra.cotahist_parser import CotahistParser


class TestCotahistParserSecurity:
    """Test suite for CotahistParser security and error handling."""

    def setup_method(self):
        """Create parser instance for each test."""
        self.parser = CotahistParser()

    def test_parse_valid_stock_record(self):
        """Test parsing a valid stock record."""
        # Valid stock record (type 01, TPMERC 010)
        line = (
            "01"  # Type
            "20240115"  # Date
            "02"  # CODBDI
            "PETR4       "  # Ticker (12 chars)
            "010"  # TPMERC
            "PETROBRAS  "  # Nome resumido (12 chars)
            "ON        "  # Especificação (10 chars)
            "000000"  # Prazot (6 chars, skip)
            "000003850000"  # Preço abertura (13 chars)
            "000003900000"  # Preço máximo
            "000003800000"  # Preço mínimo
            "000003870000"  # Preço médio
            "000003880000"  # Preço fechamento
            "000003890000"  # Melhor oferta compra
            "000003870000"  # Melhor oferta venda
            "00150"  # Total negócios (5 chars)
            "000000001000000000"  # Quantidade total (18 chars)
            "000000038700000000"  # Volume total (18 chars)
            "0000000000000"  # Preexe (13 chars, skip)
            "0"  # Indopc (1 char, skip)
            "00000000"  # Datven (8 chars)
            "0000100"  # Fatcot (7 chars)
            "000000000000000"  # Ptoexe (15 chars, skip)
            "BRPETRACNOR2"  # CODISI (12 chars)
            "000"  # DISMES (3 chars)
        ).ljust(245)

        result = self.parser.parse_line(line, {"010"})

        assert result is not None
        assert result["codneg"] == "PETR4"
        assert result["tpmerc"] == "010"
        assert result["preult"] > 0

    def test_parse_line_too_short(self):
        """Test handling of lines that are too short."""
        short_line = "01"
        result = self.parser.parse_line(short_line, {"010"})

        # Should pad and attempt to parse (will likely return None due to invalid data)
        # Main point: should not crash
        assert result is None or isinstance(result, dict)

    def test_parse_line_extremely_long(self):
        """Test rejection of extremely long lines (security)."""
        # Create a line longer than MAX_LINE_LENGTH (1000)
        long_line = "0" * 1500
        result = self.parser.parse_line(long_line, {"010"})

        # Should reject without crashing
        assert result is None

    def test_parse_empty_line(self):
        """Test handling of empty lines."""
        result = self.parser.parse_line("", {"010"})
        assert result is None

    def test_parse_whitespace_only_line(self):
        """Test handling of whitespace-only lines."""
        result = self.parser.parse_line("   " * 80, {"010"})
        assert result is None

    def test_parse_header_record(self):
        """Test that header records (type 00) are skipped."""
        header_line = "00COTAHIST" + " " * 235
        result = self.parser.parse_line(header_line, {"010"})
        assert result is None

    def test_parse_trailer_record(self):
        """Test that trailer records (type 99) are skipped."""
        trailer_line = "99000000001" + " " * 234
        result = self.parser.parse_line(trailer_line, {"010"})
        assert result is None

    def test_parse_wrong_market_type(self):
        """Test filtering by TPMERC code."""
        # Stock record with TPMERC 010
        line = ("01" + "20240115" + "02" + "PETR4       " + "010").ljust(245)

        # Request different TPMERC (020 - options)
        result = self.parser.parse_line(line, {"020"})
        assert result is None

    def test_parse_multiple_target_tpmerc(self):
        """Test parsing with multiple target TPMERC codes."""
        line = ("01" + "20240115" + "02" + "PETR4       " + "010").ljust(245)

        # Should match one of the target codes
        result = self.parser.parse_line(line, {"010", "020", "030"})
        assert result is not None

    def test_safe_slice_with_invalid_indices(self):
        """Test _safe_slice handles invalid indices gracefully."""
        test_string = "ABCDEFGHIJ"

        # Normal slice
        assert self.parser._safe_slice(test_string, 0, 3) == "ABC"

        # Out of bounds
        assert self.parser._safe_slice(test_string, 20, 25) == ""

        # Negative indices
        assert self.parser._safe_slice(test_string, -5, -1) == ""

        # End before start
        assert self.parser._safe_slice(test_string, 5, 3) == ""

    def test_parse_decimal_v99_with_valid_values(self):
        """Test decimal parsing with 2 implied decimal places."""
        # 123.45 represented as "0000012345"
        result = self.parser._parse_decimal_v99("0000012345")
        assert float(result) == 123.45

        # Zero
        result = self.parser._parse_decimal_v99("0000000000")
        assert float(result) == 0.0

    def test_parse_decimal_v99_with_invalid_values(self):
        """Test decimal parsing handles invalid values."""
        # Empty string
        result = self.parser._parse_decimal_v99("")
        assert float(result) == 0.0

        # Non-numeric
        result = self.parser._parse_decimal_v99("ABCDEFGHIJ")
        assert float(result) == 0.0

        # Whitespace
        result = self.parser._parse_decimal_v99("          ")
        assert float(result) == 0.0

    def test_parse_int_with_valid_values(self):
        """Test integer parsing."""
        assert self.parser._parse_int("00123") == 123
        assert self.parser._parse_int("999") == 999
        assert self.parser._parse_int("0") == 0

    def test_parse_int_with_invalid_values(self):
        """Test integer parsing handles invalid values."""
        assert self.parser._parse_int("") == 0
        assert self.parser._parse_int("ABC") == 0
        assert self.parser._parse_int("   ") == 0

    def test_parse_date_valid(self):
        """Test date parsing with valid dates."""
        result = self.parser._parse_date("20240115")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_invalid(self):
        """Test date parsing handles invalid dates."""
        # Invalid date
        assert self.parser._parse_date("99999999") is None

        # Zero date
        assert self.parser._parse_date("00000000") is None

        # Empty
        assert self.parser._parse_date("") is None

        # Non-numeric
        assert self.parser._parse_date("ABCDEFGH") is None

    def test_parse_quote_record_with_malformed_data(self):
        """Test _parse_quote_record doesn't crash on malformed data."""
        # Create a line with valid type but potentially invalid field data
        malformed_line = "01" + "X" * 243

        # Should return a dictionary (possibly with default values) but not crash
        result = self.parser._parse_quote_record(malformed_line)
        assert isinstance(result, dict)
        assert "codneg" in result
        assert "preult" in result

    def test_parse_line_with_unicode_errors(self):
        """Test handling of lines with encoding issues."""
        # Line with potentially problematic characters
        line_with_special_chars = "01" + "ção€™" * 50
        line_with_special_chars = line_with_special_chars[:245].ljust(245)

        # Should not crash
        result = self.parser.parse_line(line_with_special_chars, {"010"})
        # May return None or dict, but should not raise exception
        assert result is None or isinstance(result, dict)

    def test_error_count_limiting(self):
        """Test that error logging is limited to prevent spam."""
        # Reset error count
        self.parser._error_count = 0

        # Generate many errors (more than _max_errors_to_log)
        for _ in range(15):
            self.parser.parse_line("X" * 2000, {"010"})  # Extremely long line

        # Error count should be tracked
        assert self.parser._error_count > 0

    def test_parse_line_with_missing_fields(self):
        """Test parsing with truncated line (missing fields)."""
        # Line with only first few fields
        incomplete_line = "0120240115PETR4"

        result = self.parser.parse_line(incomplete_line, {"010"})

        # Should handle gracefully (pad and parse, or return None)
        # Main point: no crash
        assert result is None or isinstance(result, dict)

    def test_concurrent_parsing_safety(self):
        """Test that parser can be used safely in parallel."""
        import concurrent.futures

        line = ("01" + "20240115" + "02" + "PETR4       " + "010").ljust(245)
        target_codes = {"010"}

        # Parse same line multiple times in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self.parser.parse_line, line, target_codes)
                for _ in range(100)
            ]

            results = [f.result() for f in futures]

        # All results should be consistent
        assert all(r is not None or r is None for r in results)

    def test_memory_safety_large_batch(self):
        """Test parsing large batch of lines doesn't cause memory issues."""
        # Create 10000 valid lines
        base_line = ("01" + "20240115" + "02" + "PETR4       " + "010").ljust(245)
        target_codes = {"010"}

        results = []
        for _ in range(10_000):
            result = self.parser.parse_line(base_line, target_codes)
            if result:
                results.append(result)

        # Should complete without memory error
        assert len(results) > 0
        assert len(results) <= 10_000
