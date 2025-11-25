import io
import zipfile

import pandas as pd
import pytest

from globaldatafinance.macro_infra import ReadFilesAdapter


@pytest.mark.unit
class TestReadFilesAdapter:
    @pytest.mark.parametrize(
        "content",
        [
            "col1;col2\n1;2\n3;4\n".encode("utf-8"),
            "col1;col2\n1;2\n3;4\n".encode("latin-1"),
            "col1;col2\n1;2\n3;4\n".encode("iso-8859-1"),
            "col1;col2\n1;2\n3;4\n".encode("cp1252"),
        ],
    )
    def test_read_csv_test_encoding_detects_any_supported_encoding(
        self, tmp_path, content
    ):
        csv_name = "test.csv"
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(csv_name, content)
        with zipfile.ZipFile(zip_path, "r") as zf:
            detected = ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)
        assert detected in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

    def test_read_csv_test_encoding_detects_supported_encoding_with_non_ascii(
        self, tmp_path
    ):
        csv_content = "col1;col2\n1;2\n3;á\n".encode("utf-8")
        csv_name = "test.csv"
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(csv_name, csv_content)
        with zipfile.ZipFile(zip_path, "r") as zf:
            detected = ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)
        assert detected in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

    def test_read_csv_test_encoding_logs_and_skips_bad_encoding(self, tmp_path, caplog):
        csv_name = "test.csv"
        zip_path = tmp_path / "test.zip"
        content = "col1;col2\n1;2\n3;á\n".encode("utf-8")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(csv_name, content)
        with zipfile.ZipFile(zip_path, "r") as zf:
            with caplog.at_level("DEBUG"):
                detected = ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)
        assert detected in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        assert any(
            "Validated" in r.message or "Test read failed" in r.message
            for r in caplog.records
        )

    def test_read_csv_chunk_size_yields_correct_chunks(self):
        csv_content = "col1;col2\n1;2\n3;4\n"
        wrapper = io.StringIO(csv_content)
        chunks = list(ReadFilesAdapter.read_csv_chunk_size(wrapper, chunk_size=1))
        assert len(chunks) == 2
        assert all(isinstance(chunk, pd.DataFrame) for chunk in chunks)
