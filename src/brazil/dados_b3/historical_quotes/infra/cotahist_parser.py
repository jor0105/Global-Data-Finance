from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Set


class CotahistParser:
    """Parser for COTAHIST fixed-width format files from B3.

    Each line is 245 bytes. The parser follows the official B3 layout specification.
    """

    def parse_line(
        self, line: str, target_tpmerc_codes: Set[str]
    ) -> Optional[Dict[str, Any]]:
        """Parse a single line from COTAHIST file.

        Args:
            line: A 245-byte line from COTAHIST file
            target_tpmerc_codes: Set of TPMERC codes to filter (e.g., {'010', '020'})

        Returns:
            Dictionary with parsed data if TPMERC matches filter, None otherwise
            Returns None for header (00) and trailer (99) records
        """
        if len(line) < 245:
            # Pad line if too short
            line = line.ljust(245)

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

    def _parse_quote_record(self, line: str) -> Dict[str, Any]:
        """Parse a type 01 (quote) record.

        Field positions are 1-indexed in the specification.
        Python uses 0-indexed slicing, so we subtract 1 from start positions.
        """
        return {
            # Data do Pregão (positions 3-10)
            "data_pregao": self._parse_date(line[2:10]),
            # Código BDI (positions 11-12)
            "codbdi": line[10:12].strip(),
            # Código de Negociação - Ticker (positions 13-24)
            "codneg": line[12:24].strip(),
            # Tipo de Mercado (positions 25-27)
            "tpmerc": line[24:27].strip(),
            # Nome Resumido (positions 28-39)
            "nomres": line[27:39].strip(),
            # Especificação do Papel (positions 40-49)
            "especi": line[39:49].strip(),
            # Preço de Abertura (positions 57-69, format (11)V99)
            "preabe": self._parse_decimal_v99(line[56:69]),
            # Preço Máximo (positions 70-82, format (11)V99)
            "premax": self._parse_decimal_v99(line[69:82]),
            # Preço Mínimo (positions 83-95, format (11)V99)
            "premin": self._parse_decimal_v99(line[82:95]),
            # Preço Médio (positions 96-108, format (11)V99)
            "premed": self._parse_decimal_v99(line[95:108]),
            # Preço de Fechamento (positions 109-121, format (11)V99)
            "preult": self._parse_decimal_v99(line[108:121]),
            # Melhor Oferta de Compra (positions 122-134, format (11)V99)
            "preofc": self._parse_decimal_v99(line[121:134]),
            # Melhor Oferta de Venda (positions 135-147, format (11)V99)
            "preofv": self._parse_decimal_v99(line[134:147]),
            # Número de Negócios (positions 148-152)
            "totneg": self._parse_int(line[147:152]),
            # Quantidade Total (positions 153-170)
            "quatot": self._parse_int(line[152:170]),
            # Volume Total (positions 171-188, format (16)V99)
            "voltot": self._parse_decimal_v99(line[170:188]),
            # Data de Vencimento (positions 203-210) - for options/term
            "datven": (
                self._parse_date(line[202:210]) if line[202:210].strip() else None
            ),
            # Fator de Cotação (positions 211-217)
            "fatcot": self._parse_int(line[210:217]),
            # Código ISIN (positions 231-242)
            "codisi": line[230:242].strip(),
            # Número de Distribuição (positions 243-245)
            "dismes": self._parse_int(line[242:245]),
        }

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
