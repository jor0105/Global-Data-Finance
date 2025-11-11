from typing import Any, Dict, Optional, Protocol, Set


class ICotahistParser(Protocol):
    """Interface for parsing COTAHIST file format."""

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

        Example return:
            {
                'data_pregao': date(2023, 1, 2),
                'codbdi': '02',
                'codneg': 'PETR4',
                'tpmerc': '010',
                'nomres': 'PETROBRAS',
                'especi': 'ON',
                'preabe': Decimal('28.50'),
                'premax': Decimal('29.10'),
                'premin': Decimal('28.40'),
                'premed': Decimal('28.75'),
                'preult': Decimal('28.90'),
                'preofc': Decimal('28.89'),
                'preofv': Decimal('28.91'),
                'totneg': 12345,
                'quatot': 1000000,
                'voltot': Decimal('28750000.00'),
                'fatcot': 1,
                'codisi': 'BRPETRACNOR9',
            }
        """
        ...
