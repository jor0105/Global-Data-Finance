import os
import tempfile
import zipfile
from unittest.mock import Mock, patch

import pytest

from src.brazil.cvm.fundamental_stocks_data.application.extractors import (
    ParquetExtractor,
)
from src.brazil.cvm.fundamental_stocks_data.application.interfaces import (
    FileExtractorRepository,
)
from src.macro_exceptions.macro_exceptions import (
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

    def test_init_with_large_chunk_size(self):
        extractor = ParquetExtractor(chunk_size=500000)
        assert extractor.chunk_size == 500000


@pytest.mark.unit
class TestParquetExtractorInterface:
    def test_extractor_implements_file_extractor(self):
        extractor = ParquetExtractor()
        assert isinstance(extractor, FileExtractorRepository)

    def test_extractor_has_extract_method(self):
        extractor = ParquetExtractor()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    def test_extract_method_signature(self):
        extractor = ParquetExtractor()
        # Should accept source_path and destination_dir
        assert (
            extractor.extract.__code__.co_argcount == 3
        )  # self, source_path, destination_dir


@pytest.mark.unit
class TestParquetExtractorExtractSuccess:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_calls_core_extractor(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "test.zip")
            dest_path = os.path.join(tmpdir, "output")

            # Create a dummy zip file
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", "test data")

            extractor.extract(zip_path, dest_path)

            mock_extractor_class.extract_zip_to_parquet.assert_called_once_with(
                zip_path, dest_path
            )

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_with_valid_paths(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "data.zip")
            dest_path = os.path.join(tmpdir, "extracted")

            # Create a zip file
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("dummy.csv", "col1,col2\n1,2\n")

            extractor.extract(zip_path, dest_path)

            mock_extractor_class.extract_zip_to_parquet.assert_called_once()


@pytest.mark.unit
class TestParquetExtractorErrorHandling:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_raises_extraction_error(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(
            side_effect=ExtractionError("/path/to/file.zip", "Extraction failed")
        )

        with pytest.raises(ExtractionError):
            extractor.extract("/path/to/file.zip", "/path/to/dest")

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_raises_corrupted_zip_error(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(
            side_effect=CorruptedZipError("/path/to/file.zip", "Invalid ZIP file")
        )

        with pytest.raises(CorruptedZipError):
            extractor.extract("/path/to/file.zip", "/path/to/dest")

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_raises_disk_full_error(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(
            side_effect=DiskFullError("/path/to/dest")
        )

        with pytest.raises(DiskFullError):
            extractor.extract("/path/to/file.zip", "/path/to/dest")

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_raises_invalid_destination_path_error(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(
            side_effect=InvalidDestinationPathError("")
        )

        with pytest.raises(InvalidDestinationPathError):
            extractor.extract("/path/to/file.zip", "")

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_wraps_unexpected_exceptions(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(
            side_effect=ValueError("Unexpected error")
        )

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract("/path/to/file.zip", "/path/to/dest")

        assert "Unexpected extraction error" in str(exc_info.value)
        assert "ValueError" in str(exc_info.value)


@pytest.mark.unit
class TestParquetExtractorLogging:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_logs_start(self, mock_extractor_class, caplog):
        import logging

        caplog.set_level(logging.INFO)

        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "test.zip")
            dest_path = os.path.join(tmpdir, "output")

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", "data")

            extractor.extract(zip_path, dest_path)

            assert any(
                "Starting Parquet extraction" in record.message
                for record in caplog.records
            )

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_logs_completion(self, mock_extractor_class, caplog):
        import logging

        caplog.set_level(logging.INFO)

        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "test.zip")
            dest_path = os.path.join(tmpdir, "output")

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", "data")

            extractor.extract(zip_path, dest_path)

            assert any(
                "completed successfully" in record.message for record in caplog.records
            )

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_logs_error_on_failure(self, mock_extractor_class, caplog):
        import logging

        caplog.set_level(logging.ERROR)

        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(
            side_effect=ValueError("Test error")
        )

        with pytest.raises(ExtractionError):
            extractor.extract("/path/to/file.zip", "/path/to/dest")

        assert any(
            "Unexpected error during extraction" in record.message
            for record in caplog.records
        )


@pytest.mark.unit
class TestParquetExtractorEdgeCases:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_with_long_paths(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        long_path = "/very/long/path/" + "a" * 200 + "/file.zip"
        long_dest = "/very/long/destination/" + "b" * 200

        extractor.extract(long_path, long_dest)

        mock_extractor_class.extract_zip_to_parquet.assert_called_once()

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_extract_with_special_characters_in_path(self, mock_extractor_class):
        extractor = ParquetExtractor()
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        special_path = "/path/with/spëcîal-chàrs/file (1).zip"
        special_dest = "/dest/with/spëcîal-chàrs"

        extractor.extract(special_path, special_dest)

        mock_extractor_class.extract_zip_to_parquet.assert_called_once()


@pytest.mark.unit
class TestParquetExtractorIntegration:
    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_multiple_extractions_with_same_instance(self, mock_extractor_class):
        extractor = ParquetExtractor(chunk_size=10000)
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        files = [
            ("/path1/file1.zip", "/dest1"),
            ("/path2/file2.zip", "/dest2"),
            ("/path3/file3.zip", "/dest3"),
        ]

        for source, dest in files:
            extractor.extract(source, dest)

        assert mock_extractor_class.extract_zip_to_parquet.call_count == 3

    @patch(
        "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
    )
    def test_chunk_size_preserved_across_calls(self, mock_extractor_class):
        extractor = ParquetExtractor(chunk_size=75000)
        mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

        assert extractor.chunk_size == 75000

        extractor.extract("/file1.zip", "/dest1")
        assert extractor.chunk_size == 75000

        extractor.extract("/file2.zip", "/dest2")
        assert extractor.chunk_size == 75000


@pytest.mark.unit
class TestParquetExtractorErrorRecovery:
    def test_can_extract_after_previous_error(self):
        extractor = ParquetExtractor()

        with patch(
            "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
        ) as mock_extractor_class:
            # First call fails
            mock_extractor_class.extract_zip_to_parquet = Mock(
                side_effect=ExtractionError("/file1.zip", "Error")
            )

            with pytest.raises(ExtractionError):
                extractor.extract("/file1.zip", "/dest1")

            # Second call succeeds - change the side_effect
            mock_extractor_class.extract_zip_to_parquet = Mock(return_value=None)

            extractor.extract("/file2.zip", "/dest2")

            # The mock was replaced, so we check each individually
            # Just verify no exception was raised on second call
            assert True  # Test passes if we reach here

    def test_different_errors_handled_correctly(self):
        extractor = ParquetExtractor()

        errors = [
            ExtractionError("/file.zip", "Extraction failed"),
            CorruptedZipError("/file.zip", "Corrupted"),
            DiskFullError("/dest"),
            InvalidDestinationPathError("/bad/path"),
        ]

        for error in errors:
            with patch(
                "src.brazil.cvm.fundamental_stocks_data.application.extractors.parquet_extractor.Extractor"
            ) as mock_extractor_class:
                mock_extractor_class.extract_zip_to_parquet = Mock(side_effect=error)

                with pytest.raises(type(error)):
                    extractor.extract("/file.zip", "/dest")
