from datetime import date

from ..exceptions import InvalidFirstYear, InvalidLastYear


class AvailableYears:
    __MIN_YEAR: int = 1986

    def get_atual_year(self) -> int:
        return date.today().year

    def get_minimal_year(self) -> int:
        return self.__MIN_YEAR

    def __validate_years(self, initial_year: int, last_year: int) -> None:
        """Validate that initial_year and last_year are integers inside allowed bounds.

        If either argument is None, use the class' configured defaults.
        """
        if (
            not isinstance(initial_year, int)
            or initial_year < self.get_minimal_year()
            or initial_year > self.get_atual_year()
        ):
            raise InvalidFirstYear(self.get_minimal_year(), self.get_atual_year())

        if (
            not isinstance(last_year, int)
            or last_year > self.get_atual_year()
            or initial_year > last_year
        ):
            raise InvalidLastYear(initial_year, self.get_atual_year())

    def return_range_years(self, initial_year: int, last_year: int) -> range:
        """Return a range of years from initial_year to last_year inclusive."""
        self.__validate_years(initial_year, last_year)
        return range(initial_year, last_year + 1)
