import pytest

from src.brazil.cvm.fundamental_stocks_data import WgetLibraryError, WgetValueError


@pytest.mark.unit
class TestWgetLibraryError:
    def test_with_doc_name_only(self):
        doc_name = "DRE"
        exception = WgetLibraryError(doc_name)
        assert isinstance(exception, Exception)
        assert "Wget library error" in str(exception)
        assert doc_name in str(exception)

    def test_with_doc_name_and_message(self):
        doc_name = "BPARMS"
        message = "Internal wget error"
        exception = WgetLibraryError(doc_name, message)
        exc_str = str(exception)
        assert doc_name in exc_str
        assert message in exc_str

    def test_with_none_message(self):
        exception = WgetLibraryError("DRE", None)
        assert "DRE" in str(exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(WgetLibraryError):
            raise WgetLibraryError("DRE", "Internal error")

    def test_with_empty_doc_name(self):
        exception = WgetLibraryError("", "Error message")
        assert isinstance(exception, WgetLibraryError)

    def test_with_various_error_messages(self):
        messages = [
            "Connection timeout",
            "SSL verification failed",
            "URL not found",
            "Permission denied",
            None,
        ]
        for msg in messages:
            exception = WgetLibraryError("DRE", msg)
            assert isinstance(exception, WgetLibraryError)

    def test_with_special_characters_in_message(self):
        doc_name = "DRE_2023"
        message = "Erro: conexão falhou [SSL: CERTIFICATE_VERIFY_FAILED]"
        exception = WgetLibraryError(doc_name, message)
        assert doc_name in str(exception)
        assert "Erro" in str(exception)

    def test_with_unicode_characters(self):
        message = "Erro de conexão: çãõé"
        exception = WgetLibraryError("DRE", message)
        assert "Erro" in str(exception)

    def test_message_always_contains_wget_prefix(self):
        cases = [("DRE", None), ("ITR", "msg"), ("", "error")]
        for doc, msg in cases:
            exception = WgetLibraryError(doc, msg)
            assert "Wget library error" in str(exception)

    def test_with_numeric_doc_names(self):
        exception = WgetLibraryError("DRE_2023_Q1")
        assert "DRE_2023_Q1" in str(exception)

    def test_with_long_message(self):
        long_message = "Error: " * 100
        exception = WgetLibraryError("DRE", long_message)
        assert isinstance(exception, WgetLibraryError)


@pytest.mark.unit
class TestWgetValueError:
    def test_with_string_value(self):
        value = "invalid_url"
        exception = WgetValueError(value)
        assert isinstance(exception, Exception)
        assert "Value error" in str(exception)
        assert value in str(exception)

    def test_with_integer_value(self):
        value = 12345
        exception = WgetValueError(value)
        assert str(value) in str(exception)

    def test_with_none_value(self):
        exception = WgetValueError(None)
        assert isinstance(exception, WgetValueError)

    def test_with_empty_string(self):
        exception = WgetValueError("")
        assert isinstance(exception, WgetValueError)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(WgetValueError):
            raise WgetValueError("invalid_url")

    def test_with_list_value(self):
        value = ["url1", "url2"]
        exception = WgetValueError(value)
        assert isinstance(exception, WgetValueError)

    def test_with_dict_value(self):
        value = {"key": "value"}
        exception = WgetValueError(value)
        assert isinstance(exception, WgetValueError)

    def test_with_float_value(self):
        value = 3.14
        exception = WgetValueError(value)
        assert isinstance(exception, WgetValueError)

    def test_with_boolean_value(self):
        exc_true = WgetValueError(True)
        exc_false = WgetValueError(False)
        assert isinstance(exc_true, WgetValueError)
        assert isinstance(exc_false, WgetValueError)

    def test_message_always_contains_value_error_prefix(self):
        values = ["string", 123, None, [], {}, 3.14]
        for value in values:
            exception = WgetValueError(value)
            assert "Value error" in str(exception)

    def test_with_special_characters(self):
        value = "invalid_url_with_çãõé_chars"
        exception = WgetValueError(value)
        assert isinstance(exception, WgetValueError)

    def test_with_very_long_value(self):
        long_value = "url" * 1000
        exception = WgetValueError(long_value)
        assert isinstance(exception, WgetValueError)


@pytest.mark.unit
class TestInfrastructureExceptionsIntegration:
    def test_both_exceptions_inherit_from_exception(self):
        exceptions = [WgetLibraryError("DRE"), WgetValueError("value")]
        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_catch_wget_library_error_specifically(self):
        with pytest.raises(WgetLibraryError):
            raise WgetLibraryError("DRE", "Internal error")

    def test_catch_wget_value_error_specifically(self):
        with pytest.raises(WgetValueError):
            raise WgetValueError("invalid_value")

    def test_catch_both_as_generic_exception(self):
        errors = [WgetLibraryError("DRE", "error"), WgetValueError("value")]
        for error in errors:
            with pytest.raises(Exception):
                raise error

    def test_all_exceptions_have_non_empty_messages(self):
        exceptions = [
            WgetLibraryError("DRE", "Internal error"),
            WgetValueError("invalid_url"),
        ]
        for exc in exceptions:
            exc_str = str(exc)
            assert len(exc_str) > 0, f"{type(exc).__name__} has empty message"
            assert isinstance(
                exc_str, str
            ), f"{type(exc).__name__} message is not string"

    def test_multiple_exception_handling_workflow(self):
        errors = []

        def simulate_download(should_fail, error_type):
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
        lib_error = WgetLibraryError("DRE", "message")
        val_error = WgetValueError("value")

        assert isinstance(lib_error, WgetLibraryError)
        assert not isinstance(lib_error, WgetValueError)

        assert isinstance(val_error, WgetValueError)
        assert not isinstance(val_error, WgetLibraryError)

    def test_exceptions_in_try_except_block(self):
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
        try:
            try:
                raise WgetValueError("invalid_url")
            except WgetValueError:
                raise WgetLibraryError("DRE", "Failed to download")
        except WgetLibraryError:
            pass
        else:
            pytest.fail("Exception should have been raised")

    def test_download_workflow_simulation(self):
        def download_document(doc_name, url):
            if not isinstance(url, str) or url == "":
                raise WgetValueError(url)
            if "failed" in url:
                raise WgetLibraryError(doc_name, "Connection failed")
            return f"Downloaded {doc_name}"

        # Teste válido
        result = download_document("DRE", "https://example.com/dre")
        assert "Downloaded" in result

        # Teste com valor inválido
        with pytest.raises(WgetValueError):
            download_document("DRE", 123)

        # Teste com erro de biblioteca
        with pytest.raises(WgetLibraryError):
            download_document("DRE", "https://failed.com/dre")
