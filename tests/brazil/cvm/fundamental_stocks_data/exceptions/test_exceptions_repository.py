"""
Testes para exceções de repositório.

Cobre:
- InvalidRepositoryTypeError: tipo de repositório inválido
"""

import pytest

from src.brazil.cvm.fundamental_stocks_data.exceptions import InvalidRepositoryTypeError


@pytest.mark.unit
class TestInvalidRepositoryTypeError:
    """Testes para a exceção InvalidRepositoryTypeError."""

    def test_is_type_error_subclass(self):
        """Deve herdar de TypeError."""
        exception = InvalidRepositoryTypeError("IExpectedRepo", "InvalidRepo")
        assert isinstance(exception, TypeError)

    def test_message_shows_expected_vs_actual(self):
        """Deve mostrar tipo esperado vs tipo atual."""
        expected = "IDocumentRepository"
        actual = "string"
        exception = InvalidRepositoryTypeError(expected, actual)
        exc_str = str(exception)
        assert expected in exc_str
        assert actual in exc_str

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(InvalidRepositoryTypeError):
            raise InvalidRepositoryTypeError("IRepo", "dict")

    def test_with_various_types(self):
        """Deve funcionar com diferentes tipos."""
        test_cases = [
            ("IRepository", "str"),
            ("IAdapter", "int"),
            ("IHandler", "list"),
            ("IService", "NoneType"),
        ]
        for expected, actual in test_cases:
            exception = InvalidRepositoryTypeError(expected, actual)
            assert expected in str(exception)
            assert actual in str(exception)

    def test_can_be_caught_as_type_error(self):
        """Deve ser capturável como TypeError genérico."""
        with pytest.raises(TypeError):
            raise InvalidRepositoryTypeError("IRepo", "str")

    def test_message_mentions_instance(self):
        """Deve mencionar que deve ser instância."""
        exception = InvalidRepositoryTypeError("IMyInterface", "WrongClass")
        assert "instance" in str(exception).lower()

    def test_with_class_names(self):
        """Deve funcionar com nomes de classes."""
        exception = InvalidRepositoryTypeError("DocumentRepository", "str")
        assert "DocumentRepository" in str(exception)
        assert "str" in str(exception)

    def test_with_module_qualified_names(self):
        """Deve funcionar com nomes qualificados de módulo."""
        expected = "myapp.repos.IRepository"
        actual = "myapp.models.Document"
        exception = InvalidRepositoryTypeError(expected, actual)
        assert expected in str(exception)
        assert actual in str(exception)

    def test_with_empty_type_names(self):
        """Deve lidar com nomes de tipos vazios."""
        exception = InvalidRepositoryTypeError("", "SomeType")
        assert isinstance(exception, InvalidRepositoryTypeError)

    def test_with_special_characters_in_names(self):
        """Deve lidar com caracteres especiais em nomes."""
        expected = "IRepository[T]"
        actual = "Dict[str, Any]"
        exception = InvalidRepositoryTypeError(expected, actual)
        assert expected in str(exception) or "[" in str(exception)


@pytest.mark.unit
class TestRepositoryExceptionIntegration:
    """Testes de integração para exceções de repositório."""

    def test_exception_is_type_error(self):
        """Deve herdar de TypeError."""
        exc = InvalidRepositoryTypeError("IRepo", "str")
        assert isinstance(exc, TypeError)

    def test_catch_as_exception(self):
        """Deve capturar como Exception genérica."""
        with pytest.raises(Exception):
            raise InvalidRepositoryTypeError("IRepo", "str")

    def test_has_non_empty_message(self):
        """Deve ter mensagem não vazia."""
        exc = InvalidRepositoryTypeError("IRepo", "str")
        exc_str = str(exc)
        assert len(exc_str) > 0
        assert isinstance(exc_str, str)

    def test_repository_validation_workflow(self):
        """Deve simular um fluxo de validação de repositório."""

        def validate_repository(repo, expected_interface_name):
            """Valida tipo de repositório."""
            if not hasattr(repo, "validate"):
                actual_type = type(repo).__name__
                raise InvalidRepositoryTypeError(expected_interface_name, actual_type)
            return True

        # Simular repositório válido
        class ValidRepository:
            def validate(self):
                return True

        # Teste com tipo válido
        repo = ValidRepository()
        assert validate_repository(repo, "IRepository")

        # Teste com tipo inválido
        with pytest.raises(InvalidRepositoryTypeError):
            validate_repository("not_a_repo", "IRepository")

    def test_multiple_type_validations(self):
        """Deve validar múltiplos tipos em sequência."""

        def check_type(obj, expected_type_name):
            if not hasattr(obj, "validate"):
                raise InvalidRepositoryTypeError(expected_type_name, type(obj).__name__)
            return True

        class ValidClass:
            def validate(self):
                pass

        valid_obj = ValidClass()
        assert check_type(valid_obj, "IValidator")

        with pytest.raises(InvalidRepositoryTypeError):
            check_type("not_valid", "IValidator")

    def test_with_different_error_scenarios(self):
        """Deve cobrir diferentes cenários de erro."""
        scenarios = [
            ("IDocumentRepository", "None"),
            ("IAdapter", "list"),
            ("IService", "dict"),
            ("IFactory", "function"),
        ]

        for expected, actual in scenarios:
            with pytest.raises(InvalidRepositoryTypeError):
                raise InvalidRepositoryTypeError(expected, actual)

    def test_exception_message_clarity(self):
        """Mensagem deve ser clara e útil para debug."""
        exception = InvalidRepositoryTypeError("IMyRepository", "str")
        exc_str = str(exception)
        # Deve conter informações úteis
        assert "IMyRepository" in exc_str
        assert "str" in exc_str
        assert len(exc_str) > 20  # Mensagem descritiva

    def test_repository_type_mismatch_scenarios(self):
        """Deve cobrir cenários reais de incompatibilidade de tipo."""
        test_cases = [
            # (expected, actual, context)
            ("DocumentRepository", "string", "passing string instead of repo"),
            ("IAdapter", "int", "passing integer instead of adapter"),
            ("Handler", "list", "passing list instead of handler"),
        ]

        for expected, actual, context in test_cases:
            exception = InvalidRepositoryTypeError(expected, actual)
            assert expected in str(exception), f"Failed: {context}"
            assert actual in str(exception), f"Failed: {context}"
