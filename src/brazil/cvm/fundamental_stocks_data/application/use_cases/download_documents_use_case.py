"""Use case for orchestrating CVM document downloads.

This module contains the main orchestrator use case that coordinates
the validation, URL generation, and download execution following
the Single Responsibility Principle.
"""

import logging
from typing import List, Optional

from ...domain import DownloadResult
from ...exceptions import InvalidRepositoryTypeError
from ..interfaces import DownloadDocsCVMRepository
from .generate_download_urls_use_case import GenerateDownloadUrlsUseCase
from .validate_download_request_use_case import ValidateDownloadRequestUseCase

logger = logging.getLogger(__name__)


class DownloadDocumentsUseCase:
    """Orchestrator use case for downloading CVM documents.

    This use case orchestrates the complete download workflow by coordinating
    multiple smaller, focused use cases following the Single Responsibility Principle:
    - Validation of request parameters
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
        ...     doc_types=["DFP", "ITR"],
        ...     start_year=2020,
        ...     end_year=2023
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
                expected_type="DownloadDocsCVMRepository",
                actual_type=type(repository).__name__,
            )

        self._repository = repository
        self._validator = ValidateDownloadRequestUseCase()
        self._url_generator = GenerateDownloadUrlsUseCase()

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
        """Execute the download operation by orchestrating sub-use cases.

        This method coordinates the complete workflow:
        1. Validates input parameters (ValidateDownloadRequestUseCase)
        2. Generates download URLs (GenerateDownloadUrlsUseCase)
        3. Executes downloads via repository
        4. Returns combined results

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
            InvalidRepositoryTypeError: If repository is not a DownloadDocsCVMRepository instance.
            InvalidDestinationPathError: If path is invalid (empty, whitespace, or wrong type).
            PathIsNotDirectoryError: If path exists but is a file.
            PathPermissionError: If path lacks write permissions.
            EmptyDocumentListError: If doc_types is an empty list.
            InvalidDocName: If invalid document type is specified.
            InvalidTypeDoc: If document type is not a string.
            InvalidFirstYear: If start_year is outside valid range.
            InvalidLastYear: If end_year is outside valid range.
            OSError: If directory cannot be created.
        """
        logger.info(
            f"Starting download orchestration: "
            f"path={destination_path}, "
            f"docs={doc_types}, "
            f"years={start_year}-{end_year}"
        )

        # Step 1: Validate request (fills defaults for None values)
        request_dto = self._validator.execute(
            destination_path=destination_path,
            doc_types=doc_types,
            start_year=start_year,
            end_year=end_year,
        )

        # Step 2: Generate URLs
        dict_zips = self._url_generator.execute(
            doc_types=request_dto.doc_types,
            start_year=request_dto.start_year,
            end_year=request_dto.end_year,
        )

        # Step 3: Execute downloads
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
            logger.error(f"Download execution failed: {e}", exc_info=True)
            raise
