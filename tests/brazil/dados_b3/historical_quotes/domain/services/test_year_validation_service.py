"""Comprehensive tests for YearValidationService domain service.

This test suite ensures complete coverage of all success and error paths
in the YearValidationService class.
"""

from datetime import date
from unittest.mock import patch

import pytest

from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    InvalidFirstYear,
    InvalidLastYear,
)
from src.brazil.dados_b3.historical_quotes.domain.services.year_validation_service import (
    YearValidationService,
)
from src.brazil.dados_b3.historical_quotes.domain.value_objects.year_range import (
    YearRange,
)


class TestGetCurrentYear:
    """Test get_current_year method."""

    def test_returns_current_year(self):
        """Should return the current year."""
        result = YearValidationService.get_current_year()
        expected = date.today().year

        assert result == expected
        assert isinstance(result, int)

    @patch(
        "src.brazil.dados_b3.historical_quotes.domain.services.year_validation_service.date"
    )
    def test_uses_date_today(self, mock_date):
        """Should use date.today() to get current year."""
        mock_date.today.return_value.year = 2025
        result = YearValidationService.get_current_year()

        assert result == 2025
        mock_date.today.assert_called_once()


class TestGetMinYear:
    """Test get_min_year method."""

    def test_returns_1986(self):
        """Should return 1986 as minimum year for B3 COTAHIST data."""
        result = YearValidationService.get_min_year()

        assert result == 1986
        assert isinstance(result, int)

    def test_matches_class_constant(self):
        """Should match MIN_YEAR class constant."""
        result = YearValidationService.get_min_year()
        assert result == YearValidationService.MIN_YEAR


class TestValidateAndCreateYearRange:
    """Test validate_and_create_year_range method - Success cases."""

    def test_valid_year_range_returns_year_range_object(self):
        """Should return YearRange object for valid range."""
        result = YearValidationService.validate_and_create_year_range(2020, 2023)

        assert isinstance(result, YearRange)
        assert result.initial_year == 2020
        assert result.last_year == 2023

    def test_minimum_year_to_current_year(self):
        """Should accept range from minimum year to current year."""
        current_year = date.today().year
        result = YearValidationService.validate_and_create_year_range(
            1986, current_year
        )

        assert isinstance(result, YearRange)
        assert result.initial_year == 1986
        assert result.last_year == current_year

    def test_single_year_range(self):
        """Should accept a range where initial_year equals last_year."""
        result = YearValidationService.validate_and_create_year_range(2023, 2023)

        assert isinstance(result, YearRange)
        assert result.initial_year == 2023
        assert result.last_year == 2023

    def test_recent_years_range(self):
        """Should accept range of recent years."""
        result = YearValidationService.validate_and_create_year_range(2020, 2024)

        assert isinstance(result, YearRange)
        assert result.span_years() == 5

    def test_full_historical_range(self):
        """Should accept the full historical range."""
        current_year = date.today().year
        result = YearValidationService.validate_and_create_year_range(
            1986, current_year
        )

        assert isinstance(result, YearRange)
        assert result.span_years() == current_year - 1986 + 1


class TestValidateAndCreateYearRangeInvalidFirstYear:
    """Test validate_and_create_year_range - InvalidFirstYear errors."""

    def test_initial_year_before_minimum_raises_error(self):
        """Should raise InvalidFirstYear when initial_year < 1986."""
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(1985, 2023)

    def test_initial_year_in_future_raises_error(self):
        """Should raise InvalidFirstYear when initial_year is in the future."""
        future_year = date.today().year + 10
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                future_year, future_year
            )

    def test_initial_year_not_integer_raises_error(self):
        """Should raise InvalidFirstYear when initial_year is not an integer."""
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range("2020", 2023)

        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(2020.5, 2023)

        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(None, 2023)

    def test_initial_year_zero_raises_error(self):
        """Should raise InvalidFirstYear for year zero."""
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(0, 2023)

    def test_initial_year_negative_raises_error(self):
        """Should raise InvalidFirstYear for negative years."""
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(-2020, 2023)


class TestValidateAndCreateYearRangeInvalidLastYear:
    """Test validate_and_create_year_range - InvalidLastYear errors."""

    def test_last_year_in_future_raises_error(self):
        """Should raise InvalidLastYear when last_year is in the future."""
        future_year = date.today().year + 1
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(2020, future_year)

    def test_last_year_before_initial_year_raises_error(self):
        """Should raise InvalidLastYear when last_year < initial_year."""
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(2023, 2020)

    def test_last_year_not_integer_raises_error(self):
        """Should raise InvalidLastYear when last_year is not an integer."""
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(2020, "2023")

        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(2020, 2023.5)

        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(2020, None)

    def test_last_year_much_earlier_than_initial_raises_error(self):
        """Should raise InvalidLastYear when last_year is much earlier."""
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(2020, 1990)


class TestIsValidYear:
    """Test is_valid_year method."""

    def test_current_year_is_valid(self):
        """Should return True for current year."""
        current_year = date.today().year
        assert YearValidationService.is_valid_year(current_year) is True

    def test_minimum_year_is_valid(self):
        """Should return True for minimum year (1986)."""
        assert YearValidationService.is_valid_year(1986) is True

    def test_year_between_min_and_current_is_valid(self):
        """Should return True for years between 1986 and current."""
        assert YearValidationService.is_valid_year(2000) is True
        assert YearValidationService.is_valid_year(2010) is True
        assert YearValidationService.is_valid_year(2020) is True

    def test_year_before_minimum_is_invalid(self):
        """Should return False for years before 1986."""
        assert YearValidationService.is_valid_year(1985) is False
        assert YearValidationService.is_valid_year(1900) is False
        assert YearValidationService.is_valid_year(1) is False

    def test_future_year_is_invalid(self):
        """Should return False for future years."""
        future_year = date.today().year + 1
        assert YearValidationService.is_valid_year(future_year) is False

    def test_non_integer_is_invalid(self):
        """Should return False for non-integer inputs."""
        assert YearValidationService.is_valid_year("2020") is False
        assert YearValidationService.is_valid_year(2020.5) is False
        assert YearValidationService.is_valid_year(None) is False
        assert YearValidationService.is_valid_year([2020]) is False

    def test_negative_year_is_invalid(self):
        """Should return False for negative years."""
        assert YearValidationService.is_valid_year(-2020) is False

    def test_zero_is_invalid(self):
        """Should return False for year zero."""
        assert YearValidationService.is_valid_year(0) is False


class TestGetValidYearRangeDescription:
    """Test get_valid_year_range_description method."""

    def test_returns_string(self):
        """Should return a string description."""
        result = YearValidationService.get_valid_year_range_description()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_minimum_year(self):
        """Should contain minimum year (1986) in description."""
        result = YearValidationService.get_valid_year_range_description()

        assert "1986" in result

    def test_contains_current_year(self):
        """Should contain current year in description."""
        result = YearValidationService.get_valid_year_range_description()
        current_year = str(date.today().year)

        assert current_year in result

    def test_is_human_readable(self):
        """Should be human-readable."""
        result = YearValidationService.get_valid_year_range_description()

        # Should contain words that make it readable
        assert "Valid" in result or "year" in result.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("src.brazil.dados_b3.historical_quotes.domain.value_objects.year_range.date")
    @patch(
        "src.brazil.dados_b3.historical_quotes.domain.services.year_validation_service.date"
    )
    def test_validates_against_mocked_current_year(
        self, mock_service_date, mock_vo_date
    ):
        """Should validate correctly even when current year is mocked."""
        mock_service_date.today.return_value.year = 2030
        mock_vo_date.today.return_value.year = 2030

        # Should accept year up to 2030
        result = YearValidationService.validate_and_create_year_range(2020, 2030)
        assert result.last_year == 2030

        # Should reject year 2031
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(2020, 2031)

    def test_validates_at_exact_boundaries(self):
        """Should correctly validate at exact boundary values."""
        current_year = date.today().year

        # At minimum boundary
        result = YearValidationService.validate_and_create_year_range(1986, 1986)
        assert result.initial_year == 1986

        # At maximum boundary
        result = YearValidationService.validate_and_create_year_range(
            current_year, current_year
        )
        assert result.last_year == current_year

    def test_large_year_range(self):
        """Should handle large year ranges correctly."""
        current_year = date.today().year
        result = YearValidationService.validate_and_create_year_range(
            1986, current_year
        )

        assert result.span_years() > 30  # At least 30+ years
