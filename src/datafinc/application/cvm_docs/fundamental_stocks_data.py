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

from typing import Dict, List, Optional

from ...brazil import (
    DownloadDocumentsUseCaseCVM,
    GetAvailableDocsUseCaseCVM,
    HttpxAsyncDownloadAdapterCVM,
    ParquetExtractorCVM,
)
from ...core import get_logger
from .download_result_formatter import DownloadResultFormatter

logger = get_logger(__name__)


class FundamentalStocksData:
    """High-level interface for CVM fundamental stocks data operations.

    This class provides a simple API for downloading CVM financial documents
    and discovering available data. It uses the HttpxAsyncDownloadAdapterCVM by default
    for 3-5x faster downloads compared to wget, with automatic retry logic.

    You can also customize the adapter:
    - HttpxAsyncDownloadAdapterCVM (default): Fast, no external dependencies
    - Aria2cAdapter: Maximum speed (5-10x faster), requires aria2 installation
    - WgetDownloadAdapter: Original single-threaded, for compatibility

    Attributes:
        None - all dependencies are managed internally

    Example:
        >>> # Basic usage (uses ThreadPool by default)
        >>> cvm = FundamentalStocksData()
        >>>
        >>> # Download all document types for recent years
        >>> result = cvm.download(
        ...     destination_path="/home/user/cvm_data",
        ...     initial_year=2022
        ... )
        >>>
        >>> # Download specific documents
        >>> result = cvm.download(
        ...     destination_path="/home/user/cvm_data",
        ...     list_docs=["DFP"],
        ...     initial_year=2020,
        ...     last_year=2023
        ... )
        >>>
        >>> if result.has_errors():
        ...     print(f"Some downloads failed: {result.errors}")
    """

    def __init__(self):
        """Initialize the FundamentalStocksData client.

        The automatic_extractor option can be passed per download call.
        See download() method for details.
        """
        # Initialize with ParquetExtractorCVM and automatic_extractor=False by default
        # automatic_extractor can be overridden per download call
        self.download_adapter = HttpxAsyncDownloadAdapterCVM(
            file_extractor_repository=ParquetExtractorCVM()
        )
        self.__download_use_case = DownloadDocumentsUseCaseCVM(self.download_adapter)
        self.__available_docs_use_case = GetAvailableDocsUseCaseCVM()
        self.__available_years_use_case = GetAvailableYearsUseCase()
        self.__result_formatter = DownloadResultFormatter(use_colors=True)

        logger.info(
            "FundamentalStocksData client initialized with HttpxAsyncDownloadAdapterCVM "
            "(automatic_extractor can be set per download call)"
        )

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
            DownloadResultCVM object containing:
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
            >>> # Download documents without extraction (padrão)
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
        return self.__available_docs_use_case.execute()

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
            >>> minimal_year = years['Geral Docs']
            >>> max_year = years['Current Year']
            >>> result = cvm.download(
            ...     destination_path="/data",
            ...     list_docs=["DFP"],
            ...     initial_year=minimal_year,
            ...     last_year=max_year
            ... )
        """
        logger.debug("Retrieving available years information")
        return self.__available_years_use_case.execute()

    def __repr__(self) -> str:
        """Return a string representation of the client."""
        return "FundamentalStocksData()"
