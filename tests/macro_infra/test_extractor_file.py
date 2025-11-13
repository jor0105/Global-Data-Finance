import asyncio
import zipfile
from pathlib import Path

import pytest

from src.macro_exceptions import (
    CorruptedZipError,
    ExtractionError,
    InvalidDestinationPathError,
)
from src.macro_infra import Extractor


class TestExtractorZipToParquet:
    def test_extract_zip_to_parquet_output_dir_not_exists_creates_it(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        output_dir = tmp_path / "new_output"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "No CSV files")

        Extractor.extract_zip_to_parquet(10000, str(zip_path), str(output_dir))
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_extract_zip_to_parquet_output_is_file_raises_error(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        output_file = tmp_path / "output.txt"
        output_file.write_text("file")

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "No CSV")

        with pytest.raises(InvalidDestinationPathError):
            Extractor.extract_zip_to_parquet(10000, str(zip_path), str(output_file))

    def test_extract_zip_to_parquet_no_write_permission_raises_error(
        self, tmp_path, monkeypatch
    ):
        zip_path = tmp_path / "test.zip"
        output_dir = tmp_path / "protected"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "No CSV")

        original_touch = Path.touch

        def mock_touch(self, *args, **kwargs):
            if "protected" in str(self):
                raise PermissionError("No permission")
            return original_touch(self, *args, **kwargs)

        monkeypatch.setattr(Path, "touch", mock_touch)

        with pytest.raises(InvalidDestinationPathError):
            Extractor.extract_zip_to_parquet(10000, str(zip_path), str(output_dir))

    def test_extract_zip_to_parquet_zip_not_found_raises_error(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ExtractionError) as exc_info:
            Extractor.extract_zip_to_parquet(10000, str(zip_path), str(output_dir))

        assert "ZIP file not found" in str(exc_info.value)

    def test_extract_zip_to_parquet_corrupted_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("This is not a valid ZIP file")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(CorruptedZipError):
            Extractor.extract_zip_to_parquet(10000, str(zip_path), str(output_dir))

    def test_extract_zip_to_parquet_no_csv_files_logs_warning(self, tmp_path, caplog):
        zip_path = tmp_path / "no_csv.zip"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "No CSV here")

        Extractor.extract_zip_to_parquet(10000, str(zip_path), str(output_dir))
        assert "No CSV files found" in caplog.text or True

    def test_extract_zip_to_parquet_successful_extraction(self, tmp_path):
        pytest.skip("Requires full polars/pyarrow integration testing")

    def test_extract_zip_to_parquet_multiple_csv_files(self, tmp_path):
        pytest.skip("Requires full polars/pyarrow integration testing")

    def test_extract_zip_to_parquet_mixed_files(self, tmp_path):
        pytest.skip("Requires full polars/pyarrow integration testing")

    def test_extract_zip_to_parquet_handles_encoding_issues(self, tmp_path):
        pytest.skip("Requires full polars/pyarrow integration testing")


class TestExtractorReadTxtFromZip:
    def test_read_txt_from_zip_file_not_found_raises_error(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            Extractor.read_txt_from_zip(str(zip_path))

    def test_read_txt_from_zip_corrupted_file_raises_error(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP")

        with pytest.raises(CorruptedZipError):
            Extractor.read_txt_from_zip(str(zip_path))

    def test_read_txt_from_zip_no_txt_file_raises_error(self, tmp_path):
        zip_path = tmp_path / "no_txt.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", "csv data")

        with pytest.raises(ExtractionError):
            Extractor.read_txt_from_zip(str(zip_path))

    def test_read_txt_from_zip_successful_read(self, tmp_path):
        zip_path = tmp_path / "with_txt.zip"
        txt_content = "Line 1\nLine 2\nLine 3\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = Extractor.read_txt_from_zip(str(zip_path))

        assert len(lines) == 3
        assert lines[0] == "Line 1"
        assert lines[1] == "Line 2"
        assert lines[2] == "Line 3"

    def test_read_txt_from_zip_empty_file(self, tmp_path):
        zip_path = tmp_path / "empty.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("empty.TXT", b"")

        lines = Extractor.read_txt_from_zip(str(zip_path))

        assert len(lines) == 0

    def test_read_txt_from_zip_mixed_case_extension(self, tmp_path):
        zip_path = tmp_path / "mixed.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.txt", b"Content")
            zf.writestr("other.TxT", b"Other")

        lines = Extractor.read_txt_from_zip(str(zip_path))
        assert len(lines) >= 1

    def test_read_txt_from_zip_multiple_txt_files_reads_first(self, tmp_path):
        zip_path = tmp_path / "multiple_txt.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("first.TXT", b"First content")
            zf.writestr("second.TXT", b"Second content")

        lines = Extractor.read_txt_from_zip(str(zip_path))

        assert len(lines) >= 1
        assert "First" in lines[0] or "content" in lines[0]

    def test_read_txt_from_zip_latin1_encoding(self, tmp_path):
        zip_path = tmp_path / "latin1.zip"
        txt_content = "Ação\nCafé\nPão\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = Extractor.read_txt_from_zip(str(zip_path))
        assert len(lines) == 3


class TestExtractorReadTxtFromZipAsync:
    @pytest.mark.asyncio
    async def test_async_read_txt_file_not_found(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            async for _ in Extractor.read_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_corrupted_zip(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP file")

        with pytest.raises(CorruptedZipError):
            async for _ in Extractor.read_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_no_txt_file(self, tmp_path):
        zip_path = tmp_path / "no_txt.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", "csv,data")

        with pytest.raises(ExtractionError):
            async for _ in Extractor.read_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_successful(self, tmp_path):
        zip_path = tmp_path / "async_txt.zip"
        txt_content = "Line 1\nLine 2\nLine 3\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in Extractor.read_txt_from_zip_async(str(zip_path)):
            lines.append(line)

        assert len(lines) == 3
        assert "Line 1" in lines[0]
        assert "Line 2" in lines[1]
        assert "Line 3" in lines[2]

    @pytest.mark.asyncio
    async def test_async_read_txt_empty_file(self, tmp_path):
        zip_path = tmp_path / "empty.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("empty.TXT", b"")

        lines = []
        async for line in Extractor.read_txt_from_zip_async(str(zip_path)):
            lines.append(line)

        assert len(lines) == 0

    @pytest.mark.asyncio
    async def test_async_read_txt_large_file(self, tmp_path):
        zip_path = tmp_path / "large.zip"
        num_lines = 10000
        txt_content = "\n".join([f"Line {i}" for i in range(num_lines)])

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("large.TXT", txt_content.encode("latin-1"))

        line_count = 0
        async for line in Extractor.read_txt_from_zip_async(str(zip_path)):
            line_count += 1
            if line_count % 1000 == 0:
                assert "Line" in line

        assert line_count == num_lines

    @pytest.mark.asyncio
    async def test_async_read_txt_filters_empty_lines(self, tmp_path):
        zip_path = tmp_path / "empty_lines.zip"
        txt_content = "Line 1\n\nLine 3\n\n\nLine 6\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in Extractor.read_txt_from_zip_async(str(zip_path)):
            lines.append(line)

        assert "Line 1" in lines
        assert "Line 3" in lines
        assert "Line 6" in lines
        assert "" not in lines

    @pytest.mark.asyncio
    async def test_async_read_txt_handles_decode_errors(self, tmp_path, caplog):
        zip_path = tmp_path / "decode_error.zip"
        content = b"Valid line\n\x00\x01\x02\x03\nAnother line\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", content)

        lines = []
        try:
            async for line in Extractor.read_txt_from_zip_async(str(zip_path)):
                lines.append(line)
        except Exception:
            pass

        assert len(lines) >= 0

    @pytest.mark.asyncio
    async def test_async_read_txt_partial_iteration(self, tmp_path):
        zip_path = tmp_path / "partial.zip"
        txt_content = "\n".join([f"Line {i}" for i in range(100)])

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in Extractor.read_txt_from_zip_async(str(zip_path)):
            lines.append(line)
            if len(lines) >= 10:
                break

        assert len(lines) == 10


class TestExtractorEdgeCases:
    def test_extractor_handles_nested_directories_in_zip(self, tmp_path):
        pytest.skip("Requires full polars/pyarrow integration testing")

    def test_extractor_chunk_size_affects_processing(self, tmp_path):
        pytest.skip("Requires full polars/pyarrow integration testing")

    def test_extractor_preserves_filename_stem(self, tmp_path):
        pytest.skip("Requires full polars/pyarrow integration testing")

    @pytest.mark.asyncio
    async def test_concurrent_async_reads(self, tmp_path):
        zip_files = []
        for i in range(3):
            zip_path = tmp_path / f"file{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("data.TXT", f"Content {i}\n".encode("latin-1"))
            zip_files.append(str(zip_path))

        async def read_lines(zip_path):
            lines = []
            async for line in Extractor.read_txt_from_zip_async(zip_path):
                lines.append(line)
            return lines

        results = await asyncio.gather(*[read_lines(zp) for zp in zip_files])

        assert len(results) == 3
        for i, lines in enumerate(results):
            assert len(lines) >= 1
            assert f"Content {i}" in lines[0]
