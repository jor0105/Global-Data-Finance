import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.exceptions.exceptions import (
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidTypeDoc,
)


@pytest.mark.unit
class TestInvalidFirstYear:
    def test_invalid_first_year_message(self):
        minimal_year = 2010
        atual_year = 2025
        exception = InvalidFirstYear(minimal_year, atual_year)

        expected_message = (
            f"Invalid first year. You must provide an integer value greater than or equal to "
            f"{minimal_year} year and less than or equal to {atual_year}."
        )

        assert str(exception) == expected_message

    def test_invalid_first_year_is_exception(self):
        exception = InvalidFirstYear(2010, 2025)
        assert isinstance(exception, Exception)

    def test_invalid_first_year_can_be_raised(self):
        with pytest.raises(InvalidFirstYear) as exc_info:
            raise InvalidFirstYear(2010, 2025)

        assert "Invalid first year" in str(exc_info.value)

    def test_invalid_first_year_with_different_years(self):
        exception = InvalidFirstYear(2000, 2030)
        assert "2000" in str(exception)
        assert "2030" in str(exception)


@pytest.mark.unit
class TestInvalidLastYear:
    def test_invalid_last_year_message(self):
        first_year = 2020
        atual_year = 2025
        exception = InvalidLastYear(first_year, atual_year)

        expected_message = (
            f"Invalid last year. You must provide an integer value greater than or equal to "
            f"the {first_year} year and less than or equal to {atual_year}."
        )

        assert str(exception) == expected_message

    def test_invalid_last_year_is_exception(self):
        exception = InvalidLastYear(2020, 2025)
        assert isinstance(exception, Exception)

    def test_invalid_last_year_can_be_raised(self):
        with pytest.raises(InvalidLastYear) as exc_info:
            raise InvalidLastYear(2020, 2025)

        assert "Invalid last year" in str(exc_info.value)

    def test_invalid_last_year_with_different_years(self):
        exception = InvalidLastYear(2015, 2023)
        assert "2015" in str(exception)
        assert "2023" in str(exception)

    def test_invalid_last_year_shows_first_year_reference(self):
        exception = InvalidLastYear(2010, 2025)
        assert "the 2010 year" in str(exception)


@pytest.mark.unit
class TestInvalidDocName:
    def test_invalid_doc_name_message(self):
        doc_name = "INVALID_DOC"
        available_docs = ["DFP", "ITR", "FRE"]
        exception = InvalidDocName(doc_name, available_docs)

        expected_message = f"Invalid document name: {doc_name}. Documents must be a string and one of: {available_docs}."

        assert str(exception) == expected_message

    def test_invalid_doc_name_is_exception(self):
        exception = InvalidDocName("INVALID", ["DFP", "ITR"])
        assert isinstance(exception, Exception)

    def test_invalid_doc_name_can_be_raised(self):
        with pytest.raises(InvalidDocName) as exc_info:
            raise InvalidDocName("WRONG", ["DFP", "ITR"])

        assert "Invalid document name" in str(exc_info.value)
        assert "WRONG" in str(exc_info.value)

    def test_invalid_doc_name_shows_available_docs(self):
        available_docs = ["DFP", "ITR", "FRE", "FCA"]
        exception = InvalidDocName("INVALID", available_docs)

        for doc in available_docs:
            assert doc in str(exception)

    def test_invalid_doc_name_with_empty_list(self):
        exception = InvalidDocName("TEST", [])
        assert "TEST" in str(exception)
        assert "[]" in str(exception)

    def test_invalid_doc_name_with_single_doc(self):
        exception = InvalidDocName("WRONG", ["DFP"])
        assert "WRONG" in str(exception)
        assert "DFP" in str(exception)


@pytest.mark.unit
class TestInvalidTypeDoc:
    def test_invalid_type_doc_message(self):
        doc_name = 123
        exception = InvalidTypeDoc(doc_name)

        expected_message = (
            f"Invalid type document: {doc_name}. Documents must be a string."
        )

        assert str(exception) == expected_message

    def test_invalid_type_doc_is_exception(self):
        exception = InvalidTypeDoc(123)
        assert isinstance(exception, Exception)

    def test_invalid_type_doc_can_be_raised(self):
        with pytest.raises(InvalidTypeDoc) as exc_info:
            raise InvalidTypeDoc(123)

        assert "Invalid type document" in str(exc_info.value)
        assert "123" in str(exc_info.value)

    def test_invalid_type_doc_with_different_types(self):
        exception_int = InvalidTypeDoc(42)
        assert "42" in str(exception_int)
        assert "must be a string" in str(exception_int)

        exception_list = InvalidTypeDoc([1, 2, 3])
        assert "[1, 2, 3]" in str(exception_list)

        exception_none = InvalidTypeDoc(None)
        assert "None" in str(exception_none)

        exception_float = InvalidTypeDoc(3.14)
        assert "3.14" in str(exception_float)

    def test_invalid_type_doc_with_dict(self):
        doc_dict = {"key": "value"}
        exception = InvalidTypeDoc(doc_dict)
        assert "must be a string" in str(exception)

    def test_invalid_type_doc_with_boolean(self):
        exception = InvalidTypeDoc(True)
        assert "True" in str(exception)
        assert "must be a string" in str(exception)
