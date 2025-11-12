"""Service for validating year ranges for historical data extraction.

This is a Domain Service that handles business logic related to year validation,
ensuring that requested year ranges are valid for B3 historical data.
"""

from datetime import date

from ..exceptions import InvalidFirstYear, InvalidLastYear
from ..value_objects.year_range import YearRange


class YearValidationService:
    """Domain service for validating year ranges.

    This service is stateless and contains business logic for validating
    that year ranges are appropriate for B3 historical quotes data extraction.

    The B3 COTAHIST files are available starting from 1986.
    """

    MIN_YEAR = 1986

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
        return cls.MIN_YEAR

    @classmethod
    def validate_and_create_year_range(
        cls, initial_year: int, last_year: int
    ) -> YearRange:
        """Validate a year range and create a YearRange value object.

        This method ensures that:
        1. Both years are integers
        2. initial_year is within valid bounds (MIN_YEAR to current year)
        3. last_year is within valid bounds (MIN_YEAR to current year)
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

        # Validate initial_year
        if (
            not isinstance(initial_year, int)
            or initial_year < cls.MIN_YEAR
            or initial_year > current_year
        ):
            raise InvalidFirstYear(cls.MIN_YEAR, current_year)

        # Validate last_year
        if (
            not isinstance(last_year, int)
            or last_year > current_year
            or initial_year > last_year
        ):
            raise InvalidLastYear(initial_year, current_year)

        # Create and return the YearRange value object
        return YearRange(initial_year=initial_year, last_year=last_year)

    @classmethod
    def is_valid_year(cls, year: int) -> bool:
        """Check if a specific year is valid for historical data.

        Args:
            year: The year to check

        Returns:
            bool: True if the year is valid, False otherwise
        """
        if not isinstance(year, int):
            return False
        return cls.MIN_YEAR <= year <= cls.get_current_year()

    @classmethod
    def get_valid_year_range_description(cls) -> str:
        """Get a description of the valid year range.

        Returns:
            str: Human-readable description of valid years
        """
        return f"Valid years: {cls.MIN_YEAR} to {cls.get_current_year()}"
