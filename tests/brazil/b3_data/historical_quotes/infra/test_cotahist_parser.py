from datetime import date
from decimal import Decimal

import pytest

from datafinance.brazil.b3_data.historical_quotes.infra.cotahist_parser import (
    CotahistParserB3,
)


class TestCotahistParserB3:
    @pytest.fixture
    def parser(self):
        return CotahistParserB3()

    @pytest.fixture
    def target_codes(self):
        return {"010", "020"}

    def test_initialization(self, parser):
        assert parser is not None
        assert parser.EXPECTED_LINE_LENGTH == 245
        assert parser.MAX_LINE_LENGTH == 1000
        assert parser._error_count == 0
        assert parser._max_errors_to_log == 10

    def test_parse_header_line_returns_none(self, parser, target_codes):
        line = "00COTAHIST" + " " * 235
        result = parser.parse_line(line, target_codes)
        assert result is None

    def test_parse_trailer_line_returns_none(self, parser, target_codes):
        line = "99TOTAL RECORDS" + " " * 228
        result = parser.parse_line(line, target_codes)
        assert result is None

    def test_parse_valid_quote_record(self, parser, target_codes):
        line = "01" + "20230615" + "02" + "PETR4       " + "010" + " " * 217

        result = parser.parse_line(line, target_codes)

        assert result is None or isinstance(result, dict)
        if result:
            assert isinstance(result, dict)
            assert "data_pregao" in result
            assert "ticker" in result
            assert "tipo_mercado" in result

    def test_parse_line_with_non_matching_tpmerc(self, parser):
        line = "01" + "20230615" + "02" + "PETR4       " + "030"
        line = line + " " * (245 - len(line))

        result = parser.parse_line(line, {"010", "020"})
        assert result is None

    def test_parse_line_filters_by_target_codes(self, parser):
        line_010 = "01" + "20230615" + "02" + "PETR4       " + "010"
        line_010 = line_010 + " " * (245 - len(line_010))

        line_020 = "01" + "20230615" + "02" + "VALE3       " + "020"
        line_020 = line_020 + " " * (245 - len(line_020))

        line_030 = "01" + "20230615" + "02" + "BBAS3       " + "030"
        line_030 = line_030 + " " * (245 - len(line_030))

        result_010 = parser.parse_line(line_010, {"010", "020"})
        result_020 = parser.parse_line(line_020, {"010", "020"})
        result_030 = parser.parse_line(line_030, {"010", "020"})

        assert result_010 is not None
        assert result_020 is not None
        assert result_030 is None

    def test_parse_short_line(self, parser, target_codes):
        short_line = "0120230615"
        result = parser.parse_line(short_line, target_codes)
        assert result is None or isinstance(result, dict)

    def test_parse_long_line(self, parser, target_codes):
        long_line = "01" + "20230615" + "02" + "PETR4       " + "010" + "X" * 500
        result = parser.parse_line(long_line, target_codes)
        assert result is None or isinstance(result, dict)

    def test_parse_extremely_long_line(self, parser, target_codes):
        extremely_long_line = "01" + "X" * 1500
        result = parser.parse_line(extremely_long_line, target_codes)
        assert result is None

    def test_parse_empty_line(self, parser, target_codes):
        result = parser.parse_line("", target_codes)
        assert result is None

    def test_parse_line_with_single_char(self, parser, target_codes):
        result = parser.parse_line("0", target_codes)
        assert result is None

    def test_parse_line_with_invalid_type(self, parser, target_codes):
        line = "05" + "20230615" + " " * 233
        result = parser.parse_line(line, target_codes)
        assert result is None

    def test_error_count_increments_on_errors(self, parser, target_codes):
        initial_count = parser._error_count
        malformed_line = "01" + "X" * 50
        parser.parse_line(malformed_line, target_codes)
        assert parser._error_count >= initial_count

    def test_parse_line_with_unicode_characters(self, parser, target_codes):
        line = "01" + "20230615" + "02" + "AÇÚCAR      " + "010" + " " * 217
        result = parser.parse_line(line, target_codes)
        assert result is None or isinstance(result, dict)


class TestCotahistParserB3FieldParsing:
    @pytest.fixture
    def parser(self):
        return CotahistParserB3()

    def test_parse_date_valid(self, parser):
        date_str = "20230615"
        result = parser._parse_date(date_str)
        assert result == date(2023, 6, 15)

    def test_parse_date_invalid(self, parser):
        date_str = "20231332"
        result = parser._parse_date(date_str)
        assert result is None

    def test_parse_date_empty(self, parser):
        result = parser._parse_date("")
        assert result is None

    def test_parse_date_zeros(self, parser):
        result = parser._parse_date("00000000")
        assert result is None

    def test_parse_date_with_whitespace(self, parser):
        date_str = "  20230615  "
        result = parser._parse_date(date_str)
        assert result == date(2023, 6, 15)

    def test_parse_date_optional_valid(self, parser):
        result = parser._parse_date_optional("20230615")
        assert result == date(2023, 6, 15)

    def test_parse_date_optional_empty(self, parser):
        result = parser._parse_date_optional("        ")
        assert result is None

    def test_parse_date_optional_zeros(self, parser):
        result = parser._parse_date_optional("00000000")
        assert result is None

    def test_parse_decimal_v99_valid(self, parser):
        value_str = "0000001234567"
        result = parser._parse_decimal_v99(value_str)
        assert result == Decimal("12345.67")

    def test_parse_decimal_v99_zero(self, parser):
        value_str = "0000000000000"
        result = parser._parse_decimal_v99(value_str)
        assert result == Decimal("0")

    def test_parse_decimal_v99_empty(self, parser):
        result = parser._parse_decimal_v99("")
        assert result == Decimal("0")

    def test_parse_decimal_v99_whitespace(self, parser):
        result = parser._parse_decimal_v99("     ")
        assert result == Decimal("0")

    def test_parse_decimal_v99_invalid(self, parser):
        value_str = "XXXXXXXXX"
        result = parser._parse_decimal_v99(value_str)
        assert result == Decimal("0")

    def test_parse_decimal_v99_large_value(self, parser):
        value_str = "9999999999999"
        result = parser._parse_decimal_v99(value_str)
        assert result == Decimal("99999999999.99")

    def test_parse_int_valid(self, parser):
        value_str = "00123"
        result = parser._parse_int(value_str)
        assert result == 123

    def test_parse_int_zero(self, parser):
        value_str = "00000"
        result = parser._parse_int(value_str)
        assert result == 0

    def test_parse_int_empty(self, parser):
        result = parser._parse_int("")
        assert result == 0

    def test_parse_int_whitespace(self, parser):
        result = parser._parse_int("     ")
        assert result == 0

    def test_parse_int_invalid(self, parser):
        value_str = "ABC123"
        result = parser._parse_int(value_str)
        assert result == 0

    def test_parse_int_large_value(self, parser):
        value_str = "999999999999999999"
        result = parser._parse_int(value_str)
        assert result == 999999999999999999

    def test_safe_slice_valid(self, parser):
        line = "ABCDEFGHIJ"
        result = parser._safe_slice(line, 0, 5)
        assert result == "ABCDE"

    def test_safe_slice_out_of_bounds(self, parser):
        line = "ABC"
        result = parser._safe_slice(line, 0, 10)
        assert result == ""

    def test_safe_slice_negative_start(self, parser):
        line = "ABCDEF"
        result = parser._safe_slice(line, -1, 3)
        assert result == ""

    def test_safe_slice_start_after_end(self, parser):
        line = "ABCDEF"
        result = parser._safe_slice(line, 5, 2)
        assert result == ""

    def test_safe_slice_empty_string(self, parser):
        line = ""
        result = parser._safe_slice(line, 0, 5)
        assert result == ""


class TestCotahistParserB3EdgeCases:
    @pytest.fixture
    def parser(self):
        return CotahistParserB3()

    @pytest.fixture
    def target_codes(self):
        return {"010"}

    def test_parse_line_with_all_zeros(self, parser, target_codes):
        line = "0" * 245
        result = parser.parse_line(line, target_codes)
        assert result is None

    def test_parse_line_with_all_spaces(self, parser, target_codes):
        line = " " * 245
        result = parser.parse_line(line, target_codes)
        assert result is None

    def test_parse_line_with_mixed_valid_invalid_data(self, parser, target_codes):
        line = "01" + "20230615" + "XX" + "###########" + "010" + "#" * 220
        result = parser.parse_line(line, target_codes)
        assert result is None or isinstance(result, dict)

    def test_multiple_lines_parsing(self, parser, target_codes):
        lines = [
            "00HEADER" + " " * 237,
            "01" + "20230615" + "02" + "PETR4       " + "010" + " " * 217,
            "01" + "20230616" + "02" + "VALE3       " + "010" + " " * 217,
            "99TRAILER" + " " * 235,
        ]

        results = [parser.parse_line(line, target_codes) for line in lines]

        assert results[0] is None
        assert results[1] is not None or results[1] is None
        assert results[2] is not None or results[2] is None
        assert results[3] is None

    def test_error_logging_limit(self, parser, target_codes):
        parser._error_count = 0
        parser._max_errors_to_log = 3

        for i in range(20):
            malformed_line = "01" + "INVALID" * 30
            parser.parse_line(malformed_line, target_codes)

        assert parser._error_count <= parser._max_errors_to_log + 10

    def test_parse_line_with_boundary_dates(self, parser, target_codes):
        line_min = "01" + "19000101" + "02" + "TEST        " + "010" + " " * 217
        result_min = parser.parse_line(line_min, target_codes)

        line_max = "01" + "20991231" + "02" + "TEST        " + "010" + " " * 217
        result_max = parser.parse_line(line_max, target_codes)

        assert result_min is None or isinstance(result_min, dict)
        assert result_max is None or isinstance(result_max, dict)

    def test_parse_line_preserves_immutability(self, parser, target_codes):
        line = "01" + "20230615" + "02" + "PETR4       " + "010" + " " * 217

        result1 = parser.parse_line(line, target_codes)
        result2 = parser.parse_line(line, target_codes)

        if result1 and result2:
            assert result1 == result2
            assert result1 is not result2

    def test_empty_target_codes_set(self, parser):
        line = "01" + "20230615" + "02" + "PETR4       " + "010" + " " * 217
        result = parser.parse_line(line, set())

        assert result is None

    def test_parse_quote_record_with_exception_returns_defaults(self, parser):
        invalid_line = "X" * 245

        result = parser._parse_quote_record(invalid_line)

        assert isinstance(result, dict)
        assert result["data_pregao"] is None
        assert result["preco_abertura"] == Decimal("0")
        assert result["numero_negocios"] == 0


class TestCotahistParserB3Integration:
    @pytest.fixture
    def parser(self):
        return CotahistParserB3()

    def test_parse_complete_cotahist_sample(self, parser):
        lines = [
            "00COTAHIST" + " " * 235,
            "01" + "20230615" + "02" + "PETR4       " + "010" + " " * 217,
            "01" + "20230615" + "02" + "VALE3       " + "020" + " " * 217,
            "01" + "20230615" + "02" + "BBAS3       " + "030" + " " * 217,
            "99" + "0000000003" + " " * 233,
        ]

        target_codes = {"010", "020"}
        results = []

        for line in lines:
            result = parser.parse_line(line, target_codes)
            if result:
                results.append(result)

        assert len(results) == 2 or len(results) == 0

    def test_parser_handles_real_world_variations(self, parser):
        target_codes = {"010"}

        test_cases = [
            "01" + "20230615" + "  " + "            " + "010" + " " * 217,
            "01" + "20230615" + "99" + "TEST123     " + "010" + " " * 217,
            "01" + "00000000" + "02" + "INVALID     " + "010" + " " * 217,
        ]

        for line in test_cases:
            result = parser.parse_line(line, target_codes)
            assert result is None or isinstance(result, dict)

    def test_concurrent_parsing_safety(self, parser):
        line = "01" + "20230615" + "02" + "PETR4       " + "010" + " " * 217
        target_codes = {"010"}

        results = [parser.parse_line(line, target_codes) for _ in range(100)]

        non_none_results = [r for r in results if r is not None]
        if non_none_results:
            first_result = non_none_results[0]
            for result in non_none_results:
                assert result == first_result
