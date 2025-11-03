import zipfile
from unittest.mock import patch

import pytest

from src.brazil.cvm.fundamental_stocks_data import ParquetExtractor
from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
)


@pytest.mark.unit
class TestParquetExtractorInitialization:
    def test_init_with_default_chunk_size(self):
        extractor = ParquetExtractor()
        assert extractor.chunk_size == 50000

    def test_init_with_custom_chunk_size(self):
        extractor = ParquetExtractor(chunk_size=100000)
        assert extractor.chunk_size == 100000

    def test_init_with_small_chunk_size(self):
        extractor = ParquetExtractor(chunk_size=1000)
        assert extractor.chunk_size == 1000

    def test_init_with_very_large_chunk_size(self):
        extractor = ParquetExtractor(chunk_size=1000000)
        assert extractor.chunk_size == 1000000


@pytest.mark.unit
class TestParquetExtractorSuccessfulExtraction:
    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_delegates_to_core_extractor(self, mock_extract):
        extractor = ParquetExtractor(chunk_size=50000)
        source_path = "/tmp/data.zip"
        dest_dir = "/tmp/output"

        extractor.extract(source_path, dest_dir)

        mock_extract.assert_called_once_with(50000, source_path, dest_dir)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_with_different_chunk_sizes(self, mock_extract):
        chunk_sizes = [1000, 10000, 50000, 100000]

        for chunk_size in chunk_sizes:
            mock_extract.reset_mock()
            extractor = ParquetExtractor(chunk_size=chunk_size)
            extractor.extract("/tmp/data.zip", "/tmp/output")

            mock_extract.assert_called_once_with(
                chunk_size, "/tmp/data.zip", "/tmp/output"
            )

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_with_special_characters_in_paths(self, mock_extract):
        extractor = ParquetExtractor()
        source_path = "/tmp/açúcar_café_2023.zip"
        dest_dir = "/tmp/saída/dados"

        extractor.extract(source_path, dest_dir)

        mock_extract.assert_called_once_with(50000, source_path, dest_dir)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_with_relative_paths(self, mock_extract):
        extractor = ParquetExtractor()
        source_path = "data/input.zip"
        dest_dir = "data/output"

        extractor.extract(source_path, dest_dir)

        mock_extract.assert_called_once_with(50000, source_path, dest_dir)


@pytest.mark.unit
class TestParquetExtractorErrorHandling:
    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_raises_extraction_error_on_corrupted_zip(self, mock_extract):
        mock_extract.side_effect = CorruptedZipError("/tmp/data.zip", "Bad ZIP header")

        extractor = ParquetExtractor()

        with pytest.raises(CorruptedZipError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert "Bad ZIP header" in str(exc_info.value)
        assert "/tmp/data.zip" in str(exc_info.value)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_raises_disk_full_error(self, mock_extract):
        mock_extract.side_effect = DiskFullError("/tmp/output")

        extractor = ParquetExtractor()

        with pytest.raises(DiskFullError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert "disk space" in str(exc_info.value).lower()

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_raises_invalid_destination_path_error(self, mock_extract):
        mock_extract.side_effect = InvalidDestinationPathError("Path does not exist")

        extractor = ParquetExtractor()

        with pytest.raises(InvalidDestinationPathError) as exc_info:
            extractor.extract("/tmp/data.zip", "/invalid/path")

        assert "Invalid destination path" in str(exc_info.value)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_raises_extraction_error(self, mock_extract):
        mock_extract.side_effect = ExtractionError(
            "/tmp/data.zip", "CSV parsing failed"
        )

        extractor = ParquetExtractor()

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert "CSV parsing failed" in str(exc_info.value)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_wraps_unexpected_exception(self, mock_extract):
        mock_extract.side_effect = RuntimeError("Unexpected error")

        extractor = ParquetExtractor()

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert "Unexpected extraction error" in str(exc_info.value)
        assert "RuntimeError" in str(exc_info.value)
        assert "/tmp/data.zip" in str(exc_info.value)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_wraps_key_error(self, mock_extract):
        mock_extract.side_effect = KeyError("missing_column")

        extractor = ParquetExtractor()

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert "KeyError" in str(exc_info.value)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_wraps_value_error(self, mock_extract):
        mock_extract.side_effect = ValueError("Invalid data format")

        extractor = ParquetExtractor()

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert "ValueError" in str(exc_info.value)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_wraps_os_error(self, mock_extract):
        mock_extract.side_effect = OSError("Cannot read file")

        extractor = ParquetExtractor()

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert "OSError" in str(exc_info.value)


@pytest.mark.unit
class TestParquetExtractorKnownExceptionsPassthrough:
    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_corrupted_zip_error_not_wrapped(self, mock_extract):
        original_error = CorruptedZipError("/tmp/data.zip", "Bad header")
        mock_extract.side_effect = original_error

        extractor = ParquetExtractor()

        with pytest.raises(CorruptedZipError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert exc_info.value is original_error

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extraction_error_not_wrapped(self, mock_extract):
        original_error = ExtractionError("/tmp/data.zip", "Error")
        mock_extract.side_effect = original_error

        extractor = ParquetExtractor()

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert exc_info.value is original_error

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_disk_full_error_not_wrapped(self, mock_extract):
        original_error = DiskFullError("/tmp/output")
        mock_extract.side_effect = original_error

        extractor = ParquetExtractor()

        with pytest.raises(DiskFullError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert exc_info.value is original_error

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_invalid_destination_path_error_not_wrapped(self, mock_extract):
        original_error = InvalidDestinationPathError("Invalid path")
        mock_extract.side_effect = original_error

        extractor = ParquetExtractor()

        with pytest.raises(InvalidDestinationPathError) as exc_info:
            extractor.extract("/tmp/data.zip", "/tmp/output")

        assert exc_info.value is original_error


@pytest.mark.unit
class TestParquetExtractorEdgeCases:
    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_with_empty_string_paths(self, mock_extract):
        extractor = ParquetExtractor()

        extractor.extract("", "")

        mock_extract.assert_called_once_with(50000, "", "")

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_with_very_long_paths(self, mock_extract):
        extractor = ParquetExtractor()
        long_path = "/tmp/" + "a" * 200 + "/data.zip"
        long_dest = "/tmp/" + "b" * 200 + "/output"

        extractor.extract(long_path, long_dest)

        mock_extract.assert_called_once_with(50000, long_path, long_dest)

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_called_multiple_times(self, mock_extract):
        extractor = ParquetExtractor()

        for i in range(5):
            extractor.extract(f"/tmp/data{i}.zip", f"/tmp/output{i}")

        assert mock_extract.call_count == 5

    @patch("src.macro_infra.extractor_file.Extractor.extract_zip_to_parquet")
    def test_extract_with_unicode_paths(self, mock_extract):
        extractor = ParquetExtractor()
        unicode_path = "/tmp/数据_データ_데이터.zip"
        unicode_dest = "/tmp/输出_出力_출력"

        extractor.extract(unicode_path, unicode_dest)

        mock_extract.assert_called_once_with(50000, unicode_path, unicode_dest)


@pytest.mark.unit
class TestParquetExtractorIntegration:
    def test_extract_real_zip_file(self, tmp_path):
        zip_path = tmp_path / "test_data.zip"
        output_dir = tmp_path / "output"

        csv_content = "col1;col2;col3\n1;2;3\n4;5;6\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.csv", csv_content)

        extractor = ParquetExtractor(chunk_size=1000)
        extractor.extract(str(zip_path), str(output_dir))

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == "test.parquet"

    def test_extract_multiple_csv_files(self, tmp_path):
        zip_path = tmp_path / "multi_data.zip"
        output_dir = tmp_path / "output"

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(3):
                csv_content = f"col1;col2\n{i};{i+1}\n"
                zf.writestr(f"test_{i}.csv", csv_content)

        extractor = ParquetExtractor()
        extractor.extract(str(zip_path), str(output_dir))

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 3

    def test_extract_nonexistent_zip_raises_error(self, tmp_path):
        extractor = ParquetExtractor()
        nonexistent_zip = tmp_path / "nonexistent.zip"
        output_dir = tmp_path / "output"

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(str(nonexistent_zip), str(output_dir))

        assert "not found" in str(exc_info.value).lower()

    def test_extract_empty_zip(self, tmp_path):
        zip_path = tmp_path / "empty.zip"
        output_dir = tmp_path / "output"

        with zipfile.ZipFile(zip_path, "w"):
            pass

        extractor = ParquetExtractor()
        extractor.extract(str(zip_path), str(output_dir))

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 0

    def test_extract_zip_with_non_csv_files(self, tmp_path):
        zip_path = tmp_path / "mixed.zip"
        output_dir = tmp_path / "output"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", "col1;col2\n1;2\n")
            zf.writestr("readme.txt", "This is a readme")
            zf.writestr("image.png", b"\x89PNG\r\n")

        extractor = ParquetExtractor()
        extractor.extract(str(zip_path), str(output_dir))

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == "data.parquet"


@pytest.mark.unit
class TestParquetExtractorFileExtractorInterface:
    def test_implements_extract_method(self):
        extractor = ParquetExtractor()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    def test_extract_signature_matches_interface(self):
        import inspect

        from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
            FileExtractorRepository,
        )

        interface_sig = inspect.signature(FileExtractorRepository.extract)
        impl_sig = inspect.signature(ParquetExtractor.extract)

        interface_params = list(interface_sig.parameters.keys())
        impl_params = list(impl_sig.parameters.keys())

        assert interface_params == impl_params

    def test_can_be_used_as_file_extractor_repository(self):
        from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
            FileExtractorRepository,
        )

        extractor: FileExtractorRepository = ParquetExtractor()
        assert isinstance(extractor, ParquetExtractor)
