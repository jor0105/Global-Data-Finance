from .exceptions_domain import (
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidTypeDoc,
)
from .exceptions_infra import WgetLibraryError, WgetValueError

__all__ = [
    "InvalidFirstYear",
    "InvalidLastYear",
    "InvalidDocName",
    "InvalidTypeDoc",
    "WgetLibraryError",
    "WgetValueError",
]
