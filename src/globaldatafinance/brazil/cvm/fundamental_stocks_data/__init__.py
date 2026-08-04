"""CVM fundamental_stocks_data source implementation.

Provides direct access to CVM regulatory document downloading, validation,
and extraction features using a straightforward, role-oriented structure.
"""

from .client import (
    DownloadDocumentsUseCaseCVM,
    VerifyPathsUseCasesCVM,
    generate_range_years,
    generate_urls,
    get_available_docs,
    get_available_years,
)
from .core import (
    AvailableYearsCVM,
    AvailableYearsInfoCVM,
    DictZipsToDownloadCVM,
    DownloadResultCVM,
)
from .errors import (
    EmptyDocumentListError,
    InvalidDocumentName,
    InvalidDocumentType,
    InvalidFirstYear,
    InvalidLastYear,
    MissingDownloadUrlError,
)
from .extract import ParquetExtractorAdapterCVM
from .http import AsyncDownloadAdapterCVM

__all__ = [
    # IO adapters
    'AsyncDownloadAdapterCVM',
    # core (domain)
    'AvailableYearsCVM',
    'AvailableYearsInfoCVM',
    'DictZipsToDownloadCVM',
    # client (use cases)
    'DownloadDocumentsUseCaseCVM',
    'DownloadResultCVM',
    'EmptyDocumentListError',
    'InvalidDocumentName',
    'InvalidDocumentType',
    # errors
    'InvalidFirstYear',
    'InvalidLastYear',
    'MissingDownloadUrlError',
    'ParquetExtractorAdapterCVM',
    'VerifyPathsUseCasesCVM',
    'generate_range_years',
    'generate_urls',
    'get_available_docs',
    'get_available_years',
]
