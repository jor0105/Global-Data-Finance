"""CVM fundamental_stocks_data — flat per-source layout.

`InvalidRepositoryTypeError` was removed when the single-impl ABCs were
dropped (`DownloadDocsCVMRepositoryCVM`, `FileExtractorRepositoryCVM`).
"""

from .client import (
    DownloadDocumentsUseCaseCVM,
    GenerateRangeYearsUseCasesCVM,
    GenerateUrlsUseCaseCVM,
    GetAvailableDocsUseCaseCVM,
    GetAvailableYearsUseCaseCVM,
    VerifyPathsUseCasesCVM,
)
from .core import (
    AvailableDocsCVM,
    AvailableYearsCVM,
    DictZipsToDownloadCVM,
    DownloadResultCVM,
    UrlDocsCVM,
)
from .errors import (
    EmptyDocumentListError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidTypeDoc,
    MissingDownloadUrlError,
)
from .extract import ParquetExtractorAdapterCVM
from .http import AsyncDownloadAdapterCVM

__all__ = [
    # core (domain)
    'AvailableDocsCVM',
    'UrlDocsCVM',
    'AvailableYearsCVM',
    'DictZipsToDownloadCVM',
    'DownloadResultCVM',
    # client (use cases)
    'DownloadDocumentsUseCaseCVM',
    'GenerateUrlsUseCaseCVM',
    'GenerateRangeYearsUseCasesCVM',
    'GetAvailableDocsUseCaseCVM',
    'GetAvailableYearsUseCaseCVM',
    'VerifyPathsUseCasesCVM',
    # IO adapters
    'AsyncDownloadAdapterCVM',
    'ParquetExtractorAdapterCVM',
    # errors
    'InvalidFirstYear',
    'InvalidLastYear',
    'InvalidDocName',
    'InvalidTypeDoc',
    'EmptyDocumentListError',
    'MissingDownloadUrlError',
]
