from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class AssetClass:
    """Immutable value object representing an asset class.

    This represents a specific type of financial instrument traded on B3,
    along with its corresponding TPMERC codes used in COTAHIST files.

    Attributes:
        name: The identifier of the asset class (e.g., "ações", "etf")
        tpmerc_codes: Tuple of TPMERC codes associated with this asset class
        description: Optional human-readable description of the asset class

    Examples:
        >>> stocks = AssetClass("ações", ("010", "020"), "Ações no mercado à vista")
        >>> stocks.name
        'ações'
        >>> stocks.tpmerc_codes
        ('010', '020')
    """

    name: str
    tpmerc_codes: Tuple[str, ...]
    description: str = ""

    def __post_init__(self) -> None:
        """Validate the asset class attributes after initialization.

        Raises:
            ValueError: If name is empty or tpmerc_codes is empty
        """
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Asset class name must be a non-empty string")

        if not self.tpmerc_codes or not all(
            isinstance(code, str) for code in self.tpmerc_codes
        ):
            raise ValueError("TPMERC codes must be a non-empty tuple of strings")

        # Ensure all codes are exactly 3 digits
        if not all(len(code) == 3 and code.isdigit() for code in self.tpmerc_codes):
            raise ValueError("TPMERC codes must be 3-digit strings")

    def has_code(self, tpmerc_code: str) -> bool:
        """Check if this asset class includes a specific TPMERC code.

        Args:
            tpmerc_code: The TPMERC code to check

        Returns:
            bool: True if the code is in this asset class, False otherwise
        """
        return tpmerc_code in self.tpmerc_codes

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            str: The asset class name
        """
        return self.name

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            str: Detailed representation including name and codes
        """
        return f"AssetClass(name='{self.name}', tpmerc_codes={self.tpmerc_codes})"
