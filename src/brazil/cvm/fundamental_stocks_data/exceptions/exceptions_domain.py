from typing import List


class InvalidRepositoryTypeError(TypeError):
    def __init__(self, actual_type):
        super().__init__(f"Repository must be a string, got {actual_type}.")


class InvalidFirstYear(Exception):
    def __init__(self, minimal_first_year: int, atual_year: int):
        super().__init__(
            f"Invalid first year. You must provide an integer value greater than or equal to {minimal_first_year} year and less than or equal to {atual_year}."
        )


class InvalidLastYear(Exception):
    def __init__(self, first_year: int, atual_year: int):
        super().__init__(
            f"Invalid last year. You must provide an integer value greater than or equal to the {first_year} year and less than or equal to {atual_year}."
        )


class InvalidDocName(Exception):
    def __init__(self, doc_name: str, list_available_docs: List):
        super().__init__(
            f"Invalid document name: {doc_name}. Documents must be a string and one of: {list_available_docs}."
        )


class InvalidTypeDoc(Exception):
    def __init__(self, doc_name: str):
        super().__init__(
            f"Invalid type document: {doc_name}. Documents must be a string."
        )


class EmptyDocumentListError(Exception):
    """Exception raised when document list is empty."""

    def __init__(self, message: str = "Document list cannot be empty."):
        super().__init__(message)
