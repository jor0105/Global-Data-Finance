from datetime import date
from decimal import Decimal

import pytest

from src.brazil.dados_b3.historical_quotes.infra import CotahistParser


class TestCotahistParser:
    """Test suite for COTAHIST parser."""

    @pytest.fixture
    def parser(self):
        return CotahistParser()

    @pytest.fixture
    def sample_quote_line(self):
        """Sample line from COTAHIST file (type 01 - quote record)."""
        # This is a simplified example - real lines are 245 bytes
        # Format: TIPREG(2) + DATA(8) + CODBDI(2) + CODNEG(12) + TPMERC(3) + ...
        line = "01"  # TIPREG
        line += "20231215"  # DATA (2023-12-15)
        line += "02"  # CODBDI
        line += "PETR4       "  # CODNEG (padded to 12)
        line += "010"  # TPMERC (market type - cash)
        line += "PETROBRAS   "  # NOMRES (padded to 12)
        line += "ON        "  # ESPECI (padded to 10)
        line += "       "  # PRAZOT (7 spaces)
        line += "BRL"  # MODREF (3)
        line += "0000000003150"  # PREABE (31.50)
        line += "0000000003200"  # PREMAX (32.00)
        line += "0000000003100"  # PREMIN (31.00)
        line += "0000000003150"  # PREMED (31.50)
        line += "0000000003180"  # PREULT (31.80)
        line += "0000000003179"  # PREOFC (31.79)
        line += "0000000003181"  # PREOFV (31.81)
        line += "12345"  # TOTNEG (5)
        line += "000000000100000000"  # QUATOT (18)
        line += "000000003180000000"  # VOLTOT (18, format V99)
        line += "0000000003180"  # PREEXE (13)
        line += "1"  # INDOPC (1)
        line += "00000000"  # DATVEN (8)
        line += "0000001"  # FATCOT (7)
        line += "0000000003185"  # PTOEXE (13)
        line += "BRPETRACNOR9"  # CODISI (12)
        line += "123"  # DISMES (3)

        # Pad to 245 bytes
        line = line.ljust(245)
        return line

    def test_parse_header_returns_none(self, parser):
        """Header lines (type 00) should return None."""
        header_line = "00COTAHIST.2023BOVESPA " + " " * 220
        result = parser.parse_line(header_line, {"010"})
        assert result is None

    def test_parse_trailer_returns_none(self, parser):
        """Trailer lines (type 99) should return None."""
        trailer_line = "9912345" + " " * 238
        result = parser.parse_line(trailer_line, {"010"})
        assert result is None

    def test_parse_quote_line_with_matching_tpmerc(self, parser, sample_quote_line):
        """Quote lines with matching TPMERC should be parsed."""
        result = parser.parse_line(sample_quote_line, {"010"})

        assert result is not None
        assert result["tpmerc"] == "010"
        assert result["codneg"] == "PETR4"
        assert result["data_pregao"] == date(2023, 12, 15)
        assert result["preult"] == Decimal("31.80")
        assert result["preabe"] == Decimal("31.50")
        assert result["premax"] == Decimal("32.00")
        assert result["premin"] == Decimal("31.00")
        assert result["totneg"] == 12345

    def test_parse_quote_line_with_non_matching_tpmerc(self, parser, sample_quote_line):
        """Quote lines with non-matching TPMERC should return None."""
        result = parser.parse_line(sample_quote_line, {"070", "080"})  # Options only
        assert result is None

    def test_parse_decimal_v99(self, parser):
        """Test decimal conversion with 2 implied decimal places."""
        assert parser._parse_decimal_v99("0000001234567") == Decimal("12345.67")
        assert parser._parse_decimal_v99("0000000000100") == Decimal("1.00")
        assert parser._parse_decimal_v99("0000000000000") == Decimal("0.00")
        assert parser._parse_decimal_v99("") == Decimal("0.00")

    def test_parse_date(self, parser):
        """Test date parsing in YYYYMMDD format."""
        assert parser._parse_date("20231215") == date(2023, 12, 15)
        assert parser._parse_date("20240101") == date(2024, 1, 1)
        assert parser._parse_date("00000000") is None
        assert parser._parse_date("") is None

    def test_parse_int(self, parser):
        """Test integer parsing."""
        assert parser._parse_int("12345") == 12345
        assert parser._parse_int("00001") == 1
        assert parser._parse_int("") == 0
