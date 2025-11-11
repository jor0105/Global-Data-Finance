from typing import Dict, List, Set

from ..exceptions import EmptyAssetListError, InvalidAssetsName


class AvailableAssets:
    __AVAILABLEASSETS: Dict[str, List[str]] = {
        "ações": ["010", "020"],  # '010' (CASH) + '020' (FRACTIONARY) [cite: 92]
        "etf": ["010", "020"],  # '010' (CASH) + '020' (FRACTIONARY) [cite: 92]
        "opções": ["070", "080"],  # '070' (CALL) + '080' (PUT) [cite: 92]
        "termo": ["030"],  # '030' (TERM) [cite: 92]
        "exercicio_opcoes": [
            "012",
            "013",
        ],  # '012' (CALL EXERCISE) + '013' (PUT EXERCISE) [cite: 92]
        "forward": [
            "050",
            "060",
        ],  # '050' (FORWARD W/ GAIN) + '060' (FORWARD W/ MOVEMENT) [cite: 92]
        "leilao": ["017"],  # '017' (AUCTION) [cite: 92]
    }

    @classmethod
    def create_set_assets(cls, assets_list: List[str]) -> Set[str]:
        """Validate the list of asset classes provided.

        Raises:
            EmptyAssetListError: If the list is empty or not a list.
            InvalidAssetsName: If any item is not a string or not among the allowed classes.
        """
        if not isinstance(assets_list, list) or not assets_list:
            raise EmptyAssetListError()

        if not all(isinstance(asset, str) for asset in assets_list) or not all(
            asset in cls.__AVAILABLEASSETS.keys() for asset in assets_list
        ):
            raise InvalidAssetsName(
                assets_list=assets_list,
                list_available_assets=list(cls.__AVAILABLEASSETS.keys()),
            )

        return set(assets_list)

    @classmethod
    def get_available_assets(cls) -> List[str]:
        """Return the list of available asset classes."""
        return list(cls.__AVAILABLEASSETS.keys())

    @classmethod
    def get_target_tmerc_codes(cls, set_assets: Set[str]) -> Set[str]:
        """Validate the user input and return a set of TPMERC codes."""
        valid_codes = set()
        invalid_inputs = []

        for asset_class in set_assets:
            normalized_class = asset_class.lower().strip()
            if normalized_class in cls.__AVAILABLEASSETS:
                codes = cls.__AVAILABLEASSETS[normalized_class]
                valid_codes.update(codes)
            else:
                invalid_inputs.append(asset_class)

        if invalid_inputs:
            print(f"Warning: Invalid asset classes were ignored: {invalid_inputs}")

        return valid_codes
