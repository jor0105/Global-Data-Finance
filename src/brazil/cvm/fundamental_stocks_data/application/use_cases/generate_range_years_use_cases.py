import logging
from typing import Optional

from src.brazil.cvm.fundamental_stocks_data.domain import AvailableYears

logger = logging.getLogger(__name__)


class GenerateRangeYearsUseCases:
    def __init__(self) -> None:
        self.__range_years = AvailableYears()
        logger.debug("GenerateRangeYearsUseCases initialized")

    def execute(
        self,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> range:
        logger.debug(f"Generating Range Years, " f"years={initial_year}-{last_year}")

        try:
            range_years = self.__range_years.return_range_years(
                initial_year=initial_year,
                last_year=last_year,
            )

            logger.info(f"Generated range of years: {list(range_years)}")

            return range_years

        except Exception as e:
            logger.error(f"Failed to generate range of years: {e}")
            raise
