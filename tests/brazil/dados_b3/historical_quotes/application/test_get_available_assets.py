from datafinance.brazil.dados_b3.historical_quotes.application.use_cases import (
    GetAvailableAssetsUseCaseB3,
)


class TestGetAvailableAssetsUseCase:
    def test_execute_returns_list(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert isinstance(result, list)

    def test_execute_returns_non_empty_list(self):
        result = GetAvailableAssetsUseCaseB3.execute()
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
        result = GetAvailableAssetsUseCaseB3.execute()
        for asset in expected_assets:
            assert asset in result

    def test_execute_returns_seven_assets(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert len(result) == 7

    def test_execute_returns_strings(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert all(isinstance(asset, str) for asset in result)

    def test_execute_has_acoes(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert "ações" in result

    def test_execute_has_etf(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert "etf" in result

    def test_execute_has_opcoes(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert "opções" in result

    def test_execute_has_termo(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert "termo" in result

    def test_execute_has_exercicio_opcoes(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert "exercicio_opcoes" in result

    def test_execute_has_forward(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert "forward" in result

    def test_execute_has_leilao(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert "leilao" in result

    def test_execute_no_duplicates(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert len(result) == len(set(result))

    def test_execute_is_static_method(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        assert result is not None

    def test_execute_consistent_results(self):
        result1 = GetAvailableAssetsUseCaseB3.execute()
        result2 = GetAvailableAssetsUseCaseB3.execute()
        assert result1 == result2

    def test_execute_returns_lowercase_assets(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        for asset in result:
            if asset != "exercicio_opcoes":
                assert asset.islower() or "_" in asset

    def test_execute_returns_valid_identifiers(self):
        result = GetAvailableAssetsUseCaseB3.execute()
        for asset in result:
            assert isinstance(asset, str)
            assert len(asset) > 0
            assert not asset.isspace()
