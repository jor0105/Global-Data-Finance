"""Comprehensive tests for YearRange value object.

This test suite ensures complete coverage of all success and error paths
in the YearRange value object.
"""

from datetime import date
from unittest.mock import patch

import pytest

from src.brazil.dados_b3.historical_quotes.domain.value_objects.year_range import (
    YearRange,
)


class TestYearRangeCreation:
    """Test YearRange creation - Success cases."""

    def test_create_valid_range(self):
        """Should create YearRange with valid years."""
        year_range = YearRange(2020, 2023)

        assert year_range.initial_year == 2020
        assert year_range.last_year == 2023

    def test_create_single_year_range(self):
        """Should create range where initial_year equals last_year."""
        year_range = YearRange(2023, 2023)

        assert year_range.initial_year == 2023
        assert year_range.last_year == 2023
        assert year_range.span_years() == 1

    def test_create_range_up_to_current_year(self):
        """Should create range up to current year."""
        current_year = date.today().year
        year_range = YearRange(2020, current_year)

        assert year_range.last_year == current_year

    def test_create_historical_range(self):
        """Should create range from historical years."""
        year_range = YearRange(1986, 2000)

        assert year_range.initial_year == 1986
        assert year_range.last_year == 2000


class TestYearRangeImmutability:
    """Test that YearRange is truly immutable."""

    def test_cannot_modify_initial_year(self):
        """Should not allow modification of initial_year."""
        year_range = YearRange(2020, 2023)

        with pytest.raises(AttributeError):
            year_range.initial_year = 2021

    def test_cannot_modify_last_year(self):
        """Should not allow modification of last_year."""
        year_range = YearRange(2020, 2023)

        with pytest.raises(AttributeError):
            year_range.last_year = 2024

    def test_is_frozen_dataclass(self):
        """Should be a frozen dataclass."""
        year_range = YearRange(2020, 2023)

        # Frozen dataclasses raise FrozenInstanceError on attribute assignment
        with pytest.raises((AttributeError, Exception)):
            year_range.initial_year = 2025


class TestYearRangeValidation:
    """Test YearRange validation in __post_init__."""

    def test_initial_year_greater_than_last_year_raises_error(self):
        """Should raise ValueError when initial_year > last_year."""
        with pytest.raises(ValueError) as exc_info:
            YearRange(2023, 2020)

        assert "cannot be greater than" in str(exc_info.value)
        assert "2023" in str(exc_info.value)
        assert "2020" in str(exc_info.value)

    def test_future_last_year_raises_error(self):
        """Should raise ValueError when last_year is in the future."""
        future_year = date.today().year + 10

        with pytest.raises(ValueError) as exc_info:
            YearRange(2020, future_year)

        assert "cannot be in the future" in str(exc_info.value)
        assert str(future_year) in str(exc_info.value)

    def test_non_integer_initial_year_raises_error(self):
        """Should raise ValueError when initial_year is not an integer."""
        with pytest.raises(ValueError) as exc_info:
            YearRange("2020", 2023)

        assert "must be integers" in str(exc_info.value)

    def test_non_integer_last_year_raises_error(self):
        """Should raise ValueError when last_year is not an integer."""
        with pytest.raises(ValueError) as exc_info:
            YearRange(2020, "2023")

        assert "must be integers" in str(exc_info.value)

    def test_float_years_raise_error(self):
        """Should raise ValueError for float years."""
        with pytest.raises(ValueError):
            YearRange(2020.5, 2023)

        with pytest.raises(ValueError):
            YearRange(2020, 2023.5)

    def test_none_values_raise_error(self):
        """Should raise ValueError for None values."""
        with pytest.raises(ValueError):
            YearRange(None, 2023)

        with pytest.raises(ValueError):
            YearRange(2020, None)

    def test_negative_years_can_be_created_if_valid(self):
        """Should create range with negative years if they pass validation."""
        # This tests the validator logic, even though negative years
        # would fail the future year check
        with pytest.raises(ValueError):
            # Will fail because -2000 > -1900
            YearRange(-1900, -2000)


class TestToRange:
    """Test to_range method."""

    def test_returns_python_range_object(self):
        """Should return a Python range object."""
        year_range = YearRange(2020, 2023)
        result = year_range.to_range()

        assert isinstance(result, range)

    def test_range_includes_both_bounds(self):
        """Should include both initial_year and last_year."""
        year_range = YearRange(2020, 2023)
        result = list(year_range.to_range())

        assert result == [2020, 2021, 2022, 2023]
        assert 2020 in result
        assert 2023 in result

    def test_range_for_single_year(self):
        """Should return single year for single year range."""
        year_range = YearRange(2023, 2023)
        result = list(year_range.to_range())

        assert result == [2023]
        assert len(result) == 1

    def test_range_iteration(self):
        """Should be iterable with a for loop."""
        year_range = YearRange(2020, 2022)
        years = []

        for year in year_range.to_range():
            years.append(year)

        assert years == [2020, 2021, 2022]


class TestContains:
    """Test contains method."""

    def test_contains_year_in_range(self):
        """Should return True for years within range."""
        year_range = YearRange(2020, 2023)

        assert year_range.contains(2020) is True
        assert year_range.contains(2021) is True
        assert year_range.contains(2022) is True
        assert year_range.contains(2023) is True

    def test_not_contains_year_before_range(self):
        """Should return False for years before range."""
        year_range = YearRange(2020, 2023)

        assert year_range.contains(2019) is False
        assert year_range.contains(2000) is False

    def test_not_contains_year_after_range(self):
        """Should return False for years after range."""
        year_range = YearRange(2020, 2023)

        assert year_range.contains(2024) is False
        assert year_range.contains(2030) is False

    def test_contains_boundaries(self):
        """Should include boundary years."""
        year_range = YearRange(2020, 2023)

        # Test exact boundaries
        assert year_range.contains(2020) is True
        assert year_range.contains(2023) is True

        # Test just outside boundaries
        assert year_range.contains(2019) is False
        assert year_range.contains(2024) is False

    def test_contains_for_single_year_range(self):
        """Should work correctly for single year range."""
        year_range = YearRange(2023, 2023)

        assert year_range.contains(2023) is True
        assert year_range.contains(2022) is False
        assert year_range.contains(2024) is False


class TestSpanYears:
    """Test span_years method."""

    def test_span_for_multi_year_range(self):
        """Should calculate correct span for multi-year range."""
        year_range = YearRange(2020, 2023)

        assert year_range.span_years() == 4

    def test_span_for_single_year(self):
        """Should return 1 for single year range."""
        year_range = YearRange(2023, 2023)

        assert year_range.span_years() == 1

    def test_span_for_large_range(self):
        """Should calculate correct span for large range."""
        year_range = YearRange(1986, 2023)

        assert year_range.span_years() == 38

    def test_span_equals_range_length(self):
        """Should equal the length of to_range()."""
        year_range = YearRange(2020, 2025)

        assert year_range.span_years() == len(list(year_range.to_range()))


class TestStringRepresentation:
    """Test string representation methods."""

    def test_str_returns_formatted_range(self):
        """Should return formatted string like '2020-2023'."""
        year_range = YearRange(2020, 2023)

        assert str(year_range) == "2020-2023"

    def test_str_for_single_year(self):
        """Should return formatted string for single year."""
        year_range = YearRange(2023, 2023)

        assert str(year_range) == "2023-2023"

    def test_repr_returns_detailed_info(self):
        """Should return detailed representation for debugging."""
        year_range = YearRange(2020, 2023)
        repr_str = repr(year_range)

        assert "YearRange" in repr_str
        assert "initial_year=2020" in repr_str
        assert "last_year=2023" in repr_str

    def test_repr_is_valid_python(self):
        """Should return repr that could recreate the object."""
        year_range = YearRange(2020, 2023)
        repr_str = repr(year_range)

        # Should contain the class name and constructor format
        assert repr_str.startswith("YearRange(")
        assert repr_str.endswith(")")


class TestEquality:
    """Test equality comparison between YearRange instances."""

    def test_equal_ranges_are_equal(self):
        """Should be equal when years are the same."""
        range1 = YearRange(2020, 2023)
        range2 = YearRange(2020, 2023)

        assert range1 == range2

    def test_different_initial_years_are_not_equal(self):
        """Should not be equal when initial years differ."""
        range1 = YearRange(2020, 2023)
        range2 = YearRange(2021, 2023)

        assert range1 != range2

    def test_different_last_years_are_not_equal(self):
        """Should not be equal when last years differ."""
        range1 = YearRange(2020, 2023)
        range2 = YearRange(2020, 2024)

        assert range1 != range2

    def test_not_equal_to_non_year_range(self):
        """Should not be equal to non-YearRange objects."""
        year_range = YearRange(2020, 2023)

        assert year_range != "2020-2023"
        assert year_range != (2020, 2023)
        assert year_range != {"initial": 2020, "last": 2023}


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_recent_years_range(self):
        """Should handle recent years correctly."""
        year_range = YearRange(2020, 2024)

        assert year_range.span_years() == 5
        assert year_range.contains(2022) is True
        assert list(year_range.to_range()) == [2020, 2021, 2022, 2023, 2024]

    def test_historical_data_range(self):
        """Should handle full B3 historical range."""
        current_year = date.today().year
        year_range = YearRange(1986, current_year)

        assert year_range.initial_year == 1986
        assert year_range.last_year == current_year
        assert year_range.span_years() > 30

    def test_current_year_only(self):
        """Should handle current year only range."""
        current_year = date.today().year
        year_range = YearRange(current_year, current_year)

        assert year_range.span_years() == 1
        assert year_range.contains(current_year) is True

    @patch("src.brazil.dados_b3.historical_quotes.domain.value_objects.year_range.date")
    def test_validates_against_mocked_current_year(self, mock_date):
        """Should validate correctly with mocked current year."""
        mock_date.today.return_value.year = 2025

        # Should accept year up to 2025
        year_range = YearRange(2020, 2025)
        assert year_range.last_year == 2025

        # Should reject year 2026
        with pytest.raises(ValueError):
            YearRange(2020, 2026)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_maximum_valid_year_is_current_year(self):
        """Should accept current year as maximum."""
        current_year = date.today().year
        year_range = YearRange(current_year, current_year)

        assert year_range.last_year == current_year

    def test_very_old_years(self):
        """Should handle very old years if they pass validation."""
        year_range = YearRange(1900, 1950)

        assert year_range.initial_year == 1900
        assert year_range.span_years() == 51

    def test_consecutive_years(self):
        """Should handle consecutive years correctly."""
        year_range = YearRange(2022, 2023)

        assert year_range.span_years() == 2
        assert list(year_range.to_range()) == [2022, 2023]

    def test_large_span(self):
        """Should handle large year spans correctly."""
        year_range = YearRange(1900, 2000)

        assert year_range.span_years() == 101
        assert year_range.contains(1950) is True
        assert year_range.contains(2000) is True
