import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.application.use_cases import (
    CreateSetAssetsUseCaseB3,
)
from globaldatafinance.brazil.b3_data.historical_quotes.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
)


class TestCreateSetAssetsUseCaseB3:
    def test_execute_returns_set(self):
        result = CreateSetAssetsUseCaseB3.execute(["ações"])
        assert isinstance(result, set)

    def test_execute_with_single_asset(self):
        result = CreateSetAssetsUseCaseB3.execute(["ações"])
        assert result == {"ações"}

    def test_execute_with_multiple_assets(self):
        result = CreateSetAssetsUseCaseB3.execute(["ações", "etf", "opções"])
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
        result = CreateSetAssetsUseCaseB3.execute(all_assets)
        assert len(result) == 7
        assert result == set(all_assets)

    def test_execute_removes_duplicates(self):
        result = CreateSetAssetsUseCaseB3.execute(["ações", "ações", "etf", "etf"])
        assert len(result) == 2
        assert result == {"ações", "etf"}

    def test_execute_raises_empty_asset_list_error_for_empty_list(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCaseB3.execute([])

    def test_execute_raises_empty_asset_list_error_for_non_list(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCaseB3.execute("ações")

    def test_execute_raises_empty_asset_list_error_for_none(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCaseB3.execute(None)

    def test_execute_raises_invalid_assets_name_for_invalid_asset(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCaseB3.execute(["invalid_asset"])

    def test_execute_raises_invalid_assets_name_for_mixed_valid_invalid(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCaseB3.execute(["ações", "invalid", "etf"])

    def test_execute_raises_invalid_assets_name_for_non_string(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCaseB3.execute(["ações", 123, "etf"])

    def test_execute_is_case_insensitive(self):
        result = CreateSetAssetsUseCaseB3.execute(["AÇÕES"])
        assert result == {"ações"}

    def test_execute_with_acoes(self):
        result = CreateSetAssetsUseCaseB3.execute(["ações"])
        assert "ações" in result

    def test_execute_with_etf(self):
        result = CreateSetAssetsUseCaseB3.execute(["etf"])
        assert "etf" in result

    def test_execute_with_opcoes(self):
        result = CreateSetAssetsUseCaseB3.execute(["opções"])
        assert "opções" in result

    def test_execute_with_termo(self):
        result = CreateSetAssetsUseCaseB3.execute(["termo"])
        assert "termo" in result

    def test_execute_with_exercicio_opcoes(self):
        result = CreateSetAssetsUseCaseB3.execute(["exercicio_opcoes"])
        assert "exercicio_opcoes" in result

    def test_execute_with_forward(self):
        result = CreateSetAssetsUseCaseB3.execute(["forward"])
        assert "forward" in result

    def test_execute_with_leilao(self):
        result = CreateSetAssetsUseCaseB3.execute(["leilao"])
        assert "leilao" in result

    def test_execute_is_static_method(self):
        result = CreateSetAssetsUseCaseB3.execute(["ações"])
        assert result is not None

    def test_execute_raises_empty_asset_list_error_for_dict(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCaseB3.execute({"ações": True})

    def test_execute_raises_empty_asset_list_error_for_set(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCaseB3.execute({"ações", "etf"})

    def test_execute_with_tuple_input(self):
        with pytest.raises(EmptyAssetListError):
            CreateSetAssetsUseCaseB3.execute(("ações", "etf"))

    def test_execute_preserves_valid_assets_only(self):
        valid_assets = ["ações", "etf"]
        result = CreateSetAssetsUseCaseB3.execute(valid_assets)
        assert result == {"ações", "etf"}

    def test_execute_with_list_containing_empty_string(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCaseB3.execute(["ações", ""])

    def test_execute_with_list_containing_whitespace(self):
        with pytest.raises(InvalidAssetsName):
            CreateSetAssetsUseCaseB3.execute(["ações", "   "])

    def test_execute_returns_set_not_list(self):
        result = CreateSetAssetsUseCaseB3.execute(["ações", "etf"])
        assert isinstance(result, set)
        assert not isinstance(result, list)
