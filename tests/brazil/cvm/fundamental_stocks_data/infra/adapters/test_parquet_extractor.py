import zipfile
from pathlib import Path

import pytest

from datafinc.brazil.cvm.fundamental_stocks_data import ParquetExtractorCVM
from datafinc.macro_exceptions import (
    CorruptedZipError,
    ExtractionError,
    InvalidDestinationPathError,
)


@pytest.mark.unit
class TestParquetExtractorInitialization:
    def test_init_with_default_chunk_size(self):
        extractor = ParquetExtractorCVM()
        assert extractor.chunk_size == 50000

    def test_init_with_custom_chunk_size(self):
        extractor = ParquetExtractorCVM(chunk_size=100000)
        assert extractor.chunk_size == 50000  # Capped at 50000

    def test_init_with_small_chunk_size(self):
        extractor = ParquetExtractorCVM(chunk_size=1000)
        assert extractor.chunk_size == 1000

    def test_init_with_very_large_chunk_size(self):
        extractor = ParquetExtractorCVM(chunk_size=1000000)
        assert extractor.chunk_size == 50000  # Capped at 50000

    def test_init_with_custom_encodings(self):
        encodings = ["utf-8", "latin-1"]
        extractor = ParquetExtractorCVM(encodings=encodings)
        assert extractor.encodings == encodings

    def test_init_with_default_encodings(self):
        extractor = ParquetExtractorCVM()
        assert extractor.encodings == ["latin-1", "utf-8", "iso-8859-1", "cp1252"]

    def test_init_with_custom_max_fallback_size(self):
        extractor = ParquetExtractorCVM(max_fallback_size_mb=1000)
        assert extractor.max_fallback_size_mb == 1000


@pytest.mark.unit
class TestParquetExtractorValidateDestination:
    def test_validate_destination_creates_directory_if_not_exists(self, tmp_path):
        extractor = ParquetExtractorCVM()
        dest_dir = tmp_path / "new_output"

        extractor._validate_destination(str(dest_dir))

        assert dest_dir.exists()
        assert dest_dir.is_dir()

    def test_validate_destination_raises_error_if_not_directory(self, tmp_path):
        extractor = ParquetExtractorCVM()
        dest_file = tmp_path / "output.txt"
        dest_file.write_text("file")

        with pytest.raises(InvalidDestinationPathError) as exc_info:
            extractor._validate_destination(str(dest_file))

        assert "not a directory" in str(exc_info.value)

    def test_validate_destination_raises_error_if_no_write_permission(
        self, tmp_path, monkeypatch
    ):
        extractor = ParquetExtractorCVM()
        dest_dir = tmp_path / "protected"
        dest_dir.mkdir()

        original_touch = Path.touch

        def mock_touch(self, *args, **kwargs):
            if "protected" in str(self) and ".write_test" in str(self):
                raise PermissionError("No permission")
            return original_touch(self, *args, **kwargs)

        monkeypatch.setattr(Path, "touch", mock_touch)

        with pytest.raises(InvalidDestinationPathError) as exc_info:
            extractor._validate_destination(str(dest_dir))

        assert "No write permission" in str(exc_info.value)


@pytest.mark.unit
class TestParquetExtractorErrorHandling:
    def test_extract_raises_error_on_nonexistent_zip(self, tmp_path):
        extractor = ParquetExtractorCVM()
        zip_path = tmp_path / "nonexistent.zip"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(str(zip_path), str(output_dir))

        assert "not found" in str(exc_info.value).lower()

    def test_extract_raises_corrupted_zip_error(self, tmp_path):
        extractor = ParquetExtractorCVM()
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(CorruptedZipError):
            extractor.extract(str(zip_path), str(output_dir))

    def test_extract_wraps_unexpected_exception(self, tmp_path, monkeypatch):
        extractor = ParquetExtractorCVM()
        zip_path = tmp_path / "test.zip"
        output_dir = tmp_path / "output"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.csv", "col1;col2\n1;2\n")

        def mock_extract(*args):
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(extractor, "_extract_with_transaction", mock_extract)

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(str(zip_path), str(output_dir))

        assert "Unexpected extraction error" in str(exc_info.value)
        assert "RuntimeError" in str(exc_info.value)


@pytest.mark.unit
class TestParquetExtractorSuccessfulExtraction:
    def test_extract_real_zip_file(self, tmp_path):
        zip_path = tmp_path / "test_data.zip"
        output_dir = tmp_path / "output"

        csv_content = "col1;col2;col3\n1;2;3\n4;5;6\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.csv", csv_content)

        extractor = ParquetExtractorCVM(chunk_size=1000)
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

        extractor = ParquetExtractorCVM()
        extractor.extract(str(zip_path), str(output_dir))

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 3

    def test_extract_nonexistent_zip_raises_error(self, tmp_path):
        extractor = ParquetExtractorCVM()
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

        extractor = ParquetExtractorCVM()
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

        extractor = ParquetExtractorCVM()
        extractor.extract(str(zip_path), str(output_dir))

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == "data.parquet"


@pytest.mark.unit
class TestParquetExtractorFileExtractorInterface:
    def test_implements_extract_method(self):
        extractor = ParquetExtractorCVM()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    def test_extract_signature_matches_interface(self):
        import inspect

        from datafinc.brazil.cvm.fundamental_stocks_data.application.interfaces import (
            FileExtractorRepositoryCVM,
        )

        interface_sig = inspect.signature(FileExtractorRepositoryCVM.extract)
        impl_sig = inspect.signature(ParquetExtractorCVM.extract)

        interface_params = list(interface_sig.parameters.keys())
        impl_params = list(impl_sig.parameters.keys())

        assert interface_params == impl_params

    def test_can_be_used_as_file_extractor_repository(self):
        from datafinc.brazil.cvm.fundamental_stocks_data.application.interfaces import (
            FileExtractorRepositoryCVM,
        )

        extractor: FileExtractorRepositoryCVM = ParquetExtractorCVM()
        assert isinstance(extractor, ParquetExtractorCVM)
