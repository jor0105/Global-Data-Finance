import pytest

from src.macro_exceptions.exception_network_errors import (
    DiskFullError,
    FileNotFoundError,
    NetworkError,
    PermissionError,
    TimeoutError,
)


class TestNetworkError:
    def test_network_error_with_doc_name_only(self):
        """Deve criar exceção com apenas o nome do documento."""
        doc_name = "DRE"
        error = NetworkError(doc_name)

        assert isinstance(error, Exception)
        assert "Network error" in str(error)
        assert doc_name in str(error)

    def test_network_error_with_message(self):
        """Deve criar exceção com nome do documento e mensagem."""
        doc_name = "BPARMS"
        message = "Connection refused"
        error = NetworkError(doc_name, message)

        assert doc_name in str(error)
        assert message in str(error)

    def test_network_error_with_none_message(self):
        """Deve aceitar None como mensagem."""
        error = NetworkError("DRE", None)
        assert "DRE" in str(error)

    def test_network_error_is_exception(self):
        """Deve herdar de Exception."""
        error = NetworkError("DRE")
        assert isinstance(error, Exception)

    def test_network_error_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(NetworkError):
            raise NetworkError("DRE", "Connection failed")

    def test_network_error_with_special_characters(self):
        """Deve lidar com caracteres especiais no nome do documento."""
        error = NetworkError("DRE_2023", "Erro na conexão: timeout")
        assert "DRE_2023" in str(error)
        assert "Erro" in str(error)

    def test_network_error_with_empty_doc_name(self):
        """Deve lidar com nome de documento vazio."""
        error = NetworkError("", "Connection error")
        assert isinstance(error, NetworkError)

    def test_network_error_message_format(self):
        """Deve validar o formato da mensagem de erro."""
        error = NetworkError("DRE", "Failed to download")
        error_str = str(error)
        assert "Network error" in error_str
        assert "downloading" in error_str or "DRE" in error_str


class TestTimeoutError:
    def test_timeout_error_with_doc_name_only(self):
        """Deve criar exceção com apenas o nome do documento."""
        doc_name = "BPARMS"
        error = TimeoutError(doc_name)

        assert isinstance(error, Exception)
        assert "Timeout" in str(error)
        assert doc_name in str(error)

    def test_timeout_error_with_timeout_value(self):
        """Deve criar exceção com nome e valor de timeout."""
        doc_name = "DMPL"
        timeout = 30.5
        error = TimeoutError(doc_name, timeout)

        assert doc_name in str(error)
        assert "30.5" in str(error) or "30" in str(error)

    def test_timeout_error_with_none_timeout(self):
        """Deve aceitar None como timeout."""
        error = TimeoutError("DRE", None)
        assert "DRE" in str(error)

    def test_timeout_error_is_exception(self):
        """Deve herdar de Exception."""
        error = TimeoutError("DRE")
        assert isinstance(error, Exception)

    def test_timeout_error_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(TimeoutError):
            raise TimeoutError("BPARMS", 60.0)

    def test_timeout_error_with_zero_timeout(self):
        """Deve aceitar valor zero de timeout."""
        error = TimeoutError("DRE", 0)
        assert "DRE" in str(error)

    def test_timeout_error_with_large_timeout_value(self):
        """Deve aceitar valores grandes de timeout."""
        error = TimeoutError("DRE", 3600.0)
        assert "DRE" in str(error)

    def test_timeout_error_message_format(self):
        """Deve validar o formato da mensagem de erro."""
        error = TimeoutError("DRE", 30)
        error_str = str(error)
        assert "Timeout" in error_str
        assert "DRE" in error_str


class TestPermissionError:
    def test_permission_error_with_valid_path(self):
        """Deve criar exceção com caminho válido."""
        path = "/path/to/save/directory"
        error = PermissionError(path)

        assert isinstance(error, Exception)
        assert "Permission denied" in str(error)
        assert path in str(error)

    def test_permission_error_with_relative_path(self):
        """Deve aceitar caminho relativo."""
        path = "data/downloads"
        error = PermissionError(path)
        assert path in str(error)

    def test_permission_error_with_file_path(self):
        """Deve aceitar caminho de arquivo."""
        path = "/home/user/file.zip"
        error = PermissionError(path)
        assert path in str(error)

    def test_permission_error_is_exception(self):
        """Deve herdar de Exception."""
        error = PermissionError("/path")
        assert isinstance(error, Exception)

    def test_permission_error_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(PermissionError):
            raise PermissionError("/home/user/protected")

    def test_permission_error_with_empty_path(self):
        """Deve lidar com caminho vazio."""
        error = PermissionError("")
        assert isinstance(error, PermissionError)

    def test_permission_error_with_special_characters(self):
        """Deve lidar com caracteres especiais no caminho."""
        path = "/home/user/Programação/dados_ação"
        error = PermissionError(path)
        assert path in str(error)

    def test_permission_error_message_format(self):
        """Deve validar o formato da mensagem de erro."""
        path = "/path/to/save"
        error = PermissionError(path)
        error_str = str(error)
        assert "Permission" in error_str
        assert path in error_str


class TestFileNotFoundError:
    def test_file_not_found_error_with_valid_path(self):
        """Deve criar exceção com caminho válido."""
        path = "/path/to/nonexistent/directory"
        error = FileNotFoundError(path)

        assert isinstance(error, Exception)
        assert "not found" in str(error)
        assert path in str(error)

    def test_file_not_found_error_with_relative_path(self):
        """Deve aceitar caminho relativo."""
        path = "data/downloads/missing.zip"
        error = FileNotFoundError(path)
        assert path in str(error)

    def test_file_not_found_error_is_exception(self):
        """Deve herdar de Exception."""
        error = FileNotFoundError("/path")
        assert isinstance(error, Exception)

    def test_file_not_found_error_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(FileNotFoundError):
            raise FileNotFoundError("/home/user/missing_file.zip")

    def test_file_not_found_error_with_special_characters(self):
        """Deve lidar com caracteres especiais no caminho."""
        path = "/home/user/arquivo_dados_ação.zip"
        error = FileNotFoundError(path)
        assert path in str(error)

    def test_file_not_found_error_message_format(self):
        """Deve validar o formato da mensagem de erro."""
        path = "/path/to/missing"
        error = FileNotFoundError(path)
        error_str = str(error)
        assert "not found" in error_str
        assert path in error_str


class TestDiskFullError:
    def test_disk_full_error_with_valid_path(self):
        """Deve criar exceção com caminho válido."""
        path = "/path/to/save/directory"
        error = DiskFullError(path)

        assert isinstance(error, Exception)
        assert "Insufficient disk space" in str(error)
        assert path in str(error)

    def test_disk_full_error_with_relative_path(self):
        """Deve aceitar caminho relativo."""
        path = "data/downloads"
        error = DiskFullError(path)
        assert path in str(error)

    def test_disk_full_error_is_exception(self):
        """Deve herdar de Exception."""
        error = DiskFullError("/path")
        assert isinstance(error, Exception)

    def test_disk_full_error_can_be_raised_and_caught(self):
        """Deve poder ser levantada e capturada."""
        with pytest.raises(DiskFullError):
            raise DiskFullError("/home/user/full_disk")

    def test_disk_full_error_with_special_characters(self):
        """Deve lidar com caracteres especiais no caminho."""
        path = "/mnt/armazenamento_dados"
        error = DiskFullError(path)
        assert path in str(error)

    def test_disk_full_error_message_format(self):
        """Deve validar o formato da mensagem de erro."""
        path = "/path/to/save"
        error = DiskFullError(path)
        error_str = str(error)
        assert "disk space" in error_str or "Insufficient" in error_str
        assert path in error_str


class TestMacroExceptionsIntegration:
    def test_all_exceptions_inherit_from_exception(self):
        """Todas as exceções devem herdar de Exception."""
        exceptions = [
            NetworkError("DRE"),
            TimeoutError("BPARMS"),
            PermissionError("/path"),
            FileNotFoundError("/path"),
            DiskFullError("/path"),
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_catch_network_error_specifically(self):
        """Deve capturar NetworkError especificamente."""
        with pytest.raises(NetworkError):
            raise NetworkError("DRE", "Connection failed")

    def test_catch_timeout_error_specifically(self):
        """Deve capturar TimeoutError especificamente."""
        with pytest.raises(TimeoutError):
            raise TimeoutError("BPARMS", 30.0)

    def test_catch_permission_error_specifically(self):
        """Deve capturar PermissionError especificamente."""
        with pytest.raises(PermissionError):
            raise PermissionError("/path/protected")

    def test_catch_file_not_found_error_specifically(self):
        """Deve capturar FileNotFoundError especificamente."""
        with pytest.raises(FileNotFoundError):
            raise FileNotFoundError("/path/missing")

    def test_catch_disk_full_error_specifically(self):
        """Deve capturar DiskFullError especificamente."""
        with pytest.raises(DiskFullError):
            raise DiskFullError("/path/full")

    def test_catch_all_as_generic_exception(self):
        """Deve capturar todas as exceções como Exception genérica."""
        errors = [
            NetworkError("DRE", "error"),
            TimeoutError("BPARMS", 30),
            PermissionError("/path"),
            FileNotFoundError("/path"),
            DiskFullError("/path"),
        ]

        for error in errors:
            with pytest.raises(Exception):
                raise error

    def test_exception_string_representations(self):
        """Deve ter representações de string significativas."""
        exceptions = {
            "NetworkError": NetworkError("DRE", "Connection failed"),
            "TimeoutError": TimeoutError("BPARMS", 30.0),
            "PermissionError": PermissionError("/path"),
            "FileNotFoundError": FileNotFoundError("/path"),
            "DiskFullError": DiskFullError("/path"),
        }

        for name, exc in exceptions.items():
            exc_str = str(exc)
            assert len(exc_str) > 0
            assert isinstance(exc_str, str)

    def test_multiple_exception_handling_workflow(self):
        """Deve simular um fluxo de tratamento de múltiplas exceções."""
        errors = []

        def simulate_download(doc_name, should_fail, error_type):
            """Simula o download de um documento."""
            if should_fail:
                if error_type == "network":
                    raise NetworkError(doc_name, "Failed")
                elif error_type == "timeout":
                    raise TimeoutError(doc_name, 30)
                elif error_type == "permission":
                    raise PermissionError("/path")
                elif error_type == "disk":
                    raise DiskFullError("/path")

        # Simular downloads
        download_specs = [
            ("DRE", False, None),
            ("BPARMS", True, "network"),
            ("DMPL", True, "timeout"),
            ("IROT", True, "permission"),
        ]

        for doc_name, should_fail, error_type in download_specs:
            try:
                simulate_download(doc_name, should_fail, error_type)
            except (NetworkError, TimeoutError, PermissionError, DiskFullError) as e:
                errors.append(str(e))

        assert len(errors) == 3

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
            error = NetworkError("DRE", msg)
            assert msg in str(error) or "DRE" in str(error)
