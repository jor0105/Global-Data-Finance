"""
Testes para exceções de domínio.

Cobre:
- InvalidFirstYear: validação de primeiro ano
- InvalidLastYear: validação de último ano
- InvalidDocName: validação de nome de documento
- InvalidTypeDoc: validação de tipo de documento
- EmptyDocumentListError: lista de documentos vazia
"""

import pytest

from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    EmptyDocumentListError,
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidTypeDoc,
)


@pytest.mark.unit
class TestInvalidFirstYear:
    """Testes para a exceção InvalidFirstYear."""

    def test_message_format_exact(self):
        """Deve gerar mensagem exata com formato correto."""
        minimal = 2010
        atual = 2025
        exception = InvalidFirstYear(minimal, atual)
        expected = (
            f"Invalid first year. You must provide an integer value greater than or equal to "
            f"{minimal} year and less than or equal to {atual}."
        )
        assert str(exception) == expected

    def test_is_exception_subclass(self):
        """Deve herdar de Exception."""
        exception = InvalidFirstYear(2010, 2025)
        assert isinstance(exception, Exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(InvalidFirstYear) as exc_info:
            raise InvalidFirstYear(2010, 2025)
        assert "Invalid first year" in str(exc_info.value)

    def test_with_different_year_ranges(self):
        """Deve funcionar com diferentes intervalos de anos."""
        test_cases = [(2000, 2023), (1980, 2020), (2010, 2024), (1990, 2030)]
        for minimal, atual in test_cases:
            exception = InvalidFirstYear(minimal, atual)
            assert str(minimal) in str(exception)
            assert str(atual) in str(exception)

    def test_with_boundary_years(self):
        """Deve validar anos limítrofes."""
        exc1 = InvalidFirstYear(1900, 2025)
        assert "1900" in str(exc1)
        exc2 = InvalidFirstYear(2024, 2025)
        assert "2024" in str(exc2)

    def test_message_contains_keywords(self):
        """Deve conter palavras-chave importantes."""
        exception = InvalidFirstYear(2010, 2025)
        exc_str = str(exception).lower()
        assert "greater than or equal to" in exc_str or ">=" in exc_str
        assert "less than or equal to" in exc_str or "<=" in exc_str


@pytest.mark.unit
class TestInvalidLastYear:
    """Testes para a exceção InvalidLastYear."""

    def test_message_format_exact(self):
        """Deve gerar mensagem exata com formato correto."""
        first_year = 2020
        atual = 2025
        exception = InvalidLastYear(first_year, atual)
        expected = (
            f"Invalid last year. You must provide an integer value greater than or equal to "
            f"the {first_year} year and less than or equal to {atual}."
        )
        assert str(exception) == expected

    def test_is_exception_subclass(self):
        """Deve herdar de Exception."""
        exception = InvalidLastYear(2020, 2025)
        assert isinstance(exception, Exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(InvalidLastYear) as exc_info:
            raise InvalidLastYear(2020, 2025)
        assert "Invalid last year" in str(exc_info.value)

    def test_with_different_year_ranges(self):
        """Deve funcionar com diferentes intervalos de anos."""
        test_cases = [(2000, 2023), (2010, 2020), (2015, 2024), (2000, 2030)]
        for first_year, atual in test_cases:
            exception = InvalidLastYear(first_year, atual)
            assert str(first_year) in str(exception)
            assert str(atual) in str(exception)

    def test_shows_first_year_reference(self):
        """Deve mencionar o primeiro ano de forma clara."""
        exception = InvalidLastYear(2010, 2025)
        assert "the 2010 year" in str(exception)

    def test_with_boundary_years(self):
        """Deve validar anos limítrofes."""
        exc1 = InvalidLastYear(2000, 1999)
        assert "2000" in str(exc1)
        exc2 = InvalidLastYear(2024, 2024)
        assert "2024" in str(exc2)

    def test_message_contains_keywords(self):
        """Deve conter palavras-chave importantes."""
        exception = InvalidLastYear(2020, 2025)
        exc_str = str(exception).lower()
        assert "greater than or equal to" in exc_str or ">=" in exc_str
        assert "less than or equal to" in exc_str or "<=" in exc_str


@pytest.mark.unit
class TestInvalidDocName:
    """Testes para a exceção InvalidDocName."""

    def test_message_format_exact(self):
        """Deve gerar mensagem exata com formato correto."""
        doc_name = "INVALID_DOC"
        available_docs = ["DFP", "ITR", "FRE"]
        exception = InvalidDocName(doc_name, available_docs)
        expected = f"Invalid document name: {doc_name}. Documents must be a string and one of: {available_docs}."
        assert str(exception) == expected

    def test_is_exception_subclass(self):
        """Deve herdar de Exception."""
        exception = InvalidDocName("INVALID", ["DFP", "ITR"])
        assert isinstance(exception, Exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(InvalidDocName) as exc_info:
            raise InvalidDocName("WRONG", ["DFP", "ITR"])
        assert "Invalid document name" in str(exc_info.value)
        assert "WRONG" in str(exc_info.value)

    def test_shows_all_available_docs(self):
        """Deve exibir todos os documentos válidos."""
        available_docs = ["DFP", "ITR", "FRE", "FCA"]
        exception = InvalidDocName("INVALID", available_docs)
        for doc in available_docs:
            assert doc in str(exception)

    def test_with_empty_doc_name(self):
        """Deve lidar com nome de documento vazio."""
        exception = InvalidDocName("", ["DFP"])
        assert "" in str(exception)
        assert "DFP" in str(exception)

    def test_with_empty_available_list(self):
        """Deve lidar com lista vazia de documentos válidos."""
        exception = InvalidDocName("TEST", [])
        assert "TEST" in str(exception)
        assert "[]" in str(exception)

    def test_with_single_available_doc(self):
        """Deve funcionar com apenas um documento válido."""
        exception = InvalidDocName("WRONG", ["DFP"])
        assert "WRONG" in str(exception)
        assert "DFP" in str(exception)

    def test_with_many_available_docs(self):
        """Deve funcionar com muitos documentos válidos."""
        available_docs = [f"DOC_{i}" for i in range(50)]
        exception = InvalidDocName("INVALID", available_docs)
        assert "INVALID" in str(exception)
        assert "DOC_" in str(exception)

    def test_with_special_characters(self):
        """Deve lidar com caracteres especiais."""
        doc_name = "DRE_AÇÃO_2023"
        available_docs = ["DRE", "BPARMS"]
        exception = InvalidDocName(doc_name, available_docs)
        assert doc_name in str(exception)

    def test_with_accented_characters(self):
        """Deve lidar com caracteres acentuados."""
        doc_name = "AÇÚCAR"
        available_docs = ["DFP", "ITR"]
        exception = InvalidDocName(doc_name, available_docs)
        assert doc_name in str(exception)

    def test_with_numeric_doc_names(self):
        """Deve lidar com nomes contendo números."""
        exception = InvalidDocName("DFP123", ["DFP", "ITR"])
        assert "DFP123" in str(exception)

    def test_message_contains_string_keyword(self):
        """Deve mencionar que deve ser string."""
        exception = InvalidDocName("WRONG", ["DFP"])
        assert "string" in str(exception).lower()


@pytest.mark.unit
class TestInvalidTypeDoc:
    """Testes para a exceção InvalidTypeDoc."""

    def test_message_format_exact_with_string_input(self):
        """Deve gerar mensagem exata com input string."""
        doc_name = "123"
        exception = InvalidTypeDoc(doc_name)
        expected = f"Invalid type document: {doc_name}. Documents must be a string."
        assert str(exception) == expected

    def test_message_format_exact_with_int_input(self):
        """Deve gerar mensagem exata com input inteiro."""
        doc_name = 123
        exception = InvalidTypeDoc(doc_name)
        expected = f"Invalid type document: {doc_name}. Documents must be a string."
        assert str(exception) == expected

    def test_is_exception_subclass(self):
        """Deve herdar de Exception."""
        exception = InvalidTypeDoc(123)
        assert isinstance(exception, Exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(InvalidTypeDoc) as exc_info:
            raise InvalidTypeDoc(123)
        assert "Invalid type document" in str(exc_info.value)

    def test_with_integer_value(self):
        """Deve lidar com valor inteiro."""
        exception = InvalidTypeDoc(42)
        assert "42" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_float_value(self):
        """Deve lidar com valor float."""
        exception = InvalidTypeDoc(3.14)
        assert "3.14" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_none_value(self):
        """Deve lidar com valor None."""
        exception = InvalidTypeDoc(None)
        assert "None" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_list_value(self):
        """Deve lidar com valor tipo lista."""
        value = [1, 2, 3]
        exception = InvalidTypeDoc(value)
        assert "[1, 2, 3]" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_dict_value(self):
        """Deve lidar com valor tipo dicionário."""
        value = {"key": "value"}
        exception = InvalidTypeDoc(value)
        assert "must be a string" in str(exception)

    def test_with_boolean_true(self):
        """Deve lidar com valor True."""
        exception = InvalidTypeDoc(True)
        assert "True" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_boolean_false(self):
        """Deve lidar com valor False."""
        exception = InvalidTypeDoc(False)
        assert "False" in str(exception)
        assert "must be a string" in str(exception)

    def test_with_empty_string(self):
        """Deve lidar com string vazia."""
        exception = InvalidTypeDoc("")
        assert "" in str(exception)

    def test_message_always_mentions_string_requirement(self):
        """Deve sempre mencionar que deve ser string."""
        values = [123, 3.14, None, [], {}, True, False]
        for value in values:
            exception = InvalidTypeDoc(value)
            assert "must be a string" in str(exception).lower()


@pytest.mark.unit
class TestEmptyDocumentListError:
    """Testes para a exceção EmptyDocumentListError."""

    def test_message_format(self):
        """Deve gerar mensagem clara sobre lista vazia."""
        exception = EmptyDocumentListError()
        assert "Document list cannot be empty" in str(exception)

    def test_is_exception_subclass(self):
        """Deve herdar de Exception."""
        exception = EmptyDocumentListError()
        assert isinstance(exception, Exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(EmptyDocumentListError):
            raise EmptyDocumentListError()

    def test_suggests_alternative(self):
        """Deve sugerir usar None para todos os tipos."""
        exception = EmptyDocumentListError()
        exc_str = str(exception)
        assert "None" in exc_str

    def test_message_mentions_at_least_one(self):
        """Deve mencionar necessidade de pelo menos um elemento."""
        exception = EmptyDocumentListError()
        assert "at least one" in str(exception).lower()


@pytest.mark.unit
class TestDomainExceptionsIntegration:
    """Testes de integração para exceções de domínio."""

    def test_all_domain_exceptions_are_exceptions(self):
        """Todas as exceções de domínio devem herdar de Exception."""
        exceptions = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc(123),
            EmptyDocumentListError(),
        ]
        for exc in exceptions:
            assert isinstance(
                exc, Exception
            ), f"{type(exc).__name__} is not an Exception"

    def test_catch_all_as_generic_exception(self):
        """Deve capturar todas como Exception genérica."""
        exceptions = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc(123),
            EmptyDocumentListError(),
        ]
        for exc in exceptions:
            with pytest.raises(Exception):
                raise exc

    def test_specific_exception_catching(self):
        """Deve capturar exceções específicas sem capturar outras."""
        with pytest.raises(InvalidLastYear):
            try:
                raise InvalidLastYear(2000, 2023)
            except InvalidFirstYear:
                pass

    def test_all_exceptions_have_non_empty_messages(self):
        """Todas as exceções devem ter mensagens não vazias."""
        exceptions = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc(123),
            EmptyDocumentListError(),
        ]
        for exc in exceptions:
            exc_str = str(exc)
            assert len(exc_str) > 0, f"{type(exc).__name__} has empty message"
            assert isinstance(
                exc_str, str
            ), f"{type(exc).__name__} message is not string"

    def test_validation_workflow(self):
        """Deve simular um fluxo de validação."""

        def validate_document_selection(
            first_year,
            last_year,
            doc_name,
            valid_years_range=(1990, 2023),
            valid_docs=["DRE", "BPARMS", "DMPL"],
        ):
            """Valida seleção de documento."""
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

    def test_year_boundary_conditions(self):
        """Deve funcionar com anos limítrofes."""
        exc1 = InvalidFirstYear(2023, 2023)
        assert "2023" in str(exc1)

        exc2 = InvalidFirstYear(1900, 2100)
        assert "1900" in str(exc2) and "2100" in str(exc2)

    def test_doc_exceptions_with_many_documents(self):
        """Deve funcionar com muitos documentos."""
        docs = [f"DOC_{i}" for i in range(1000)]
        exc = InvalidDocName("INVALID", docs)
        assert "INVALID" in str(exc)
