from datetime import date

from ..exceptions import InvalidFirstYear, InvalidLastYear
from ..value_objects import YearRange


class YearValidationService:
    """Domain service for validating year ranges.

    This service is stateless and contains business logic for validating
    that year ranges are appropriate for B3 historical quotes data extraction.

    The B3 COTAHIST files are available starting from 1986.
    """

    __MIN_YEAR = 1986

    @classmethod
    def get_current_year(cls) -> int:
        """Get the current year.

        Returns:
            int: The current year
        """
        return date.today().year

    @classmethod
    def get_min_year(cls) -> int:
        """Get the minimum year for which historical data is available.

        Returns:
            int: The minimum year (1986 for B3 COTAHIST data)
        """
        return cls.__MIN_YEAR

    @classmethod
    def validate_and_create_year_range(
        cls, initial_year: int, last_year: int
    ) -> YearRange:
        """Validate a year range and create a YearRange value object.

        This method ensures that:
        1. Both years are integers
        2. initial_year is within valid bounds (__MIN_YEAR to current year)
        3. last_year is within valid bounds (__MIN_YEAR to current year)
        4. initial_year <= last_year

        Args:
            initial_year: The starting year for the range
            last_year: The ending year for the range

        Returns:
            YearRange: A validated year range value object

        Raises:
            InvalidFirstYear: If initial_year is invalid
            InvalidLastYear: If last_year is invalid
        """
        current_year = cls.get_current_year()

        if (
            not isinstance(initial_year, int)
            or initial_year < cls.__MIN_YEAR
            or initial_year > current_year
        ):
            raise InvalidFirstYear(cls.__MIN_YEAR, current_year)

        if (
            not isinstance(last_year, int)
            or last_year > current_year
            or initial_year > last_year
        ):
            raise InvalidLastYear(initial_year, current_year)

        return YearRange(initial_year=initial_year, last_year=last_year)
