from ...domain import YearValidationServiceB3


class GetAvailableYearsUseCaseB3:
    def get_atual_year(self) -> int:
        """Get the current available year for historical quotes data.

        Returns:
            int: The current year
        """
        return YearValidationServiceB3.get_current_year()

    def get_minimal_year(self) -> int:
        """Get the minimal available year for historical quotes data.

        Returns:
            int: The minimum year (1986 for B3 COTAHIST data)
        """
        return YearValidationServiceB3.get_min_year()
