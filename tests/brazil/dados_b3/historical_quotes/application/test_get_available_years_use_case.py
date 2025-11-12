"""Tests for GetAvailableYearsUseCase."""

from datetime import date

from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    GetAvailableYearsUseCase,
)


class TestGetAvailableYearsUseCase:
    """Test suite for GetAvailableYearsUseCase."""

    def test_get_atual_year_returns_current_year(self):
        """Test that get_atual_year returns current year."""
        # Arrange
        use_case = GetAvailableYearsUseCase()
        expected_year = date.today().year

        # Act
        result = use_case.get_atual_year()

        # Assert
        assert result == expected_year

    def test_get_atual_year_returns_integer(self):
        """Test that get_atual_year returns an integer."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        result = use_case.get_atual_year()

        # Assert
        assert isinstance(result, int)

    def test_get_atual_year_returns_reasonable_value(self):
        """Test that get_atual_year returns reasonable year value."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        result = use_case.get_atual_year()

        # Assert
        assert result >= 2020
        assert result <= 2100

    def test_get_minimal_year_returns_1986(self):
        """Test that get_minimal_year returns 1986."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        result = use_case.get_minimal_year()

        # Assert
        assert result == 1986

    def test_get_minimal_year_returns_integer(self):
        """Test that get_minimal_year returns an integer."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        result = use_case.get_minimal_year()

        # Assert
        assert isinstance(result, int)

    def test_get_minimal_year_is_constant(self):
        """Test that get_minimal_year returns constant value."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        result1 = use_case.get_minimal_year()
        result2 = use_case.get_minimal_year()

        # Assert
        assert result1 == result2

    def test_minimal_year_less_than_atual_year(self):
        """Test that minimal year is less than current year."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        minimal = use_case.get_minimal_year()
        atual = use_case.get_atual_year()

        # Assert
        assert minimal < atual

    def test_can_instantiate_use_case(self):
        """Test that use case can be instantiated."""
        # Act
        use_case = GetAvailableYearsUseCase()

        # Assert
        assert use_case is not None
        assert isinstance(use_case, GetAvailableYearsUseCase)

    def test_methods_are_callable(self):
        """Test that both methods are callable."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act & Assert
        assert callable(use_case.get_atual_year)
        assert callable(use_case.get_minimal_year)

    def test_multiple_instances_return_same_values(self):
        """Test that multiple instances return same values."""
        # Arrange
        use_case1 = GetAvailableYearsUseCase()
        use_case2 = GetAvailableYearsUseCase()

        # Act
        minimal1 = use_case1.get_minimal_year()
        minimal2 = use_case2.get_minimal_year()
        atual1 = use_case1.get_atual_year()
        atual2 = use_case2.get_atual_year()

        # Assert
        assert minimal1 == minimal2
        assert atual1 == atual2

    def test_year_range_is_valid(self):
        """Test that the year range from minimal to atual is valid."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        minimal = use_case.get_minimal_year()
        atual = use_case.get_atual_year()

        # Assert
        assert atual - minimal >= 0
        assert atual - minimal < 200  # Reasonable upper bound

    def test_minimal_year_in_past(self):
        """Test that minimal year is in the past."""
        # Arrange
        use_case = GetAvailableYearsUseCase()
        current_year = date.today().year

        # Act
        minimal = use_case.get_minimal_year()

        # Assert
        assert minimal < current_year

    def test_get_atual_year_consistent_with_date_module(self):
        """Test that get_atual_year is consistent with date module."""
        # Arrange
        use_case = GetAvailableYearsUseCase()
        expected = date.today().year

        # Act
        result = use_case.get_atual_year()

        # Assert
        assert result == expected

    def test_get_minimal_year_matches_b3_history(self):
        """Test that minimal year matches B3 COTAHIST history (1986)."""
        # Arrange
        use_case = GetAvailableYearsUseCase()

        # Act
        result = use_case.get_minimal_year()

        # Assert
        assert result == 1986  # B3 COTAHIST data starts in 1986
