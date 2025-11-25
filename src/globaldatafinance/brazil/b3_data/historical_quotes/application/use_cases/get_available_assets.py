from typing import List

from ...domain import AvailableAssetsServiceB3


class GetAvailableAssetsUseCaseB3:
    @staticmethod
    def execute() -> List[str]:
        """Get the list of available assets for historical quotes data.

        Returns:
            List of available asset class codes (e.g., ['ações', 'etf', 'opções'])
        """
        return AvailableAssetsServiceB3.get_available_assets()
