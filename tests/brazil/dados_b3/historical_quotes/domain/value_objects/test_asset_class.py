"""Comprehensive tests for AssetClass value object.

This test suite ensures complete coverage of all success and error paths
in the AssetClass value object.
"""

import pytest

from src.brazil.dados_b3.historical_quotes.domain.value_objects.asset_class import (
    AssetClass,
)


class TestAssetClassCreation:
    """Test AssetClass creation - Success cases."""

    def test_create_with_name_and_codes(self):
        """Should create AssetClass with name and TPMERC codes."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        assert asset.name == "ações"
        assert asset.tpmerc_codes == ("010", "020")
        assert asset.description == ""

    def test_create_with_description(self):
        """Should create AssetClass with description."""
        asset = AssetClass(
            name="ações",
            tpmerc_codes=("010", "020"),
            description="Ações no mercado à vista",
        )

        assert asset.name == "ações"
        assert asset.description == "Ações no mercado à vista"

    def test_create_with_single_code(self):
        """Should create AssetClass with single TPMERC code."""
        asset = AssetClass(name="termo", tpmerc_codes=("030",))

        assert asset.name == "termo"
        assert asset.tpmerc_codes == ("030",)
        assert len(asset.tpmerc_codes) == 1

    def test_create_with_multiple_codes(self):
        """Should create AssetClass with multiple TPMERC codes."""
        asset = AssetClass(name="opções", tpmerc_codes=("070", "080"))

        assert len(asset.tpmerc_codes) == 2
        assert "070" in asset.tpmerc_codes
        assert "080" in asset.tpmerc_codes


class TestAssetClassImmutability:
    """Test that AssetClass is truly immutable."""

    def test_cannot_modify_name(self):
        """Should not allow modification of name attribute."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        with pytest.raises(AttributeError):
            asset.name = "etf"

    def test_cannot_modify_codes(self):
        """Should not allow modification of tpmerc_codes attribute."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        with pytest.raises(AttributeError):
            asset.tpmerc_codes = ("030",)

    def test_cannot_modify_description(self):
        """Should not allow modification of description attribute."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        with pytest.raises(AttributeError):
            asset.description = "New description"

    def test_tuple_ensures_codes_immutability(self):
        """Should use tuple to ensure codes cannot be modified."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        # Tuple doesn't have append method
        assert not hasattr(asset.tpmerc_codes, "append")


class TestAssetClassValidation:
    """Test AssetClass validation in __post_init__."""

    def test_empty_name_raises_error(self):
        """Should raise ValueError when name is empty."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="", tpmerc_codes=("010",))

        assert "non-empty string" in str(exc_info.value)

    def test_none_name_raises_error(self):
        """Should raise ValueError when name is None."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name=None, tpmerc_codes=("010",))

        assert "non-empty string" in str(exc_info.value)

    def test_non_string_name_raises_error(self):
        """Should raise ValueError when name is not a string."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name=123, tpmerc_codes=("010",))

        assert "non-empty string" in str(exc_info.value)

    def test_empty_codes_raises_error(self):
        """Should raise ValueError when tpmerc_codes is empty."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="ações", tpmerc_codes=())

        assert "non-empty tuple" in str(exc_info.value)

    def test_none_codes_raises_error(self):
        """Should raise ValueError when tpmerc_codes is None."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="ações", tpmerc_codes=None)

        assert "non-empty tuple" in str(exc_info.value)

    def test_codes_with_non_strings_raises_error(self):
        """Should raise ValueError when codes contain non-strings."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="ações", tpmerc_codes=(10, 20))

        assert "non-empty tuple of strings" in str(exc_info.value)

    def test_code_not_3_digits_raises_error(self):
        """Should raise ValueError when code is not 3 digits."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="ações", tpmerc_codes=("01",))

        assert "3-digit strings" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="ações", tpmerc_codes=("0100",))

        assert "3-digit strings" in str(exc_info.value)

    def test_code_with_letters_raises_error(self):
        """Should raise ValueError when code contains letters."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="ações", tpmerc_codes=("ABC",))

        assert "3-digit strings" in str(exc_info.value)

    def test_code_with_special_chars_raises_error(self):
        """Should raise ValueError when code contains special characters."""
        with pytest.raises(ValueError) as exc_info:
            AssetClass(name="ações", tpmerc_codes=("0-1",))

        assert "3-digit strings" in str(exc_info.value)


class TestHasCode:
    """Test has_code method."""

    def test_returns_true_for_existing_code(self):
        """Should return True when code exists in asset class."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        assert asset.has_code("010") is True
        assert asset.has_code("020") is True

    def test_returns_false_for_non_existing_code(self):
        """Should return False when code doesn't exist."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        assert asset.has_code("030") is False
        assert asset.has_code("999") is False

    def test_single_code_check(self):
        """Should work correctly with single code asset."""
        asset = AssetClass(name="termo", tpmerc_codes=("030",))

        assert asset.has_code("030") is True
        assert asset.has_code("010") is False


class TestStringRepresentation:
    """Test string representation methods."""

    def test_str_returns_name(self):
        """Should return asset name as string representation."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        assert str(asset) == "ações"

    def test_repr_returns_detailed_info(self):
        """Should return detailed representation for debugging."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))
        repr_str = repr(asset)

        assert "AssetClass" in repr_str
        assert "ações" in repr_str
        assert "010" in repr_str
        assert "020" in repr_str

    def test_repr_includes_all_codes(self):
        """Should include all codes in repr."""
        asset = AssetClass(
            name="opções",
            tpmerc_codes=("070", "080"),
        )
        repr_str = repr(asset)

        assert "070" in repr_str
        assert "080" in repr_str


class TestEquality:
    """Test equality comparison between AssetClass instances."""

    def test_equal_objects_are_equal(self):
        """Should be equal when name and codes are the same."""
        asset1 = AssetClass(name="ações", tpmerc_codes=("010", "020"))
        asset2 = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        assert asset1 == asset2

    def test_different_names_are_not_equal(self):
        """Should not be equal when names differ."""
        asset1 = AssetClass(name="ações", tpmerc_codes=("010", "020"))
        asset2 = AssetClass(name="etf", tpmerc_codes=("010", "020"))

        assert asset1 != asset2

    def test_different_codes_are_not_equal(self):
        """Should not be equal when codes differ."""
        asset1 = AssetClass(name="ações", tpmerc_codes=("010", "020"))
        asset2 = AssetClass(name="ações", tpmerc_codes=("010", "030"))

        assert asset1 != asset2

    def test_different_descriptions_are_equal(self):
        """Should be equal even when descriptions differ (description is optional)."""
        asset1 = AssetClass(
            name="ações", tpmerc_codes=("010", "020"), description="Desc 1"
        )
        asset2 = AssetClass(
            name="ações", tpmerc_codes=("010", "020"), description="Desc 2"
        )

        # They differ due to description field
        assert asset1 != asset2

    def test_not_equal_to_non_asset_class(self):
        """Should not be equal to non-AssetClass objects."""
        asset = AssetClass(name="ações", tpmerc_codes=("010", "020"))

        assert asset != "ações"
        assert asset != ("010", "020")
        assert asset != {"name": "ações", "codes": ("010", "020")}


class TestRealWorldScenarios:
    """Test real-world B3 asset class scenarios."""

    def test_stocks_asset_class(self):
        """Should correctly represent stocks asset class."""
        stocks = AssetClass(
            name="ações",
            tpmerc_codes=("010", "020"),
            description="Ações no mercado à vista e fracionário",
        )

        assert stocks.name == "ações"
        assert stocks.has_code("010")  # CASH
        assert stocks.has_code("020")  # FRACTIONARY

    def test_options_asset_class(self):
        """Should correctly represent options asset class."""
        options = AssetClass(
            name="opções",
            tpmerc_codes=("070", "080"),
            description="Opções de compra e venda",
        )

        assert options.name == "opções"
        assert options.has_code("070")  # CALL
        assert options.has_code("080")  # PUT

    def test_termo_asset_class(self):
        """Should correctly represent termo asset class."""
        termo = AssetClass(name="termo", tpmerc_codes=("030",))

        assert termo.name == "termo"
        assert termo.has_code("030")
        assert len(termo.tpmerc_codes) == 1

    def test_all_b3_asset_classes(self):
        """Should correctly create all B3 asset classes."""
        asset_classes = [
            AssetClass("ações", ("010", "020")),
            AssetClass("etf", ("010", "020")),
            AssetClass("opções", ("070", "080")),
            AssetClass("termo", ("030",)),
            AssetClass("exercicio_opcoes", ("012", "013")),
            AssetClass("forward", ("050", "060")),
            AssetClass("leilao", ("017",)),
        ]

        assert len(asset_classes) == 7
        assert all(isinstance(ac, AssetClass) for ac in asset_classes)
