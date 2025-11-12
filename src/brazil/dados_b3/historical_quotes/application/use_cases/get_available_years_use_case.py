from ...domain import YearValidationService


class GetAvailableYearsUseCase:
    """Use case for retrieving available years range for historical quotes data."""

    def get_atual_year(self) -> int:
        """Get the current available year for historical quotes data.

        Returns:
            int: The current year
        """
        return YearValidationService.get_current_year()

    def get_minimal_year(self) -> int:
        """Get the minimal available year for historical quotes data.

        Returns:
            int: The minimum year (1986 for B3 COTAHIST data)
        """
        return YearValidationService.get_min_year()
