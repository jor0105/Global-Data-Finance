from dataclasses import dataclass, field
from typing import List

from ..value_objects import AvailableAssets, AvailableYears, DocumentListToDownload


@dataclass
class DocsToExtractor:
    assets_list: List[str]
    initial_year: int
    last_year: int
    range_years: List[int] = field(default_factory=list)
    document_list_to_download: DocumentListToDownload = field(
        default_factory=DocumentListToDownload
    )

    def __post_init__(self):
        AvailableAssets.validate_assets(self.assets_list)
        self.range_years = AvailableYears().return_range_years(
            self.initial_year, self.last_year
        )
