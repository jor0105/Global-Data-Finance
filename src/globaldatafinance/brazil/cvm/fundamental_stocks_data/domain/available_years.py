from datetime import date
from typing import Optional

from ..exceptions import InvalidFirstYear, InvalidLastYear


class AvailableYearsCVM:
    """Provides the minimum allowed years and helper functions for CVM documents."""

    __MIN_GENERAL_YEAR: int = 2010
    __MIN_ITR_YEAR: int = 2011
    __MIN_CGVN_VLMO_YEAR: int = 2018

    def get_current_year(self) -> int:
        """Returns the current year (based on the system date)."""
        return date.today().year

    def get_minimal_general_year(self) -> int:
        """Returns the minimum supported year for general documents."""
        return self.__MIN_GENERAL_YEAR

    def get_minimal_itr_year(self) -> int:
        """Returns the minimum supported year for ITR documents."""
        return self.__MIN_ITR_YEAR

    def get_minimal_cgvn_vlmo_year(self) -> int:
        """Returns the minimum supported year for CGVN/VLMO documents."""
        return self.__MIN_CGVN_VLMO_YEAR

    def __validate_years(self, initial_year: int, last_year: int) -> None:
        """
        Validates that `initial_year` and `last_year` are integers within the allowed bounds.

        Raises domain-specific exceptions when values are out of range.
        """
        if (
            not isinstance(initial_year, int)
            or initial_year < self.get_minimal_general_year()
            or initial_year > self.get_current_year()
        ):
            raise InvalidFirstYear(
                self.get_minimal_general_year(), self.get_current_year()
            )

        if (
            not isinstance(last_year, int)
            or last_year > self.get_current_year()
            or initial_year > last_year
        ):
            raise InvalidLastYear(initial_year, self.get_current_year())

    def return_range_years(
        self,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> range:
        """
        Returns a range of years from `initial_year` to `last_year` inclusive.

        Defaults to the class's minimum general year through the current year.
        """
        if initial_year is None:
            initial_year = self.get_minimal_general_year()
        if last_year is None:
            last_year = self.get_current_year()

        self.__validate_years(initial_year, last_year)

        return range(initial_year, last_year + 1)
