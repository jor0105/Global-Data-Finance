"""Use case for validating download requests.

This module contains the use case responsible for validating
download request parameters following the Single Responsibility Principle.
"""

import logging
from typing import List, Optional

from ..dtos import DownloadPathDTO

logger = logging.getLogger(__name__)


class ValidateDownloadRequestUseCase:
    """Use case for validating download request parameters.

    This use case is responsible solely for validating input parameters
    for download requests, ensuring they meet all business rules and
    constraints.

    Example:
        >>> validator = ValidateDownloadRequestUseCase()
        >>> validated_dto = validator.execute(
        ...     destination_path="/path/to/download",
        ...     doc_types=["DFP", "ITR"],
        ...     start_year=2020,
        ...     end_year=2023
        ... )
        >>> print(validated_dto.destination_path)
        /path/to/download
    """

    def execute(
        self,
        destination_path: str,
        doc_types: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> DownloadPathDTO:
        """Validate download request parameters.

        Args:
            destination_path: Directory path where files will be saved.
            doc_types: List of document type codes (e.g., ["DFP", "ITR"]).
                      If None, uses all available document types.
            start_year: Starting year for downloads (inclusive).
                       If None, uses minimum available year.
            end_year: Ending year for downloads (inclusive).
                     If None, uses current year.

        Returns:
            DownloadPathDTO: Validated and normalized request parameters with defaults filled.

        Raises:
            InvalidDestinationPathError: If path is invalid (empty, whitespace, or wrong type).
            PathIsNotDirectoryError: If path exists but is a file.
            PathPermissionError: If path lacks write permissions.
            EmptyDocumentListError: If doc_types is an empty list.
            InvalidDocName: If invalid document type is specified.
            InvalidTypeDoc: If document type is not a string.
            InvalidFirstYear: If start_year is outside valid range.
            InvalidLastYear: If end_year is outside valid range.
            OSError: If destination_path cannot be created.

        Example:
            >>> validator = ValidateDownloadRequestUseCase()
            >>> try:
            ...     dto = validator.execute("/invalid/path", ["INVALID"], 1900, 2030)
            ... except (ValueError, InvalidDocName) as e:
            ...     print(f"Validation failed: {e}")
        """
        from ...domain import AvailableDocs, AvailableYears

        logger.debug(
            f"Validating download request: "
            f"path={destination_path}, docs={doc_types}, "
            f"years={start_year}-{end_year}"
        )

        # Fill defaults before validation
        final_doc_types = doc_types
        if final_doc_types is None:
            available_docs = AvailableDocs()
            final_doc_types = list(available_docs.get_available_docs().keys())

        available_years = AvailableYears()
        final_start_year = (
            start_year
            if start_year is not None
            else available_years.get_minimal_geral_year()
        )
        final_end_year = (
            end_year if end_year is not None else available_years.get_atual_year()
        )

        try:
            request_dto = DownloadPathDTO(
                destination_path=destination_path,
                doc_types=final_doc_types,
                start_year=final_start_year,
                end_year=final_end_year,
            )

            doc_count = (
                len(request_dto.doc_types)
                if request_dto.doc_types is not None
                else "all"
            )
            logger.info(
                f"Request validated successfully: "
                f"{doc_count} document types, "
                f"years {request_dto.start_year}-{request_dto.end_year}"
            )

            return request_dto

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
