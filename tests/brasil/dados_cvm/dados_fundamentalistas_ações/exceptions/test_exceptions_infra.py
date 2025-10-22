import pytest

from src.brasil.dados_cvm.dados_fundamentalistas_ações.exceptions import (
    WgetLibraryError,
    WgetValueError,
)


class TestWgetLibraryError:
    def test_wget_library_error_with_doc_name_only(self):
        """Deve criar exceção com apenas o nome do documento."""
        doc_name = "DRE"
        error = WgetLibraryError(doc_name)

        assert isinstance(error, Exception)
        assert "Wget library error" in str(error)
        assert doc_name in str(error)

    def test_wget_library_error_with_message(self):
        """Deve criar exceção com nome e mensagem."""
        doc_name = "BPARMS"
        message = "Internal wget error"
        error = WgetLibraryError(doc_name, message)

        assert doc_name in str(error)
        assert message in str(error)

    def test_wget_library_error_with_none_message(self):
        """Deve aceitar None como mensagem."""
        error = WgetLibraryError("DRE", None)
        assert "DRE" in str(error)

    def test_wget_library_error_is_exception(self):
        """Deve herdar de Exception."""
        error = WgetLibraryError("DRE")
        assert isinstance(error, Exception)

    def test_wget_library_error_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(WgetLibraryError):
            raise WgetLibraryError("DRE", "Internal error")

    def test_wget_library_error_with_empty_doc_name(self):
        """Deve lidar com nome de documento vazio."""
        error = WgetLibraryError("", "Error message")
        assert isinstance(error, WgetLibraryError)

    def test_wget_library_error_message_format(self):
        """Deve validar o formato da mensagem de erro."""
        error = WgetLibraryError("DMPL", "SSL error")
        error_str = str(error)
        assert "Wget library error" in error_str
        assert "DMPL" in error_str

    def test_wget_library_error_with_special_characters(self):
        """Deve lidar com caracteres especiais."""
        doc_name = "DRE_2023"
        message = "Erro: conexão falhou [SSL: CERTIFICATE_VERIFY_FAILED]"
        error = WgetLibraryError(doc_name, message)

        assert doc_name in str(error)
        assert "Erro" in str(error)


class TestWgetValueError:
    """Testes para a exceção WgetValueError."""

    def test_wget_value_error_with_string_value(self):
        """Deve criar exceção com valor string."""
        value = "invalid_url"
        error = WgetValueError(value)

        assert isinstance(error, Exception)
        assert "Value error" in str(error)
        assert value in str(error)

    def test_wget_value_error_with_integer_value(self):
        """Deve criar exceção com valor inteiro."""
        value = 12345
        error = WgetValueError(value)

        assert str(value) in str(error)

    def test_wget_value_error_with_none_value(self):
        """Deve criar exceção com valor None."""
        error = WgetValueError(None)
        assert isinstance(error, WgetValueError)

    def test_wget_value_error_with_empty_string(self):
        """Deve criar exceção com string vazia."""
        error = WgetValueError("")
        assert isinstance(error, WgetValueError)

    def test_wget_value_error_is_exception(self):
        """Deve herdar de Exception."""
        error = WgetValueError("some_value")
        assert isinstance(error, Exception)

    def test_wget_value_error_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(WgetValueError):
            raise WgetValueError("invalid_url")

    def test_wget_value_error_with_list_value(self):
        """Deve lidar com valor tipo lista."""
        value = ["url1", "url2"]
        error = WgetValueError(value)
        assert isinstance(error, WgetValueError)

    def test_wget_value_error_with_dict_value(self):
        """Deve lidar com valor tipo dicionário."""
        value = {"key": "value"}
        error = WgetValueError(value)
        assert isinstance(error, WgetValueError)

    def test_wget_value_error_message_format(self):
        """Deve validar o formato da mensagem de erro."""
        value = "bad_url"
        error = WgetValueError(value)
        error_str = str(error)
        assert "Value error" in error_str
        assert value in error_str


class TestInfraExceptionsIntegration:
    """Testes de integração para exceções de infraestrutura."""

    def test_both_exceptions_inherit_from_exception(self):
        """Ambas exceções devem herdar de Exception."""
        exceptions = [WgetLibraryError("DRE"), WgetValueError("value")]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_catch_wget_library_error_specifically(self):
        """Deve capturar WgetLibraryError especificamente."""
        with pytest.raises(WgetLibraryError):
            raise WgetLibraryError("DRE", "Internal error")

    def test_catch_wget_value_error_specifically(self):
        """Deve capturar WgetValueError especificamente."""
        with pytest.raises(WgetValueError):
            raise WgetValueError("invalid_value")

    def test_catch_both_as_generic_exception(self):
        """Deve capturar ambas como Exception genérica."""
        errors = [WgetLibraryError("DRE", "error"), WgetValueError("value")]

        for error in errors:
            with pytest.raises(Exception):
                raise error

    def test_exception_string_representations(self):
        """Deve ter representações de string significativas."""
        exceptions = {
            "WgetLibraryError": WgetLibraryError("DRE", "Internal error"),
            "WgetValueError": WgetValueError("invalid_url"),
        }

        for name, exc in exceptions.items():
            exc_str = str(exc)
            assert len(exc_str) > 0
            assert isinstance(exc_str, str)

    def test_multiple_exception_handling_workflow(self):
        """Deve simular fluxo de tratamento de múltiplas exceções."""
        errors = []

        def simulate_download(should_fail, error_type):
            """Simula download com tratamento de erro."""
            if should_fail:
                if error_type == "library":
                    raise WgetLibraryError("DRE", "Wget failed")
                elif error_type == "value":
                    raise WgetValueError("bad_url")

        specs = [
            (False, None),
            (True, "library"),
            (True, "value"),
            (False, None),
        ]

        for should_fail, error_type in specs:
            try:
                simulate_download(should_fail, error_type)
            except (WgetLibraryError, WgetValueError) as e:
                errors.append(str(e))

        assert len(errors) == 2

    def test_exception_with_different_message_formats(self):
        """Deve lidar com diferentes formatos de mensagens."""
        messages = [
            "Simple error message",
            "Error with special chars: @#$%",
            "Error with numbers 123456",
            "Erro com acentuação: çãõé",
            "Error with: colons; semicolons, commas.",
        ]

        for msg in messages:
            error = WgetLibraryError("DRE", msg)
            assert msg in str(error) or "DRE" in str(error)

    def test_wget_library_error_vs_wget_value_error(self):
        """Deve diferenciar entre os dois tipos de erro."""
        lib_error = WgetLibraryError("DRE", "message")
        val_error = WgetValueError("value")

        assert isinstance(lib_error, WgetLibraryError)
        assert not isinstance(lib_error, WgetValueError)

        assert isinstance(val_error, WgetValueError)
        assert not isinstance(val_error, WgetLibraryError)

    def test_exceptions_in_try_except_block(self):
        """Deve funcionar corretamente em blocos try/except."""

        def function_that_may_fail(error_type):
            if error_type == "library":
                raise WgetLibraryError("DRE", "Library error")
            elif error_type == "value":
                raise WgetValueError("invalid")
            return "success"

        # Testar sucesso
        result = function_that_may_fail("success")
        assert result == "success"

        # Testar tratamento de erro
        with pytest.raises(WgetLibraryError):
            function_that_may_fail("library")

        with pytest.raises(WgetValueError):
            function_that_may_fail("value")

    def test_nested_exception_handling(self):
        """Deve lidar com exceções aninhadas."""
        try:
            try:
                raise WgetValueError("invalid_url")
            except WgetValueError:
                raise WgetLibraryError("DRE", "Failed to download")
        except WgetLibraryError:
            pass  # Deve ser capturada
        else:
            pytest.fail("Exception should have been raised")
