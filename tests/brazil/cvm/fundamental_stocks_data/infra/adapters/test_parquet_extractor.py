import zipfile

import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    ParquetExtractorAdapterCVM,
)
from globaldatafinance.macro_exceptions import (
    CorruptedZipError,
    ExtractionError,
)


@pytest.mark.unit
class TestParquetExtractorInitialization:
    def test_init_creates_extractor_adapter(self):
        extractor = ParquetExtractorAdapterCVM()
        assert extractor.extractor_adapter is not None


@pytest.mark.unit
class TestParquetExtractorErrorHandling:
    def test_extract_raises_error_on_nonexistent_zip(self, tmp_path):
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / "nonexistent.zip"

        with pytest.raises(ExtractionError):
            extractor.extract(str(zip_path), str(tmp_path))

    def test_extract_raises_corrupted_zip_error(self, tmp_path):
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP")

        with pytest.raises(CorruptedZipError):
            extractor.extract(str(zip_path), str(tmp_path))

    def test_extract_wraps_unexpected_exception(self, tmp_path, monkeypatch):
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.csv", "col1;col2\n1;2\n")

        def mock_extract(*args):
            raise RuntimeError("Unexpected error")

        monkeypatch.setattr(
            extractor,
            "_ParquetExtractorAdapterCVM__extract_with_transaction",
            mock_extract,
        )

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(str(zip_path), str(tmp_path))

        assert "Unexpected extraction error" in str(exc_info.value)
        assert "RuntimeError" in str(exc_info.value)


@pytest.mark.unit
class TestParquetExtractorSuccessfulExtraction:
    def test_extract_real_zip_file(self, tmp_path):
        zip_path = tmp_path / "test_data.zip"

        csv_content = "col1;col2;col3\n1;2;3\n4;5;6\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.csv", csv_content)

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob("*.parquet"))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == "test.parquet"

    def test_extract_multiple_csv_files(self, tmp_path):
        zip_path = tmp_path / "multi_data.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(3):
                csv_content = f"col1;col2\n{i};{i + 1}\n"
                zf.writestr(f"test_{i}.csv", csv_content)

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob("*.parquet"))
        assert len(parquet_files) == 3

    def test_extract_nonexistent_zip_raises_error(self, tmp_path):
        extractor = ParquetExtractorAdapterCVM()
        nonexistent_zip = tmp_path / "nonexistent.zip"

        with pytest.raises(ExtractionError):
            extractor.extract(str(nonexistent_zip), str(tmp_path))

    def test_extract_empty_zip(self, tmp_path):
        zip_path = tmp_path / "empty.zip"

        with zipfile.ZipFile(zip_path, "w"):
            pass

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob("*.parquet"))
        assert len(parquet_files) == 0

    def test_extract_zip_with_non_csv_files(self, tmp_path):
        zip_path = tmp_path / "mixed.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", "col1;col2\n1;2\n")
            zf.writestr("readme.txt", "This is a readme")
            zf.writestr("image.png", b"\x89PNG\r\n")

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob("*.parquet"))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == "data.parquet"


@pytest.mark.unit
class TestParquetExtractorFileExtractorInterface:
    def test_implements_extract_method(self):
        extractor = ParquetExtractorAdapterCVM()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    def test_extract_signature_matches_interface(self):
        import inspect

        from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.interfaces import (
            FileExtractorRepositoryCVM,
        )

        interface_sig = inspect.signature(FileExtractorRepositoryCVM.extract)
        impl_sig = inspect.signature(ParquetExtractorAdapterCVM.extract)

        interface_params = list(interface_sig.parameters.keys())
        impl_params = list(impl_sig.parameters.keys())

        assert interface_params == impl_params

    def test_can_be_used_as_file_extractor_repository(self):
        from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.interfaces import (
            FileExtractorRepositoryCVM,
        )

        extractor: FileExtractorRepositoryCVM = ParquetExtractorAdapterCVM()
        assert isinstance(extractor, ParquetExtractorAdapterCVM)
