from typing import List, Optional

from ...domain.entities.docs_to_extractor import DocsToExtractor
from .range_years_use_case import CreateRangeYearsUseCase
from .set_assets_use_case import CreateSetAssetsUseCase
from .set_docs_to_download_use_case import CreateSetToDownloadUseCase
from .validate_destination_path_use_case import VerifyDestinationPathsUseCase


class CreateDocsToExtractUseCase:
    def __init__(
        self,
        assets_list: List[str],
        initial_year: int,
        last_year: int,
        path_of_docs: str,
        destination_path: Optional[str] = None,
    ):
        self.assets_list = assets_list
        self.initial_year = initial_year
        self.last_year = last_year
        self.path_of_docs = path_of_docs
        self.destination_path = (
            destination_path if destination_path else self.path_of_docs
        )

    def execute(self) -> DocsToExtractor:
        set_assests = CreateSetAssetsUseCase.execute(self.assets_list)

        range_years = CreateRangeYearsUseCase.execute(self.initial_year, self.last_year)

        VerifyDestinationPathsUseCase().execute(self.destination_path)

        set_documents_to_download = CreateSetToDownloadUseCase.execute(
            range_years, self.path_of_docs
        )

        docs_to_extract = DocsToExtractor(
            set_assets=set_assests,
            range_years=range_years,
            path_of_docs=self.path_of_docs,
            destination_path=self.destination_path,
            set_documents_to_download=set_documents_to_download,
        )
        return docs_to_extract
