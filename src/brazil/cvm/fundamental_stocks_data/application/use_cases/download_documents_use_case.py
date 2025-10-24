import logging
from typing import List, Optional

from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
from src.brazil.cvm.fundamental_stocks_data.exceptions import InvalidRepositoryTypeError

from ..interfaces import DownloadDocsCVMRepository
from .generate_range_years_use_cases import GenerateRangeYearsUseCases
from .generate_urls_use_case import GenerateUrlsUseCase
from .verify_paths_use_cases import VerifyPathsUseCases

logger = logging.getLogger(__name__)


class DownloadDocumentsUseCase:
    """Orchestrator use case for downloading CVM documents.

    This use case orchestrates the complete download workflow by coordinating
    multiple smaller, focused use cases following the Single Responsibility Principle:
    - Verify and Create Paths
    - Generation of range of years
    - Generation of download URLs
    - Execution of downloads via repository

    This orchestrator pattern allows for:
    - Better testability (each sub-use case can be tested in isolation)
    - Reusability (URL generation can be used independently)
    - Maintainability (changes to validation don't affect URL generation)

    Example:
        >>> repository = ThreadPoolDownloadAdapter()  # Recommended for performance
        >>> use_case = DownloadDocumentsUseCase(repository)
        >>> result = use_case.execute(
        ...     destination_path="/path/to/download",
        ...     list_docs=["DFP", "ITR"],
        ...     initial_year=2020,
        ...     last_year=2023
        ... )
        >>> print(f"Downloaded {result.success_count} files")
    """

    def __init__(self, repository: DownloadDocsCVMRepository) -> None:
        """Initialize the orchestrator with a repository and sub-use cases.

        Args:
            repository: Implementation of DownloadDocsCVMRepository.
                       Options: ThreadPoolDownloadAdapter (recommended),
                               Aria2cAdapter (maximum speed),
                               WgetDownloadAdapter (compatibility)
        """
        if not isinstance(repository, DownloadDocsCVMRepository):
            raise InvalidRepositoryTypeError(
                actual_type=type(repository).__name__,
            )

        self.__repository = repository
        self.__url_generator = GenerateUrlsUseCase()
        self.__range_years_generator = GenerateRangeYearsUseCases()

        logger.debug(
            f"DownloadDocumentsUseCase initialized with "
            f"repository={repository.__class__.__name__}"
        )

    def execute(
        self,
        destination_path: str,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> DownloadResult:
        """Execute the download operation by orchestrating sub-use cases.

        This method coordinates the complete workflow:

        Args:
            destination_path: Directory path where files will be saved.
                             Will be created if it doesn't exist.
            list_docs: List of document type codes (e.g., ["DFP", "ITR"]).
                      If None, downloads all available document types.
            initial_year: Starting year for downloads (inclusive).
                       If None, uses minimum available year for each document type.
            last_year: Ending year for downloads (inclusive).
                     If None, uses current year.

        Returns:
            DownloadResult containing successful downloads and encountered errors.

        Raises:
            InvalidRepositoryTypeError: If repository is not a DownloadDocsCVMRepository instance.
            InvalidDestinationPathError: If path is invalid (empty, whitespace, or wrong type).
            PathIsNotDirectoryError: If path exists but is a file.
            PathPermissionError: If path lacks write permissions.
            EmptyDocumentListError: If list_docs is an empty list.
            InvalidDocName: If invalid document type is specified.
            InvalidTypeDoc: If document type is not a string.
            InvalidFirstYear: If initial_year is outside valid range.
            InvalidLastYear: If last_year is outside valid range.
            OSError: If directory cannot be created.
        """
        logger.info(
            f"Starting download orchestration: "
            f"path={destination_path}, "
            f"docs={list_docs}, "
            f"years={initial_year}-{last_year}"
        )

        range_years = self.__range_years_generator.execute(
            initial_year=initial_year,
            last_year=last_year,
        )

        dict_urls_zips, new_set_docs = self.__url_generator.execute(
            list_docs=list_docs,
            initial_year=initial_year,
            last_year=last_year,
        )

        verify_paths = VerifyPathsUseCases(
            destination_path=destination_path,
            new_set_docs=new_set_docs,
            range_years=range_years,
        )
        verify_paths.execute()

        try:
            result = self.__repository.download_docs(destination_path, dict_urls_zips)

            logger.info(
                f"Download completed: "
                f"✓ {result.success_count} successful, "
                f"✗ {result.error_count} errors"
            )

            if result.successful_downloads:
                logger.debug(
                    f"Successfully downloaded: {', '.join(result.successful_downloads)}"
                )

            if result.failed_downloads:
                failed_info = "; ".join(
                    [
                        f"{doc}: {error}"
                        for doc, error in result.failed_downloads.items()
                    ]
                )
                logger.warning(f"Failed downloads: {failed_info}")

            return result

        except Exception as e:
            logger.error(f"Download execution failed: {e}", exc_info=True)
            raise
