from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Set

from src.core import get_logger

logger = get_logger(__name__)


class CotahistParser:
    """Parser for COTAHIST fixed-width format files from B3.

    Each line is 245 bytes. The parser follows the official B3 layout specification.
    Includes robust error handling and validation for malformed data.
    """

    # Expected line length for COTAHIST format
    EXPECTED_LINE_LENGTH = 245

    # Maximum allowed line length (safety limit)
    MAX_LINE_LENGTH = 1000

    # Counter for tracking parse errors
    _error_count = 0
    _max_errors_to_log = 10  # Only log first 10 errors to avoid spam

    def parse_line(
        self, line: str, target_tpmerc_codes: Set[str]
    ) -> Optional[Dict[str, Any]]:
        """Parse a single line from COTAHIST file with robust error handling.

        Args:
            line: A line from COTAHIST file (expected 245 bytes)
            target_tpmerc_codes: Set of TPMERC codes to filter (e.g., {'010', '020'})

        Returns:
            Dictionary with parsed data if TPMERC matches filter, None otherwise
            Returns None for header (00), trailer (99), invalid, or malformed records
        """
        if len(line) > self.MAX_LINE_LENGTH:
            if self._error_count < self._max_errors_to_log:
                logger.warning(
                    f"Line exceeds maximum length ({len(line)} > {self.MAX_LINE_LENGTH}), skipping"
                )
                self._error_count += 1
            return None

        # Ensure line is at least long enough for type check
        if len(line) < 2:
            return None

        # Pad or truncate line to expected length
        if len(line) < self.EXPECTED_LINE_LENGTH:
            line = line.ljust(self.EXPECTED_LINE_LENGTH)
        elif len(line) > self.EXPECTED_LINE_LENGTH:
            line = line[: self.EXPECTED_LINE_LENGTH]

        try:
            # Check record type (positions 1-2, Python index 0-2)
            tipreg = line[0:2]

            # Skip header and trailer
            if tipreg in ("00", "99"):
                return None

            # Only process quote records (type 01)
            if tipreg != "01":
                return None

            # Extract TPMERC (positions 25-27, Python index 24-27)
            tpmerc = line[24:27].strip()

            # Filter by target market types
            if tpmerc not in target_tpmerc_codes:
                return None

            # Parse all fields for matching records
            return self._parse_quote_record(line)

        except (IndexError, ValueError, AttributeError) as e:
            if self._error_count < self._max_errors_to_log:
                logger.warning(
                    f"Error parsing line (error #{self._error_count + 1}): {type(e).__name__} - {e}",
                    extra={"line_preview": line[:50] if len(line) >= 50 else line},
                )
                self._error_count += 1
            return None
        except Exception as e:
            if self._error_count < self._max_errors_to_log:
                logger.error(
                    f"Unexpected error parsing line: {e}",
                    extra={"line_preview": line[:50] if len(line) >= 50 else line},
                    exc_info=True,
                )
                self._error_count += 1

            return None

    def _parse_quote_record(self, line: str) -> Dict[str, Any]:
        """Parse a type 01 (quote) record with safe field extraction.

        Field positions are 1-indexed in the specification.
        Python uses 0-indexed slicing, so we subtract 1 from start positions.

        Args:
            line: A 245-character line from COTAHIST file

        Returns:
            Dictionary with parsed fields
        """
        try:
            return {
                # Data do Pregão (positions 3-10)
                "data_pregao": self._parse_date(self._safe_slice(line, 2, 10)),
                # Código BDI (positions 11-12)
                "codbdi": self._safe_slice(line, 10, 12).strip(),
                # Código de Negociação - Ticker (positions 13-24)
                "codneg": self._safe_slice(line, 12, 24).strip(),
                # Tipo de Mercado (positions 25-27)
                "tpmerc": self._safe_slice(line, 24, 27).strip(),
                # Nome Resumido (positions 28-39)
                "nomres": self._safe_slice(line, 27, 39).strip(),
                # Especificação do Papel (positions 40-49)
                "especi": self._safe_slice(line, 39, 49).strip(),
                # Preço de Abertura (positions 57-69, format (11)V99)
                "preabe": self._parse_decimal_v99(self._safe_slice(line, 56, 69)),
                # Preço Máximo (positions 70-82, format (11)V99)
                "premax": self._parse_decimal_v99(self._safe_slice(line, 69, 82)),
                # Preço Mínimo (positions 83-95, format (11)V99)
                "premin": self._parse_decimal_v99(self._safe_slice(line, 82, 95)),
                # Preço Médio (positions 96-108, format (11)V99)
                "premed": self._parse_decimal_v99(self._safe_slice(line, 95, 108)),
                # Preço de Fechamento (positions 109-121, format (11)V99)
                "preult": self._parse_decimal_v99(self._safe_slice(line, 108, 121)),
                # Melhor Oferta de Compra (positions 122-134, format (11)V99)
                "preofc": self._parse_decimal_v99(self._safe_slice(line, 121, 134)),
                # Melhor Oferta de Venda (positions 135-147, format (11)V99)
                "preofv": self._parse_decimal_v99(self._safe_slice(line, 134, 147)),
                # Número de Negócios (positions 148-152)
                "totneg": self._parse_int(self._safe_slice(line, 147, 152)),
                # Quantidade Total (positions 153-170)
                "quatot": self._parse_int(self._safe_slice(line, 152, 170)),
                # Volume Total (positions 171-188, format (16)V99)
                "voltot": self._parse_decimal_v99(self._safe_slice(line, 170, 188)),
                # Data de Vencimento (positions 203-210) - for options/term
                "datven": self._parse_date_optional(self._safe_slice(line, 202, 210)),
                # Fator de Cotação (positions 211-217)
                "fatcot": self._parse_int(self._safe_slice(line, 210, 217)),
                # Código ISIN (positions 231-242)
                "codisi": self._safe_slice(line, 230, 242).strip(),
                # Número de Distribuição (positions 243-245)
                "dismes": self._parse_int(self._safe_slice(line, 242, 245)),
            }
        except Exception as e:
            logger.error(f"Error parsing quote record: {e}", exc_info=True)
            return {
                "data_pregao": None,
                "codbdi": "",
                "codneg": "",
                "tpmerc": "",
                "nomres": "",
                "especi": "",
                "preabe": Decimal("0"),
                "premax": Decimal("0"),
                "premin": Decimal("0"),
                "premed": Decimal("0"),
                "preult": Decimal("0"),
                "preofc": Decimal("0"),
                "preofv": Decimal("0"),
                "totneg": 0,
                "quatot": 0,
                "voltot": Decimal("0"),
                "datven": None,
                "fatcot": 0,
                "codisi": "",
                "dismes": 0,
            }

    def _safe_slice(self, line: str, start: int, end: int) -> str:
        """Safely slice a string with bounds checking.

        Args:
            line: String to slice
            start: Start index
            end: End index

        Returns:
            Sliced string, empty if indices are out of bounds
        """
        try:
            if start < 0 or end > len(line) or start >= end:
                return ""
            return line[start:end]
        except Exception:
            return ""

    def _parse_date_optional(self, date_str: str) -> Optional[date]:
        """Parse optional date field.

        Args:
            date_str: Date string in YYYYMMDD format

        Returns:
            date object or None if empty/invalid
        """
        date_str = date_str.strip()
        if not date_str or date_str == "00000000":
            return None
        return self._parse_date(date_str)

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date in YYYYMMDD format.

        Args:
            date_str: Date string in YYYYMMDD format

        Returns:
            date object or None if invalid
        """
        date_str = date_str.strip()
        if not date_str or date_str == "00000000":
            return None

        try:
            return datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            return None

    def _parse_decimal_v99(self, value_str: str) -> Decimal:
        """Parse decimal value with 2 implied decimal places.

        Format (X)V99 means the value has 2 implicit decimal places.
        Example: "0000001234567" represents 12345.67

        Args:
            value_str: String representation of the number

        Returns:
            Decimal value with proper decimal places
        """
        value_str = value_str.strip()
        if not value_str:
            return Decimal("0")

        try:
            # Convert to Decimal and divide by 100 for 2 decimal places
            return Decimal(value_str) / Decimal("100")
        except (ValueError, InvalidOperation):
            return Decimal("0")

    def _parse_int(self, value_str: str) -> int:
        """Parse integer value.

        Args:
            value_str: String representation of the integer

        Returns:
            Integer value
        """
        value_str = value_str.strip()
        if not value_str:
            return 0

        try:
            return int(value_str)
        except ValueError:
            return 0
