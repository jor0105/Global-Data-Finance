from .exceptions_domain import (
    EmptyDocumentListError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidRepositoryTypeError,
    InvalidTypeDoc,
)
from .exceptions_infra import WgetLibraryError, WgetValueError

__all__ = [
    "InvalidFirstYear",
    "InvalidLastYear",
    "InvalidDocName",
    "InvalidTypeDoc",
    "InvalidRepositoryTypeError",
    "EmptyDocumentListError",
    "WgetLibraryError",
    "WgetValueError",
]
