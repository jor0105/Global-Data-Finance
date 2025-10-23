"""
Testes para exceções de caminho e validação de diretórios.

Cobre:
- InvalidDestinationPathError: caminho inválido
- PathIsNotDirectoryError: caminho não é diretório
- PathPermissionError: sem permissão de escrita
"""

import pytest

from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)


@pytest.mark.unit
class TestInvalidDestinationPathError:
    """Testes para a exceção InvalidDestinationPathError."""

    def test_is_value_error_subclass(self):
        """Deve herdar de ValueError."""
        exception = InvalidDestinationPathError("test reason")
        assert isinstance(exception, ValueError)

    def test_message_includes_reason(self):
        """Deve incluir motivo fornecido."""
        reason = "Path is empty"
        exception = InvalidDestinationPathError(reason)
        assert reason in str(exception)
        assert "Invalid destination path" in str(exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(InvalidDestinationPathError):
            raise InvalidDestinationPathError("empty path")

    def test_with_various_reasons(self):
        """Deve lidar com diferentes motivos."""
        reasons = [
            "Path is empty",
            "Path contains only whitespace",
            "Path is not a string",
            "Path contains invalid characters",
        ]
        for reason in reasons:
            exception = InvalidDestinationPathError(reason)
            assert reason in str(exception)

    def test_can_be_caught_as_value_error(self):
        """Deve ser capturável como ValueError genérico."""
        with pytest.raises(ValueError):
            raise InvalidDestinationPathError("test")

    def test_with_long_reason(self):
        """Deve lidar com motivo longo."""
        reason = "This is a very long reason " * 10
        exception = InvalidDestinationPathError(reason)
        assert reason in str(exception)

    def test_with_empty_reason(self):
        """Deve lidar com motivo vazio."""
        exception = InvalidDestinationPathError("")
        assert isinstance(exception, InvalidDestinationPathError)


@pytest.mark.unit
class TestPathIsNotDirectoryError:
    """Testes para a exceção PathIsNotDirectoryError."""

    def test_is_value_error_subclass(self):
        """Deve herdar de ValueError."""
        exception = PathIsNotDirectoryError("/path/to/file.txt")
        assert isinstance(exception, ValueError)

    def test_message_mentions_file_not_directory(self):
        """Deve mencionar que é file não directory."""
        path = "/path/to/file.txt"
        exception = PathIsNotDirectoryError(path)
        exc_str = str(exception)
        assert "directory" in exc_str.lower()
        assert "file" in exc_str.lower()

    def test_includes_path_in_message(self):
        """Deve incluir caminho na mensagem."""
        path = "/path/to/file.txt"
        exception = PathIsNotDirectoryError(path)
        assert path in str(exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(PathIsNotDirectoryError):
            raise PathIsNotDirectoryError("/tmp/file")

    def test_with_different_paths(self):
        """Deve funcionar com diferentes caminhos."""
        paths = ["/path/to/file.txt", "C:\\Users\\file.txt", "~/document.pdf"]
        for path in paths:
            exception = PathIsNotDirectoryError(path)
            assert path in str(exception)

    def test_with_relative_path(self):
        """Deve funcionar com caminhos relativos."""
        exception = PathIsNotDirectoryError("./file.txt")
        assert "./file.txt" in str(exception)

    def test_with_absolute_path(self):
        """Deve funcionar com caminhos absolutos."""
        exception = PathIsNotDirectoryError("/absolute/path/file")
        assert "/absolute/path/file" in str(exception)

    def test_can_be_caught_as_value_error(self):
        """Deve ser capturável como ValueError genérico."""
        with pytest.raises(ValueError):
            raise PathIsNotDirectoryError("/tmp/file")

    def test_with_empty_path(self):
        """Deve lidar com caminho vazio."""
        exception = PathIsNotDirectoryError("")
        assert isinstance(exception, PathIsNotDirectoryError)

    def test_with_special_characters_in_path(self):
        """Deve lidar com caracteres especiais no caminho."""
        path = "/path/to/file_with_üñíçödé.txt"
        exception = PathIsNotDirectoryError(path)
        assert path in str(exception)


@pytest.mark.unit
class TestPathPermissionError:
    """Testes para a exceção PathPermissionError."""

    def test_is_os_error_subclass(self):
        """Deve herdar de OSError."""
        exception = PathPermissionError("/path/to/dir")
        assert isinstance(exception, OSError)

    def test_message_mentions_permission_denied(self):
        """Deve mencionar permissão negada."""
        path = "/path/to/dir"
        exception = PathPermissionError(path)
        exc_str = str(exception).lower()
        assert "permission" in exc_str
        assert "denied" in exc_str or "no write" in exc_str

    def test_includes_path_in_message(self):
        """Deve incluir caminho na mensagem."""
        path = "/var/restricted"
        exception = PathPermissionError(path)
        assert path in str(exception)

    def test_can_be_raised_and_caught(self):
        """Deve ser levantada e capturada corretamente."""
        with pytest.raises(PathPermissionError):
            raise PathPermissionError("/restricted/path")

    def test_with_different_paths(self):
        """Deve funcionar com diferentes caminhos."""
        paths = ["/root/protected", "/var/log/restricted", "/sys/config"]
        for path in paths:
            exception = PathPermissionError(path)
            assert path in str(exception)

    def test_can_be_caught_as_os_error(self):
        """Deve ser capturável como OSError genérico."""
        with pytest.raises(OSError):
            raise PathPermissionError("/tmp")

    def test_with_write_permission_mention(self):
        """Deve mencionar permissão de escrita."""
        exception = PathPermissionError("/root")
        assert "write" in str(exception).lower()

    def test_with_relative_path(self):
        """Deve funcionar com caminhos relativos."""
        exception = PathPermissionError("./restricted_dir")
        assert "./restricted_dir" in str(exception)

    def test_with_empty_path(self):
        """Deve lidar com caminho vazio."""
        exception = PathPermissionError("")
        assert isinstance(exception, PathPermissionError)

    def test_with_special_characters_in_path(self):
        """Deve lidar com caracteres especiais no caminho."""
        path = "/path/to/restricted_üñíçödé"
        exception = PathPermissionError(path)
        assert path in str(exception)


@pytest.mark.unit
class TestPathExceptionsIntegration:
    """Testes de integração para exceções de caminho."""

    def test_all_path_exceptions_inherit_from_error(self):
        """Todas as exceções de caminho devem herdar corretamente."""
        assert isinstance(InvalidDestinationPathError("test"), ValueError)
        assert isinstance(PathIsNotDirectoryError("/path"), ValueError)
        assert isinstance(PathPermissionError("/path"), OSError)

    def test_catch_all_as_exception(self):
        """Deve capturar todas como Exception genérica."""
        exceptions = [
            InvalidDestinationPathError("test"),
            PathIsNotDirectoryError("/path"),
            PathPermissionError("/path"),
        ]
        for exc in exceptions:
            with pytest.raises(Exception):
                raise exc

    def test_specific_exception_catching(self):
        """Deve capturar exceções específicas sem capturar outras."""
        with pytest.raises(PathIsNotDirectoryError):
            try:
                raise PathIsNotDirectoryError("/tmp/file")
            except InvalidDestinationPathError:
                pass

    def test_all_exceptions_have_non_empty_messages(self):
        """Todas as exceções devem ter mensagens não vazias."""
        exceptions = [
            InvalidDestinationPathError("reason"),
            PathIsNotDirectoryError("/path"),
            PathPermissionError("/path"),
        ]
        for exc in exceptions:
            exc_str = str(exc)
            assert len(exc_str) > 0, f"{type(exc).__name__} has empty message"
            assert isinstance(
                exc_str, str
            ), f"{type(exc).__name__} message is not string"

    def test_catch_value_error_variants(self):
        """Deve capturar exceções de caminho como ValueError."""
        errors = [
            InvalidDestinationPathError("test"),
            PathIsNotDirectoryError("/path"),
        ]
        for error in errors:
            with pytest.raises(ValueError):
                raise error

    def test_catch_os_error_variant(self):
        """Deve capturar PathPermissionError como OSError."""
        with pytest.raises(OSError):
            raise PathPermissionError("/path")

    def test_path_validation_workflow(self):
        """Deve simular um fluxo de validação de caminho."""

        def validate_destination_path(path):
            """Valida destino do caminho."""
            if not path or not isinstance(path, str):
                raise InvalidDestinationPathError("Path must be a non-empty string")

            if path.strip() == "":
                raise InvalidDestinationPathError("Path cannot be whitespace only")

            # Simulando verificações
            if path.endswith(".txt"):
                raise PathIsNotDirectoryError(path)

            if path.startswith("/root"):
                raise PathPermissionError(path)

            return True

        # Teste válido
        assert validate_destination_path("/valid/path")

        # Testes inválidos
        with pytest.raises(InvalidDestinationPathError):
            validate_destination_path("")

        with pytest.raises(InvalidDestinationPathError):
            validate_destination_path("   ")

        with pytest.raises(PathIsNotDirectoryError):
            validate_destination_path("/tmp/file.txt")

        with pytest.raises(PathPermissionError):
            validate_destination_path("/root/restricted")

    def test_path_exceptions_with_very_long_paths(self):
        """Deve funcionar com caminhos muito longos."""
        long_path = "/very/" * 100 + "long/path"

        exc1 = InvalidDestinationPathError(long_path)
        exc2 = PathIsNotDirectoryError(long_path)
        exc3 = PathPermissionError(long_path)

        assert long_path in str(exc1) or "/" in str(exc1)
        assert long_path in str(exc2) or "/" in str(exc2)
        assert long_path in str(exc3) or "/" in str(exc3)

    def test_multiple_path_exceptions_in_sequence(self):
        """Deve lidar com múltiplas exceções em sequência."""
        errors = []

        test_cases = [
            (InvalidDestinationPathError("test"), "invalid_dest"),
            (PathIsNotDirectoryError("/path"), "not_directory"),
            (PathPermissionError("/path"), "permission_denied"),
        ]

        for exc, test_type in test_cases:
            try:
                raise exc
            except (
                InvalidDestinationPathError,
                PathIsNotDirectoryError,
                PathPermissionError,
            ):
                errors.append(test_type)

        assert len(errors) == 3
        assert "invalid_dest" in errors
        assert "not_directory" in errors
        assert "permission_denied" in errors
