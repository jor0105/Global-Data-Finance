"""
Testes para exceções de repositório.

Cobre:
- InvalidRepositoryTypeError: tipo de repositório inválido
"""

import pytest

from src.brazil.cvm.fundamental_stocks_data import InvalidRepositoryTypeError


@pytest.mark.unit
class TestInvalidRepositoryTypeError:
    """Testes para a exceção InvalidRepositoryTypeError."""

    def test_is_type_error_subclass(self):
        """Deve herdar de TypeError."""
        exception = InvalidRepositoryTypeError("dict")
        assert isinstance(exception, TypeError)

    def test_message_shows_actual_type(self):
        """Deve mostrar tipo inválido recebido."""
        actual = "string"
        exception = InvalidRepositoryTypeError(actual)
        exc_str = str(exception)
        assert actual in exc_str
        assert "Repository" in exc_str

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(InvalidRepositoryTypeError):
            raise InvalidRepositoryTypeError("dict")

    def test_with_various_types(self):
        """Deve funcionar com diferentes tipos."""
        test_cases = ["str", "int", "list", "NoneType", "dict"]
        for actual in test_cases:
            exception = InvalidRepositoryTypeError(actual)
            assert actual in str(exception)

    def test_can_be_caught_as_type_error(self):
        """Deve ser capturável como TypeError genérico."""
        with pytest.raises(TypeError):
            raise InvalidRepositoryTypeError("str")

    def test_message_mentions_repository(self):
        """Deve mencionar repositório na mensagem."""
        exception = InvalidRepositoryTypeError("WrongClass")
        assert "Repository" in str(exception)

    def test_with_builtin_types(self):
        """Deve funcionar com tipos built-in."""
        exception = InvalidRepositoryTypeError("str")
        assert "str" in str(exception)
        assert "Repository" in str(exception)

    def test_with_custom_class_names(self):
        """Deve funcionar com nomes de classes customizadas."""
        exception = InvalidRepositoryTypeError("DocumentClass")
        assert "DocumentClass" in str(exception)

    def test_with_complex_type_expressions(self):
        """Deve funcionar com expressões de tipo complexas."""
        actual = "Dict[str, Any]"
        exception = InvalidRepositoryTypeError(actual)
        assert actual in str(exception) or "Dict" in str(exception)

    def test_with_empty_type_names(self):
        """Deve lidar com nomes de tipos vazios."""
        exception = InvalidRepositoryTypeError("")
        assert isinstance(exception, InvalidRepositoryTypeError)

    def test_with_special_characters_in_names(self):
        """Deve lidar com caracteres especiais em nomes."""
        actual = "Dict[str, Any]"
        exception = InvalidRepositoryTypeError(actual)
        assert actual in str(exception) or "[" in str(exception)


@pytest.mark.unit
class TestRepositoryExceptionIntegration:
    """Testes de integração para exceções de repositório."""

    def test_exception_is_type_error(self):
        """Deve herdar de TypeError."""
        exc = InvalidRepositoryTypeError("str")
        assert isinstance(exc, TypeError)

    def test_catch_as_exception(self):
        """Deve capturar como Exception genérica."""
        with pytest.raises(Exception):
            raise InvalidRepositoryTypeError("str")

    def test_has_non_empty_message(self):
        """Deve ter mensagem não vazia."""
        exc = InvalidRepositoryTypeError("str")
        exc_str = str(exc)
        assert len(exc_str) > 0
        assert isinstance(exc_str, str)

    def test_repository_validation_workflow(self):
        """Deve simular um fluxo de validação de repositório."""

        def validate_repository(repo):
            """Valida tipo de repositório."""
            if not hasattr(repo, "validate"):
                actual_type = type(repo).__name__
                raise InvalidRepositoryTypeError(actual_type)
            return True

        # Simular repositório válido
        class ValidRepository:
            def validate(self):
                return True

        # Teste com tipo válido
        repo = ValidRepository()
        assert validate_repository(repo)

        # Teste com tipo inválido
        with pytest.raises(InvalidRepositoryTypeError):
            validate_repository("not_a_repo")

    def test_multiple_type_validations(self):
        """Deve validar múltiplos tipos em sequência."""

        def check_type(obj):
            if not hasattr(obj, "validate"):
                raise InvalidRepositoryTypeError(type(obj).__name__)
            return True

        class ValidClass:
            def validate(self):
                pass

        valid_obj = ValidClass()
        assert check_type(valid_obj)

        with pytest.raises(InvalidRepositoryTypeError):
            check_type("not_valid")

    def test_with_different_error_scenarios(self):
        """Deve cobrir diferentes cenários de erro."""
        scenarios = [
            "None",
            "list",
            "dict",
            "function",
        ]

        for actual in scenarios:
            with pytest.raises(InvalidRepositoryTypeError):
                raise InvalidRepositoryTypeError(actual)

    def test_exception_message_clarity(self):
        """Mensagem deve ser clara e útil para debug."""
        exception = InvalidRepositoryTypeError("str")
        exc_str = str(exception)
        # Deve conter informações úteis
        assert "str" in exc_str
        assert len(exc_str) > 10  # Mensagem descritiva

    def test_repository_type_mismatch_scenarios(self):
        """Deve cobrir cenários reais de incompatibilidade de tipo."""
        test_cases = [
            "string",
            "int",
            "list",
        ]

        for actual in test_cases:
            exception = InvalidRepositoryTypeError(actual)
            assert actual in str(exception)
