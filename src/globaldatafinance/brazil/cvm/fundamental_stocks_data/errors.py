"""Exceptions for CVM fundamental_stocks_data module.

Contains all specific domain and validation exception types raised
during CVM regulatory data processing, filtering, and extraction.
"""


class CvmError(Exception):
    """Base exception for all CVM feature exceptions."""


class InvalidFirstYear(CvmError):
    def __init__(self, minimal_first_year: int, current_year: int):
        super().__init__(
            f'Invalid first year. You must provide an integer value greater than or equal to {minimal_first_year} and less than or equal to {current_year}.'
        )


class InvalidLastYear(CvmError):
    def __init__(self, first_year: int, current_year: int):
        super().__init__(
            f'Invalid last year. You must provide an integer value greater than or equal to {first_year} and less than or equal to {current_year}.'
        )


class InvalidDocumentName(CvmError):
    def __init__(self, doc_name: str, list_available_docs: list):
        super().__init__(
            f'Invalid document name: {doc_name}. The document name must be a string and one of the following: {list_available_docs}.'
        )


class InvalidDocumentType(CvmError):
    def __init__(self, doc_name: str):
        super().__init__(
            f'Invalid document type: {doc_name}. The document name must be a string.'
        )


class EmptyDocumentListError(CvmError):
    def __init__(self, message: str = 'The document list cannot be empty.'):
        super().__init__(message)


class MissingDownloadUrlError(CvmError):
    def __init__(self, doc_name: str):
        super().__init__(
            f'No download URL was found for the document: {doc_name}'
        )
