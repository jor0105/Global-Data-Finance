from typing import List


class InvalidRepositoryTypeError(TypeError):
    def __init__(self, actual_type):
        super().__init__(
            f"The repository must be a valid repository instance, but received {actual_type}."
        )


class InvalidFirstYear(Exception):
    def __init__(self, minimal_first_year: int, current_year: int):
        super().__init__(
            f"Invalid first year. You must provide an integer value greater than or equal to {minimal_first_year} and less than or equal to {current_year}."
        )


class InvalidLastYear(Exception):
    def __init__(self, first_year: int, current_year: int):
        super().__init__(
            f"Invalid last year. You must provide an integer value greater than or equal to {first_year} and less than or equal to {current_year}."
        )


class InvalidDocName(Exception):
    def __init__(self, doc_name: str, list_available_docs: List):
        super().__init__(
            f"Invalid document name: {doc_name}. The document name must be a string and one of the following: {list_available_docs}."
        )


class InvalidTypeDoc(Exception):
    def __init__(self, doc_name: str):
        super().__init__(
            f"Invalid document type: {doc_name}. The document name must be a string."
        )


class EmptyDocumentListError(Exception):
    def __init__(self, message: str = "The document list cannot be empty."):
        super().__init__(message)


class MissingDownloadUrlError(Exception):
    def __init__(self, doc_name: str):
        super().__init__(f"No download URL was found for the document: {doc_name}")
