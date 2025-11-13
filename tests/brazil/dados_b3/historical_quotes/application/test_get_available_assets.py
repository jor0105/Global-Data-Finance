from src.brazil.dados_b3.historical_quotes.application.use_cases import (
    GetAvailableAssetsUseCase,
)


class TestGetAvailableAssetsUseCase:
    def test_execute_returns_list(self):
        result = GetAvailableAssetsUseCase.execute()
        assert isinstance(result, list)

    def test_execute_returns_non_empty_list(self):
        result = GetAvailableAssetsUseCase.execute()
        assert len(result) > 0

    def test_execute_returns_expected_assets(self):
        expected_assets = [
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        ]
        result = GetAvailableAssetsUseCase.execute()
        for asset in expected_assets:
            assert asset in result

    def test_execute_returns_seven_assets(self):
        result = GetAvailableAssetsUseCase.execute()
        assert len(result) == 7

    def test_execute_returns_strings(self):
        result = GetAvailableAssetsUseCase.execute()
        assert all(isinstance(asset, str) for asset in result)

    def test_execute_has_acoes(self):
        result = GetAvailableAssetsUseCase.execute()
        assert "ações" in result

    def test_execute_has_etf(self):
        result = GetAvailableAssetsUseCase.execute()
        assert "etf" in result

    def test_execute_has_opcoes(self):
        result = GetAvailableAssetsUseCase.execute()
        assert "opções" in result

    def test_execute_has_termo(self):
        result = GetAvailableAssetsUseCase.execute()
        assert "termo" in result

    def test_execute_has_exercicio_opcoes(self):
        result = GetAvailableAssetsUseCase.execute()
        assert "exercicio_opcoes" in result

    def test_execute_has_forward(self):
        result = GetAvailableAssetsUseCase.execute()
        assert "forward" in result

    def test_execute_has_leilao(self):
        result = GetAvailableAssetsUseCase.execute()
        assert "leilao" in result

    def test_execute_no_duplicates(self):
        result = GetAvailableAssetsUseCase.execute()
        assert len(result) == len(set(result))

    def test_execute_is_static_method(self):
        result = GetAvailableAssetsUseCase.execute()
        assert result is not None

    def test_execute_consistent_results(self):
        result1 = GetAvailableAssetsUseCase.execute()
        result2 = GetAvailableAssetsUseCase.execute()
        assert result1 == result2

    def test_execute_returns_lowercase_assets(self):
        result = GetAvailableAssetsUseCase.execute()
        for asset in result:
            if asset != "exercicio_opcoes":
                assert asset.islower() or "_" in asset

    def test_execute_returns_valid_identifiers(self):
        result = GetAvailableAssetsUseCase.execute()
        for asset in result:
            assert isinstance(asset, str)
            assert len(asset) > 0
            assert not asset.isspace()
