from dataclasses import dataclass, field
from typing import Set


@dataclass
class DocsToExtractor:
    path_of_docs: str
    set_assets: Set[str]
    range_years: range
    destination_path: str
    set_documents_to_download: Set[str] = field(default_factory=set)
