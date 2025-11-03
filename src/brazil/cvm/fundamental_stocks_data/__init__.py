from src.brazil.cvm.fundamental_stocks_data.application import (
    DownloadDocsCVMRepository,
    DownloadDocumentsUseCase,
    FileExtractorRepository,
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
    MissingDownloadUrlError,
)

# Infrastructure layer - adapters
from src.brazil.cvm.fundamental_stocks_data.infra import (
    HttpxAsyncDownloadAdapter,
    ParquetExtractor,
)

# Core utilities
from src.core import RetryStrategy, SimpleProgressBar

# Macro exceptions - shared error handling
from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
    NetworkError,
    PathIsNotDirectoryError,
    PathPermissionError,
    TimeoutError,
)

# Macro infrastructure - shared adapters
from src.macro_infra import Extractor, RequestsAdapter

__all__ = [
    # Domain
    "AvailableDocs",
    "UrlDocs",
    "AvailableYears",
    "DictZipsToDownload",
    "DownloadResult",
    # Application
    "DownloadDocsCVMRepository",
    "FileExtractorRepository",
    "DownloadDocumentsUseCase",
    "GenerateUrlsUseCase",
    "GenerateRangeYearsUseCases",
    "GetAvailableDocsUseCase",
    "GetAvailableYearsUseCase",
    "VerifyPathsUseCases",
    # Infrastructure - adapters
    "ParquetExtractor",
    "HttpxAsyncDownloadAdapter",
    # Core utilities
    "RetryStrategy",
    "SimpleProgressBar",
    # Macro infrastructure
    "Extractor",
    "RequestsAdapter",
    # Exceptions - domain specific
    "InvalidFirstYear",
    "InvalidLastYear",
    "InvalidDocName",
    "InvalidTypeDoc",
    "InvalidRepositoryTypeError",
    "EmptyDocumentListError",
    "MissingDownloadUrlError",
    # Exceptions - macro/shared
    "CorruptedZipError",
    "DiskFullError",
    "ExtractionError",
    "InvalidDestinationPathError",
    "NetworkError",
    "PathIsNotDirectoryError",
    "PathPermissionError",
    "TimeoutError",
]
