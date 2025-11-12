from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class YearRange:
    """Immutable value object representing a validated range of years.

    This represents a continuous period of years for which historical
    data should be extracted. Both bounds are inclusive.

    Attributes:
        initial_year: The starting year (inclusive)
        last_year: The ending year (inclusive)

    Examples:
        >>> year_range = YearRange(2020, 2024)
        >>> year_range.initial_year
        2020
        >>> year_range.last_year
        2024
        >>> list(year_range.to_range())
        [2020, 2021, 2022, 2023, 2024]
    """

    initial_year: int
    last_year: int

    def __post_init__(self) -> None:
        """Validate the year range after initialization.

        Raises:
            ValueError: If years are not integers or if the range is invalid
        """
        if not isinstance(self.initial_year, int) or not isinstance(
            self.last_year, int
        ):
            raise ValueError("Years must be integers")

        if self.initial_year > self.last_year:
            raise ValueError(
                f"Initial year ({self.initial_year}) cannot be greater than "
                f"last year ({self.last_year})"
            )

        current_year = date.today().year
        if self.last_year > current_year:
            raise ValueError(
                f"Last year ({self.last_year}) cannot be in the future "
                f"(current year: {current_year})"
            )

    def to_range(self) -> range:
        """Convert the year range to a Python range object.

        Returns:
            range: Python range from initial_year to last_year (inclusive)
        """
        return range(self.initial_year, self.last_year + 1)

    def contains(self, year: int) -> bool:
        """Check if a specific year is within this range.

        Args:
            year: The year to check

        Returns:
            bool: True if the year is in this range, False otherwise
        """
        return self.initial_year <= year <= self.last_year

    def span_years(self) -> int:
        """Calculate the number of years in this range.

        Returns:
            int: The number of years (inclusive)
        """
        return self.last_year - self.initial_year + 1

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            str: String representation of the year range
        """
        return f"{self.initial_year}-{self.last_year}"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            str: Detailed representation of the year range
        """
        return (
            f"YearRange(initial_year={self.initial_year}, last_year={self.last_year})"
        )
