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
    ...     list_docs=["DFP", "ITR"],
    ...     initial_year=2020,
    ...     last_year=2023
    ... )
    >>> print(f"Downloaded {result.success_count_downloads} files successfully")
"""

import logging
from typing import Dict, List, Optional

from src.brazil.cvm.fundamental_stocks_data import (
    DownloadDocumentsUseCase,
    GetAvailableDocsUseCase,
    GetAvailableYearsUseCase,
    HttpxAsyncDownloadAdapter,
    ParquetExtractor,
)

from .download_result_formatter import DownloadResultFormatter

logger = logging.getLogger(__name__)


class FundamentalStocksData:
    """High-level interface for CVM fundamental stocks data operations.

    This class provides a simple API for downloading CVM financial documents
    and discovering available data. It uses the HttpxAsyncDownloadAdapter by default

    Example:
        >>> cvm = FundamentalStocksData()
        >>> docs = cvm.get_available_docs()
        >>>
        >>> # Lists all available document types
        >>> for code, description in docs.items():
        ...     print(f"{code}: {description}")
        >>>
        >>> # Checks if a specific document type exists
        >>> if "DFP" in docs:
        ...     print(f"DFP available: {docs['DFP']}")
    """

    def __init__(self):
        """Initialize the FundamentalStocksData client."""
        self.__available_docs_use_case = GetAvailableDocsUseCase()
        self.__available_years_use_case = GetAvailableYearsUseCase()
        self.__parquet_extractor = ParquetExtractor()
        self.download_adapter = HttpxAsyncDownloadAdapter(
            file_extractor_repository=self.__parquet_extractor
        )
        self.__download_use_case = DownloadDocumentsUseCase(
            repository=self.download_adapter
        )
        self.__result_formatter = DownloadResultFormatter()

    def get_available_docs(self) -> Dict[str, str]:
        """Get all available CVM document types with descriptions.

        This method retrieves a mapping of document type codes to their
        full descriptions, helping you understand what data is available.

        Returns:
            Dictionary mapping document codes to descriptions.
            Example: {
                'DFP': 'Standardized Financial Statement',
                'ITR': 'Quarterly Information',
                'FCA': 'Registration Form',
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
        return self.__available_docs_use_case.execute()

    def get_available_years(self) -> Dict[str, int]:
        """
        Gets information about the available years for CVM documents.

        This method returns the year ranges for which documents are available,
        including the minimum years for different document types and the current year.

        Returns:
            A dictionary with year information:
            - 'General Docs': The minimum year for general documents (e.g., 1998).
            - 'ITR Documents': The minimum year for ITR documents (e.g., 2011).
            - 'CGVN and VLMO Documents': The minimum year for CGVN/VLMO (e.g., 2017).
            - 'Current Year': The current year (e.g., 2025).

        Example:
            >>> cvm = FundamentalStocksData()
            >>> years = cvm.get_available_years()
            >>>
            >>> # Displays available year ranges
            >>> print(f"General documents available from: {years['General Docs']}")
            >>> print(f"ITR documents available from: {years['ITR Documents']}")
            >>> print(f"Current year: {years['Current Year']}")
            >>>
            >>> # Uses this info to make informed download requests
            >>> min_year = years['General Docs']
            >>> max_year = years['Current Year']
            >>> result = cvm.download(
            ...     destination_path="/data",
            ...     list_docs=["DFP"],
            ...     initial_year=min_year,
            ...     last_year=max_year
            ... )
        """
        logger.debug("Retrieving available years information")
        return self.__available_years_use_case.execute()

    def __repr__(self) -> str:
        """Returns a string representation of the client."""
        return "FundamentalStocksData()"

    def download(
        self,
        destination_path: str,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
        automatic_extractor: bool = False,
    ) -> None:
        """Download CVM financial documents to a specified location.

        This method handles the complete download process, including:
        - Creating the destination directory if needed
        - Validating document types and year ranges
        - Downloading all requested documents with automatic retry
        - Optionally extracting downloaded files to Parquet format
        - Providing organized and easy-to-understand result display

        Args:
            destination_path: Directory path where files will be saved.
                             The directory will be created if it doesn't exist.
                             Example: "/home/user/cvm_data"
            list_docs: List of document type codes to download.
                      If None, downloads all available types.
                      Valid types: DFP, ITR, FCA, FRE, etc.
                      Example: ["DFP", "ITR"]
            initial_year: Starting year for downloads (inclusive).
                       If None, uses the minimum available year for each document type.
                       Example: 2020
            last_year: Ending year for downloads (inclusive).
                     If None, uses the current year.
                     Example: 2023
            automatic_extractor: If True, automatically extracts downloaded ZIP files
                                to Parquet format. If False or None, keeps ZIP files.
                                Default: False (keeps original ZIP files)
                                Example: True

        Returns:
            DownloadResult object containing:
            - success_count_downloads: Number of successfully downloaded files
            - error_count_downloads: Number of failed downloads
            - successful_downloads: List of successfully downloaded files
            - failed_downloads: Dictionary mapping files to error messages
            - Methods: add_success_downloads(), add_error_downloads()

        Raises:
            InvalidDocName: If an invalid document type is specified.
            InvalidFirstYear: If initial_year is outside valid range.
            InvalidLastYear: If last_year is outside valid range.
            ValueError: If destination_path is invalid.
            OSError: If directory cannot be created due to permissions.

        Example:
            >>> cvm = FundamentalStocksData()
            >>>
            >>> # Download documents without extraction (default)
            >>> result = cvm.download(
            ...     destination_path="/home/user/cvm_data",
            ...     initial_year=2022
            ... )
            >>>
            >>> # Download specific documents WITH extraction to Parquet
            >>> result = cvm.download(
            ...     destination_path="/home/user/dfp_data",
            ...     list_docs=["DFP"],
            ...     initial_year=2020,
            ...     last_year=2023,
            ...     automatic_extractor=True
            ... )
            >>>
            >>> # Check results programmatically
            >>> if result.error_count_downloads > 0:
            ...     print(f"Some downloads failed: {result.failed_downloads}")
        """
        # Override automatic_extractor if explicitly provided
        if automatic_extractor:
            self.download_adapter.automatic_extractor = True
            logger.debug("Automatic extractor enabled for this download")
        else:
            logger.debug("Automatic extractor disabled for this download")

        logger.info(
            f"Download requested: path={destination_path}, "
            f"docs={list_docs}, years={initial_year}-{last_year}, "
            f"auto_extract={automatic_extractor}"
        )

        result = self.__download_use_case.execute(
            destination_path=destination_path,
            list_docs=list_docs,
            initial_year=initial_year,
            last_year=last_year,
        )

        logger.info(
            f"Download completed: {result.success_count_downloads} successful, "
            f"{result.error_count_downloads} errors"
        )

        # Display formatted output
        self.__result_formatter.print_result(result)
