"""Tests for domain exceptions."""

import pytest

from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidRepositoryTypeError,
)


class TestInvalidRepositoryTypeError:
    """Test suite for InvalidRepositoryTypeError exception."""

    def test_exception_with_int_type(self):
        """Test exception with integer type."""
        # Arrange
        actual_type = int

        # Act
        exception = InvalidRepositoryTypeError(actual_type)

        # Assert
        assert isinstance(exception, TypeError)
        assert "Repository must be a string" in str(exception)
        assert "int" in str(exception)

    def test_exception_with_list_type(self):
        """Test exception with list type."""
        # Arrange
        actual_type = list

        # Act
        exception = InvalidRepositoryTypeError(actual_type)

        # Assert
        assert "list" in str(exception)

    def test_exception_with_dict_type(self):
        """Test exception with dict type."""
        # Arrange
        actual_type = dict

        # Act
        exception = InvalidRepositoryTypeError(actual_type)

        # Assert
        assert "dict" in str(exception)

    def test_exception_is_type_error(self):
        """Test that exception inherits from TypeError."""
        # Arrange & Act
        exception = InvalidRepositoryTypeError(int)

        # Assert
        assert isinstance(exception, TypeError)

    def test_exception_can_be_raised(self):
        """Test that exception can be raised and caught."""
        # Act & Assert
        with pytest.raises(InvalidRepositoryTypeError) as exc_info:
            raise InvalidRepositoryTypeError(float)

        assert "float" in str(exc_info.value)


class TestInvalidFirstYear:
    """Test suite for InvalidFirstYear exception."""

    def test_exception_with_valid_parameters(self):
        """Test exception with valid parameters."""
        # Arrange
        minimal_first_year = 1986
        atual_year = 2024

        # Act
        exception = InvalidFirstYear(minimal_first_year, atual_year)

        # Assert
        assert isinstance(exception, Exception)
        assert "1986" in str(exception)
        assert "2024" in str(exception)
        assert "Invalid first year" in str(exception)

    def test_exception_message_contains_constraints(self):
        """Test that exception message contains constraint information."""
        # Arrange
        minimal_first_year = 1986
        atual_year = 2024

        # Act
        exception = InvalidFirstYear(minimal_first_year, atual_year)

        # Assert
        message = str(exception)
        assert "greater than or equal to" in message
        assert "less than or equal to" in message

    def test_exception_with_different_years(self):
        """Test exception with different year values."""
        # Arrange
        minimal_first_year = 2000
        atual_year = 2025

        # Act
        exception = InvalidFirstYear(minimal_first_year, atual_year)

        # Assert
        assert "2000" in str(exception)
        assert "2025" in str(exception)

    def test_exception_can_be_raised(self):
        """Test that exception can be raised and caught."""
        # Act & Assert
        with pytest.raises(InvalidFirstYear) as exc_info:
            raise InvalidFirstYear(1986, 2024)

        assert "1986" in str(exc_info.value)
        assert "2024" in str(exc_info.value)

    def test_exception_with_current_year(self):
        """Test exception with actual current year."""
        # Arrange
        from datetime import date

        minimal_first_year = 1986
        atual_year = date.today().year

        # Act
        exception = InvalidFirstYear(minimal_first_year, atual_year)

        # Assert
        assert str(atual_year) in str(exception)


class TestInvalidLastYear:
    """Test suite for InvalidLastYear exception."""

    def test_exception_with_valid_parameters(self):
        """Test exception with valid parameters."""
        # Arrange
        first_year = 2020
        atual_year = 2024

        # Act
        exception = InvalidLastYear(first_year, atual_year)

        # Assert
        assert isinstance(exception, Exception)
        assert "2020" in str(exception)
        assert "2024" in str(exception)
        assert "Invalid last year" in str(exception)

    def test_exception_message_contains_constraints(self):
        """Test that exception message contains constraint information."""
        # Arrange
        first_year = 2020
        atual_year = 2024

        # Act
        exception = InvalidLastYear(first_year, atual_year)

        # Assert
        message = str(exception)
        assert "greater than or equal to" in message
        assert "less than or equal to" in message

    def test_exception_with_different_years(self):
        """Test exception with different year values."""
        # Arrange
        first_year = 2015
        atual_year = 2025

        # Act
        exception = InvalidLastYear(first_year, atual_year)

        # Assert
        assert "2015" in str(exception)
        assert "2025" in str(exception)

    def test_exception_can_be_raised(self):
        """Test that exception can be raised and caught."""
        # Act & Assert
        with pytest.raises(InvalidLastYear) as exc_info:
            raise InvalidLastYear(2020, 2024)

        assert "2020" in str(exc_info.value)
        assert "2024" in str(exc_info.value)

    def test_exception_references_first_year(self):
        """Test that exception message references the first year."""
        # Arrange
        first_year = 2018
        atual_year = 2024

        # Act
        exception = InvalidLastYear(first_year, atual_year)

        # Assert
        assert f"the {first_year} year" in str(exception)


class TestInvalidAssetsName:
    """Test suite for InvalidAssetsName exception."""

    def test_exception_with_single_invalid_asset(self):
        """Test exception with single invalid asset."""
        # Arrange
        assets_list = ["invalid"]
        available_assets = ["ações", "etf", "opções"]

        # Act
        exception = InvalidAssetsName(assets_list, available_assets)

        # Assert
        assert isinstance(exception, Exception)
        assert "Invalid assets names" in str(exception)
        assert "invalid" in str(exception)

    def test_exception_with_multiple_invalid_assets(self):
        """Test exception with multiple invalid assets."""
        # Arrange
        assets_list = ["invalid1", "invalid2", "invalid3"]
        available_assets = ["ações", "etf", "opções"]

        # Act
        exception = InvalidAssetsName(assets_list, available_assets)

        # Assert
        message = str(exception)
        assert "invalid1" in message
        assert "invalid2" in message
        assert "invalid3" in message

    def test_exception_shows_available_assets(self):
        """Test that exception shows available assets."""
        # Arrange
        assets_list = ["invalid"]
        available_assets = ["ações", "etf", "opções", "termo"]

        # Act
        exception = InvalidAssetsName(assets_list, available_assets)

        # Assert
        message = str(exception)
        assert "ações" in message
        assert "etf" in message
        assert "opções" in message
        assert "termo" in message

    def test_exception_with_empty_available_list(self):
        """Test exception with empty available assets list."""
        # Arrange
        assets_list = ["ações"]
        available_assets = []

        # Act
        exception = InvalidAssetsName(assets_list, available_assets)

        # Assert
        assert "[]" in str(exception) or "list" in str(exception).lower()

    def test_exception_can_be_raised(self):
        """Test that exception can be raised and caught."""
        # Act & Assert
        with pytest.raises(InvalidAssetsName) as exc_info:
            raise InvalidAssetsName(["invalid"], ["ações", "etf"])

        assert "invalid" in str(exc_info.value)

    def test_exception_message_structure(self):
        """Test the structure of exception message."""
        # Arrange
        assets_list = ["wrong"]
        available_assets = ["ações", "etf"]

        # Act
        exception = InvalidAssetsName(assets_list, available_assets)

        # Assert
        message = str(exception)
        assert "Invalid assets names:" in message
        assert "Assets must be" in message
        assert "one of:" in message


class TestEmptyAssetListError:
    """Test suite for EmptyAssetListError exception."""

    def test_exception_with_default_message(self):
        """Test exception with default message."""
        # Act
        exception = EmptyAssetListError()

        # Assert
        assert isinstance(exception, Exception)
        assert "Asset list cannot be empty" in str(exception)

    def test_exception_with_custom_message(self):
        """Test exception with custom message."""
        # Arrange
        custom_message = "Custom error: no assets provided"

        # Act
        exception = EmptyAssetListError(custom_message)

        # Assert
        assert custom_message in str(exception)
        assert str(exception) == custom_message

    def test_exception_can_be_raised_with_default_message(self):
        """Test that exception can be raised with default message."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError) as exc_info:
            raise EmptyAssetListError()

        assert "Asset list cannot be empty" in str(exc_info.value)

    def test_exception_can_be_raised_with_custom_message(self):
        """Test that exception can be raised with custom message."""
        # Arrange
        custom_message = "No assets were specified"

        # Act & Assert
        with pytest.raises(EmptyAssetListError) as exc_info:
            raise EmptyAssetListError(custom_message)

        assert custom_message in str(exc_info.value)

    def test_exception_is_exception_type(self):
        """Test that exception inherits from Exception."""
        # Act
        exception = EmptyAssetListError()

        # Assert
        assert isinstance(exception, Exception)

    def test_exception_with_empty_string_message(self):
        """Test exception with empty string message."""
        # Act
        exception = EmptyAssetListError("")

        # Assert
        assert str(exception) == ""

    def test_exception_with_multiline_message(self):
        """Test exception with multiline message."""
        # Arrange
        multiline_message = "Asset list is empty.\nPlease provide at least one asset."

        # Act
        exception = EmptyAssetListError(multiline_message)

        # Assert
        assert multiline_message in str(exception)
        assert "\n" in str(exception)
