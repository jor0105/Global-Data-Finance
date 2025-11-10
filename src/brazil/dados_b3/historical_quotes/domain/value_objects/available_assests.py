from typing import List

from ..exceptions import InvalidAssetsName


class AvailableAssets:
    __AVAILABLEASSETS: List[str] = [
        "ações",
        "etfs",
        "bdrs",
        "fundos imobiliários",
    ]

    @classmethod
    def validate_assets(cls, assets_list: List[str]) -> bool:
        if not isinstance(assets_list, list) or not all(
            isinstance(x, str) for x in assets_list
        ):
            raise InvalidAssetsName(
                assets_list=assets_list, list_available_assets=cls.__AVAILABLEASSETS
            )

        return True

    @classmethod
    def get_available_assets(cls) -> List[str]:
        return cls.__AVAILABLEASSETS.copy()
