from .exceptions_domain import (
    EmptyDocumentListError,
    InvalidDestinationPathError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidRepositoryTypeError,
    InvalidTypeDoc,
    PathIsNotDirectoryError,
    PathPermissionError,
)
from .exceptions_infra import WgetLibraryError, WgetValueError

__all__ = [
    "InvalidFirstYear",
    "InvalidLastYear",
    "InvalidDocName",
    "InvalidTypeDoc",
    "EmptyDocumentListError",
    "InvalidDestinationPathError",
    "PathIsNotDirectoryError",
    "PathPermissionError",
    "InvalidRepositoryTypeError",
    "WgetLibraryError",
    "WgetValueError",
]
