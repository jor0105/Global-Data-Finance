from ..cotahist_parser import CotahistParserB3
from .types import ParsedRecord


def parse_lines_batch(
    lines: list[str], target_tpmerc_codes: set[str]
) -> list[ParsedRecord]:
    """Parse a batch of lines using a fresh parser instance."""
    parser = CotahistParserB3()
    parsed = [parser.parse_line(line, target_tpmerc_codes) for line in lines]
    return [record for record in parsed if record is not None]
