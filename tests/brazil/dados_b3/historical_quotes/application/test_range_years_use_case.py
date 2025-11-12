"""Tests for CreateRangeYearsUseCase."""

from datetime import date

import pytest

from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    CreateRangeYearsUseCase,
)
from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    InvalidFirstYear,
    InvalidLastYear,
)


class TestCreateRangeYearsUseCase:
    """Test suite for CreateRangeYearsUseCase."""

    def test_execute_returns_range(self):
        """Test that execute returns a range object."""
        # Act
        result = CreateRangeYearsUseCase.execute(2020, 2024)

        # Assert
        assert isinstance(result, range)

    def test_execute_with_valid_years(self):
        """Test execute with valid year range."""
        # Act
        result = CreateRangeYearsUseCase.execute(2020, 2024)

        # Assert
        assert list(result) == [2020, 2021, 2022, 2023, 2024]

    def test_execute_with_single_year(self):
        """Test execute with same initial and last year."""
        # Act
        result = CreateRangeYearsUseCase.execute(2020, 2020)

        # Assert
        assert list(result) == [2020]

    def test_execute_with_consecutive_years(self):
        """Test execute with consecutive years."""
        # Act
        result = CreateRangeYearsUseCase.execute(2020, 2021)

        # Assert
        assert list(result) == [2020, 2021]

    def test_execute_from_min_year(self):
        """Test execute from minimum year (1986)."""
        # Act
        result = CreateRangeYearsUseCase.execute(1986, 1990)

        # Assert
        assert list(result)[0] == 1986
        assert len(list(result)) == 5

    def test_execute_to_current_year(self):
        """Test execute to current year."""
        # Arrange
        current_year = date.today().year

        # Act
        result = CreateRangeYearsUseCase.execute(2020, current_year)

        # Assert
        assert list(result)[-1] == current_year

    def test_execute_long_range(self):
        """Test execute with long year range."""
        # Act
        result = CreateRangeYearsUseCase.execute(1986, 2024)

        # Assert
        years = list(result)
        assert len(years) == 39  # 1986 to 2024 inclusive
        assert years[0] == 1986
        assert years[-1] == 2024

    def test_execute_raises_invalid_first_year_for_year_before_1986(self):
        """Test that year before 1986 raises InvalidFirstYear."""
        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCase.execute(1985, 2024)

    def test_execute_raises_invalid_first_year_for_future_year(self):
        """Test that future initial year raises InvalidFirstYear."""
        # Arrange
        future_year = date.today().year + 1

        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCase.execute(future_year, future_year + 1)

    def test_execute_raises_invalid_first_year_for_non_integer(self):
        """Test that non-integer initial year raises InvalidFirstYear."""
        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCase.execute("2020", 2024)

    def test_execute_raises_invalid_first_year_for_float(self):
        """Test that float initial year raises InvalidFirstYear."""
        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCase.execute(2020.5, 2024)

    def test_execute_raises_invalid_first_year_for_none(self):
        """Test that None as initial year raises InvalidFirstYear."""
        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCase.execute(None, 2024)

    def test_execute_raises_invalid_last_year_for_year_before_initial(self):
        """Test that last year before initial raises InvalidLastYear."""
        # Act & Assert
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCase.execute(2024, 2020)

    def test_execute_raises_invalid_last_year_for_future_year(self):
        """Test that future last year raises InvalidLastYear."""
        # Arrange
        future_year = date.today().year + 1

        # Act & Assert
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCase.execute(2020, future_year)

    def test_execute_raises_invalid_last_year_for_non_integer(self):
        """Test that non-integer last year raises InvalidLastYear."""
        # Act & Assert
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCase.execute(2020, "2024")

    def test_execute_raises_invalid_last_year_for_float(self):
        """Test that float last year raises InvalidLastYear."""
        # Act & Assert
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCase.execute(2020, 2024.5)

    def test_execute_raises_invalid_last_year_for_none(self):
        """Test that None as last year raises InvalidLastYear."""
        # Act & Assert
        with pytest.raises(InvalidLastYear):
            CreateRangeYearsUseCase.execute(2020, None)

    def test_execute_is_static_method(self):
        """Test that execute is a static method."""
        # Act & Assert - should not raise any exception
        result = CreateRangeYearsUseCase.execute(2020, 2024)
        assert result is not None

    def test_execute_range_is_inclusive(self):
        """Test that returned range includes both bounds."""
        # Act
        result = CreateRangeYearsUseCase.execute(2020, 2024)

        # Assert
        years = list(result)
        assert 2020 in years
        assert 2024 in years

    def test_execute_range_can_be_iterated(self):
        """Test that returned range can be iterated."""
        # Act
        result = CreateRangeYearsUseCase.execute(2020, 2022)

        # Assert
        years = []
        for year in result:
            years.append(year)
        assert years == [2020, 2021, 2022]

    def test_execute_range_supports_membership(self):
        """Test that range supports membership testing."""
        # Act
        result = CreateRangeYearsUseCase.execute(2020, 2024)

        # Assert
        assert 2020 in result
        assert 2022 in result
        assert 2024 in result
        assert 2019 not in result
        assert 2025 not in result

    def test_execute_with_minimum_and_current_year(self):
        """Test execute from minimum year to current year."""
        # Arrange
        current_year = date.today().year

        # Act
        result = CreateRangeYearsUseCase.execute(1986, current_year)

        # Assert
        years = list(result)
        assert years[0] == 1986
        assert years[-1] == current_year
        assert len(years) == (current_year - 1986 + 1)

    def test_execute_raises_invalid_first_year_for_negative_year(self):
        """Test that negative year raises InvalidFirstYear."""
        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCase.execute(-2020, 2024)

    def test_execute_raises_invalid_first_year_for_zero(self):
        """Test that zero as year raises InvalidFirstYear."""
        # Act & Assert
        with pytest.raises(InvalidFirstYear):
            CreateRangeYearsUseCase.execute(0, 2024)
