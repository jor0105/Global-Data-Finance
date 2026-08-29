"""Batch parsing helper used by the parallel B3 extraction path."""

from ..cotahist_parser import CotahistParserB3
from .types import ParsedRecord


def parse_lines_batch(
    lines: list[str], target_tpmerc_codes: set[str]
) -> list[ParsedRecord]:
    """Parse a batch of lines using a fresh parser instance.

    A new ``CotahistParserB3`` is created per batch on purpose: this runs in a
    thread pool worker (parallel/fast mode) and the parser keeps mutable
    per-instance counters, so it is not safe to share one across threads. The
    output is kept identical to the sequential (slow) path: both drop records
    that parse to ``None`` (header/trailer, filtered, malformed, or records
    whose parse failed catastrophically).
    """
    parser = CotahistParserB3()
    parsed = [parser.parse_line(line, target_tpmerc_codes) for line in lines]
    return [record for record in parsed if record is not None]
