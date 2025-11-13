import pytest

from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidRepositoryTypeError,
)


class TestInvalidRepositoryTypeError:
    def test_exception_with_int_type(self):
        actual_type = int
        exception = InvalidRepositoryTypeError(actual_type)
        assert isinstance(exception, TypeError)
        assert "Repository must be a string" in str(exception)
        assert "int" in str(exception)

    def test_exception_with_list_type(self):
        actual_type = list
        exception = InvalidRepositoryTypeError(actual_type)
        assert "list" in str(exception)

    def test_exception_with_dict_type(self):
        actual_type = dict
        exception = InvalidRepositoryTypeError(actual_type)
        assert "dict" in str(exception)

    def test_exception_is_type_error(self):
        exception = InvalidRepositoryTypeError(int)
        assert isinstance(exception, TypeError)

    def test_exception_can_be_raised(self):
        with pytest.raises(InvalidRepositoryTypeError) as exc_info:
            raise InvalidRepositoryTypeError(float)
        assert "float" in str(exc_info.value)


class TestInvalidFirstYear:
    def test_exception_with_valid_parameters(self):
        minimal_first_year = 1986
        atual_year = 2024
        exception = InvalidFirstYear(minimal_first_year, atual_year)
        assert isinstance(exception, Exception)
        assert "1986" in str(exception)
        assert "2024" in str(exception)
        assert "Invalid first year" in str(exception)

    def test_exception_message_contains_constraints(self):
        minimal_first_year = 1986
        atual_year = 2024
        exception = InvalidFirstYear(minimal_first_year, atual_year)
        message = str(exception)
        assert "greater than or equal to" in message
        assert "less than or equal to" in message

    def test_exception_with_different_years(self):
        minimal_first_year = 2000
        atual_year = 2025
        exception = InvalidFirstYear(minimal_first_year, atual_year)
        assert "2000" in str(exception)
        assert "2025" in str(exception)

    def test_exception_can_be_raised(self):
        with pytest.raises(InvalidFirstYear) as exc_info:
            raise InvalidFirstYear(1986, 2024)
        assert "1986" in str(exc_info.value)
        assert "2024" in str(exc_info.value)

    def test_exception_with_current_year(self):
        from datetime import date

        minimal_first_year = 1986
        atual_year = date.today().year
        exception = InvalidFirstYear(minimal_first_year, atual_year)
        assert str(atual_year) in str(exception)


class TestInvalidLastYear:
    def test_exception_with_valid_parameters(self):
        first_year = 2020
        atual_year = 2024
        exception = InvalidLastYear(first_year, atual_year)
        assert isinstance(exception, Exception)
        assert "2020" in str(exception)
        assert "2024" in str(exception)
        assert "Invalid last year" in str(exception)

    def test_exception_message_contains_constraints(self):
        first_year = 2020
        atual_year = 2024
        exception = InvalidLastYear(first_year, atual_year)
        message = str(exception)
        assert "greater than or equal to" in message
        assert "less than or equal to" in message

    def test_exception_with_different_years(self):
        first_year = 2015
        atual_year = 2025
        exception = InvalidLastYear(first_year, atual_year)
        assert "2015" in str(exception)
        assert "2025" in str(exception)

    def test_exception_can_be_raised(self):
        with pytest.raises(InvalidLastYear) as exc_info:
            raise InvalidLastYear(2020, 2024)
        assert "2020" in str(exc_info.value)
        assert "2024" in str(exc_info.value)

    def test_exception_references_first_year(self):
        first_year = 2018
        atual_year = 2024
        exception = InvalidLastYear(first_year, atual_year)
        assert f"the {first_year} year" in str(exception)


class TestInvalidAssetsName:
    def test_exception_with_single_invalid_asset(self):
        assets_list = ["invalid"]
        available_assets = ["ações", "etf", "opções"]
        exception = InvalidAssetsName(assets_list, available_assets)
        assert isinstance(exception, Exception)
        assert "Invalid assets names" in str(exception)
        assert "invalid" in str(exception)

    def test_exception_with_multiple_invalid_assets(self):
        assets_list = ["invalid1", "invalid2", "invalid3"]
        available_assets = ["ações", "etf", "opções"]
        exception = InvalidAssetsName(assets_list, available_assets)
        message = str(exception)
        assert "invalid1" in message
        assert "invalid2" in message
        assert "invalid3" in message

    def test_exception_shows_available_assets(self):
        assets_list = ["invalid"]
        available_assets = ["ações", "etf", "opções", "termo"]
        exception = InvalidAssetsName(assets_list, available_assets)
        message = str(exception)
        assert "ações" in message
        assert "etf" in message
        assert "opções" in message
        assert "termo" in message

    def test_exception_with_empty_available_list(self):
        assets_list = ["ações"]
        available_assets = []
        exception = InvalidAssetsName(assets_list, available_assets)
        assert "[]" in str(exception) or "list" in str(exception).lower()

    def test_exception_can_be_raised(self):
        with pytest.raises(InvalidAssetsName) as exc_info:
            raise InvalidAssetsName(["invalid"], ["ações", "etf"])
        assert "invalid" in str(exc_info.value)

    def test_exception_message_structure(self):
        assets_list = ["wrong"]
        available_assets = ["ações", "etf"]
        exception = InvalidAssetsName(assets_list, available_assets)
        message = str(exception)
        assert "Invalid assets names:" in message
        assert "Assets must be" in message
        assert "one of:" in message


class TestEmptyAssetListError:
    def test_exception_with_default_message(self):
        exception = EmptyAssetListError()
        assert isinstance(exception, Exception)
        assert "Asset list cannot be empty" in str(exception)

    def test_exception_with_custom_message(self):
        custom_message = "Custom error: no assets provided"
        exception = EmptyAssetListError(custom_message)
        assert custom_message in str(exception)
        assert str(exception) == custom_message

    def test_exception_can_be_raised_with_default_message(self):
        with pytest.raises(EmptyAssetListError) as exc_info:
            raise EmptyAssetListError()
        assert "Asset list cannot be empty" in str(exc_info.value)

    def test_exception_can_be_raised_with_custom_message(self):
        custom_message = "No assets were specified"
        with pytest.raises(EmptyAssetListError) as exc_info:
            raise EmptyAssetListError(custom_message)
        assert custom_message in str(exc_info.value)

    def test_exception_is_exception_type(self):
        exception = EmptyAssetListError()
        assert isinstance(exception, Exception)

    def test_exception_with_empty_string_message(self):
        exception = EmptyAssetListError("")
        assert str(exception) == ""

    def test_exception_with_multiline_message(self):
        multiline_message = "Asset list is empty.\nPlease provide at least one asset."
        exception = EmptyAssetListError(multiline_message)
        assert multiline_message in str(exception)
        assert "\n" in str(exception)
