# Low-level imports for advanced usage
from .b3_data import (
    CreateDocsToExtractUseCaseB3,
    DocsToExtractorB3,
    ExtractHistoricalQuotesUseCaseB3,
    GetAvailableAssetsUseCaseB3,
    GetAvailableYearsUseCaseB3,
    ValidateExtractionConfigUseCaseB3,
)
from .cvm import (
    AsyncDownloadAdapterCVM,
    DownloadDocumentsUseCaseCVM,
    DownloadResultCVM,
    GetAvailableDocsUseCaseCVM,
    GetAvailableYearsUseCaseCVM,
    ParquetExtractorAdapterCVM,
)

__all__ = [
    # B3 - Low-level
    'CreateDocsToExtractUseCaseB3',
    'ExtractHistoricalQuotesUseCaseB3',
    'GetAvailableAssetsUseCaseB3',
    'GetAvailableYearsUseCaseB3',
    'ValidateExtractionConfigUseCaseB3',
    'DocsToExtractorB3',
    # CVM - Low-level
    'DownloadResultCVM',
    'DownloadDocumentsUseCaseCVM',
    'GetAvailableDocsUseCaseCVM',
    'GetAvailableYearsUseCaseCVM',
    'AsyncDownloadAdapterCVM',
    'ParquetExtractorAdapterCVM',
]


# Import high-level API classes at the end to avoid circular imports
def __getattr__(name):
    """Lazy import for high-level API classes to avoid circular imports."""
    if name == 'FundamentalStocksDataCVM':
        from ..application.cvm_docs import FundamentalStocksDataCVM

        return FundamentalStocksDataCVM
    elif name == 'HistoricalQuotesB3':
        from ..application.b3_docs import HistoricalQuotesB3

        return HistoricalQuotesB3
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


# Add to __all__ for proper IDE support
__all__.extend(['FundamentalStocksDataCVM', 'HistoricalQuotesB3'])
