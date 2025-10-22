"""User-friendly interface for downloading CVM fundamental stocks data.

This module provides a simple, high-level API for working with CVM
financial documents, making it easy to download and discover available data.

Example:
    >>> from datafin.cvm_docs import FundamentalStocksData
    >>>
    >>> # Initialize the client
    >>> cvm = FundamentalStocksData()
    >>>
    >>> # See available document types
    >>> docs = cvm.get_available_docs()
    >>> print(docs)
    >>>
    >>> # See available years
    >>> years = cvm.get_available_years()
    >>> print(years)
    >>>
    >>> # Download documents
    >>> result = cvm.download(
    ...     destination_path="/path/to/save",
    ...     doc_types=["DFP", "ITR"],
    ...     start_year=2020,
    ...     end_year=2023
    ... )
    >>> print(f"Downloaded {result.success_count} files successfully")
"""

import logging
from typing import Dict, List, Optional

from ...brazil.dados_cvm.fundamental_stocks_data.application.use_cases import (
    DownloadDocumentsUseCase,
    GetAvailableDocsUseCase,
    GetAvailableYearsUseCase,
)
from ...brazil.dados_cvm.fundamental_stocks_data.domain import DownloadResult
from ...brazil.dados_cvm.fundamental_stocks_data.infra.adapters import (
    WgetDownloadAdapter,
)

logger = logging.getLogger(__name__)


class FundamentalStocksData:
    """High-level interface for CVM fundamental stocks data operations.

    This class provides a simple API for downloading CVM financial documents
    and discovering available data. It uses the WgetDownloadAdapter by default
    for reliable downloads with automatic retry logic.

    Attributes:
        None - all dependencies are managed internally

    Example:
        >>> # Basic usage
        >>> cvm = FundamentalStocksData()
        >>>
        >>> # Download all document types for recent years
        >>> result = cvm.download(
        ...     destination_path="/home/user/cvm_data",
        ...     start_year=2022
        ... )
        >>>
        >>> # Download specific documents
        >>> result = cvm.download(
        ...     destination_path="/home/user/cvm_data",
        ...     doc_types=["DFP"],
        ...     start_year=2020,
        ...     end_year=2023
        ... )
        >>>
        >>> if result.has_errors():
        ...     print(f"Some downloads failed: {result.errors}")
    """

    def __init__(self):
        """Initialize the CVM data client.

        Example:
            >>> cvm = FundamentalStocksData()
        """
        # Initialize the download adapter with default configuration
        self._download_adapter = WgetDownloadAdapter()

        # Initialize use cases
        self._download_use_case = DownloadDocumentsUseCase(self._download_adapter)
        self._available_docs_use_case = GetAvailableDocsUseCase()
        self._available_years_use_case = GetAvailableYearsUseCase()

        logger.info("FundamentalStocksData client initialized")

    def download(
        self,
        destination_path: str,
        doc_types: Optional[List[str]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> DownloadResult:
        """Download CVM financial documents to a specified location.

        This method handles the complete download process, including:
        - Creating the destination directory if needed
        - Validating document types and year ranges
        - Downloading all requested documents with automatic retry
        - Providing detailed results and error information

        Args:
            destination_path: Directory path where files will be saved.
                             The directory will be created if it doesn't exist.
                             Example: "/home/user/cvm_data"
            doc_types: List of document type codes to download.
                      If None, downloads all available types.
                      Valid types: DFP, ITR, FCA, FRE, etc.
                      Example: ["DFP", "ITR"]
            start_year: Starting year for downloads (inclusive).
                       If None, uses the minimum available year for each document type.
                       Example: 2020
            end_year: Ending year for downloads (inclusive).
                     If None, uses the current year.
                     Example: 2023

        Returns:
            DownloadResult object containing:
            - success_count: Number of successfully downloaded files
            - error_count: Number of failed downloads
            - successful_downloads: List of (doc_type, year) tuples
            - errors: List of error messages
            - Methods: has_errors(), has_successes(), get_summary()

        Raises:
            InvalidDocName: If an invalid document type is specified.
            InvalidFirstYear: If start_year is outside valid range.
            InvalidLastYear: If end_year is outside valid range.
            ValueError: If destination_path is invalid.
            OSError: If directory cannot be created due to permissions.

        Example:
            >>> cvm = FundamentalStocksData()
            >>>
            >>> # Download all document types from 2022 onwards
            >>> result = cvm.download(
            ...     destination_path="/home/user/cvm_data",
            ...     start_year=2022
            ... )
            >>> print(f"Success: {result.success_count}, Errors: {result.error_count}")
            >>>
            >>> # Download specific documents for a year range
            >>> result = cvm.download(
            ...     destination_path="/home/user/dfp_data",
            ...     doc_types=["DFP"],
            ...     start_year=2020,
            ...     end_year=2023
            ... )
            >>>
            >>> # Check for errors
            >>> if result.has_errors():
            ...     print("Failed downloads:")
            ...     for error in result.errors:
            ...         print(f"  - {error}")
            >>>
            >>> # View successful downloads
            >>> for doc_type, year in result.successful_downloads:
            ...     print(f"Downloaded: {doc_type} {year}")
        """
        logger.info(
            f"Download requested: path={destination_path}, "
            f"docs={doc_types}, years={start_year}-{end_year}"
        )

        result = self._download_use_case.execute(
            destination_path=destination_path,
            doc_types=doc_types,
            start_year=start_year,
            end_year=end_year,
        )

        logger.info(
            f"Download completed: {result.success_count} successful, "
            f"{result.error_count} errors"
        )

        return result

    def get_available_docs(self) -> Dict[str, str]:
        """Get all available CVM document types with descriptions.

        This method retrieves a mapping of document type codes to their
        full descriptions, helping you understand what data is available.

        Returns:
            Dictionary mapping document codes to descriptions.
            Example: {
                'DFP': 'Demonstração Financeira Padronizada',
                'ITR': 'Informação Trimestral',
                'FCA': 'Formulário Cadastral',
                ...
            }

        Example:
            >>> cvm = FundamentalStocksData()
            >>> docs = cvm.get_available_docs()
            >>>
            >>> # List all available document types
            >>> for code, description in docs.items():
            ...     print(f"{code}: {description}")
            >>>
            >>> # Check if a specific document type exists
            >>> if "DFP" in docs:
            ...     print(f"DFP available: {docs['DFP']}")
        """
        logger.debug("Retrieving available document types")
        return self._available_docs_use_case.execute()

    def get_available_years(self) -> Dict[str, int]:
        """Get information about available years for CVM documents.

        This method returns the year ranges for which documents are available,
        including minimum years for different document types and the current year.

        Returns:
            Dictionary with year information:
            - 'Geral Docs': Minimum year for general documents (e.g., 1998)
            - 'ITR Documents': Minimum year for ITR documents (e.g., 2011)
            - 'CGVN and VLMO Documents': Minimum year for CGVN/VLMO (e.g., 2017)
            - 'Current Year': Current year (e.g., 2025)

        Example:
            >>> cvm = FundamentalStocksData()
            >>> years = cvm.get_available_years()
            >>>
            >>> # Display available year ranges
            >>> print(f"General documents available from: {years['Geral Docs']}")
            >>> print(f"ITR documents available from: {years['ITR Documents']}")
            >>> print(f"Current year: {years['Current Year']}")
            >>>
            >>> # Use this info to make informed download requests
            >>> min_year = years['Geral Docs']
            >>> max_year = years['Current Year']
            >>> result = cvm.download(
            ...     destination_path="/data",
            ...     doc_types=["DFP"],
            ...     start_year=min_year,
            ...     end_year=max_year
            ... )
        """
        logger.debug("Retrieving available years information")
        return self._available_years_use_case.execute()

    def __repr__(self) -> str:
        """Return a string representation of the client."""
        return "FundamentalStocksData()"
