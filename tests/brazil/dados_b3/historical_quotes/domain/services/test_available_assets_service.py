import pytest

from src.brazil.dados_b3.historical_quotes.domain.exceptions import (
    EmptyAssetListError,
    InvalidAssetsName,
)
from src.brazil.dados_b3.historical_quotes.domain.services.available_assets_service import (
    AvailableAssetsService,
)


class TestGetAvailableAssets:
    """Test get_available_assets method."""

    def test_returns_list_of_strings(self):
        """Should return a list containing string asset class names."""
        result = AvailableAssetsService.get_available_assets()

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(asset, str) for asset in result)

    def test_contains_expected_asset_classes(self):
        """Should contain all expected B3 asset classes."""
        result = AvailableAssetsService.get_available_assets()

        expected_assets = [
            "ações",
            "etf",
            "opções",
            "termo",
            "exercicio_opcoes",
            "forward",
            "leilao",
        ]
        for expected in expected_assets:
            assert expected in result, f"Expected asset class '{expected}' not found"

    def test_returns_exactly_seven_asset_classes(self):
        """Should return exactly 7 asset classes."""
        result = AvailableAssetsService.get_available_assets()
        assert len(result) == 7


class TestValidateAndCreateAssetSet:
    """Test validate_and_create_asset_set method - Success cases."""

    def test_valid_single_asset(self):
        """Should accept a single valid asset class."""
        result = AvailableAssetsService.validate_and_create_asset_set(["ações"])

        assert isinstance(result, set)
        assert "ações" in result
        assert len(result) == 1

    def test_valid_multiple_assets(self):
        """Should accept multiple valid asset classes."""
        assets = ["ações", "etf", "opções"]
        result = AvailableAssetsService.validate_and_create_asset_set(assets)

        assert isinstance(result, set)
        assert result == {"ações", "etf", "opções"}
        assert len(result) == 3

    def test_all_asset_classes(self):
        """Should accept all available asset classes."""
        all_assets = AvailableAssetsService.get_available_assets()
        result = AvailableAssetsService.validate_and_create_asset_set(all_assets)

        assert isinstance(result, set)
        assert len(result) == 7

    def test_removes_duplicates(self):
        """Should remove duplicate asset classes in the result set."""
        assets = ["ações", "ações", "etf", "etf"]
        result = AvailableAssetsService.validate_and_create_asset_set(assets)

        assert len(result) == 2
        assert result == {"ações", "etf"}


class TestValidateAndCreateAssetSetErrors:
    """Test validate_and_create_asset_set method - Error cases."""

    def test_empty_list_raises_error(self):
        """Should raise EmptyAssetListError when list is empty."""
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set([])

    def test_none_raises_error(self):
        """Should raise EmptyAssetListError when input is None."""
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set(None)

    def test_not_a_list_raises_error(self):
        """Should raise EmptyAssetListError when input is not a list."""
        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set("ações")

        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set({"ações"})

        with pytest.raises(EmptyAssetListError):
            AvailableAssetsService.validate_and_create_asset_set(123)

    def test_invalid_asset_name_raises_error(self):
        """Should raise InvalidAssetsName when asset class is invalid."""
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(["invalid_asset"])

    def test_mixed_valid_and_invalid_raises_error(self):
        """Should raise InvalidAssetsName when list contains invalid asset."""
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(["ações", "invalid"])

    def test_non_string_elements_raise_error(self):
        """Should raise InvalidAssetsName when list contains non-strings."""
        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set([123, 456])

        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set(["ações", 123])

        with pytest.raises(InvalidAssetsName):
            AvailableAssetsService.validate_and_create_asset_set([None])


class TestGetTpmercCodesForAssets:
    """Test get_tpmerc_codes_for_assets method."""

    def test_single_asset_returns_codes(self):
        """Should return TPMERC codes for a single asset class."""
        asset_set = {"ações"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        assert isinstance(result, set)
        assert "010" in result  # CASH
        assert "020" in result  # FRACTIONARY
        assert len(result) == 2

    def test_multiple_assets_return_combined_codes(self):
        """Should return combined TPMERC codes for multiple assets."""
        asset_set = {"ações", "etf"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        assert isinstance(result, set)
        # Both ações and etf use the same codes
        assert "010" in result
        assert "020" in result

    def test_options_returns_correct_codes(self):
        """Should return correct TPMERC codes for options."""
        asset_set = {"opções"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        assert "070" in result  # CALL
        assert "080" in result  # PUT
        assert len(result) == 2

    def test_termo_returns_correct_code(self):
        """Should return correct TPMERC code for termo."""
        asset_set = {"termo"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        assert "030" in result
        assert len(result) == 1

    def test_exercicio_opcoes_returns_correct_codes(self):
        """Should return correct codes for exercicio_opcoes."""
        asset_set = {"exercicio_opcoes"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        assert "012" in result  # CALL EXERCISE
        assert "013" in result  # PUT EXERCISE
        assert len(result) == 2

    def test_forward_returns_correct_codes(self):
        """Should return correct codes for forward."""
        asset_set = {"forward"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        assert "050" in result  # FORWARD WITH GAIN
        assert "060" in result  # FORWARD WITH MOVEMENT
        assert len(result) == 2

    def test_leilao_returns_correct_code(self):
        """Should return correct code for leilao."""
        asset_set = {"leilao"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        assert "017" in result
        assert len(result) == 1

    def test_all_assets_return_all_codes(self):
        """Should return all TPMERC codes when all assets are requested."""
        all_assets = set(AvailableAssetsService.get_available_assets())
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(all_assets)

        assert isinstance(result, set)
        # Should have at least 10 unique codes
        assert len(result) >= 10

    def test_empty_set_returns_empty_set(self):
        """Should return empty set when input set is empty."""
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(set())

        assert isinstance(result, set)
        assert len(result) == 0

    def test_invalid_asset_prints_warning(self, capsys):
        """Should print warning for invalid asset classes but not fail."""
        asset_set = {"invalid_asset"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Should return empty set
        assert len(result) == 0

        # Should print warning
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "invalid_asset" in captured.out

    def test_mixed_valid_invalid_returns_only_valid_codes(self, capsys):
        """Should return codes for valid assets and warn about invalid ones."""
        asset_set = {"ações", "invalid_asset"}
        result = AvailableAssetsService.get_tpmerc_codes_for_assets(asset_set)

        # Should return codes for ações
        assert "010" in result
        assert "020" in result

        # Should print warning
        captured = capsys.readouterr()
        assert "invalid_asset" in captured.out


class TestIsValidAssetClass:
    """Test is_valid_asset_class method."""

    def test_valid_asset_returns_true(self):
        """Should return True for valid asset classes."""
        assert AvailableAssetsService.is_valid_asset_class("ações") is True
        assert AvailableAssetsService.is_valid_asset_class("etf") is True
        assert AvailableAssetsService.is_valid_asset_class("opções") is True

    def test_invalid_asset_returns_false(self):
        """Should return False for invalid asset classes."""
        assert AvailableAssetsService.is_valid_asset_class("invalid") is False
        assert AvailableAssetsService.is_valid_asset_class("stocks") is False
        assert AvailableAssetsService.is_valid_asset_class("") is False

    def test_all_available_assets_are_valid(self):
        """Should return True for all assets from get_available_assets."""
        all_assets = AvailableAssetsService.get_available_assets()
        for asset in all_assets:
            assert AvailableAssetsService.is_valid_asset_class(asset) is True


class TestGetTpmercCodesForSingleAsset:
    """Test get_tpmerc_codes_for_single_asset method."""

    def test_valid_asset_returns_codes(self):
        """Should return list of TPMERC codes for valid asset."""
        result = AvailableAssetsService.get_tpmerc_codes_for_single_asset("ações")

        assert isinstance(result, list)
        assert "010" in result
        assert "020" in result

    def test_all_assets_return_codes(self):
        """Should return codes for all valid asset classes."""
        all_assets = AvailableAssetsService.get_available_assets()

        for asset in all_assets:
            result = AvailableAssetsService.get_tpmerc_codes_for_single_asset(asset)
            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(code, str) for code in result)

    def test_invalid_asset_raises_key_error(self):
        """Should raise KeyError for invalid asset class."""
        with pytest.raises(KeyError) as exc_info:
            AvailableAssetsService.get_tpmerc_codes_for_single_asset("invalid")

        assert "invalid" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_error_message_includes_available_assets(self):
        """Should include available assets in error message."""
        with pytest.raises(KeyError) as exc_info:
            AvailableAssetsService.get_tpmerc_codes_for_single_asset("invalid")

        error_message = str(exc_info.value)
        assert "Available:" in error_message
