"""Tests for YearValidationService."""

from datetime import date
from unittest.mock import patch

import pytest

from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    InvalidFirstYear,
    InvalidLastYear,
)
from src.brazil.dados_b3.historical_quotes.domain.services import YearValidationService
from src.brazil.dados_b3.historical_quotes.domain.value_objects import YearRange


class TestGetCurrentYear:
    """Test suite for get_current_year method."""

    def test_returns_current_year(self):
        """Test that method returns the current year."""
        # Arrange
        expected_year = date.today().year

        # Act
        result = YearValidationService.get_current_year()

        # Assert
        assert result == expected_year

    def test_returns_integer(self):
        """Test that method returns an integer."""
        # Act
        result = YearValidationService.get_current_year()

        # Assert
        assert isinstance(result, int)

    def test_returns_reasonable_year(self):
        """Test that returned year is reasonable (after 2020)."""
        # Act
        result = YearValidationService.get_current_year()

        # Assert
        assert result >= 2020
        assert result <= 2100

    def test_is_class_method(self):
        """Test that method can be called as class method."""
        # Act & Assert - should not raise any exception
        result = YearValidationService.get_current_year()
        assert result is not None


class TestGetMinYear:
    """Test suite for get_min_year method."""

    def test_returns_1986(self):
        """Test that minimum year is 1986."""
        # Act
        result = YearValidationService.get_min_year()

        # Assert
        assert result == 1986

    def test_returns_integer(self):
        """Test that method returns an integer."""
        # Act
        result = YearValidationService.get_min_year()

        # Assert
        assert isinstance(result, int)

    def test_is_class_method(self):
        """Test that method can be called as class method."""
        # Act & Assert - should not raise any exception
        result = YearValidationService.get_min_year()
        assert result is not None

    def test_min_year_is_constant(self):
        """Test that minimum year is constant across calls."""
        # Act
        result1 = YearValidationService.get_min_year()
        result2 = YearValidationService.get_min_year()

        # Assert
        assert result1 == result2


class TestValidateAndCreateYearRange:
    """Test suite for validate_and_create_year_range method."""

    def test_creates_valid_year_range(self):
        """Test creation of valid year range."""
        # Arrange
        initial_year = 2020
        last_year = 2024

        # Act
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )

        # Assert
        assert isinstance(result, YearRange)
        assert result.initial_year == initial_year
        assert result.last_year == last_year

    def test_creates_range_with_same_year(self):
        """Test creation of range with same initial and last year."""
        # Arrange
        year = 2020

        # Act
        result = YearValidationService.validate_and_create_year_range(year, year)

        # Assert
        assert result.initial_year == year
        assert result.last_year == year

    def test_creates_range_from_min_year_to_current(self):
        """Test creation of range from minimum year to current year."""
        # Arrange
        initial_year = 1986
        last_year = date.today().year

        # Act
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )

        # Assert
        assert result.initial_year == 1986
        assert result.last_year == last_year

    def test_creates_range_for_single_recent_year(self):
        """Test creation of range for single recent year."""
        # Arrange
        year = date.today().year

        # Act
        result = YearValidationService.validate_and_create_year_range(year, year)

        # Assert
        assert result.initial_year == year
        assert result.last_year == year

    def test_raises_invalid_first_year_for_year_before_1986(self):
        """Test that year before 1986 raises InvalidFirstYear."""
        # Arrange
        initial_year = 1985
        last_year = 2024

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_future_year(self):
        """Test that future initial year raises InvalidFirstYear."""
        # Arrange
        initial_year = date.today().year + 1
        last_year = date.today().year + 2

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_non_integer(self):
        """Test that non-integer initial year raises InvalidFirstYear."""
        # Arrange
        initial_year = "2020"
        last_year = 2024

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_float(self):
        """Test that float initial year raises InvalidFirstYear."""
        # Arrange
        initial_year = 2020.5
        last_year = 2024

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_none(self):
        """Test that None as initial year raises InvalidFirstYear."""
        # Arrange
        initial_year = None
        last_year = 2024

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_year_before_initial(self):
        """Test that last year before initial year raises InvalidLastYear."""
        # Arrange
        initial_year = 2024
        last_year = 2020

        # Act & Assert
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_future_year(self):
        """Test that future last year raises InvalidLastYear."""
        # Arrange
        initial_year = 2020
        last_year = date.today().year + 1

        # Act & Assert
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_non_integer(self):
        """Test that non-integer last year raises InvalidLastYear."""
        # Arrange
        initial_year = 2020
        last_year = "2024"

        # Act & Assert
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_float(self):
        """Test that float last year raises InvalidLastYear."""
        # Arrange
        initial_year = 2020
        last_year = 2024.5

        # Act & Assert
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_last_year_for_none(self):
        """Test that None as last year raises InvalidLastYear."""
        # Arrange
        initial_year = 2020
        last_year = None

        # Act & Assert
        with pytest.raises(InvalidLastYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_accepts_min_year_as_initial(self):
        """Test that minimum year (1986) is accepted as initial year."""
        # Arrange
        initial_year = 1986
        last_year = 2000

        # Act
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )

        # Assert
        assert result.initial_year == 1986

    def test_accepts_current_year_as_last(self):
        """Test that current year is accepted as last year."""
        # Arrange
        current_year = date.today().year
        initial_year = 2020
        last_year = current_year

        # Act
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )

        # Assert
        assert result.last_year == current_year

    def test_validates_with_mocked_current_year(self):
        """Test validation with mocked current year."""
        # Arrange
        initial_year = 2020
        last_year = 2023

        # Act
        with patch(
            "src.brazil.dados_b3.historical_quotes.domain.services.year_validation_service.date"
        ) as mock_date:
            mock_date.today.return_value.year = 2024
            result = YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

        # Assert
        assert result.initial_year == initial_year
        assert result.last_year == last_year

    def test_validates_long_year_range(self):
        """Test validation of long year range."""
        # Arrange
        initial_year = 1986
        last_year = date.today().year

        # Act
        result = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )

        # Assert
        years_in_range = list(result.to_range())
        assert len(years_in_range) == (last_year - initial_year + 1)

    def test_raises_invalid_first_year_for_negative_year(self):
        """Test that negative year raises InvalidFirstYear."""
        # Arrange
        initial_year = -2020
        last_year = 2024

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_raises_invalid_first_year_for_zero(self):
        """Test that zero as year raises InvalidFirstYear."""
        # Arrange
        initial_year = 0
        last_year = 2024

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

    def test_is_class_method(self):
        """Test that method can be called as class method."""
        # Act & Assert - should not raise any exception
        result = YearValidationService.validate_and_create_year_range(2020, 2024)
        assert result is not None

    def test_exception_contains_correct_min_year(self):
        """Test that exception contains correct minimum year."""
        # Arrange
        initial_year = 1985
        last_year = 2024

        # Act & Assert
        with pytest.raises(InvalidFirstYear) as exc_info:
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

        assert "1986" in str(exc_info.value)

    def test_exception_contains_correct_current_year(self):
        """Test that exception contains correct current year."""
        # Arrange
        initial_year = date.today().year + 1
        last_year = date.today().year + 2

        # Act & Assert
        with pytest.raises(InvalidFirstYear) as exc_info:
            YearValidationService.validate_and_create_year_range(
                initial_year, last_year
            )

        assert str(date.today().year) in str(exc_info.value)
