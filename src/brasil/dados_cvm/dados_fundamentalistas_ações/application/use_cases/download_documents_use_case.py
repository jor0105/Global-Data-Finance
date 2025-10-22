import logging
from typing import List, Optional

from ...domain import AvailableDocs, AvailableYears, DictZipsToDownload, DownloadResult
from ..dtos import DownloadPathDTO
from ..interfaces import DownloadDocsCVMRepository

logger = logging.getLogger(__name__)


class DownloadDocumentsUseCase:
    """Use case for downloading CVM documents.

    This orchestrates the business logic of downloading financial documents from CVM,
    including:
    - Validating document types and year ranges
    - Generating URLs
    - Delegating downloads to the repository
    - Logging and error handling

    Example:
        >>> repository = WgetDownloadAdapter()
        >>> use_case = DownloadDocumentsUseCase(repository)
        >>> result = use_case.execute(
        ...     destination_path="/path/to/download",
        ...     doc_types=["DFP", "ITR"],
        ...     start_year=2020,
        ...     end_year=2023
        ... )
        >>> print(f"Downloaded {result.success_count} files")
    """

    def __init__(self, repository: DownloadDocsCVMRepository) -> None:
        """Initialize the use case with a repository implementation.

        Args:
            repository: Implementation of DownloadDocsCVMRepository.
                       Typically WgetDownloadAdapter or another adapter.
        """
        if not isinstance(repository, DownloadDocsCVMRepository):
            raise TypeError(
                f"repository must be an instance of DownloadDocsCVMRepository, "
                f"got {type(repository).__name__}"
            )

        self._repository = repository
        self._dict_generator = DictZipsToDownload()
        self._available_docs = AvailableDocs()
        self._available_years = AvailableYears()

        logger.debug(
            f"DownloadDocumentsUseCase initialized with "
            f"repository={repository.__class__.__name__}"
        )

    def execute(
        self,
        destination_path: str,
        doc_types: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> DownloadResult:
        """Execute the download operation for specified documents and years.

        This method orchestrates the complete workflow:
        1. Validates input parameters using DownloadPathDTO
        2. Creates destination directory if it doesn't exist
        3. Generates URLs for all combinations
        4. Delegates to repository for actual downloads
        5. Returns combined results

        Args:
            destination_path: Directory path where files will be saved.
                             Will be created if it doesn't exist.
            doc_types: List of document type codes (e.g., ["DFP", "ITR"]).
                      If None, downloads all available document types.
            start_year: Starting year for downloads (inclusive).
                       If None, uses minimum available year for each document type.
            end_year: Ending year for downloads (inclusive).
                     If None, uses current year.

        Returns:
            DownloadResult containing successful downloads and encountered errors.

        Raises:
            TypeError: If repository is not a DownloadDocsCVMRepository instance.
            InvalidDocName: If invalid document type is specified.
            InvalidFirstYear: If start_year is outside valid range.
            InvalidLastYear: If end_year is outside valid range.
            ValueError: If destination_path is invalid (see DownloadPathDTO).
            OSError: If directory cannot be created due to permissions.
        """
        logger.info(
            f"Starting download use case: "
            f"path={destination_path}, "
            f"docs={doc_types}, "
            f"years={start_year}-{end_year}"
        )

        # Validate inputs using DTO
        try:
            request_dto = DownloadPathDTO(
                destination_path=destination_path,
                doc_types=doc_types,
                start_year=start_year,
                end_year=end_year,
            )
        except (TypeError, ValueError, OSError) as e:
            logger.error(f"Invalid download request: {e}")
            raise

        # Generate URLs
        try:
            dict_zips = self._dict_generator.get_dict_zips_to_download(
                list_docs=request_dto.doc_types,
                initial_year=request_dto.start_year,
                last_year=request_dto.end_year,
            )

            logger.info(
                f"Generated URLs: {sum(len(urls) for urls in dict_zips.values())} files "
                f"from {len(dict_zips)} document types"
            )

        except Exception as e:
            logger.error(f"Failed to generate URLs: {e}")
            raise

        # Delegate to repository
        try:
            result = self._repository.download_docs(
                request_dto.destination_path, dict_zips
            )

            logger.info(
                f"Download completed: "
                f"{result.success_count} successful, "
                f"{result.error_count} errors"
            )

            return result

        except Exception as e:
            logger.error(f"Download operation failed: {e}", exc_info=True)
            raise
