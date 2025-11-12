"""Tests for CreateSetAssetsUseCase."""

import pytest

from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    CreateSetAssetsUseCase,
)
from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
)


class TestCreateSetAssetsUseCase:
    """Test suite for CreateSetAssetsUseCase."""

    def test_execute_returns_set(self):
        """Test that execute returns a set."""
        # Act
        result = CreateSetAssetsUseCase.execute(["ações"])

        # Assert
        assert isinstance(result, set)

    def test_execute_with_single_asset(self):
        """Test execute with single valid asset."""
        # Act
        result = CreateSetAssetsUseCase.execute(["ações"])

        # Assert
        assert result == {"ações"}

    def test_execute_with_multiple_assets(self):
        """Test execute with multiple valid assets."""
        # Act
        result = CreateSetAssetsUseCase.execute(["ações", "etf", "opções"])

        # Assert
        assert result == {"ações", "etf", "opções"}

    def test_execute_with_all_assets(self):
        """Test execute with all available assets."""
        # Arrange
        all_assets = [
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        ]

        # Act
        result = CreateSetAssetsUseCase.execute(all_assets)

        # Assert
        assert len(result) == 7
        assert result == set(all_assets)

    def test_execute_removes_duplicates(self):
        """Test that duplicates are removed."""
        # Act
        result = CreateSetAssetsUseCase.execute(["ações", "ações", "etf", "etf"])

        # Assert
        assert len(result) == 2
        assert result == {"ações", "etf"}

    def test_execute_raises_empty_asset_list_error_for_empty_list(self):
        """Test that empty list raises EmptyAssetListError."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute([])

    def test_execute_raises_empty_asset_list_error_for_non_list(self):
        """Test that non-list input raises EmptyAssetListError."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute("ações")

    def test_execute_raises_empty_asset_list_error_for_none(self):
        """Test that None input raises EmptyAssetListError."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute(None)

    def test_execute_raises_invalid_assets_name_for_invalid_asset(self):
        """Test that invalid asset name raises InvalidAssetsName."""
        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["invalid_asset"])

    def test_execute_raises_invalid_assets_name_for_mixed_valid_invalid(self):
        """Test that mixed valid and invalid assets raise InvalidAssetsName."""
        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", "invalid", "etf"])

    def test_execute_raises_invalid_assets_name_for_non_string(self):
        """Test that non-string elements raise InvalidAssetsName."""
        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", 123, "etf"])

    def test_execute_is_case_sensitive(self):
        """Test that validation is case sensitive."""
        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["AÇÕES"])

    def test_execute_with_acoes(self):
        """Test execute with ações."""
        # Act
        result = CreateSetAssetsUseCase.execute(["ações"])

        # Assert
        assert "ações" in result

    def test_execute_with_etf(self):
        """Test execute with ETF."""
        # Act
        result = CreateSetAssetsUseCase.execute(["etf"])

        # Assert
        assert "etf" in result

    def test_execute_with_opcoes(self):
        """Test execute with opções."""
        # Act
        result = CreateSetAssetsUseCase.execute(["opções"])

        # Assert
        assert "opções" in result

    def test_execute_with_termo(self):
        """Test execute with termo."""
        # Act
        result = CreateSetAssetsUseCase.execute(["termo"])

        # Assert
        assert "termo" in result

    def test_execute_with_exercicio_opcoes(self):
        """Test execute with exercicio_opcoes."""
        # Act
        result = CreateSetAssetsUseCase.execute(["exercicio_opcoes"])

        # Assert
        assert "exercicio_opcoes" in result

    def test_execute_with_forward(self):
        """Test execute with forward."""
        # Act
        result = CreateSetAssetsUseCase.execute(["forward"])

        # Assert
        assert "forward" in result

    def test_execute_with_leilao(self):
        """Test execute with leilao."""
        # Act
        result = CreateSetAssetsUseCase.execute(["leilao"])

        # Assert
        assert "leilao" in result

    def test_execute_is_static_method(self):
        """Test that execute is a static method."""
        # Act & Assert - should not raise any exception
        result = CreateSetAssetsUseCase.execute(["ações"])
        assert result is not None

    def test_execute_raises_empty_asset_list_error_for_dict(self):
        """Test that dict input raises EmptyAssetListError."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute({"ações": True})

    def test_execute_raises_empty_asset_list_error_for_set(self):
        """Test that set input raises EmptyAssetListError (expects list)."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute({"ações", "etf"})

    def test_execute_with_tuple_input(self):
        """Test that tuple input raises EmptyAssetListError (expects list)."""
        # Act & Assert
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute(("ações", "etf"))

    def test_execute_preserves_valid_assets_only(self):
        """Test that only valid assets are preserved."""
        # Arrange
        valid_assets = ["ações", "etf"]

        # Act
        result = CreateSetAssetsUseCase.execute(valid_assets)

        # Assert
        assert result == {"ações", "etf"}

    def test_execute_with_list_containing_empty_string(self):
        """Test that list containing empty string raises InvalidAssetsName."""
        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", ""])

    def test_execute_with_list_containing_whitespace(self):
        """Test that list containing whitespace raises InvalidAssetsName."""
        # Act & Assert
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", "   "])

    def test_execute_returns_set_not_list(self):
        """Test that return type is set, not list."""
        # Act
        result = CreateSetAssetsUseCase.execute(["ações", "etf"])

        # Assert
        assert isinstance(result, set)
        assert not isinstance(result, list)
