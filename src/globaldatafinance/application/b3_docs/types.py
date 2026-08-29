"""Public typed contracts for the B3 historical quotes facade."""

from typing import TypedDict


class ExtractionResultB3(TypedDict):
    """Public shape of the dict returned by ``HistoricalQuotesB3.extract``.

    It is a required-field ``TypedDict`` (not a dataclass) so existing
    ``result['key']`` access keeps working, while consumers gain type checking
    and editor autocomplete on the complete public contract. Every public
    extraction response contains all declared fields, including when no
    matching input file is found.
    """

    success: bool
    message: str
    total_files: int
    success_count: int
    error_count: int
    total_records: int
    output_file: str
    errors: dict[str, str]
    assets: list[str]
    processing_mode: str
    elapsed_time: float
