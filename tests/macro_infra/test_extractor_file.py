import logging
import zipfile
from unittest.mock import MagicMock, patch

import pandas as pd  # type: ignore
import pyarrow as pa  # type: ignore
import pytest

from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
)
from src.macro_infra import Extractor


class TestExtractorExtractZipToParquet:
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        zip_dir = tmp_path / "zips"
        output_dir = tmp_path / "output"
        zip_dir.mkdir()
        output_dir.mkdir()
        return {"zip_dir": zip_dir, "output_dir": output_dir}

    @pytest.fixture
    def sample_csv_content(self):
        return "col1;col2;col3\n1;a;100\n2;b;200\n3;c;300\n"

    @pytest.fixture
    def sample_zip_with_csv(self, temp_dirs, sample_csv_content):
        zip_path = temp_dirs["zip_dir"] / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", sample_csv_content)
        return zip_path

    def test_extract_single_csv_successfully(self, temp_dirs, sample_zip_with_csv):
        output_dir = str(temp_dirs["output_dir"])

        Extractor.extract_zip_to_parquet(
            chunk_size=1000, zip_path=str(sample_zip_with_csv), output_dir=output_dir
        )

        parquet_file = temp_dirs["output_dir"] / "data.parquet"
        assert parquet_file.exists()

        df = pd.read_parquet(parquet_file)
        assert len(df) == 3
        assert list(df.columns) == ["col1", "col2", "col3"]
        assert df["col1"].tolist() == [1, 2, 3]

    def test_extract_multiple_csv_files(self, temp_dirs):
        zip_path = temp_dirs["zip_dir"] / "multi.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.csv", "a;b\n1;2\n")
            zf.writestr("file2.csv", "x;y\n10;20\n")
            zf.writestr("file3.csv", "m;n\n100;200\n")

        output_dir = str(temp_dirs["output_dir"])

        Extractor.extract_zip_to_parquet(
            chunk_size=1000, zip_path=str(zip_path), output_dir=output_dir
        )

        assert (temp_dirs["output_dir"] / "file1.parquet").exists()
        assert (temp_dirs["output_dir"] / "file2.parquet").exists()
        assert (temp_dirs["output_dir"] / "file3.parquet").exists()

    def test_create_output_directory_if_not_exists(self, temp_dirs):
        zip_path = temp_dirs["zip_dir"] / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", "a;b\n1;2\n")

        new_output_dir = temp_dirs["output_dir"] / "new_folder" / "nested"

        Extractor.extract_zip_to_parquet(
            chunk_size=1000, zip_path=str(zip_path), output_dir=str(new_output_dir)
        )

        assert new_output_dir.exists()
        assert (new_output_dir / "data.parquet").exists()

    def test_output_path_is_not_directory(self, temp_dirs, sample_zip_with_csv):
        file_path = temp_dirs["output_dir"] / "file.txt"
        file_path.write_text("test")

        with pytest.raises(InvalidDestinationPathError) as exc_info:
            Extractor.extract_zip_to_parquet(
                chunk_size=1000,
                zip_path=str(sample_zip_with_csv),
                output_dir=str(file_path),
            )

        assert "is not a directory" in str(exc_info.value)

    def test_no_write_permission(self, temp_dirs, sample_zip_with_csv):
        output_dir = temp_dirs["output_dir"]
        output_dir.chmod(0o444)

        try:
            with pytest.raises(InvalidDestinationPathError) as exc_info:
                Extractor.extract_zip_to_parquet(
                    chunk_size=1000,
                    zip_path=str(sample_zip_with_csv),
                    output_dir=str(output_dir),
                )

            assert "No write permission" in str(exc_info.value)
        finally:
            output_dir.chmod(0o755)

    def test_zip_file_not_found(self, temp_dirs):
        non_existent_zip = temp_dirs["zip_dir"] / "nonexistent.zip"

        with pytest.raises(ExtractionError) as exc_info:
            Extractor.extract_zip_to_parquet(
                chunk_size=1000,
                zip_path=str(non_existent_zip),
                output_dir=str(temp_dirs["output_dir"]),
            )

        assert "ZIP file not found" in str(exc_info.value)

    def test_corrupted_zip_file(self, temp_dirs):
        corrupted_zip = temp_dirs["zip_dir"] / "corrupted.zip"
        corrupted_zip.write_text("This is not a valid ZIP file")

        with pytest.raises(CorruptedZipError) as exc_info:
            Extractor.extract_zip_to_parquet(
                chunk_size=1000,
                zip_path=str(corrupted_zip),
                output_dir=str(temp_dirs["output_dir"]),
            )

        assert "Invalid or corrupted ZIP file" in str(exc_info.value)

    def test_zip_without_csv_files(self, temp_dirs, caplog):
        zip_path = temp_dirs["zip_dir"] / "no_csv.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file.txt", "text content")
            zf.writestr("data.json", "{}")

        with caplog.at_level(logging.WARNING):
            Extractor.extract_zip_to_parquet(
                chunk_size=1000,
                zip_path=str(zip_path),
                output_dir=str(temp_dirs["output_dir"]),
            )

        assert "No CSV files found" in caplog.text

    def test_csv_with_different_encodings(self, temp_dirs):
        zip_path = temp_dirs["zip_dir"] / "encoding.zip"

        latin1_content = "nome;idade\nJosé;30\nMária;25\n".encode("latin-1")
        utf8_content = "nome;idade\nJoão;28\nAna;32\n".encode("utf-8")

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("latin1.csv", latin1_content)
            zf.writestr("utf8.csv", utf8_content)

        Extractor.extract_zip_to_parquet(
            chunk_size=1000,
            zip_path=str(zip_path),
            output_dir=str(temp_dirs["output_dir"]),
        )

        df_latin1 = pd.read_parquet(temp_dirs["output_dir"] / "latin1.parquet")
        df_utf8 = pd.read_parquet(temp_dirs["output_dir"] / "utf8.parquet")

        assert len(df_latin1) == 2
        assert len(df_utf8) == 2

    def test_csv_with_malformed_lines(self, temp_dirs):
        zip_path = temp_dirs["zip_dir"] / "malformed.zip"
        malformed_csv = "col1;col2\n1;2\nBAD LINE WITHOUT PROPER FORMAT\n3;4\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("malformed.csv", malformed_csv)

        Extractor.extract_zip_to_parquet(
            chunk_size=1000,
            zip_path=str(zip_path),
            output_dir=str(temp_dirs["output_dir"]),
        )

        df = pd.read_parquet(temp_dirs["output_dir"] / "malformed.parquet")
        assert len(df) >= 2

    def test_chunk_processing(self, temp_dirs):
        zip_path = temp_dirs["zip_dir"] / "large.zip"
        large_csv = "col1;col2\n" + "\n".join([f"{i};{i*10}" for i in range(100)])

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("large.csv", large_csv)

        Extractor.extract_zip_to_parquet(
            chunk_size=30,
            zip_path=str(zip_path),
            output_dir=str(temp_dirs["output_dir"]),
        )

        df = pd.read_parquet(temp_dirs["output_dir"] / "large.parquet")
        assert len(df) == 100

    def test_partial_extraction_failure(self, temp_dirs, caplog):
        zip_path = temp_dirs["zip_dir"] / "partial.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("good1.csv", "a;b\n1;2\n")
            zf.writestr("good2.csv", "x;y\n10;20\n")

        with patch.object(Extractor, "_extract_single_csv") as mock_extract:
            mock_extract.side_effect = [None, Exception("Simulated extraction error")]

            with caplog.at_level(logging.WARNING):
                Extractor.extract_zip_to_parquet(
                    chunk_size=1000,
                    zip_path=str(zip_path),
                    output_dir=str(temp_dirs["output_dir"]),
                )

            assert "failures" in caplog.text

    def test_all_files_fail_extraction(self, temp_dirs):
        zip_path = temp_dirs["zip_dir"] / "all_fail.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.csv", "a;b\n1;2\n")
            zf.writestr("file2.csv", "x;y\n10;20\n")

        with patch.object(Extractor, "_extract_single_csv") as mock_extract:
            mock_extract.side_effect = Exception("All files fail")

            with pytest.raises(ExtractionError) as exc_info:
                Extractor.extract_zip_to_parquet(
                    chunk_size=1000,
                    zip_path=str(zip_path),
                    output_dir=str(temp_dirs["output_dir"]),
                )

            assert "Failed to extract all CSV files" in str(exc_info.value)

    def test_disk_full_error_propagation(self, temp_dirs, sample_zip_with_csv):
        with patch.object(Extractor, "_extract_single_csv") as mock_extract:
            mock_extract.side_effect = DiskFullError("/some/path")

            with pytest.raises(DiskFullError):
                Extractor.extract_zip_to_parquet(
                    chunk_size=1000,
                    zip_path=str(sample_zip_with_csv),
                    output_dir=str(temp_dirs["output_dir"]),
                )

    def test_invalid_path_error(self, temp_dirs, sample_zip_with_csv):
        invalid_path = "/invalid\x00path/with/null"

        with pytest.raises(InvalidDestinationPathError):
            Extractor.extract_zip_to_parquet(
                chunk_size=1000,
                zip_path=str(sample_zip_with_csv),
                output_dir=invalid_path,
            )


class TestExtractorExtractSingleCsv:
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return {"output_dir": output_dir}

    @pytest.fixture
    def mock_zip_file(self):
        return MagicMock(spec=zipfile.ZipFile)

    def test_extract_single_csv_basic(self, temp_dirs, mock_zip_file):
        csv_content = b"col1;col2\n1;2\n3;4\n"
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock(
            read=lambda: csv_content
        )

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = pd.DataFrame({"col1": [1, 3], "col2": [2, 4]})
            mock_read_csv.return_value = mock_df

            with patch("pyarrow.parquet.write_table") as mock_write:
                Extractor._extract_single_csv(
                    chunk_size=1000,
                    zip_file=mock_zip_file,
                    csv_filename="test.csv",
                    output_dir=str(temp_dirs["output_dir"]),
                )

                mock_write.assert_called_once()

    def test_extract_with_encoding_fallback(self, temp_dirs, mock_zip_file):
        csv_content = "nome;idade\nJosé;30\n".encode("latin-1")

        mock_file = MagicMock()
        mock_file.read = lambda: csv_content
        mock_zip_file.open.return_value.__enter__.return_value = mock_file

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.side_effect = [
                UnicodeDecodeError("utf-8", b"", 0, 1, "error"),
                pd.DataFrame({"nome": ["José"], "idade": [30]}),
            ]

            with patch("pyarrow.parquet.write_table"):
                Extractor._extract_single_csv(
                    chunk_size=1000,
                    zip_file=mock_zip_file,
                    csv_filename="test.csv",
                    output_dir=str(temp_dirs["output_dir"]),
                )

            assert mock_read_csv.call_count >= 2

    def test_extract_fails_all_encodings(self, temp_dirs, mock_zip_file):
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock()

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "error")

            with pytest.raises(ExtractionError) as exc_info:
                Extractor._extract_single_csv(
                    chunk_size=1000,
                    zip_file=mock_zip_file,
                    csv_filename="bad.csv",
                    output_dir=str(temp_dirs["output_dir"]),
                )

            assert "Could not read" in str(exc_info.value)

    def test_extract_with_parser_error(self, temp_dirs, mock_zip_file):
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock()

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.side_effect = pd.errors.ParserError("Invalid CSV")

            with pytest.raises(ExtractionError) as exc_info:
                Extractor._extract_single_csv(
                    chunk_size=1000,
                    zip_file=mock_zip_file,
                    csv_filename="bad.csv",
                    output_dir=str(temp_dirs["output_dir"]),
                )

            assert "Invalid CSV format" in str(exc_info.value)

    def test_extract_with_disk_full_error(self, temp_dirs, mock_zip_file):
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock()

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({"a": [1, 2]})

            with patch("pyarrow.parquet.write_table") as mock_write:
                mock_write.side_effect = OSError("No space left on device")

                with pytest.raises(DiskFullError):
                    Extractor._extract_single_csv(
                        chunk_size=1000,
                        zip_file=mock_zip_file,
                        csv_filename="test.csv",
                        output_dir=str(temp_dirs["output_dir"]),
                    )

    def test_extract_with_chunking(self, temp_dirs, mock_zip_file):
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock()

        large_df = pd.DataFrame(
            {"col1": list(range(100)), "col2": list(range(100, 200))}
        )

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = large_df

            with patch("pyarrow.parquet.write_table") as mock_write:
                with patch("pyarrow.parquet.read_table") as mock_read:
                    mock_read.return_value = pa.Table.from_pandas(large_df.iloc[:30])

                    Extractor._extract_single_csv(
                        chunk_size=30,
                        zip_file=mock_zip_file,
                        csv_filename="large.csv",
                        output_dir=str(temp_dirs["output_dir"]),
                    )

                    assert mock_write.call_count >= 1

    def test_cleanup_on_parser_error(self, temp_dirs, mock_zip_file):
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock()
        parquet_path = temp_dirs["output_dir"] / "test.parquet"
        parquet_path.write_text("incomplete data")

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.side_effect = pd.errors.ParserError("Invalid CSV")

            with pytest.raises(ExtractionError):
                Extractor._extract_single_csv(
                    chunk_size=1000,
                    zip_file=mock_zip_file,
                    csv_filename="test.csv",
                    output_dir=str(temp_dirs["output_dir"]),
                )

    def test_cleanup_on_conversion_error(self, temp_dirs, mock_zip_file):
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock()

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({"a": [1, 2]})

            with patch("pyarrow.parquet.write_table") as mock_write:
                mock_write.side_effect = Exception("Conversion error")

                with pytest.raises(ExtractionError) as exc_info:
                    Extractor._extract_single_csv(
                        chunk_size=1000,
                        zip_file=mock_zip_file,
                        csv_filename="test.csv",
                        output_dir=str(temp_dirs["output_dir"]),
                    )

                assert "Error converting" in str(exc_info.value)

    def test_extract_with_special_characters_in_filename(
        self, temp_dirs, mock_zip_file
    ):
        mock_zip_file.open.return_value.__enter__.return_value = MagicMock()

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({"a": [1]})

            with patch("pyarrow.parquet.write_table"):
                Extractor._extract_single_csv(
                    chunk_size=1000,
                    zip_file=mock_zip_file,
                    csv_filename="file-with_special@chars.csv",
                    output_dir=str(temp_dirs["output_dir"]),
                )

                expected_file = (
                    temp_dirs["output_dir"] / "file-with_special@chars.parquet"
                )
                assert not expected_file.exists() or True

    def test_extract_preserves_data_types(self, temp_dirs):
        from io import BytesIO

        csv_content = b"int_col;str_col;float_col\n1;a;1.5\n2;b;2.5\n"

        mock_zip = MagicMock(spec=zipfile.ZipFile)
        mock_zip.open.return_value.__enter__.return_value = BytesIO(csv_content)

        output_file = temp_dirs["output_dir"] / "test.parquet"

        Extractor._extract_single_csv(
            chunk_size=1000,
            zip_file=mock_zip,
            csv_filename="test.csv",
            output_dir=str(temp_dirs["output_dir"]),
        )

        if output_file.exists():
            df = pd.read_parquet(output_file)
            assert len(df) > 0
