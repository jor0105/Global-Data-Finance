import pytest

from src.brazil.cvm.fundamental_stocks_data import (
    EmptyDocumentListError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidRepositoryTypeError,
    InvalidTypeDoc,
    MissingDownloadUrlError,
)


@pytest.mark.unit
class TestInvalidFirstYear:
    def test_exception_is_exception(self):
        assert issubclass(InvalidFirstYear, Exception)

    def test_message_format_exact(self):
        minimal = 2010
        atual = 2025
        exception = InvalidFirstYear(minimal, atual)
        expected = (
            f"Invalid first year. You must provide an integer value greater than or equal to "
            f"{minimal} and less than or equal to {atual}."
        )
        assert str(exception) == expected

    def test_can_be_raised_and_caught(self):
        with pytest.raises(InvalidFirstYear) as exc_info:
            raise InvalidFirstYear(2010, 2025)
        assert "Invalid first year" in str(exc_info.value)

    def test_with_different_year_ranges(self):
        test_cases = [(2000, 2023), (1980, 2020), (2010, 2024), (1990, 2030)]
        for minimal, atual in test_cases:
            exception = InvalidFirstYear(minimal, atual)
            assert str(minimal) in str(exception)
            assert str(atual) in str(exception)

    def test_with_boundary_years(self):
        exc1 = InvalidFirstYear(1900, 2025)
        assert "1900" in str(exc1)
        exc2 = InvalidFirstYear(2024, 2025)
        assert "2024" in str(exc2)

    def test_message_contains_keywords(self):
        exception = InvalidFirstYear(2010, 2025)
        exc_str = str(exception).lower()
        assert "greater than or equal to" in exc_str or ">=" in exc_str
        assert "less than or equal to" in exc_str or "<=" in exc_str


@pytest.mark.unit
class TestInvalidLastYear:
    def test_exception_is_exception(self):
        assert issubclass(InvalidLastYear, Exception)

    def test_message_format_exact(self):
        first_year = 2020
        atual = 2025
        exception = InvalidLastYear(first_year, atual)
        expected = (
            f"Invalid last year. You must provide an integer value greater than or equal to "
            f"{first_year} and less than or equal to {atual}."
        )
        assert str(exception) == expected

    def test_can_be_raised_and_caught(self):
        with pytest.raises(InvalidLastYear) as exc_info:
            raise InvalidLastYear(2020, 2025)
        assert "Invalid last year" in str(exc_info.value)

    def test_with_different_year_ranges(self):
        test_cases = [(2000, 2023), (2010, 2020), (2015, 2024), (2000, 2030)]
        for first_year, atual in test_cases:
            exception = InvalidLastYear(first_year, atual)
            assert str(first_year) in str(exception)
            assert str(atual) in str(exception)

    def test_shows_first_year_reference(self):
        exception = InvalidLastYear(2010, 2025)
        assert "2010" in str(exception)

    def test_with_boundary_years(self):
        exc1 = InvalidLastYear(2000, 1999)
        assert "2000" in str(exc1)
        exc2 = InvalidLastYear(2024, 2024)
        assert "2024" in str(exc2)

    def test_message_contains_keywords(self):
        exception = InvalidLastYear(2020, 2025)
        exc_str = str(exception).lower()
        assert "greater than or equal to" in exc_str or ">=" in exc_str
        assert "less than or equal to" in exc_str or "<=" in exc_str


@pytest.mark.unit
class TestInvalidDocName:
    def test_exception_is_exception(self):
        assert issubclass(InvalidDocName, Exception)

    def test_message_format_exact(self):
        doc_name = "INVALID_DOC"
        available_docs = ["DFP", "ITR", "FRE"]
        exception = InvalidDocName(doc_name, available_docs)
        expected = f"Invalid document name: {doc_name}. The document name must be a string and one of the following: {available_docs}."
        assert str(exception) == expected

    def test_can_be_raised_and_caught(self):
        with pytest.raises(InvalidDocName) as exc_info:
            raise InvalidDocName("WRONG", ["DFP", "ITR"])
        assert "Invalid document name" in str(exc_info.value)
        assert "WRONG" in str(exc_info.value)

    def test_shows_all_available_docs(self):
        available_docs = ["DFP", "ITR", "FRE", "FCA"]
        exception = InvalidDocName("INVALID", available_docs)
        for doc in available_docs:
            assert doc in str(exception)

    def test_with_empty_doc_name(self):
        exception = InvalidDocName("", ["DFP"])
        assert "" in str(exception)
        assert "DFP" in str(exception)

    def test_with_empty_available_list(self):
        exception = InvalidDocName("TEST", [])
        assert "TEST" in str(exception)
        assert "[]" in str(exception)

    def test_with_single_available_doc(self):
        exception = InvalidDocName("WRONG", ["DFP"])
        assert "WRONG" in str(exception)
        assert "DFP" in str(exception)

    def test_with_many_available_docs(self):
        available_docs = [f"DOC_{i}" for i in range(50)]
        exception = InvalidDocName("INVALID", available_docs)
        assert "INVALID" in str(exception)
        assert "DOC_" in str(exception)

    def test_with_special_characters(self):
        doc_name = "DRE_AÇÃO_2023"
        available_docs = ["DRE", "BPARMS"]
        exception = InvalidDocName(doc_name, available_docs)
        assert doc_name in str(exception)

    def test_with_accented_characters(self):
        doc_name = "AÇÚCAR"
        available_docs = ["DFP", "ITR"]
        exception = InvalidDocName(doc_name, available_docs)
        assert doc_name in str(exception)

    def test_with_numeric_doc_names(self):
        exception = InvalidDocName("DFP123", ["DFP", "ITR"])
        assert "DFP123" in str(exception)

    def test_message_contains_string_keyword(self):
        exception = InvalidDocName("WRONG", ["DFP"])
        assert "string" in str(exception).lower()


@pytest.mark.unit
class TestInvalidTypeDoc:
    def test_exception_is_exception(self):
        assert issubclass(InvalidTypeDoc, Exception)

    def test_message_format_exact_with_string_input(self):
        doc_name = "123"
        exception = InvalidTypeDoc(doc_name)
        expected = (
            f"Invalid document type: {doc_name}. The document name must be a string."
        )
        assert str(exception) == expected

    def test_message_format_exact_with_int_input(self):
        doc_name = 123
        exception = InvalidTypeDoc(doc_name)
        expected = (
            f"Invalid document type: {doc_name}. The document name must be a string."
        )
        assert str(exception) == expected

    def test_can_be_raised_and_caught(self):
        with pytest.raises(InvalidTypeDoc) as exc_info:
            raise InvalidTypeDoc(123)
        assert "Invalid document type" in str(exc_info.value)

    def test_with_integer_value(self):
        exception = InvalidTypeDoc(42)
        assert "42" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_float_value(self):
        exception = InvalidTypeDoc(3.14)
        assert "3.14" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_none_value(self):
        exception = InvalidTypeDoc(None)
        assert "None" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_list_value(self):
        value = [1, 2, 3]
        exception = InvalidTypeDoc(value)
        assert "[1, 2, 3]" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_dict_value(self):
        value = {"key": "value"}
        exception = InvalidTypeDoc(value)
        assert "must be a string" in str(exception)

    def test_with_boolean_true(self):
        exception = InvalidTypeDoc(True)
        assert "True" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_boolean_false(self):
        exception = InvalidTypeDoc(False)
        assert "False" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_empty_string(self):
        exception = InvalidTypeDoc("")
        assert "" in str(exception)

    def test_message_always_mentions_string_requirement(self):
        values = [123, 3.14, None, [], {}, True, False]
        for value in values:
            exception = InvalidTypeDoc(value)
            assert "must be a string" in str(exception).lower()


@pytest.mark.unit
class TestEmptyDocumentListError:
    def test_exception_is_exception(self):
        assert issubclass(EmptyDocumentListError, Exception)

    def test_message_format(self):
        exception = EmptyDocumentListError()
        assert "The document list cannot be empty" in str(exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(EmptyDocumentListError):
            raise EmptyDocumentListError()

    def test_suggests_alternative(self):
        exception = EmptyDocumentListError()
        exc_str = str(exception)
        assert "empty" in exc_str.lower()

    def test_message_mentions_document_list(self):
        exception = EmptyDocumentListError()
        assert "Document list" in str(exception) or "list" in str(exception).lower()


@pytest.mark.unit
class TestInvalidRepositoryTypeError:
    def test_exception_is_type_error(self):
        assert issubclass(InvalidRepositoryTypeError, TypeError)

    def test_is_type_error_instance(self):
        exception = InvalidRepositoryTypeError("dict")
        assert isinstance(exception, TypeError)

    def test_message_shows_actual_type(self):
        actual = "string"
        exception = InvalidRepositoryTypeError(actual)
        exc_str = str(exception)
        assert actual in exc_str
        assert "repository" in exc_str

    def test_can_be_raised_and_caught(self):
        with pytest.raises(InvalidRepositoryTypeError):
            raise InvalidRepositoryTypeError("dict")

    def test_can_be_caught_as_type_error(self):
        with pytest.raises(TypeError):
            raise InvalidRepositoryTypeError("str")

    def test_with_various_types(self):
        test_cases = ["str", "int", "list", "NoneType", "dict"]
        for actual in test_cases:
            exception = InvalidRepositoryTypeError(actual)
            assert actual in str(exception)

    def test_message_mentions_repository(self):
        exception = InvalidRepositoryTypeError("WrongClass")
        assert "repository" in str(exception)

    def test_with_builtin_types(self):
        exception = InvalidRepositoryTypeError("str")
        assert "str" in str(exception)
        assert "repository" in str(exception)

    def test_with_custom_class_names(self):
        exception = InvalidRepositoryTypeError("DocumentClass")
        assert "DocumentClass" in str(exception)

    def test_with_complex_type_expressions(self):
        actual = "Dict[str, Any]"
        exception = InvalidRepositoryTypeError(actual)
        assert actual in str(exception) or "Dict" in str(exception)

    def test_with_empty_type_names(self):
        exception = InvalidRepositoryTypeError("")
        assert isinstance(exception, InvalidRepositoryTypeError)

    def test_with_special_characters_in_names(self):
        actual = "Dict[str, Any]"
        exception = InvalidRepositoryTypeError(actual)
        assert actual in str(exception) or "[" in str(exception)


@pytest.mark.unit
class TestMissingDownloadUrlError:
    def test_exception_is_exception(self):
        assert issubclass(MissingDownloadUrlError, Exception)

    def test_exception_with_doc_name(self):
        exc = MissingDownloadUrlError("DFP")
        message = str(exc)
        assert "DFP" in message
        assert "No download URL was found" in message

    def test_exception_with_different_doc_names(self):
        for doc in ["DFP", "ITR", "FRE", "CGVN", "VLMO"]:
            exc = MissingDownloadUrlError(doc)
            assert doc in str(exc)

    def test_exception_message_format(self):
        exc = MissingDownloadUrlError("ITR")
        message = str(exc)
        assert "No download URL was found for the document: ITR" in message

    def test_exception_can_be_raised_and_caught(self):
        with pytest.raises(MissingDownloadUrlError) as exc_info:
            raise MissingDownloadUrlError("DFP")
        assert "DFP" in str(exc_info.value)

    def test_exception_with_empty_string(self):
        exc = MissingDownloadUrlError("")
        message = str(exc)
        assert "No download URL was found" in message

    def test_exception_with_special_characters(self):
        exc = MissingDownloadUrlError("DFP-2020_v1.0")
        assert "DFP-2020_v1.0" in str(exc)

    def test_exception_with_whitespace(self):
        exc = MissingDownloadUrlError("  DFP  ")
        message = str(exc)
        assert "No download URL was found" in message

    def test_exception_message_consistency(self):
        docs = ["DFP", "ITR", "FRE", "CGVN", "VLMO"]
        for doc in docs:
            exc = MissingDownloadUrlError(doc)
            message = str(exc)
            assert "No download URL was found for the document:" in message
            assert doc in message


@pytest.mark.unit
class TestAllExceptionsIntegration:
    def test_all_exceptions_can_be_imported(self):
        from src.brazil.cvm.fundamental_stocks_data.exceptions import (
            EmptyDocumentListError,
            InvalidDocName,
            InvalidFirstYear,
            InvalidLastYear,
            InvalidRepositoryTypeError,
            InvalidTypeDoc,
            MissingDownloadUrlError,
        )

        assert EmptyDocumentListError is not None
        assert InvalidDocName is not None
        assert InvalidFirstYear is not None
        assert InvalidLastYear is not None
        assert InvalidRepositoryTypeError is not None
        assert InvalidTypeDoc is not None
        assert MissingDownloadUrlError is not None

    def test_exceptions_have_proper_inheritance(self):
        assert issubclass(InvalidRepositoryTypeError, TypeError)
        assert issubclass(InvalidRepositoryTypeError, BaseException)

        for exc_class in [
            InvalidFirstYear,
            InvalidLastYear,
            InvalidDocName,
            InvalidTypeDoc,
            EmptyDocumentListError,
            MissingDownloadUrlError,
        ]:
            assert issubclass(exc_class, Exception)
            assert issubclass(exc_class, BaseException)

    def test_all_exceptions_are_exceptions(self):
        exceptions = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc(123),
            InvalidRepositoryTypeError("str"),
            EmptyDocumentListError(),
            MissingDownloadUrlError("DFP"),
        ]
        for exc in exceptions:
            assert isinstance(
                exc, Exception
            ), f"{type(exc).__name__} is not an Exception"

    def test_catch_all_as_generic_exception(self):
        exceptions = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc(123),
            InvalidRepositoryTypeError("str"),
            EmptyDocumentListError(),
            MissingDownloadUrlError("DFP"),
        ]
        for exc in exceptions:
            with pytest.raises(Exception):
                raise exc

    def test_all_exceptions_have_non_empty_messages(self):
        exceptions = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc(123),
            InvalidRepositoryTypeError("str"),
            EmptyDocumentListError(),
            MissingDownloadUrlError("DFP"),
        ]
        for exc in exceptions:
            exc_str = str(exc)
            assert len(exc_str) > 0, f"{type(exc).__name__} has empty message"
            assert isinstance(
                exc_str, str
            ), f"{type(exc).__name__} message is not string"

    def test_validation_workflow_document_selection(self):
        def validate_document_selection(
            first_year,
            last_year,
            doc_name,
            valid_years_range=(1990, 2023),
            valid_docs=["DRE", "BPARMS", "DMPL"],
        ):
            min_year, atual_year = valid_years_range

            if (
                not isinstance(first_year, int)
                or first_year < min_year
                or first_year > atual_year
            ):
                raise InvalidFirstYear(min_year, atual_year)

            if (
                not isinstance(last_year, int)
                or last_year < first_year
                or last_year > atual_year
            ):
                raise InvalidLastYear(first_year, atual_year)

            if not isinstance(doc_name, str):
                raise InvalidTypeDoc(doc_name)

            if doc_name not in valid_docs:
                raise InvalidDocName(doc_name, valid_docs)

            return True

        assert validate_document_selection(2000, 2023, "DRE")

        with pytest.raises(InvalidFirstYear):
            validate_document_selection(1989, 2023, "DRE")

        with pytest.raises(InvalidLastYear):
            validate_document_selection(2020, 2024, "DRE")

        with pytest.raises(InvalidTypeDoc):
            validate_document_selection(2000, 2023, 123)

        with pytest.raises(InvalidDocName):
            validate_document_selection(2000, 2023, "INVALID")

    def test_repository_validation_workflow(self):
        def validate_repository(repo):
            if not hasattr(repo, "validate"):
                actual_type = type(repo).__name__
                raise InvalidRepositoryTypeError(actual_type)
            return True

        class ValidRepository:
            def validate(self):
                return True

        repo = ValidRepository()
        assert validate_repository(repo)

        with pytest.raises(InvalidRepositoryTypeError):
            validate_repository("not_a_repo")

    def test_year_boundary_conditions(self):
        exc1 = InvalidFirstYear(2023, 2023)
        assert "2023" in str(exc1)

        exc2 = InvalidFirstYear(1900, 2100)
        assert "1900" in str(exc2) and "2100" in str(exc2)

    def test_doc_exceptions_with_many_documents(self):
        docs = [f"DOC_{i}" for i in range(1000)]
        exc = InvalidDocName("INVALID", docs)
        assert "INVALID" in str(exc)

    def test_exception_messages_are_helpful(self):
        exc1 = InvalidFirstYear(2010, 2024)
        assert len(str(exc1)) > 20

        exc2 = InvalidDocName("WRONG", ["DFP", "ITR"])
        assert "WRONG" in str(exc2)

        exc3 = MissingDownloadUrlError("DFP")
        assert "DFP" in str(exc3)
        assert "URL" in str(exc3)

    def test_exceptions_preserve_traceback(self):
        try:
            raise InvalidDocName("INVALID", ["DFP"])
        except InvalidDocName:
            import traceback

            tb = traceback.format_exc()
            assert "InvalidDocName" in tb
            assert "INVALID" in tb
