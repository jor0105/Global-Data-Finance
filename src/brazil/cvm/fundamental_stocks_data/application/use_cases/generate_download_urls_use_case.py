"""Use case for generating download URLs.

This module contains the use case responsible for generating
download URLs from validated request parameters.
"""

import logging
from typing import Dict, List

from ...domain import DictZipsToDownload
from ...exceptions import EmptyDocumentListError

logger = logging.getLogger(__name__)


class GenerateDownloadUrlsUseCase:
    """Use case for generating download URLs.

    This use case is responsible solely for generating the dictionary
    of download URLs based on document types and year ranges.

    Example:
        >>> generator = GenerateDownloadUrlsUseCase()
        >>> urls = generator.execute(
        ...     doc_types=["DFP", "ITR"],
        ...     start_year=2020,
        ...     end_year=2023
        ... )
        >>> print(len(urls))
        2
    """

    def __init__(self) -> None:
        """Initialize the URL generator use case."""
        self._dict_generator = DictZipsToDownload()
        logger.debug("GenerateDownloadUrlsUseCase initialized")

    def execute(
        self,
        doc_types: List[str],
        start_year: int,
        end_year: int,
    ) -> Dict[str, List[str]]:
        """Generate download URLs for specified documents and years.

        Args:
            doc_types: List of document type codes (e.g., ["DFP", "ITR"]).
            start_year: Starting year for downloads (inclusive).
            end_year: Ending year for downloads (inclusive).

        Returns:
            Dict mapping document types to lists of download URLs.

        Raises:
            EmptyDocumentListError: If doc_types is an empty list.
            InvalidDocName: If invalid document type is specified.
            InvalidTypeDoc: If document type is not a string.
            InvalidFirstYear: If start_year is outside valid range.
            InvalidLastYear: If end_year is outside valid range.

        Example:
            >>> generator = GenerateDownloadUrlsUseCase()
            >>> urls = generator.execute(["DFP"], 2020, 2021)
            >>> print(urls.keys())
            dict_keys(['DFP'])
            >>> print(len(urls['DFP']))
            2
        """
        logger.debug(
            f"Generating URLs for docs={doc_types}, " f"years={start_year}-{end_year}"
        )

        # Validate None or empty list
        if doc_types is None:
            raise TypeError("doc_types cannot be None")
        if not doc_types:
            raise EmptyDocumentListError()

        try:
            dict_zips = self._dict_generator.get_dict_zips_to_download(
                list_docs=doc_types,
                initial_year=start_year,
                last_year=end_year,
            )

            total_urls = sum(len(urls) for urls in dict_zips.values())
            logger.info(
                f"Generated {total_urls} URLs from " f"{len(dict_zips)} document types"
            )

            return dict_zips

        except Exception as e:
            logger.error(f"Failed to generate URLs: {e}")
            raise
