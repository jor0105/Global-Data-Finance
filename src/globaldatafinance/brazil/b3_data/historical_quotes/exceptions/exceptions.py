from typing import List


class InvalidFirstYear(Exception):
    def __init__(self, minimal_first_year: int, atual_year: int):
        super().__init__(
            f"Invalid first year. You must provide an integer value greater than or equal to {minimal_first_year} year and less than or equal to {atual_year}."
        )


class InvalidLastYear(Exception):
    def __init__(self, first_year: int, atual_year: int):
        super().__init__(
            f"Invalid last year. You must provide an integer value greater than or equal to the {first_year} year and less than or equal to {atual_year}."
        )


class InvalidAssetsName(Exception):
    def __init__(self, assets_list: List[str], list_available_assets: List[str]):
        super().__init__(
            f"Invalid assets names: {assets_list}. Assets must be a list of strings and one of: {list_available_assets}."
        )


class EmptyAssetListError(Exception):
    def __init__(self, message: str = "Asset list cannot be empty."):
        super().__init__(message)
