from typing import Dict

from ......core import get_logger
from ...domain import AvailableYearsCVM

logger = get_logger(__name__)


class GetAvailableYearsUseCaseCVM:
    """Use case for retrieving available years for CVM documents."""

    def __init__(self) -> None:
        """Initialize the use case."""
        self.__available_years = AvailableYearsCVM()
        logger.debug("GetAvailableYearsUseCaseCVM initialized")

    def execute(self) -> Dict[str, int]:
        """Retrieve available years information.

        Returns:
            Dictionary with year information.
        """
        logger.info("Retrieving available years information")

        try:
            years_info = {
                "General Document Years": self.__available_years.get_minimal_general_year(),
                "ITR Document Years": self.__available_years.get_minimal_itr_year(),
                "CGVN and VMLO Document Years": self.__available_years.get_minimal_cgvn_vlmo_year(),
                "Current Year": self.__available_years.get_current_year(),
            }
            logger.debug(f"Retrieved years information: {years_info}")
            return years_info
        except Exception as e:
            logger.error(f"Failed to retrieve available years: {e}")
            raise
