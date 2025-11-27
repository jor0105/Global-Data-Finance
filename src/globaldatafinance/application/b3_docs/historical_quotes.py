"""
This module provides a simple, high-level API for working with B3 COTAHIST files,
making it easy to extract historical stock quotes from ZIP files to Parquet format.

Example:
    >>> from datafin.b3_docs import HistoricalQuotesB3
    >>>
    >>> # Initialize the client
    >>> b3 = HistoricalQuotesB3()
    >>>
    >>> # See available asset classes
    >>> assets = b3.get_available_assets()
    >>> print(assets)
    >>>
    >>> # See available year range
    >>> years = b3.get_available_years()
    >>> print(f"Data available from {years['minimal_year']} to {years['current_year']}")
    >>>
    >>> # Extract historical quotes
    >>> result = b3.extract(
    ...     path_of_docs="/path/to/cotahist_zips",
    ...     destination_path="/path/to/save",
    ...     assets_list=["ações", "etf"],
    ...     initial_year=2020,
    ...     last_year=2023,
    ...     processing_mode="fast"
    ... )
    >>> print(f"Extracted {result['total_records']} records successfully")
"""

import time
from typing import Any, Dict, List, Optional

from ...brazil import (
    CreateDocsToExtractUseCaseB3,
    DocsToExtractorB3,
    ExtractHistoricalQuotesUseCaseB3,
    GetAvailableAssetsUseCaseB3,
    GetAvailableYearsUseCaseB3,
    ValidateExtractionConfigUseCaseB3,
)
from ...core import get_logger
from .extraction_result_formatter import ExtractionResultFormatter
from .result_formatters import HistoricalQuotesResultFormatter

logger = get_logger(__name__)


class HistoricalQuotesB3:
    """High-level interface for B3 historical quotes extraction operations.

    This class provides a simple API for extracting historical stock quotes
    from B3 COTAHIST ZIP files and converting them to Parquet format.

    The extraction process supports two processing modes:
    - Fast mode: High performance with higher CPU/RAM usage (recommended)
    - Slow mode: Resource-efficient with lower CPU/RAM usage (for limited resources)

    Supported asset classes:
    - 'ações': Stocks (cash and fractional market)
    - 'etf': Exchange Traded Funds
    - 'opções': Options (call and put)
    - 'termo': Term market
    - 'exercicio_opcoes': Options exercise
    - 'forward': Forward market
    - 'leilao': Auction market

    Attributes:
        None - all dependencies are managed internally

    Example:
        >>> # Basic usage with fast processing mode
        >>> b3 = HistoricalQuotesB3()
        >>>
        >>> # Extract stocks and ETFs data
        >>> result = b3.extract(
        ...     path_of_docs="/data/cotahist_zips",
        ...     destination_path="/data/output",
        ...     assets_list=["ações", "etf"],
        ...     initial_year=2022
        ... )
        >>>
        >>> # Extract options data with custom output filename
        >>> result = b3.extract(
        ...     path_of_docs="/data/cotahist_zips",
        ...     destination_path="/data/options",
        ...     assets_list=["opções"],
        ...     initial_year=2020,
        ...     last_year=2023,
        ...     output_filename="options_history.parquet",
        ...     processing_mode="slow"
        ... )
        >>>
            >>> if not result['success']:
            ...     print(f"Extraction had errors: {result['message']}")
    """

    def __init__(self):
        """Initialize the HistoricalQuotesB3 client.

        Sets up the extraction use case and result formatter with sensible defaults.
        """
        self.__extract_use_case = ExtractHistoricalQuotesUseCaseB3()
        self.__available_assets_use_case = GetAvailableAssetsUseCaseB3()
        self.__available_years_use_case = GetAvailableYearsUseCaseB3()
        self.__validate_config_use_case = ValidateExtractionConfigUseCaseB3()
        self.__result_formatter = ExtractionResultFormatter(use_colors=True)

        logger.info('HistoricalQuotesB3 client initialized')

    def extract(
        self,
        path_of_docs: str,
        assets_list: List[str],
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
        destination_path: Optional[str] = None,
        output_filename: str = 'cotahist_extracted',
        processing_mode: str = 'fast',
    ) -> Dict[str, Any]:
        """Extract historical quotes from COTAHIST ZIP files to Parquet format.

        This method handles the complete extraction process, including:
        - Validating asset classes and year ranges
        - Finding all COTAHIST ZIP files in the specified path
        - Reading and parsing ZIP contents
        - Filtering data by specified asset classes
        - Writing results to Parquet format with progress tracking
        - Providing organized and easy-to-understand result display

        Args:
            path_of_docs: Directory path where COTAHIST ZIP files are located.
                         The files should follow the naming pattern: COTAHIST_AXXXX.ZIP
                         Example: "/home/user/cotahist_files"
            assets_list: List of asset class codes to extract.
                        Valid values: 'ações', 'etf', 'opções', 'termo',
                                     'exercicio_opcoes', 'forward', 'leilao'
                        Example: ["ações", "etf"]
            initial_year: Starting year for extraction (inclusive).
                       If None, uses the minimal available year (1986).
                       Must be >= 1986 (first year of B3 historical data).
                       Example: 2020
            last_year: Ending year for extraction (inclusive).
                     If None, uses the current year.
                     Must be >= initial_year and <= current year.
                     Example: 2023
            destination_path: Directory path where the output Parquet file will be saved.
                            If None, uses path_of_docs as destination.
                            The directory will be created if it doesn't exist.
                            Example: "/home/user/output"
            output_filename: Name of the output file (without .parquet extension).
                           The '.parquet' extension will be added automatically.
                           Default: "cotahist_extracted" (saves as "cotahist_extracted.parquet")
                           Example: "stocks_2020_2023" (saves as "stocks_2020_2023.parquet")
            processing_mode: Processing strategy for resource management.
                           - 'fast': High performance mode (default)
                             Uses more CPU/RAM for faster processing
                           - Dict[str, Any]'slow': Resource-efficient mode
                             Uses less CPU/RAM, suitable for limited resources
                           Example: "fast"

        Returns:
            Dictionary containing extraction results with the following keys:
            - success (bool): True if extraction completed without errors
            - message (str): Human-readable summary of the extraction
            - total_files (int): Total number of ZIP files processed
            - success_count (int): Number of successfully processed files
            - error_count (int): Number of files that failed to process
            - total_records (int): Total number of records extracted
            - output_file (str): Path to the generated Parquet file
            - errors (List[str], optional): List of error messages if any

        Raises:
            EmptyAssetListError: If assets_list is empty or not a list.
            InvalidAssetsName: If any asset class in assets_list is invalid.
            InvalidFirstYear: If initial_year is outside valid range (1986 - current year).
            InvalidLastYear: If last_year is outside valid range or < initial_year.
            ValueError: If path_of_docs is invalid.
            OSError: If directories cannot be created or accessed.

        Example:
            >>> b3 = HistoricalQuotesB3()
            >>>
            >>> # Extract stocks for recent years (fast mode)
            >>> result = b3.extract(
            ...     path_of_docs="/data/cotahist",
            ...     destination_path="/data/output",
            ...     assets_list=["ações"],
            ...     initial_year=2022
            ... )
            >>>
            >>> # Extract multiple asset classes with custom settings
            >>> result = b3.extract(
            ...     path_of_docs="/data/cotahist",
            ...     destination_path="/data/multi_asset",
            ...     assets_list=["ações", "etf", "opções"],
            ...     initial_year=2020,
            ...     last_year=2023,
            ...     output_filename="multi_asset_history",
            ...     processing_mode="slow"
            ... )
            >>>
            >>> # Check results programmatically
            >>> if result['success']:
            ...     print(f"Successfully extracted {result['total_records']} records")
            ...     print(f"Output saved to: {result['output_file']}")
            ... else:
            ...     print(f"Extraction failed: {result['message']}")
            ...     if 'errors' in result:
            ...         for error in result['errors']:
            ...             print(f"  - {error}")
        """
        initial_year = self.__resolve_initial_year(initial_year)

        last_year = self.__resolve_last_year(last_year)

        processing_mode, output_filename_with_ext = (
            self.__validate_config_use_case.execute(
                processing_mode=processing_mode,
                output_filename=output_filename,
            )
        )

        logger.info(
            f'Extraction requested: path={path_of_docs}, '
            f'destination={destination_path or path_of_docs}, '
            f'assets={assets_list}, years={initial_year}-{last_year}, '
            f'mode={processing_mode}'
        )

        docs_to_extract: DocsToExtractorB3 = CreateDocsToExtractUseCaseB3(
            path_of_docs=path_of_docs,
            assets_list=assets_list,
            initial_year=initial_year,
            last_year=last_year,
            destination_path=destination_path,
        ).execute()

        logger.info(
            f'Found {len(docs_to_extract.set_documents_to_download)} ZIP files to process'
        )

        start_time = time.time()

        result = self.__extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            processing_mode=processing_mode,
            output_filename=output_filename_with_ext,
        )

        elapsed_time = time.time() - start_time

        result_dict: Dict[str, Any] = (
            HistoricalQuotesResultFormatter.enrich_result(result)
        )

        # Add metadata for the formatter
        result['assets'] = assets_list
        result['processing_mode'] = processing_mode
        result['elapsed_time'] = elapsed_time

        logger.info(
            f'Extraction completed: {result["success_count"]} successful, '
            f'{result["error_count"]} errors, '
            f'{result["total_records"]} records extracted'
        )

        self.__result_formatter.print_result(result)

        return result_dict

    def get_available_assets(self) -> List[str]:
        """Get all available B3 asset classes that can be extracted.

        This method retrieves a list of supported asset class codes
        that can be used in the assets_list parameter of extract().

        Returns:
            List of available asset class codes:
            - 'ações': Stocks (cash and fractional market)
            - 'etf': Exchange Traded Funds
            - 'opções': Options (call and put)
            - 'termo': Term market
            - 'exercicio_opcoes': Options exercise
            - 'forward': Forward market
            - 'leilao': Auction market

        Example:
            >>> b3 = HistoricalQuotesB3()
            >>> assets = b3.get_available_assets()
            >>>
            >>> # List all available asset classes
            >>> print("Available asset classes:")
            >>> for asset in assets:
            ...     print(f"  - {asset}")
            >>>
            >>> # Check if a specific asset class is supported
            >>> if "ações" in assets:
            ...     print("Stocks extraction is supported")
            >>>
            >>> # Extract all available asset types
            >>> result = b3.extract(
            ...     path_of_docs="/data/cotahist",
            ...     assets_list=assets,  # Extract all types
            ...     initial_year=2023
            ... )
        """
        logger.debug('Retrieving available asset classes')
        result: List[str] = self.__available_assets_use_case.execute()
        return result

    def get_available_years(self) -> Dict[str, int]:
        """Get information about available years for B3 historical data.

        This method returns the year range for which COTAHIST data is available.
        B3 historical quotes data is available from 1986 to the current year.

        Returns:
            Dictionary with year information:
            - 'minimal_year': Minimum year available (1986)
            - 'current_year': Current year (maximum year available)

        Example:
            >>> b3 = HistoricalQuotesB3()
            >>> years = b3.get_available_years()
            >>>
            >>> # Display available year range
            >>> print(f"Historical data available from: {years['minimal_year']}")
            >>> print(f"Up to current year: {years['current_year']}")
            >>>
            >>> # Use this info to make informed extraction requests
            >>> minimal_year = years['minimal_year']
            >>> max_year = years['current_year']
            >>> result = b3.extract(
            ...     path_of_docs="/data/cotahist",
            ...     assets_list=["ações"],
            ...     initial_year=minimal_year,
            ...     last_year=max_year
            ... )
            >>>
            >>> # Extract only the last 5 years
            >>> current = years['current_year']
            >>> result = b3.extract(
            ...     path_of_docs="/data/cotahist",
            ...     assets_list=["ações", "etf"],
            ...     initial_year=current - 5,
            ...     last_year=current
            ... )
        """
        logger.debug('Retrieving available years information')
        return {
            'minimal_year': self.__available_years_use_case.get_minimal_year(),
            'current_year': self.__available_years_use_case.get_atual_year(),
        }

    def __repr__(self) -> str:
        """Return a string representation of the client."""
        return 'HistoricalQuotesB3()'

    def __resolve_initial_year(self, initial_year: Optional[int]) -> int:
        """Resolve initial_year to a valid value, using minimum year if None.

        Args:
            initial_year: User-provided initial year or None

        Returns:
            Valid initial year value
        """
        if initial_year is None:
            resolved: int = self.__available_years_use_case.get_minimal_year()
            logger.debug(
                f'initial_year not provided, using minimal year: {resolved}'
            )
            return resolved
        return initial_year

    def __resolve_last_year(self, last_year: Optional[int]) -> int:
        """Resolve last_year to a valid value, using current year if None.

        Args:
            last_year: User-provided last year or None

        Returns:
            Valid last year value
        """
        if last_year is None:
            resolved: int = self.__available_years_use_case.get_atual_year()
            logger.debug(
                f'last_year not provided, using current year: {resolved}'
            )
            return resolved
        return last_year
