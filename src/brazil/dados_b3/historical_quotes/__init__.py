"""
Historical Quotes Extraction Module

This module provides tools to extract and process historical stock quotes
from B3 (Brasil, Bolsa, Balcão) COTAHIST files.

Quick Start:
-----------
>>> from src.brazil.dados_b3.historical_quotes.application import (
...     CreateDocsToExtractUseCase,
...     ExtractHistoricalQuotesUseCase,
... )
>>>
>>> # Setup extraction
>>> docs = CreateDocsToExtractUseCase(
...     assets_list=['ações', 'etf'],
...     initial_year=2023,
...     last_year=2024,
...     path_of_docs='/path/to/zips',
...     destination_path='/path/to/output'
... ).execute()
>>>
>>> # Execute extraction
>>> extractor = ExtractHistoricalQuotesUseCase()
>>> result = extractor.execute_sync(docs, processing_mode='fast')
>>> print(f"Extracted {result['total_records']} records")

Supported Asset Classes:
-----------------------
- 'ações': Stocks (cash and fractional market)
- 'etf': Exchange Traded Funds
- 'opções': Options (call and put)
- 'termo': Term market
- 'exercicio_opcoes': Options exercise
- 'forward': Forward market
- 'leilao': Auction market

Processing Modes:
----------------
- 'fast': High performance (high CPU/RAM usage)
- 'slow': Resource-efficient (low CPU/RAM usage)
"""

from .application import CreateDocsToExtractUseCase, ExtractHistoricalQuotesUseCase
from .domain import AvailableAssets, AvailableYears, DocsToExtractor
from .infra import (
    CotahistParser,
    ExtractionService,
    FileSystemService,
    ParquetWriter,
    ProcessingMode,
    ZipFileReader,
)

__all__ = [
    # Application Layer
    "CreateDocsToExtractUseCase",
    "ExtractHistoricalQuotesUseCase",
    # Domain Layer
    "DocsToExtractor",
    "AvailableAssets",
    "AvailableYears",
    # Infrastructure Layer
    "FileSystemService",
    "ZipFileReader",
    "CotahistParser",
    "ParquetWriter",
    "ExtractionService",
    "ProcessingMode",
]

__version__ = "1.0.0"
__author__ = "DataFinance Team"
