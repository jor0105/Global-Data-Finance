"""Tests for YearRange value object."""

from datetime import date

import pytest

from src.brazil.dados_b3.historical_quotes.domain.value_objects import YearRange


class TestYearRangeCreation:
    """Test suite for YearRange creation and initialization."""

    def test_creates_valid_year_range(self):
        """Test creation of valid year range."""
        # Arrange
        initial_year = 2020
        last_year = 2024

        # Act
        year_range = YearRange(initial_year, last_year)

        # Assert
        assert year_range.initial_year == initial_year
        assert year_range.last_year == last_year

    def test_creates_range_with_same_year(self):
        """Test creation of range with same initial and last year."""
        # Arrange
        year = 2020

        # Act
        year_range = YearRange(year, year)

        # Assert
        assert year_range.initial_year == year
        assert year_range.last_year == year

    def test_creates_range_with_consecutive_years(self):
        """Test creation of range with consecutive years."""
        # Arrange
        initial_year = 2020
        last_year = 2021

        # Act
        year_range = YearRange(initial_year, last_year)

        # Assert
        assert year_range.initial_year == initial_year
        assert year_range.last_year == last_year

    def test_creates_range_with_large_span(self):
        """Test creation of range with large year span."""
        # Arrange
        initial_year = 1986
        last_year = 2024

        # Act
        year_range = YearRange(initial_year, last_year)

        # Assert
        assert year_range.initial_year == initial_year
        assert year_range.last_year == last_year


class TestYearRangeValidation:
    """Test suite for YearRange validation."""

    def test_raises_error_for_non_integer_initial_year(self):
        """Test that non-integer initial year raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            YearRange("2020", 2024)

        assert "Years must be integers" in str(exc_info.value)

    def test_raises_error_for_non_integer_last_year(self):
        """Test that non-integer last year raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            YearRange(2020, "2024")

        assert "Years must be integers" in str(exc_info.value)

    def test_raises_error_for_float_initial_year(self):
        """Test that float initial year raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            YearRange(2020.5, 2024)

        assert "Years must be integers" in str(exc_info.value)

    def test_raises_error_for_float_last_year(self):
        """Test that float last year raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            YearRange(2020, 2024.5)

        assert "Years must be integers" in str(exc_info.value)

    def test_raises_error_for_initial_greater_than_last(self):
        """Test that initial year greater than last year raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            YearRange(2024, 2020)

        assert "Initial year" in str(exc_info.value)
        assert "cannot be greater than" in str(exc_info.value)
        assert "last year" in str(exc_info.value)

    def test_raises_error_for_future_last_year(self):
        """Test that future last year raises ValueError."""
        # Arrange
        future_year = date.today().year + 1

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            YearRange(2020, future_year)

        assert "cannot be in the future" in str(exc_info.value)

    def test_accepts_current_year_as_last_year(self):
        """Test that current year is accepted as last year."""
        # Arrange
        current_year = date.today().year

        # Act
        year_range = YearRange(2020, current_year)

        # Assert
        assert year_range.last_year == current_year

    def test_raises_error_for_none_initial_year(self):
        """Test that None as initial year raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            YearRange(None, 2024)

    def test_raises_error_for_none_last_year(self):
        """Test that None as last year raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            YearRange(2020, None)

    def test_raises_error_for_both_none(self):
        """Test that None for both years raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            YearRange(None, None)

    def test_accepts_old_years(self):
        """Test that old years (like 1986) are accepted."""
        # Act
        year_range = YearRange(1986, 2000)

        # Assert
        assert year_range.initial_year == 1986
        assert year_range.last_year == 2000


class TestYearRangeImmutability:
    """Test suite for YearRange immutability."""

    def test_is_frozen_dataclass(self):
        """Test that YearRange is a frozen dataclass."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act & Assert
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            year_range.initial_year = 2021

    def test_cannot_modify_last_year(self):
        """Test that last_year cannot be modified."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act & Assert
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            year_range.last_year = 2025

    def test_cannot_add_new_attributes(self):
        """Test that new attributes cannot be added."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act & Assert
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            year_range.new_attribute = "value"


class TestYearRangeToRange:
    """Test suite for to_range method."""

    def test_converts_to_python_range(self):
        """Test conversion to Python range object."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act
        result = year_range.to_range()

        # Assert
        assert isinstance(result, range)

    def test_range_is_inclusive(self):
        """Test that converted range includes both bounds."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act
        result = list(year_range.to_range())

        # Assert
        assert result == [2020, 2021, 2022, 2023, 2024]

    def test_range_for_single_year(self):
        """Test conversion for single year range."""
        # Arrange
        year_range = YearRange(2020, 2020)

        # Act
        result = list(year_range.to_range())

        # Assert
        assert result == [2020]

    def test_range_for_consecutive_years(self):
        """Test conversion for consecutive years."""
        # Arrange
        year_range = YearRange(2020, 2021)

        # Act
        result = list(year_range.to_range())

        # Assert
        assert result == [2020, 2021]

    def test_range_for_long_span(self):
        """Test conversion for long year span."""
        # Arrange
        year_range = YearRange(1986, 1990)

        # Act
        result = list(year_range.to_range())

        # Assert
        assert len(result) == 5
        assert result[0] == 1986
        assert result[-1] == 1990

    def test_range_can_be_iterated(self):
        """Test that returned range can be iterated."""
        # Arrange
        year_range = YearRange(2020, 2022)

        # Act
        result = year_range.to_range()
        years = []
        for year in result:
            years.append(year)

        # Assert
        assert years == [2020, 2021, 2022]

    def test_range_can_be_used_in_membership_test(self):
        """Test that range can be used for membership testing."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act
        result = year_range.to_range()

        # Assert
        assert 2020 in result
        assert 2022 in result
        assert 2024 in result
        assert 2019 not in result
        assert 2025 not in result


class TestYearRangeStringRepresentation:
    """Test suite for YearRange string methods."""

    def test_str_representation(self):
        """Test __str__ method."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act
        result = str(year_range)

        # Assert
        assert result == "2020-2024"

    def test_str_for_single_year(self):
        """Test __str__ for single year range."""
        # Arrange
        year_range = YearRange(2020, 2020)

        # Act
        result = str(year_range)

        # Assert
        assert result == "2020-2020"

    def test_repr_representation(self):
        """Test __repr__ method."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act
        result = repr(year_range)

        # Assert
        assert "YearRange" in result
        assert "initial_year=2020" in result
        assert "last_year=2024" in result

    def test_repr_is_detailed(self):
        """Test that __repr__ provides detailed information."""
        # Arrange
        year_range = YearRange(1986, 2024)

        # Act
        result = repr(year_range)

        # Assert
        assert "1986" in result
        assert "2024" in result


class TestYearRangeEquality:
    """Test suite for YearRange equality."""

    def test_equal_year_ranges(self):
        """Test equality of identical year ranges."""
        # Arrange
        year_range1 = YearRange(2020, 2024)
        year_range2 = YearRange(2020, 2024)

        # Act & Assert
        assert year_range1 == year_range2

    def test_unequal_year_ranges_different_initial(self):
        """Test inequality when initial years differ."""
        # Arrange
        year_range1 = YearRange(2020, 2024)
        year_range2 = YearRange(2021, 2024)

        # Act & Assert
        assert year_range1 != year_range2

    def test_unequal_year_ranges_different_last(self):
        """Test inequality when last years differ."""
        # Arrange
        year_range1 = YearRange(2020, 2024)
        year_range2 = YearRange(2020, 2025)

        # Act & Assert
        assert year_range1 != year_range2

    def test_unequal_year_ranges_completely_different(self):
        """Test inequality when both years differ."""
        # Arrange
        year_range1 = YearRange(2020, 2024)
        year_range2 = YearRange(2015, 2019)

        # Act & Assert
        assert year_range1 != year_range2

    def test_not_equal_to_other_types(self):
        """Test that YearRange is not equal to other types."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act & Assert
        assert year_range != "2020-2024"
        assert year_range != (2020, 2024)
        assert year_range != [2020, 2024]
        assert year_range != range(2020, 2025)


class TestYearRangeHashability:
    """Test suite for YearRange hashability."""

    def test_is_hashable(self):
        """Test that YearRange is hashable."""
        # Arrange
        year_range = YearRange(2020, 2024)

        # Act & Assert
        assert hash(year_range) is not None

    def test_can_be_used_in_set(self):
        """Test that YearRange can be used in sets."""
        # Arrange
        year_range1 = YearRange(2020, 2024)
        year_range2 = YearRange(2015, 2019)
        year_range3 = YearRange(2020, 2024)

        # Act
        year_set = {year_range1, year_range2, year_range3}

        # Assert
        assert len(year_set) == 2  # year_range1 and year_range3 are equal

    def test_can_be_used_as_dict_key(self):
        """Test that YearRange can be used as dict key."""
        # Arrange
        year_range = YearRange(2020, 2024)
        data = {year_range: "data for 2020-2024"}

        # Act & Assert
        assert data[year_range] == "data for 2020-2024"

    def test_equal_ranges_have_same_hash(self):
        """Test that equal ranges have the same hash."""
        # Arrange
        year_range1 = YearRange(2020, 2024)
        year_range2 = YearRange(2020, 2024)

        # Act & Assert
        assert hash(year_range1) == hash(year_range2)
