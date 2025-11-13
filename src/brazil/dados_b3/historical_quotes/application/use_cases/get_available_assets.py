from typing import List

from ...domain import AvailableAssetsService


class GetAvailableAssetsUseCase:
    @staticmethod
    def execute() -> List[str]:
        """Get the list of available assets for historical quotes data.

        Returns:
            List of available asset class codes (e.g., ['ações', 'etf', 'opções'])
        """
        return AvailableAssetsService.get_available_assets()
