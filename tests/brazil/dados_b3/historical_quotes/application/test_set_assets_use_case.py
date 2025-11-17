import pytest

from datafinc.brazil.dados_b3.historical_quotes.application.use_cases import (
    CreateSetAssetsUseCase,
)
from datafinc.brazil.dados_b3.historical_quotes.domain.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
)


class TestCreateSetAssetsUseCase:
    def test_execute_returns_set(self):
        result = CreateSetAssetsUseCase.execute(["ações"])
        assert isinstance(result, set)

    def test_execute_with_single_asset(self):
        result = CreateSetAssetsUseCase.execute(["ações"])
        assert result == {"ações"}

    def test_execute_with_multiple_assets(self):
        result = CreateSetAssetsUseCase.execute(["ações", "etf", "opções"])
        assert result == {"ações", "etf", "opções"}

    def test_execute_with_all_assets(self):
        all_assets = [
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        ]
        result = CreateSetAssetsUseCase.execute(all_assets)
        assert len(result) == 7
        assert result == set(all_assets)

    def test_execute_removes_duplicates(self):
        result = CreateSetAssetsUseCase.execute(["ações", "ações", "etf", "etf"])
        assert len(result) == 2
        assert result == {"ações", "etf"}

    def test_execute_raises_empty_asset_list_error_for_empty_list(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute([])

    def test_execute_raises_empty_asset_list_error_for_non_list(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute("ações")

    def test_execute_raises_empty_asset_list_error_for_none(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute(None)

    def test_execute_raises_invalid_assets_name_for_invalid_asset(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["invalid_asset"])

    def test_execute_raises_invalid_assets_name_for_mixed_valid_invalid(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", "invalid", "etf"])

    def test_execute_raises_invalid_assets_name_for_non_string(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", 123, "etf"])

    def test_execute_is_case_sensitive(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["AÇÕES"])

    def test_execute_with_acoes(self):
        result = CreateSetAssetsUseCase.execute(["ações"])
        assert "ações" in result

    def test_execute_with_etf(self):
        result = CreateSetAssetsUseCase.execute(["etf"])
        assert "etf" in result

    def test_execute_with_opcoes(self):
        result = CreateSetAssetsUseCase.execute(["opções"])
        assert "opções" in result

    def test_execute_with_termo(self):
        result = CreateSetAssetsUseCase.execute(["termo"])
        assert "termo" in result

    def test_execute_with_exercicio_opcoes(self):
        result = CreateSetAssetsUseCase.execute(["exercicio_opcoes"])
        assert "exercicio_opcoes" in result

    def test_execute_with_forward(self):
        result = CreateSetAssetsUseCase.execute(["forward"])
        assert "forward" in result

    def test_execute_with_leilao(self):
        result = CreateSetAssetsUseCase.execute(["leilao"])
        assert "leilao" in result

    def test_execute_is_static_method(self):
        result = CreateSetAssetsUseCase.execute(["ações"])
        assert result is not None

    def test_execute_raises_empty_asset_list_error_for_dict(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute({"ações": True})

    def test_execute_raises_empty_asset_list_error_for_set(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute({"ações", "etf"})

    def test_execute_with_tuple_input(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCase.execute(("ações", "etf"))

    def test_execute_preserves_valid_assets_only(self):
        valid_assets = ["ações", "etf"]
        result = CreateSetAssetsUseCase.execute(valid_assets)
        assert result == {"ações", "etf"}

    def test_execute_with_list_containing_empty_string(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", ""])

    def test_execute_with_list_containing_whitespace(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCase.execute(["ações", "   "])

    def test_execute_returns_set_not_list(self):
        result = CreateSetAssetsUseCase.execute(["ações", "etf"])
        assert isinstance(result, set)
        assert not isinstance(result, list)
