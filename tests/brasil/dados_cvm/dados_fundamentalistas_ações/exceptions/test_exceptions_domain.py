"""
Testes para as exceções de domínio (InvalidFirstYear, InvalidLastYear, InvalidDocName, InvalidTypeDoc).

Cobre:
- Validação de anos
- Validação de documentos
- Mensagens de erro apropriadas
"""

import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.exceptions import (
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear,
    InvalidTypeDoc,
)


class TestInvalidFirstYear:
    """Testes para a exceção InvalidFirstYear."""

    def test_invalid_first_year_creation(self):
        """Deve criar exceção com anos válidos."""
        minimal = 1990
        atual = 2023
        error = InvalidFirstYear(minimal, atual)

        assert isinstance(error, Exception)
        assert "Invalid first year" in str(error)
        assert str(minimal) in str(error)
        assert str(atual) in str(error)

    def test_invalid_first_year_message_contains_range(self):
        """Deve informar o intervalo válido."""
        minimal = 1990
        atual = 2023
        error = InvalidFirstYear(minimal, atual)
        error_str = str(error)

        assert str(minimal) in error_str
        assert str(atual) in error_str

    def test_invalid_first_year_is_exception(self):
        """Deve herdar de Exception."""
        error = InvalidFirstYear(1990, 2023)
        assert isinstance(error, Exception)

    def test_invalid_first_year_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(InvalidFirstYear):
            raise InvalidFirstYear(1990, 2023)

    def test_invalid_first_year_with_different_ranges(self):
        """Deve funcionar com diferentes intervalos."""
        test_cases = [
            (2000, 2023),
            (1980, 2020),
            (2010, 2024),
        ]

        for minimal, atual in test_cases:
            error = InvalidFirstYear(minimal, atual)
            assert str(minimal) in str(error)

    def test_invalid_first_year_message_format(self):
        """Deve validar o formato da mensagem."""
        error = InvalidFirstYear(1990, 2023)
        error_str = str(error)

        assert "greater than or equal to" in error_str.lower() or ">=" in error_str
        assert "less than or equal to" in error_str.lower() or "<=" in error_str


class TestInvalidLastYear:
    """Testes para a exceção InvalidLastYear."""

    def test_invalid_last_year_creation(self):
        """Deve criar exceção com dados válidos."""
        first_year = 2000
        atual = 2023
        error = InvalidLastYear(first_year, atual)

        assert isinstance(error, Exception)
        assert "Invalid last year" in str(error)
        assert str(first_year) in str(error)
        assert str(atual) in str(error)

    def test_invalid_last_year_message_contains_range(self):
        """Deve informar o intervalo válido."""
        first_year = 2000
        atual = 2023
        error = InvalidLastYear(first_year, atual)
        error_str = str(error)

        assert str(first_year) in error_str
        assert str(atual) in error_str

    def test_invalid_last_year_is_exception(self):
        """Deve herdar de Exception."""
        error = InvalidLastYear(2000, 2023)
        assert isinstance(error, Exception)

    def test_invalid_last_year_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(InvalidLastYear):
            raise InvalidLastYear(2000, 2023)

    def test_invalid_last_year_with_different_ranges(self):
        """Deve funcionar com diferentes intervalos."""
        test_cases = [
            (2000, 2023),
            (2010, 2020),
            (2015, 2024),
        ]

        for first_year, atual in test_cases:
            error = InvalidLastYear(first_year, atual)
            assert str(first_year) in str(error)

    def test_invalid_last_year_message_format(self):
        """Deve validar o formato da mensagem."""
        error = InvalidLastYear(2000, 2023)
        error_str = str(error)

        assert "greater than or equal to" in error_str.lower() or ">=" in error_str
        assert "less than or equal to" in error_str.lower() or "<=" in error_str


class TestInvalidDocName:
    """Testes para a exceção InvalidDocName."""

    def test_invalid_doc_name_creation(self):
        """Deve criar exceção com nome de documento e lista de válidos."""
        doc_name = "INVALID"
        valid_docs = ["DRE", "BPARMS", "DMPL", "IROT"]
        error = InvalidDocName(doc_name, valid_docs)

        assert isinstance(error, Exception)
        assert "Invalid document name" in str(error)
        assert doc_name in str(error)

    def test_invalid_doc_name_shows_available_docs(self):
        """Deve listar os documentos válidos."""
        doc_name = "WRONG"
        valid_docs = ["DRE", "BPARMS", "DMPL"]
        error = InvalidDocName(doc_name, valid_docs)
        error_str = str(error)

        for doc in valid_docs:
            assert doc in error_str

    def test_invalid_doc_name_is_exception(self):
        """Deve herdar de Exception."""
        error = InvalidDocName("INVALID", ["DRE"])
        assert isinstance(error, Exception)

    def test_invalid_doc_name_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(InvalidDocName):
            raise InvalidDocName("INVALID", ["DRE", "BPARMS"])

    def test_invalid_doc_name_with_empty_doc_name(self):
        """Deve lidar com nome de documento vazio."""
        error = InvalidDocName("", ["DRE"])
        assert isinstance(error, InvalidDocName)

    def test_invalid_doc_name_with_empty_valid_list(self):
        """Deve lidar com lista vazia de documentos válidos."""
        error = InvalidDocName("DRE", [])
        assert isinstance(error, InvalidDocName)

    def test_invalid_doc_name_with_many_valid_docs(self):
        """Deve lidar com muitos documentos válidos."""
        valid_docs = [f"DOC_{i}" for i in range(100)]
        error = InvalidDocName("INVALID", valid_docs)
        error_str = str(error)

        # Deve mencionar pelo menos alguns documentos
        assert "DOC_" in error_str

    def test_invalid_doc_name_message_format(self):
        """Deve validar o formato da mensagem."""
        error = InvalidDocName("WRONG", ["DRE", "BPARMS"])
        error_str = str(error)

        assert "string" in error_str.lower()
        assert "WRONG" in error_str

    def test_invalid_doc_name_with_special_characters(self):
        """Deve lidar com caracteres especiais."""
        doc_name = "DRE_AÇÃO"
        valid_docs = ["DRE", "BPARMS"]
        error = InvalidDocName(doc_name, valid_docs)
        assert doc_name in str(error)


class TestInvalidTypeDoc:
    """Testes para a exceção InvalidTypeDoc."""

    def test_invalid_type_doc_creation(self):
        """Deve criar exceção com nome de documento."""
        doc_name = "DRE"
        error = InvalidTypeDoc(doc_name)

        assert isinstance(error, Exception)
        assert "Invalid type document" in str(error)
        assert doc_name in str(error)

    def test_invalid_type_doc_mentions_string_requirement(self):
        """Deve mencionar que deve ser string."""
        error = InvalidTypeDoc("not_a_string")
        error_str = str(error)

        assert "string" in error_str.lower()

    def test_invalid_type_doc_is_exception(self):
        """Deve herdar de Exception."""
        error = InvalidTypeDoc("something")
        assert isinstance(error, Exception)

    def test_invalid_type_doc_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(InvalidTypeDoc):
            raise InvalidTypeDoc("invalid_type")

    def test_invalid_type_doc_with_empty_name(self):
        """Deve lidar com nome vazio."""
        error = InvalidTypeDoc("")
        assert isinstance(error, InvalidTypeDoc)

    def test_invalid_type_doc_with_special_characters(self):
        """Deve lidar com caracteres especiais."""
        error = InvalidTypeDoc("DRE_123_AÇÃO")
        assert isinstance(error, InvalidTypeDoc)

    def test_invalid_type_doc_message_format(self):
        """Deve validar o formato da mensagem."""
        doc_name = "INVALID"
        error = InvalidTypeDoc(doc_name)
        error_str = str(error)

        assert "type" in error_str.lower()
        assert "string" in error_str.lower()


class TestDomainExceptionsIntegration:
    """Testes de integração para exceções de domínio."""

    def test_all_exceptions_inherit_from_exception(self):
        """Todas as exceções devem herdar de Exception."""
        exceptions = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc("value"),
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_catch_all_as_generic_exception(self):
        """Deve capturar todas as exceções como Exception genérica."""
        errors = [
            InvalidFirstYear(1990, 2023),
            InvalidLastYear(2000, 2023),
            InvalidDocName("INVALID", ["DRE"]),
            InvalidTypeDoc("value"),
        ]

        for error in errors:
            with pytest.raises(Exception):
                raise error

    def test_exception_string_representations(self):
        """Deve ter representações de string significativas."""
        exceptions = {
            "InvalidFirstYear": InvalidFirstYear(1990, 2023),
            "InvalidLastYear": InvalidLastYear(2000, 2023),
            "InvalidDocName": InvalidDocName("INVALID", ["DRE"]),
            "InvalidTypeDoc": InvalidTypeDoc("value"),
        }

        for name, exc in exceptions.items():
            exc_str = str(exc)
            assert len(exc_str) > 0
            assert isinstance(exc_str, str)

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

        # Teste válido
        assert validate_document_selection(2000, 2023, "DRE")

        # Testes inválidos
        with pytest.raises(InvalidFirstYear):
            validate_document_selection(1989, 2023, "DRE")

        with pytest.raises(InvalidLastYear):
            validate_document_selection(2020, 2024, "DRE")

        with pytest.raises(InvalidTypeDoc):
            validate_document_selection(2000, 2023, 123)

        with pytest.raises(InvalidDocName):
            validate_document_selection(2000, 2023, "INVALID")

    def test_multiple_exception_handling(self):
        """Deve lidar com múltiplas exceções em sequência."""
        errors = []

        test_cases = [
            (InvalidFirstYear(1990, 2023), "first_year"),
            (InvalidLastYear(2000, 2023), "last_year"),
            (InvalidDocName("INVALID", ["DRE"]), "doc_name"),
            (InvalidTypeDoc("value"), "type_doc"),
        ]

        for exc, test_type in test_cases:
            try:
                raise exc
            except (InvalidFirstYear, InvalidLastYear, InvalidDocName, InvalidTypeDoc):
                errors.append(test_type)

        assert len(errors) == 4
        assert "first_year" in errors
        assert "last_year" in errors
        assert "doc_name" in errors
        assert "type_doc" in errors

    def test_exception_catching_specificity(self):
        """Deve capturar exceções específicas corretamente."""
        # InvalidFirstYear
        with pytest.raises(InvalidFirstYear):
            raise InvalidFirstYear(1990, 2023)

        # InvalidLastYear
        with pytest.raises(InvalidLastYear):
            raise InvalidLastYear(2000, 2023)

        # InvalidDocName
        with pytest.raises(InvalidDocName):
            raise InvalidDocName("INVALID", ["DRE"])

        # InvalidTypeDoc
        with pytest.raises(InvalidTypeDoc):
            raise InvalidTypeDoc("value")

    def test_exceptions_independence(self):
        """Deve manter independência entre exceções."""
        exc1 = InvalidFirstYear(1990, 2023)
        exc2 = InvalidFirstYear(2000, 2024)

        assert not isinstance(exc1, InvalidLastYear)
        assert not isinstance(exc2, InvalidDocName)

    def test_year_validation_scenarios(self):
        """Deve cobrir diferentes cenários de validação de anos."""
        # Caso 1: Primeiro ano muito baixo
        with pytest.raises(InvalidFirstYear):
            raise InvalidFirstYear(1980, 2023)

        # Caso 2: Último ano após o ano atual
        with pytest.raises(InvalidLastYear):
            raise InvalidLastYear(2020, 2024)

        # Casos válidos
        error1 = InvalidFirstYear(1990, 2023)
        error2 = InvalidLastYear(2000, 2023)
        assert error1 is not None
        assert error2 is not None

    def test_document_validation_scenarios(self):
        """Deve cobrir diferentes cenários de validação de documentos."""
        valid_docs = ["DRE", "BPARMS", "DMPL", "IROT"]

        # Documento inválido
        with pytest.raises(InvalidDocName):
            raise InvalidDocName("INVALID", valid_docs)

        # Tipo inválido
        with pytest.raises(InvalidTypeDoc):
            raise InvalidTypeDoc("something")

        # Documentos válidos são aceitos implicitamente
        assert "DRE" in valid_docs
        assert "BPARMS" in valid_docs
