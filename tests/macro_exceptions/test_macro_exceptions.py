import pytest

from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    DownloadExtractionError,
    ExtractionError,
    InvalidDestinationPathError,
    NetworkError,
    PathIsNotDirectoryError,
    PathPermissionError,
    TimeoutError,
)


class TestInvalidDestinationPathError:
    def test_invalid_destination_path_error_with_reason(self):
        reason = "Path does not exist"
        error = InvalidDestinationPathError(reason)

        assert isinstance(error, ValueError)
        assert "Invalid destination path" in str(error)
        assert reason in str(error)

    def test_invalid_destination_path_error_with_detailed_reason(self):
        reason = "Permission denied for /protected/path"
        error = InvalidDestinationPathError(reason)

        assert reason in str(error)
        assert isinstance(error, ValueError)

    def test_invalid_destination_path_error_can_be_raised(self):
        with pytest.raises(InvalidDestinationPathError):
            raise InvalidDestinationPathError("Invalid path")

    def test_invalid_destination_path_error_with_empty_reason(self):
        error = InvalidDestinationPathError("")
        assert isinstance(error, InvalidDestinationPathError)
        assert isinstance(error, ValueError)

    def test_invalid_destination_path_error_with_special_characters(self):
        reason = "Path has special chars: /tmp/açúcar/café"
        error = InvalidDestinationPathError(reason)
        assert reason in str(error)

    def test_invalid_destination_path_error_inheritance(self):
        error = InvalidDestinationPathError("test")
        assert isinstance(error, ValueError)
        assert isinstance(error, Exception)


class TestPathIsNotDirectoryError:
    def test_path_is_not_directory_error_with_file_path(self):
        path = "/home/user/file.txt"
        error = PathIsNotDirectoryError(path)

        assert isinstance(error, ValueError)
        assert path in str(error)
        assert "is a file" in str(error)
        assert "must be a directory" in str(error)

    def test_path_is_not_directory_error_with_relative_path(self):
        path = "data/file.csv"
        error = PathIsNotDirectoryError(path)

        assert path in str(error)
        assert isinstance(error, ValueError)

    def test_path_is_not_directory_error_can_be_raised(self):
        with pytest.raises(PathIsNotDirectoryError):
            raise PathIsNotDirectoryError("/tmp/file.zip")

    def test_path_is_not_directory_error_inheritance(self):
        error = PathIsNotDirectoryError("/path")
        assert isinstance(error, ValueError)
        assert isinstance(error, Exception)

    def test_path_is_not_directory_error_message_format(self):
        path = "/home/user/document.pdf"
        error = PathIsNotDirectoryError(path)
        error_str = str(error)

        assert "destination path" in error_str
        assert "directory" in error_str
        assert path in error_str


class TestPathPermissionError:
    def test_path_permission_error_with_valid_path(self):
        path = "/path/to/protected/directory"
        error = PathPermissionError(path)

        assert isinstance(error, OSError)
        assert "Permission denied" in str(error)
        assert path in str(error)
        assert "No write permission" in str(error)

    def test_path_permission_error_with_relative_path(self):
        path = "data/downloads"
        error = PathPermissionError(path)
        assert path in str(error)

    def test_path_permission_error_with_file_path(self):
        path = "/home/user/file.zip"
        error = PathPermissionError(path)
        assert path in str(error)

    def test_path_permission_error_is_os_error(self):
        error = PathPermissionError("/path")
        assert isinstance(error, OSError)
        assert isinstance(error, Exception)

    def test_path_permission_error_can_be_raised(self):
        with pytest.raises(PathPermissionError):
            raise PathPermissionError("/home/user/protected")

    def test_path_permission_error_with_empty_path(self):
        error = PathPermissionError("")
        assert isinstance(error, PathPermissionError)

    def test_path_permission_error_with_special_characters(self):
        path = "/home/user/Programação/dados_ação"
        error = PathPermissionError(path)
        assert path in str(error)

    def test_path_permission_error_message_format(self):
        path = "/path/to/save"
        error = PathPermissionError(path)
        error_str = str(error)
        assert "Permission" in error_str
        assert "write" in error_str
        assert path in error_str

    def test_path_permission_error_inheritance(self):
        error = PathPermissionError("/path")
        assert isinstance(error, OSError)
        assert isinstance(error, Exception)


class TestExtractionError:
    def test_extraction_error_with_path_and_message(self):
        path = "/tmp/data.zip"
        message = "Invalid ZIP format"
        error = ExtractionError(path, message)

        assert isinstance(error, Exception)
        assert path in str(error)
        assert message in str(error)
        assert "extraction error occurred" in str(error)

    def test_extraction_error_with_detailed_message(self):
        path = "/home/user/archive.zip"
        message = "CSV parsing failed at line 1000"
        error = ExtractionError(path, message)

        assert path in str(error)
        assert message in str(error)

    def test_extraction_error_can_be_raised(self):
        with pytest.raises(ExtractionError):
            raise ExtractionError("/tmp/file.zip", "Extraction failed")

    def test_extraction_error_with_empty_message(self):
        error = ExtractionError("/path", "")
        assert "/path" in str(error)

    def test_extraction_error_inheritance(self):
        error = ExtractionError("/path", "error")
        assert isinstance(error, Exception)

    def test_extraction_error_with_special_characters_in_path(self):
        path = "/tmp/açúcar_café.zip"
        message = "Erro de extração"
        error = ExtractionError(path, message)
        assert path in str(error)
        assert message in str(error)


class TestCorruptedZipError:
    def test_corrupted_zip_error_with_path_and_message(self):
        zip_path = "/tmp/corrupted.zip"
        message = "Bad magic number"
        error = CorruptedZipError(zip_path, message)

        assert isinstance(error, ExtractionError)
        assert zip_path in str(error)
        assert "Corrupted ZIP" in str(error)
        assert message in str(error)

    def test_corrupted_zip_error_with_detailed_message(self):
        zip_path = "/data/invalid.zip"
        message = "CRC check failed"
        error = CorruptedZipError(zip_path, message)

        assert zip_path in str(error)
        assert message in str(error)
        assert "Corrupted ZIP" in str(error)

    def test_corrupted_zip_error_can_be_raised(self):
        with pytest.raises(CorruptedZipError):
            raise CorruptedZipError("/tmp/bad.zip", "Invalid header")

    def test_corrupted_zip_error_inheritance(self):
        error = CorruptedZipError("/path", "error")
        assert isinstance(error, ExtractionError)
        assert isinstance(error, Exception)

    def test_corrupted_zip_error_as_extraction_error(self):
        with pytest.raises(ExtractionError):
            raise CorruptedZipError("/tmp/file.zip", "Corrupted")

    def test_corrupted_zip_error_message_format(self):
        zip_path = "/tmp/test.zip"
        message = "Cannot read ZIP"
        error = CorruptedZipError(zip_path, message)
        error_str = str(error)

        assert "extraction error occurred" in error_str
        assert "Corrupted ZIP" in error_str
        assert zip_path in error_str
        assert message in error_str


class TestDownloadExtractionError:
    def test_download_extraction_error_with_all_attributes(self):
        doc_name = "DRE"
        year = "2023"
        zip_path = "/tmp/dre_2023.zip"
        message = "Network timeout during download"
        error = DownloadExtractionError(doc_name, year, zip_path, message)

        assert isinstance(error, Exception)
        assert error.doc_name == doc_name
        assert error.year == year
        assert error.zip_path == zip_path
        assert error.message == message

    def test_download_extraction_error_message_format(self):
        doc_name = "BPARMS"
        year = "2024"
        zip_path = "/data/bparms_2024.zip"
        message = "Download failed"
        error = DownloadExtractionError(doc_name, year, zip_path, message)

        error_str = str(error)
        assert doc_name in error_str
        assert year in error_str
        assert zip_path in error_str
        assert message in error_str
        assert "download/extraction failed" in error_str

    def test_download_extraction_error_can_be_raised(self):
        with pytest.raises(DownloadExtractionError):
            raise DownloadExtractionError("DRE", "2023", "/tmp/file.zip", "Error")

    def test_download_extraction_error_attributes_accessible(self):
        doc_name = "ITR"
        year = "2022"
        zip_path = "/tmp/itr_2022.zip"
        message = "Extraction error: corrupted ZIP"

        error = DownloadExtractionError(doc_name, year, zip_path, message)

        assert error.doc_name == doc_name
        assert error.year == year
        assert error.zip_path == zip_path
        assert error.message == message

    def test_download_extraction_error_with_empty_strings(self):
        error = DownloadExtractionError("", "", "", "")
        assert error.doc_name == ""
        assert error.year == ""
        assert error.zip_path == ""
        assert error.message == ""

    def test_download_extraction_error_with_special_characters(self):
        doc_name = "DRE_Consolidado"
        year = "2023"
        zip_path = "/tmp/relatórios/dre_2023.zip"
        message = "Erro na extração: arquivo corrompido"

        error = DownloadExtractionError(doc_name, year, zip_path, message)

        assert doc_name in str(error)
        assert year in str(error)
        assert message in str(error)

    def test_download_extraction_error_inheritance(self):
        error = DownloadExtractionError("DRE", "2023", "/tmp/file.zip", "Error")
        assert isinstance(error, Exception)


class TestDiskFullError:
    def test_disk_full_error_with_valid_path(self):
        path = "/path/to/save/directory"
        error = DiskFullError(path)

        assert isinstance(error, OSError)
        assert "not enough disk space" in str(error)
        assert path in str(error)

    def test_disk_full_error_with_relative_path(self):
        path = "data/downloads"
        error = DiskFullError(path)
        assert path in str(error)

    def test_disk_full_error_is_os_error(self):
        error = DiskFullError("/path")
        assert isinstance(error, OSError)
        assert isinstance(error, Exception)

    def test_disk_full_error_can_be_raised(self):
        with pytest.raises(DiskFullError):
            raise DiskFullError("/home/user/full_disk")

    def test_disk_full_error_with_special_characters(self):
        path = "/mnt/armazenamento_dados"
        error = DiskFullError(path)
        assert path in str(error)

    def test_disk_full_error_message_format(self):
        path = "/path/to/save"
        error = DiskFullError(path)
        error_str = str(error)
        assert "disk space" in error_str or "Insufficient" in error_str
        assert path in error_str

    def test_disk_full_error_inheritance(self):
        error = DiskFullError("/path")
        assert isinstance(error, OSError)
        assert isinstance(error, Exception)


class TestNetworkError:
    def test_network_error_with_doc_name_only(self):
        doc_name = "DRE"
        error = NetworkError(doc_name)

        assert isinstance(error, Exception)
        assert "network error occurred" in str(error)
        assert doc_name in str(error)

    def test_network_error_with_message(self):
        doc_name = "BPARMS"
        message = "Connection refused"
        error = NetworkError(doc_name, message)

        assert doc_name in str(error)
        assert message in str(error)

    def test_network_error_with_none_message(self):
        error = NetworkError("DRE", None)
        assert "DRE" in str(error)

    def test_network_error_is_exception(self):
        error = NetworkError("DRE")
        assert isinstance(error, Exception)

    def test_network_error_can_be_raised_and_caught(self):
        with pytest.raises(NetworkError):
            raise NetworkError("DRE", "Connection failed")

    def test_network_error_with_special_characters(self):
        error = NetworkError("DRE_2023", "Erro na conexão: timeout")
        assert "DRE_2023" in str(error)
        assert "Erro" in str(error)

    def test_network_error_with_empty_doc_name(self):
        error = NetworkError("", "Connection error")
        assert isinstance(error, NetworkError)

    def test_network_error_message_format(self):
        error = NetworkError("DRE", "Failed to download")
        error_str = str(error)
        assert "network error occurred" in error_str
        assert "downloading" in error_str or "DRE" in error_str

    def test_network_error_inheritance(self):
        error = NetworkError("DRE")
        assert isinstance(error, Exception)


class TestTimeoutError:
    def test_timeout_error_with_doc_name_only(self):
        doc_name = "BPARMS"
        error = TimeoutError(doc_name)

        assert isinstance(error, Exception)
        assert "timeout occurred" in str(error)
        assert doc_name in str(error)

    def test_timeout_error_with_timeout_value(self):
        doc_name = "DMPL"
        timeout = 30.5
        error = TimeoutError(doc_name, timeout)

        assert doc_name in str(error)
        assert "30.5" in str(error) or "30" in str(error)

    def test_timeout_error_with_none_timeout(self):
        error = TimeoutError("DRE", None)
        assert "DRE" in str(error)

    def test_timeout_error_is_exception(self):
        error = TimeoutError("DRE")
        assert isinstance(error, Exception)

    def test_timeout_error_can_be_raised_and_caught(self):
        with pytest.raises(TimeoutError):
            raise TimeoutError("BPARMS", 60.0)

    def test_timeout_error_with_zero_timeout(self):
        error = TimeoutError("DRE", 0)
        assert "DRE" in str(error)

    def test_timeout_error_with_large_timeout_value(self):
        error = TimeoutError("DRE", 3600.0)
        assert "DRE" in str(error)

    def test_timeout_error_message_format(self):
        error = TimeoutError("DRE", 30)
        error_str = str(error)
        assert "timeout occurred" in error_str
        assert "DRE" in error_str

    def test_timeout_error_inheritance(self):
        error = TimeoutError("DRE")
        assert isinstance(error, Exception)


class TestMacroExceptionsIntegration:
    def test_all_exceptions_inherit_from_exception(self):
        exceptions = [
            NetworkError("DRE"),
            TimeoutError("BPARMS"),
            PathPermissionError("/path"),
            DiskFullError("/path"),
            InvalidDestinationPathError("reason"),
            PathIsNotDirectoryError("/file.txt"),
            ExtractionError("/path", "error"),
            CorruptedZipError("/path", "error"),
            DownloadExtractionError("DRE", "2023", "/path", "error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_catch_network_error_specifically(self):
        with pytest.raises(NetworkError):
            raise NetworkError("DRE", "Connection failed")

    def test_catch_timeout_error_specifically(self):
        with pytest.raises(TimeoutError):
            raise TimeoutError("BPARMS", 30.0)

    def test_catch_path_permission_error_specifically(self):
        with pytest.raises(PathPermissionError):
            raise PathPermissionError("/path/protected")

    def test_catch_disk_full_error_specifically(self):
        with pytest.raises(DiskFullError):
            raise DiskFullError("/path/full")

    def test_catch_invalid_destination_path_error_specifically(self):
        with pytest.raises(InvalidDestinationPathError):
            raise InvalidDestinationPathError("Invalid path")

    def test_catch_path_is_not_directory_error_specifically(self):
        with pytest.raises(PathIsNotDirectoryError):
            raise PathIsNotDirectoryError("/file.txt")

    def test_catch_extraction_error_specifically(self):
        with pytest.raises(ExtractionError):
            raise ExtractionError("/path", "error")

    def test_catch_corrupted_zip_error_as_extraction_error(self):
        with pytest.raises(ExtractionError):
            raise CorruptedZipError("/path", "corrupted")

    def test_catch_corrupted_zip_error_specifically(self):
        with pytest.raises(CorruptedZipError):
            raise CorruptedZipError("/path", "corrupted")

    def test_catch_download_extraction_error_specifically(self):
        with pytest.raises(DownloadExtractionError):
            raise DownloadExtractionError("DRE", "2023", "/path", "error")

    def test_catch_all_as_generic_exception(self):
        errors = [
            NetworkError("DRE", "error"),
            TimeoutError("BPARMS", 30),
            PathPermissionError("/path"),
            DiskFullError("/path"),
            InvalidDestinationPathError("reason"),
            PathIsNotDirectoryError("/file.txt"),
            ExtractionError("/path", "error"),
            CorruptedZipError("/path", "error"),
            DownloadExtractionError("DRE", "2023", "/path", "error"),
        ]

        for error in errors:
            with pytest.raises(Exception):
                raise error

    def test_exception_string_representations(self):
        exceptions = {
            "NetworkError": NetworkError("DRE", "Connection failed"),
            "TimeoutError": TimeoutError("BPARMS", 30.0),
            "PathPermissionError": PathPermissionError("/path"),
            "DiskFullError": DiskFullError("/path"),
            "InvalidDestinationPathError": InvalidDestinationPathError("reason"),
            "PathIsNotDirectoryError": PathIsNotDirectoryError("/file.txt"),
            "ExtractionError": ExtractionError("/path", "error"),
            "CorruptedZipError": CorruptedZipError("/path", "error"),
            "DownloadExtractionError": DownloadExtractionError(
                "DRE", "2023", "/path", "error"
            ),
        }

        for name, exc in exceptions.items():
            exc_str = str(exc)
            assert len(exc_str) > 0
            assert isinstance(exc_str, str)

    def test_os_error_inheritance(self):
        os_errors = [
            PathPermissionError("/path"),
            DiskFullError("/path"),
        ]

        for error in os_errors:
            assert isinstance(error, OSError)
            assert isinstance(error, Exception)

    def test_value_error_inheritance(self):
        value_errors = [
            InvalidDestinationPathError("reason"),
            PathIsNotDirectoryError("/file.txt"),
        ]

        for error in value_errors:
            assert isinstance(error, ValueError)
            assert isinstance(error, Exception)

    def test_extraction_error_hierarchy(self):
        base_error = ExtractionError("/path", "error")
        corrupted_error = CorruptedZipError("/path", "corrupted")

        assert isinstance(base_error, Exception)
        assert isinstance(corrupted_error, ExtractionError)
        assert isinstance(corrupted_error, Exception)

    def test_multiple_exception_handling_workflow(self):
        errors = []

        def simulate_download(doc_name, should_fail, error_type):
            if should_fail:
                if error_type == "network":
                    raise NetworkError(doc_name, "Failed")
                elif error_type == "timeout":
                    raise TimeoutError(doc_name, 30)
                elif error_type == "permission":
                    raise PathPermissionError("/path")
                elif error_type == "disk":
                    raise DiskFullError("/path")
                elif error_type == "extraction":
                    raise ExtractionError("/path", "Failed to extract")
                elif error_type == "corrupted":
                    raise CorruptedZipError("/path", "Bad ZIP")

        # Simular downloads
        download_specs = [
            ("DRE", False, None),
            ("BPARMS", True, "network"),
            ("DMPL", True, "timeout"),
            ("IROT", True, "permission"),
            ("ITR", True, "disk"),
            ("DFC", True, "extraction"),
            ("DVA", True, "corrupted"),
        ]

        for doc_name, should_fail, error_type in download_specs:
            try:
                simulate_download(doc_name, should_fail, error_type)
            except (
                NetworkError,
                TimeoutError,
                PathPermissionError,
                DiskFullError,
                ExtractionError,
            ) as e:
                errors.append(str(e))

        assert len(errors) == 6

    def test_exception_with_different_message_formats(self):
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

    def test_exception_attributes_preserved(self):
        error = DownloadExtractionError("DRE", "2023", "/tmp/file.zip", "Test error")

        assert hasattr(error, "doc_name")
        assert hasattr(error, "year")
        assert hasattr(error, "zip_path")
        assert hasattr(error, "message")

        assert error.doc_name == "DRE"
        assert error.year == "2023"
        assert error.zip_path == "/tmp/file.zip"
        assert error.message == "Test error"

    def test_nested_exception_handling(self):
        # CorruptedZipError is-a ExtractionError
        try:
            raise CorruptedZipError("/path", "Bad ZIP")
        except ExtractionError as e:
            assert isinstance(e, CorruptedZipError)
            assert "Corrupted ZIP" in str(e)

    def test_exception_creation_with_none_optional_values(self):
        network_error = NetworkError("DRE", None)
        timeout_error = TimeoutError("DRE", None)

        assert "DRE" in str(network_error)
        assert "DRE" in str(timeout_error)
