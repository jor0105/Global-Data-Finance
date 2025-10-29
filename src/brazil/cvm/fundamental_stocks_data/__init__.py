# Domain models and entities
# Application layer - use cases and interfaces
from src.brazil.cvm.fundamental_stocks_data.application import (
    DownloadDocsCVMRepository,
    DownloadDocumentsUseCase,
    GenerateRangeYearsUseCases,
    GenerateUrlsUseCase,
    GetAvailableDocsUseCase,
    GetAvailableYearsUseCase,
    VerifyPathsUseCases,
)
from src.brazil.cvm.fundamental_stocks_data.domain import (
    AvailableDocs,
    AvailableYears,
    DictZipsToDownload,
    DownloadResult,
    UrlDocs,
)

# Exception handling
from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    EmptyDocumentListError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidRepositoryTypeError,
    InvalidTypeDoc,
    WgetLibraryError,
    WgetValueError,
)

# Infrastructure layer - adapters
from src.brazil.cvm.fundamental_stocks_data.infra import (
    HttpxAsyncDownloadAdapter,
    ThreadPoolDownloadAdapter,
    WgetDownloadAdapter,
)

# Utils
from src.brazil.cvm.fundamental_stocks_data.utils import (
    RetryStrategy,
    SimpleProgressBar,
)

__all__ = [
    # Domain
    "AvailableDocs",
    "UrlDocs",
    "AvailableYears",
    "DictZipsToDownload",
    "DownloadResult",
    # Application
    "DownloadDocsCVMRepository",
    "DownloadDocumentsUseCase",
    "GenerateUrlsUseCase",
    "GenerateRangeYearsUseCases",
    "GetAvailableDocsUseCase",
    "GetAvailableYearsUseCase",
    "VerifyPathsUseCases",
    # Infrastructure
    "WgetDownloadAdapter",
    "ThreadPoolDownloadAdapter",
    "HttpxAsyncDownloadAdapter",
    # Exceptions
    "InvalidFirstYear",
    "InvalidLastYear",
    "InvalidDocName",
    "InvalidTypeDoc",
    "InvalidRepositoryTypeError",
    "EmptyDocumentListError",
    "WgetLibraryError",
    "WgetValueError",
    # Utils
    "RetryStrategy",
    "SimpleProgressBar",
]
