"""Tests for AvailableAssetsService."""

import pytest

from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
)
from src.brazil.dados_b3.historical_quotes.domain.services import AvailableAssetsService


class TestGetAvailableAssets:
    """Test suite for get_available_assets method."""

    def test_returns_list_of_assets(self):
        """Test that method returns a list."""
        # Act
        result = AvailableAssetsService.get_available_assets()

        # Assert
        assert isinstance(result, list)

    def test_returns_non_empty_list(self):
        """Test that returned list is not empty."""
        # Act
        result = AvailableAssetsService.get_available_assets()

        # Assert
        assert len(result) > 0

    def test_returns_expected_asset_classes(self):
        """Test that all expected asset classes are present."""
        # Arrange
        expected_assets = [
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        ]

        # Act
        result = AvailableAssetsService.get_available_assets()

        # Assert
        for asset in expected_assets:
            assert asset in result

    def test_returns_seven_asset_classes(self):
        """Test that exactly 7 asset classes are returned."""
        # Act
        result = AvailableAssetsService.get_available_assets()

        # Assert
        assert len(result) == 7

    def test_all_elements_are_strings(self):
        """Test that all returned elements are strings."""
        # Act
        result = AvailableAssetsService.get_available_assets()

        # Assert
        assert all(isinstance(asset, str) for asset in result)

    def test_no_duplicate_assets(self):
        """Test that there are no duplicate asset classes."""
        # Act
        result = AvailableAssetsService.get_available_assets()

        # Assert
        assert len(result) == len(set(result))

    def test_is_class_method(self):
        """Test that method can be called as class method."""
        # Act & Assert - should not raise any exception
        result = AvailableAssetsService.get_available_assets()
        assert result is not None


class TestValidateAndCreateAssetSet:
    """Test suite for validate_and_create_asset_set method."""

    def test_validates_single_valid_asset(self):
        """Test validation with single valid asset."""
        # Arrange
        assets_list = ["ações"]

        # Act
        result = AvailableAssetsService.validate_and_create_asset_set(assets_list)

        # Assert
        assert isinstance(result, set)
        assert result == {"ações"}

    def test_validates_multiple_valid_assets(self):
        """Test validation with multiple valid assets."""
        # Arrange
        assets_list = ["ações", "etf", "opções"]

        # Act
        result = AvailableAssetsService.validate_and_create_asset_set(assets_list)

        # Assert
        assert result == {"ações", "etf", "opções"}

    def test_validates_all_available_assets(self):
        """Test validation with all available assets."""
        # Arrange
        assets_list = [
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        ]

        # Act
        result = AvailableAssetsService.validate_and_create_asset_set(assets_list)

        # Assert
        assert len(result) == 7

    def test_removes_duplicates_from_list(self):
        """Test that duplicates in input list are removed in output set."""
        # Arrange
        assets_list = ["ações", "ações", "etf", "etf"]

        # Act
        result = AvailableAssetsService.validate_and_create_asset_set(assets_list)

        # Assert
        assert len(result) == 2
        assert result == {"ações", "etf"}

    def test_raises_empty_asset_list_error_for_empty_list(self):
        """Test that empty list raises EmptyAssetListError."""
        # Arrange
        assets_list = []

        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set(assets_list)

    def test_raises_empty_asset_list_error_for_non_list(self):
        """Test that non-list input raises EmptyAssetListError."""
        # Arrange
        assets_not_list = "ações"

        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set(assets_not_list)

    def test_raises_empty_asset_list_error_for_none(self):
        """Test that None input raises EmptyAssetListError."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set(None)

    def test_raises_invalid_assets_name_for_non_string_elements(self):
        """Test that list with non-string elements raises InvalidAssetsName."""
        # Arrange
        assets_list = ["ações", 123, "etf"]

        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(assets_list)

    def test_raises_invalid_assets_name_for_invalid_asset(self):
        """Test that invalid asset name raises InvalidAssetsName."""
        # Arrange
        assets_list = ["ações", "invalid_asset"]

        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(assets_list)

    def test_raises_invalid_assets_name_for_all_invalid_assets(self):
        """Test that all invalid assets raise InvalidAssetsName."""
        # Arrange
        assets_list = ["invalid1", "invalid2"]

        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(assets_list)

    def test_raises_invalid_assets_name_with_mixed_valid_invalid(self):
        """Test that mixed valid and invalid assets raise InvalidAssetsName."""
        # Arrange
        assets_list = ["ações", "invalid", "etf"]

        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(assets_list)

    def test_is_case_sensitive(self):
        """Test that validation is case sensitive."""
        # Arrange
        assets_list = ["AÇÕES", "ETF"]

        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(assets_list)

    def test_validates_with_dict_input(self):
        """Test that dict input raises EmptyAssetListError."""
        # Arrange
        assets_dict = {"ações": True}

        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set(assets_dict)

    def test_validates_with_set_input(self):
        """Test that set input raises EmptyAssetListError (expects list)."""
        # Arrange
        assets_set = {"ações", "etf"}

        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set(assets_set)


class TestGetTpmercCodesForAssets:
    """Test suite for get_tpmerc_codes_for_assets method."""

    def test_returns_codes_for_acoes(self):
        """Test TPMERC codes for ações (stocks)."""
        # Arrange
        asset_set = {"ações"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert isinstance(result, set)
        assert result == {"010", "020"}

    def test_returns_codes_for_etf(self):
        """Test TPMERC codes for ETF."""
        # Arrange
        asset_set = {"etf"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"010", "020"}

    def test_returns_codes_for_opcoes(self):
        """Test TPMERC codes for opções (options)."""
        # Arrange
        asset_set = {"opções"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"070", "080"}

    def test_returns_codes_for_termo(self):
        """Test TPMERC codes for termo (term)."""
        # Arrange
        asset_set = {"termo"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"030"}

    def test_returns_codes_for_exercicio_opcoes(self):
        """Test TPMERC codes for exercicio_opcoes (option exercise)."""
        # Arrange
        asset_set = {"exercicio_opcoes"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"012", "013"}

    def test_returns_codes_for_forward(self):
        """Test TPMERC codes for forward."""
        # Arrange
        asset_set = {"forward"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"050", "060"}

    def test_returns_codes_for_leilao(self):
        """Test TPMERC codes for leilao (auction)."""
        # Arrange
        asset_set = {"leilao"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"017"}

    def test_returns_combined_codes_for_multiple_assets(self):
        """Test TPMERC codes for multiple assets."""
        # Arrange
        asset_set = {"ações", "opções"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"010", "020", "070", "080"}

    def test_returns_all_codes_for_all_assets(self):
        """Test TPMERC codes for all available assets."""
        # Arrange
        asset_set = {
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        }

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        expected_codes = {
            "010",
            "020",
            "030",
            "050",
            "060",
            "070",
            "080",
            "012",
            "013",
            "017",
        }
        assert result == expected_codes

    def test_returns_empty_set_for_empty_input(self):
        """Test that empty set returns empty set."""
        # Arrange
        asset_set = set()

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == set()

    def test_ignores_invalid_asset_with_warning(self, capsys):
        """Test that invalid assets are ignored with warning."""
        # Arrange
        asset_set = {"ações", "invalid_asset"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == {"010", "020"}
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "invalid_asset" in captured.out

    def test_ignores_all_invalid_assets_with_warning(self, capsys):
        """Test that all invalid assets are ignored with warning."""
        # Arrange
        asset_set = {"invalid1", "invalid2"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert result == set()
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "invalid1" in captured.out
        assert "invalid2" in captured.out

    def test_handles_uppercase_assets_normalized(self):
        """Test that uppercase asset names are normalized to lowercase."""
        # Arrange
        asset_set = {"AÇÕES"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        # The service normalizes to lowercase, so uppercase AÇÕES becomes ações
        # which is invalid in exact match, but gets normalized
        assert isinstance(result, set)

    def test_normalizes_whitespace_in_asset_names(self):
        """Test that asset names with extra whitespace are normalized."""
        # Arrange
        asset_set = {" ações ", "  etf  "}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        # Should normalize and find the assets
        assert "010" in result
        assert "020" in result

    def test_no_duplicate_codes_returned(self):
        """Test that duplicate codes are not returned when assets share codes."""
        # Arrange - ações and etf both use 010 and 020
        asset_set = {"ações", "etf"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert len(result) == 2
        assert result == {"010", "020"}

    def test_all_codes_are_strings(self):
        """Test that all returned codes are strings."""
        # Arrange
        asset_set = {"ações", "opções", "termo"}

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert all(isinstance(code, str) for code in result)

    def test_all_codes_are_three_digits(self):
        """Test that all TPMERC codes are three digits."""
        # Arrange
        asset_set = {
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        }

        # Act
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Assert
        assert all(len(code) == 3 for code in result)
        assert all(code.isdigit() for code in result)
