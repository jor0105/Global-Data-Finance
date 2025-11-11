from typing import List, Set

from ...domain.value_objects.available_assests import AvailableAssets


class CreateSetAssetsUseCase:
    @staticmethod
    def execute(assets_list: List[str]) -> Set[str]:
        """Creates a set of available assets from the AvailableAssets value object."""
        return AvailableAssets.create_set_assets(assets_list)
