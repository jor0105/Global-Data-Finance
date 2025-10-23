import logging
from typing import Dict

from src.brazil.cvm.fundamental_stocks_data.domain import AvailableYears

logger = logging.getLogger(__name__)


class GetAvailableYearsUseCase:
    """Use case for retrieving available years for CVM documents.

    This use case provides information about the year ranges for which
    CVM documents are available, including minimum available years for
    different document types and the current year.

    Example:
        >>> use_case = GetAvailableYearsUseCase()
        >>> years = use_case.execute()
        >>> print(years['general_minimum'])
        1998
    """

    def __init__(self) -> None:
        """Initialize the use case with available years data source."""
        self.__available_years = AvailableYears()
        logger.debug("GetAvailableYearsUseCase initialized")

    def execute(self) -> Dict[str, int]:
        """Retrieve available years information.

        Returns:
            Dictionary with year information:
            - general_minimum: Earliest available year for general documents
            - itr_minimum: Earliest available year for ITR documents
            - cgvn_vlmo_minimum: Earliest available year for CGVN/VLMO documents
            - current_year: Current year

        Raises:
            Exception: If unable to retrieve available years.
        """
        logger.info("Retrieving available years information")

        try:
            years_info = {
                "General Document Years": self.__available_years.get_minimal_geral_year(),
                "ITR Document Years": self.__available_years.get_minimal_itr_year(),
                "CGVN and VMLO Document Years": self.__available_years.get_minimal_cgvn_vlmo_year(),
                "Current Year": self.__available_years.get_atual_year(),
            }
            logger.debug(f"Retrieved years information: {years_info}")
            return years_info
        except Exception as e:
            logger.error(f"Failed to retrieve available years: {e}")
            raise
