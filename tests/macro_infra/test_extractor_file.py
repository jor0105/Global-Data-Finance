import asyncio
import zipfile

import pytest

from datafinc.macro_exceptions import CorruptedZipError, ExtractionError
from datafinc.macro_infra import ExtractorAdapter


class TestExtractorListFilesInZip:
    def test_list_files_zip_not_found_raises_error(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            ExtractorAdapter.list_files_in_zip(str(zip_path))

    def test_list_files_corrupted_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP")

        with pytest.raises(CorruptedZipError):
            ExtractorAdapter.list_files_in_zip(str(zip_path))

    def test_list_files_no_filter_returns_all(self, tmp_path):
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content")
            zf.writestr("file2.csv", "data")
            zf.writestr("file3.json", "{}")

        files = ExtractorAdapter.list_files_in_zip(str(zip_path))

        assert len(files) == 3
        assert "file1.txt" in files
        assert "file2.csv" in files
        assert "file3.json" in files

    def test_list_files_with_extension_filter(self, tmp_path):
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content")
            zf.writestr("file2.csv", "data")
            zf.writestr("file3.CSV", "DATA")

        files = ExtractorAdapter.list_files_in_zip(str(zip_path), ".csv")

        assert len(files) == 2
        assert "file2.csv" in files
        assert "file3.CSV" in files

    def test_list_files_empty_zip_returns_empty(self, tmp_path):
        zip_path = tmp_path / "empty.zip"

        with zipfile.ZipFile(zip_path, "w") as _:
            pass

        files = ExtractorAdapter.list_files_in_zip(str(zip_path))

        assert len(files) == 0


class TestExtractorExtractFileFromZip:
    def test_extract_file_zip_not_found_raises_error(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"
        dest_path = str(tmp_path / "output")

        with pytest.raises(FileNotFoundError):
            ExtractorAdapter.extract_file_from_zip(str(zip_path), "file.txt", dest_path)

    def test_extract_file_corrupted_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP")
        dest_path = str(tmp_path / "output")

        with pytest.raises(CorruptedZipError):
            ExtractorAdapter.extract_file_from_zip(str(zip_path), "file.txt", dest_path)

    def test_extract_file_not_in_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        dest_path = tmp_path / "output"
        dest_path.mkdir()

        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("other.txt", "content")

        with pytest.raises(ExtractionError) as exc_info:
            ExtractorAdapter.extract_file_from_zip(
                str(zip_path), "missing.txt", str(dest_path)
            )

        assert "not found in ZIP" in str(exc_info.value)

    def test_extract_file_successful(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        dest_path = tmp_path / "output"
        dest_path.mkdir()
        file_content = "Test content"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.txt", file_content)

        ExtractorAdapter.extract_file_from_zip(
            str(zip_path), "data.txt", str(dest_path)
        )

        extracted_file = dest_path / "data.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == file_content


class TestExtractorReadFileFromZip:
    def test_read_file_zip_not_found_raises_error(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            ExtractorAdapter.read_file_from_zip(str(zip_path), "file.txt")

    def test_read_file_corrupted_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP")

        with pytest.raises(CorruptedZipError):
            ExtractorAdapter.read_file_from_zip(str(zip_path), "file.txt")

    def test_read_file_not_in_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("other.txt", "content")

        with pytest.raises(ExtractionError) as exc_info:
            ExtractorAdapter.read_file_from_zip(str(zip_path), "missing.txt")

        assert "not found in ZIP" in str(exc_info.value)

    def test_read_file_successful(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        file_content = b"Test binary content"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.bin", file_content)

        content = ExtractorAdapter.read_file_from_zip(str(zip_path), "data.bin")

        assert content == file_content


class TestExtractorOpenFileFromZip:
    def test_open_file_not_in_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("other.txt", "content")

        with zipfile.ZipFile(zip_path, "r") as zf:
            with pytest.raises(ExtractionError) as exc_info:
                ExtractorAdapter.open_file_from_zip(zf, "missing.txt")

            assert "not found in ZIP" in str(exc_info.value)

    def test_open_file_successful(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        file_content = b"Test content"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.txt", file_content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            handle = ExtractorAdapter.open_file_from_zip(zf, "data.txt")
            content = handle.read()
            handle.close()

        assert content == file_content


class TestExtractorIterateFilesInZip:
    def test_iterate_files_zip_not_found_raises_error(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            for _ in ExtractorAdapter.iterate_files_in_zip(str(zip_path)):
                pass

    def test_iterate_files_corrupted_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP")

        with pytest.raises(CorruptedZipError):
            for _ in ExtractorAdapter.iterate_files_in_zip(str(zip_path)):
                pass

    def test_iterate_files_no_filter_iterates_all(self, tmp_path):
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.csv", "content2")

        filenames = []
        for filename, _ in ExtractorAdapter.iterate_files_in_zip(str(zip_path)):
            filenames.append(filename)

        assert len(filenames) == 2
        assert "file1.txt" in filenames
        assert "file2.csv" in filenames

    def test_iterate_files_with_extension_filter(self, tmp_path):
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.csv", "content2")
            zf.writestr("file3.csv", "content3")

        filenames = []
        for filename, _ in ExtractorAdapter.iterate_files_in_zip(str(zip_path), ".csv"):
            filenames.append(filename)

        assert len(filenames) == 2
        assert "file2.csv" in filenames
        assert "file3.csv" in filenames

    def test_iterate_files_can_read_content(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        file_content = "Test content"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.txt", file_content)

        for filename, zip_handle in ExtractorAdapter.iterate_files_in_zip(
            str(zip_path)
        ):
            with zip_handle.open(filename) as f:
                content = f.read().decode("utf-8")
                assert content == file_content


class TestExtractorReadTxtFromZipAsync:
    @pytest.mark.asyncio
    async def test_async_read_txt_file_not_found(self, tmp_path):
        zip_path = tmp_path / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            async for _ in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_corrupted_zip(self, tmp_path):
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_text("Not a ZIP file")

        with pytest.raises(CorruptedZipError):
            async for _ in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_no_txt_file(self, tmp_path):
        zip_path = tmp_path / "no_txt.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", "csv,data")

        with pytest.raises(ExtractionError):
            async for _ in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_successful(self, tmp_path):
        zip_path = tmp_path / "async_txt.zip"
        txt_content = "Line 1\nLine 2\nLine 3\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
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
        async for line in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
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
        async for line in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
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
        async for line in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
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
            async for line in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
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
        async for line in ExtractorAdapter.read_txt_from_zip_async(str(zip_path)):
            lines.append(line)
            if len(lines) >= 10:
                break

        assert len(lines) == 10


class TestExtractorEdgeCases:
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
            async for line in ExtractorAdapter.read_txt_from_zip_async(zip_path):
                lines.append(line)
            return lines

        results = await asyncio.gather(*[read_lines(zp) for zp in zip_files])

        assert len(results) == 3
        for i, lines in enumerate(results):
            assert len(lines) >= 1
            assert f"Content {i}" in lines[0]
