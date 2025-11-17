from typing import List, Set

from ...domain import AvailableAssetsService


class CreateSetAssetsUseCase:
    @staticmethod
    def execute(assets_list: List[str]) -> Set[str]:
        """Creates a set of available assets using the AvailableAssetsService.

        This use case validates a list of asset class identifiers and returns
        a set of valid asset classes that can be used for extraction.

        Args:
            assets_list: List of asset class identifiers (e.g., ["ações", "etf"])

        Returns:
            Set[str]: Set of validated asset class identifiers

        Raises:
            EmptyAssetListError: If the list is empty or not a list
            InvalidAssetsName: If any asset name is invalid
        """
        return AvailableAssetsService.validate_and_create_asset_set(assets_list)
