"""Tests for GetAvailableAssetsUseCase."""

from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    GetAvailableAssetsUseCase,
)


class TestGetAvailableAssetsUseCase:
    """Test suite for GetAvailableAssetsUseCase."""

    def test_execute_returns_list(self):
        """Test that execute returns a list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert isinstance(result, list)

    def test_execute_returns_non_empty_list(self):
        """Test that execute returns non-empty list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert len(result) > 0

    def test_execute_returns_expected_assets(self):
        """Test that execute returns expected asset classes."""
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
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        for asset in expected_assets:
            assert asset in result

    def test_execute_returns_seven_assets(self):
        """Test that exactly 7 asset classes are returned."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert len(result) == 7

    def test_execute_returns_strings(self):
        """Test that all returned elements are strings."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert all(isinstance(asset, str) for asset in result)

    def test_execute_has_acoes(self):
        """Test that 'ações' is in the returned list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert "ações" in result

    def test_execute_has_etf(self):
        """Test that 'etf' is in the returned list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert "etf" in result

    def test_execute_has_opcoes(self):
        """Test that 'opções' is in the returned list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert "opções" in result

    def test_execute_has_termo(self):
        """Test that 'termo' is in the returned list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert "termo" in result

    def test_execute_has_exercicio_opcoes(self):
        """Test that 'exercicio_opcoes' is in the returned list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert "exercicio_opcoes" in result

    def test_execute_has_forward(self):
        """Test that 'forward' is in the returned list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert "forward" in result

    def test_execute_has_leilao(self):
        """Test that 'leilao' is in the returned list."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert "leilao" in result

    def test_execute_no_duplicates(self):
        """Test that there are no duplicate assets."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        assert len(result) == len(set(result))

    def test_execute_is_static_method(self):
        """Test that execute can be called without instantiation."""
        # Act & Assert - should not raise any exception
        result = GetAvailableAssetsUseCase.execute()
        assert result is not None

    def test_execute_consistent_results(self):
        """Test that execute returns consistent results across calls."""
        # Act
        result1 = GetAvailableAssetsUseCase.execute()
        result2 = GetAvailableAssetsUseCase.execute()

        # Assert
        assert result1 == result2

    def test_execute_returns_lowercase_assets(self):
        """Test that all assets are lowercase (except special cases)."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        for asset in result:
            if asset != "exercicio_opcoes":  # Special case with underscore
                assert asset.islower() or "_" in asset

    def test_execute_returns_valid_identifiers(self):
        """Test that all assets are valid string identifiers."""
        # Act
        result = GetAvailableAssetsUseCase.execute()

        # Assert
        for asset in result:
            assert isinstance(asset, str)
            assert len(asset) > 0
            assert not asset.isspace()
