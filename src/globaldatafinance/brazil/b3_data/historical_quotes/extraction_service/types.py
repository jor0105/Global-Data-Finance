from typing import Any, TypedDict


ParsedRecord = dict[str, Any]


class ZipProcessingResult(TypedDict):
    records: int
    temp_file: str


class ExtractionSummary(TypedDict):
    total_files: int
    success_count: int
    error_count: int
    total_records: int
    errors: dict[str, str]
    output_file: str


ProcessSingleFileResult = tuple[str, ZipProcessingResult | Exception]
