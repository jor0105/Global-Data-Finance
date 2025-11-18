from typing import List, Optional

from ...domain import DocsToExtractorB3
from .range_years_use_case import CreateRangeYearsUseCaseB3
from .set_assets_use_case import CreateSetAssetsUseCaseB3
from .set_docs_to_download_use_case import CreateSetToDownloadUseCaseB3
from .validate_destination_path_use_case import VerifyDestinationPathsUseCaseB3


class CreateDocsToExtractUseCaseB3:
    """Use case for creating a DocsToExtractorB3 entity with validated parameters.

    This class orchestrates all validation and construction logic following
    Clean Architecture principles. The Application layer (this use case)
    coordinates Domain services and uses the Domain builder only for entity
    construction.

    Example:
        >>> use_case = CreateDocsToExtractUseCaseB3(
        ...     path_of_docs="/path/to/cotahist",
        ...     assets_list=["ações", "etf"],
        ...     initial_year=2020,
        ...     last_year=2023,
        ... )
        >>> docs = use_case.execute()
    """

    def __init__(
        self,
        path_of_docs: str,
        assets_list: List[str],
        initial_year: int,
        last_year: int,
        destination_path: Optional[str] = None,
    ):
        """Initialize the use case with extraction parameters.

        Args:
            path_of_docs: Directory containing COTAHIST ZIP files
            assets_list: List of asset class codes to extract
            initial_year: Starting year for extraction (inclusive)
            last_year: Ending year for extraction (inclusive)
            destination_path: Output directory (defaults to path_of_docs)
        """
        self.path_of_docs = path_of_docs
        self.assets_list = assets_list
        self.initial_year = initial_year
        self.last_year = last_year
        self.destination_path = destination_path if destination_path else path_of_docs

    def execute(self) -> DocsToExtractorB3:
        """Execute the use case to create a validated DocsToExtractorB3 entity.

        This method orchestrates all validations using Domain services and
        other use cases, then uses the Domain builder to construct the entity.

        Returns:
            DocsToExtractorB3: Entity containing all validated extraction parameters

        Raises:
            Various exceptions: For validation failures
        """
        set_assets = CreateSetAssetsUseCaseB3.execute(self.assets_list)

        range_years = CreateRangeYearsUseCaseB3.execute(
            self.initial_year, self.last_year
        )

        VerifyDestinationPathsUseCaseB3().execute(self.destination_path)
        set_documents_to_download = CreateSetToDownloadUseCaseB3.execute(
            range_years, self.path_of_docs
        )

        builder = DocsToExtractorB3(
            path_of_docs=self.path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=self.destination_path,
            set_documents_to_download=set_documents_to_download,
        )
        return builder
