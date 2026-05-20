"""Asset class validation and TPMERC code mapping."""

from typing import Dict, List, Set

from ....core import get_logger
from .errors import EmptyAssetListError, InvalidAssetsName

logger = get_logger(__name__)


class AvailableAssetsServiceB3:
    """Domain service for validating and managing available asset classes.

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

    _AVAILABLE_ASSETS_BY_CLASS: Dict[str, List[str]] = {
        'ações': ['010', '020'],
        'etf': ['010', '020'],
        'opções': ['070', '080'],
        'termo': ['030'],
        'exercicio_opcoes': ['012', '013'],
        'forward': ['050', '060'],
        'leilao': ['017'],
    }

    @classmethod
    def get_available_assets(cls) -> List[str]:
        """Return the list of available asset class names."""
        return list(cls._AVAILABLE_ASSETS_BY_CLASS.keys())

    @classmethod
    def validate_and_create_asset_set(cls, assets_list: List[str]) -> Set[str]:
        """Validate the provided list of asset classes and return a set."""
        if not isinstance(assets_list, list) or not assets_list:
            raise EmptyAssetListError()

        if not all(isinstance(asset, str) for asset in assets_list):
            raise InvalidAssetsName(
                assets_list=assets_list,
                list_available_assets=cls.get_available_assets(),
            )

        assets_list = [asset.lower() for asset in assets_list]

        if not all(
            asset in cls._AVAILABLE_ASSETS_BY_CLASS for asset in assets_list
        ):
            raise InvalidAssetsName(
                assets_list=assets_list,
                list_available_assets=cls.get_available_assets(),
            )

        return set(assets_list)

    @classmethod
    def get_tpmerc_codes_for_assets(cls, asset_set: Set[str]) -> Set[str]:
        """Convert a set of asset classes to their corresponding TPMERC codes.

        Invalid asset classes are logged but don't stop processing.
        """
        valid_codes: Set[str] = set()
        invalid_inputs: List[str] = []

        for asset_class in asset_set:
            normalized_class = asset_class.lower().strip()
            if normalized_class in cls._AVAILABLE_ASSETS_BY_CLASS:
                codes = cls._AVAILABLE_ASSETS_BY_CLASS[normalized_class]
                valid_codes.update(codes)
            else:
                invalid_inputs.append(asset_class)

        if invalid_inputs:
            logger.warning(
                'Invalid asset classes were ignored',
                extra={'invalid_inputs': invalid_inputs},
            )

        return valid_codes
