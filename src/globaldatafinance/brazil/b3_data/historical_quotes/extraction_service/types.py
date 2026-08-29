"""Typed result mappings shared by B3 extraction service collaborators."""

from typing import Any, TypedDict

ParsedRecord = dict[str, Any]


class ZipProcessingResult(TypedDict):
    """Result fields reported after processing one COTAHIST input."""

    records: int
    temp_file: str


class ExtractionSummary(TypedDict):
    """Aggregate result fields reported for an extraction run."""

    total_files: int
    success_count: int
    error_count: int
    total_records: int
    errors: dict[str, str]
    output_file: str


ProcessSingleFileResult = tuple[str, ZipProcessingResult | Exception]
