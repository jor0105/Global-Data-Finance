from .application import (
    DownloadDocsCVMRepositoryCVM,
    DownloadDocumentsUseCaseCVM,
    FileExtractorRepositoryCVM,
    GenerateRangeYearsUseCasesCVM,
    GenerateUrlsUseCaseCVM,
    GetAvailableDocsUseCaseCVM,
    GetAvailableYearsUseCaseCVM,
    VerifyPathsUseCasesCVM,
)
from .domain import (
    AvailableDocsCVM,
    AvailableYearsCVM,
    DictZipsToDownloadCVM,
    DownloadResultCVM,
    UrlDocsCVM,
)
from .exceptions import (
    EmptyDocumentListError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidRepositoryTypeError,
    InvalidTypeDoc,
    MissingDownloadUrlError,
)
from .infra import HttpxAsyncDownloadAdapterCVM, ParquetExtractorCVM

__all__ = [
    # Domain
    "AvailableDocsCVM",
    "UrlDocsCVM",
    "AvailableYearsCVM",
    "DictZipsToDownloadCVM",
    "DownloadResultCVM",
    # Application
    "DownloadDocsCVMRepositoryCVM",
    "FileExtractorRepositoryCVM",
    "DownloadDocumentsUseCaseCVM",
    "GenerateUrlsUseCaseCVM",
    "GenerateRangeYearsUseCasesCVM",
    "GetAvailableDocsUseCaseCVM",
    "GetAvailableYearsUseCaseCVM",
    "VerifyPathsUseCasesCVM",
    # Infrastructure - adapters
    "ParquetExtractorCVM",
    "HttpxAsyncDownloadAdapterCVM",
    # Exceptions - domain specific
    "InvalidFirstYear",
    "InvalidLastYear",
    "InvalidDocName",
    "InvalidTypeDoc",
    "InvalidRepositoryTypeError",
    "EmptyDocumentListError",
    "MissingDownloadUrlError",
]
