from datetime import date
from typing import Optional

from ..exceptions.exceptions_domain import InvalidFirstYear, InvalidLastYear


class AvailableYears:
    __MIN_GERAL_YEAR: int = 2010
    __MIN_ITR_YEAR: int = 2011
    __MIN_CGVN_VLMO_YEAR: int = 2018

    def get_atual_year(self) -> int:
        return date.today().year

    def get_minimal_geral_year(self) -> int:
        return self.__MIN_GERAL_YEAR

    def get_minimal_itr_year(self) -> int:
        return self.__MIN_ITR_YEAR

    def get_minimal_cgvn_vlmo_year(self) -> int:
        return self.__MIN_CGVN_VLMO_YEAR

    def __validate_years(self, initial_year: int, last_year: int) -> None:
        """Validate that initial_year and last_year are integers inside allowed bounds.

        If either argument is None, use the class' configured defaults.
        """
        if (
            not isinstance(initial_year, int)
            or initial_year < self.get_minimal_geral_year()
            or initial_year > self.get_atual_year()
        ):
            raise InvalidFirstYear(self.get_minimal_geral_year(), self.get_atual_year())

        if (
            not isinstance(last_year, int)
            or last_year > self.get_atual_year()
            or initial_year > last_year
        ):
            raise InvalidLastYear(initial_year, self.get_atual_year())

    def return_range_years(
        self, initial_year: Optional[int] = None, last_year: Optional[int] = None
    ) -> range:
        """Return a range of years from initial_year to last_year inclusive.

        Defaults to the class' minimal geral year through current year.
        """
        if initial_year is None:
            initial_year = self.get_minimal_geral_year()
        if last_year is None:
            last_year = self.get_atual_year()

        self.__validate_years(initial_year, last_year)

        return range(initial_year, last_year + 1)
