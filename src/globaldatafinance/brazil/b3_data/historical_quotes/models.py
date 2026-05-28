"""Data models for B3 historical quotes extraction."""

from dataclasses import dataclass, field


@dataclass
class DocsToExtractorB3:
    path_of_docs: str
    set_assets: set[str]
    range_years: range
    destination_path: str
    documents_to_download: set[str] = field(default_factory=set)
