from ...domain import YearValidationService


class CreateRangeYearsUseCase:
    """Use case for creating and validating a range of years.

    This use case validates that the provided year range is appropriate
    for historical B3 data extraction and returns a validated YearRange
    value object.
    """

    @staticmethod
    def execute(initial_year: int, last_year: int) -> range:
        """Create and validate a range of years for data extraction.

        Args:
            initial_year: The starting year (inclusive)
            last_year: The ending year (inclusive)

        Returns:
            range: Python range object from initial_year to last_year (inclusive)

        Raises:
            InvalidFirstYear: If initial_year is invalid
            InvalidLastYear: If last_year is invalid
        """
        # Validate and create YearRange value object
        year_range = YearValidationService.validate_and_create_year_range(
            initial_year, last_year
        )

        # Return as Python range for backward compatibility
        return year_range.to_range()
