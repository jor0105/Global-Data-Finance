import importlib.metadata

try:
    __version__ = importlib.metadata.version('globaldatafinance')
except importlib.metadata.PackageNotFoundError:
    __version__ = '0.2.0'

from .application import (
    ExtractionResultB3,
    FundamentalStocksDataCVM,
    HistoricalQuotesB3,
)

__all__ = [
    'ExtractionResultB3',
    'FundamentalStocksDataCVM',
    'HistoricalQuotesB3',
    '__version__',
]
