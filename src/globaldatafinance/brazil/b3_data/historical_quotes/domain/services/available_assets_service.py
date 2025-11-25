from typing import Dict, List, Set

from ...exceptions import EmptyAssetListError, InvalidAssetsName


class AvailableAssetsServiceB3:
    """Domain service for validating and managing available asset classes.

    This service is stateless and contains business logic that operates on
    asset classes and their corresponding TPMERC codes used in B3 trading.

    TPMERC Codes Reference:
    - 010: CASH (Vista)
    - 020: FRACTIONARY (Fracionário)
    - 030: TERM (Termo)
    - 050: FORWARD WITH GAIN (Forward c/ prêmio)
    - 060: FORWARD WITH MOVEMENT (Forward c/ movimentação)
    - 070: CALL OPTIONS (Opções de Compra)
    - 080: PUT OPTIONS (Opções de Venda)
    - 012: CALL EXERCISE (Exercício de Compra)
    - 013: PUT EXERCISE (Exercício de Venda)
    - 017: AUCTION (Leilão)
    """

    # Private class attribute containing the mapping of asset classes to TPMERC codes
    __AVAILABLE_ASSETS: Dict[str, List[str]] = {
        "ações": ["010", "020"],  # CASH + FRACTIONARY
        "etf": ["010", "020"],  # CASH + FRACTIONARY
        "opções": ["070", "080"],  # CALL + PUT
        "termo": ["030"],  # TERM
        "exercicio_opcoes": ["012", "013"],  # CALL EXERCISE + PUT EXERCISE
        "forward": ["050", "060"],  # FORWARD WITH GAIN + FORWARD WITH MOVEMENT
        "leilao": ["017"],  # AUCTION
    }

    @classmethod
    def get_available_assets(cls) -> List[str]:
        """Return the list of available asset class names.

        Returns:
            List[str]: List of valid asset class identifiers
        """
        return list(cls.__AVAILABLE_ASSETS.keys())

    @classmethod
    def validate_and_create_asset_set(cls, assets_list: List[str]) -> Set[str]:
        """Validate the provided list of asset classes and return a set.

        This method ensures that:
        1. The input is a non-empty list
        2. All elements are strings
        3. All asset names are valid (exist in __AVAILABLE_ASSETS)

        Args:
            assets_list: List of asset class identifiers to validate

        Returns:
            Set[str]: A set of validated asset class identifiers

        Raises:
            EmptyAssetListError: If the list is empty or not a list
            InvalidAssetsName: If any asset name is invalid or not a string
        """
        if not isinstance(assets_list, list) or not assets_list:
            raise EmptyAssetListError()

        if not all(isinstance(asset, str) for asset in assets_list):
            raise InvalidAssetsName(
                assets_list=assets_list,
                list_available_assets=cls.get_available_assets(),
            )

        if not all(asset in cls.__AVAILABLE_ASSETS.keys() for asset in assets_list):
            raise InvalidAssetsName(
                assets_list=assets_list,
                list_available_assets=cls.get_available_assets(),
            )

        return set(assets_list)

    @classmethod
    def get_tpmerc_codes_for_assets(cls, asset_set: Set[str]) -> Set[str]:
        """Convert a set of asset classes to their corresponding TPMERC codes.

        This method maps asset class identifiers to the specific TPMERC codes
        used in B3's COTAHIST files. Invalid asset classes are logged but don't
        stop processing.

        Args:
            asset_set: Set of validated asset class identifiers

        Returns:
            Set[str]: Set of TPMERC codes corresponding to the asset classes

        Note:
            Invalid asset classes are ignored with a warning message.
        """
        valid_codes = set()
        invalid_inputs = []

        for asset_class in asset_set:
            normalized_class = asset_class.lower().strip()
            if normalized_class in cls.__AVAILABLE_ASSETS:
                codes = cls.__AVAILABLE_ASSETS[normalized_class]
                valid_codes.update(codes)
            else:
                invalid_inputs.append(asset_class)

        if invalid_inputs:
            print(f"Warning: Invalid asset classes were ignored: {invalid_inputs}")

        return valid_codes
