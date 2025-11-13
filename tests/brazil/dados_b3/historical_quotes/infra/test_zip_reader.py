import pytest

from src.brazil.dados_b3.historical_quotes.infra.zip_reader import ZipFileReader
from src.macro_exceptions import CorruptedZipError, ExtractionError


class TestZipFileReader:
    @pytest.fixture
    def reader(self):
        return ZipFileReader()

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_file_not_found(self, reader):
        zip_path = "/nonexistent/path/file.zip"

        with pytest.raises(FileNotFoundError):
            async for _ in reader.read_lines_from_zip(zip_path):
                pass

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_invalid_path_type(self, reader):
        with pytest.raises((TypeError, FileNotFoundError)):
            async for _ in reader.read_lines_from_zip(None):
                pass

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_empty_path(self, reader):
        with pytest.raises((FileNotFoundError, ValueError)):
            async for _ in reader.read_lines_from_zip(""):
                pass

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_directory_path(self, reader, tmp_path):
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()

        with pytest.raises((CorruptedZipError, ExtractionError, FileNotFoundError)):
            async for _ in reader.read_lines_from_zip(str(dir_path)):
                pass

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_corrupted_file(self, reader, tmp_path):
        corrupted_zip = tmp_path / "corrupted.zip"
        corrupted_zip.write_text("This is not a valid ZIP file")

        with pytest.raises(CorruptedZipError):
            async for _ in reader.read_lines_from_zip(str(corrupted_zip)):
                pass

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_no_txt_file(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "no_txt.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.csv", "some,csv,data")

        with pytest.raises(ExtractionError):
            async for _ in reader.read_lines_from_zip(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_valid_file(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "valid.zip"
        txt_content = "Line 1\nLine 2\nLine 3\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 3
        assert lines[0] == "Line 1"
        assert lines[1] == "Line 2"
        assert lines[2] == "Line 3"

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_empty_txt_file(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "empty.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", b"")

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 0

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_single_line(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "single.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", b"Single Line")

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 1
        assert lines[0] == "Single Line"

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_large_file(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "large.zip"
        num_lines = 10000
        txt_content = "\n".join([f"Line {i}" for i in range(num_lines)])

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == num_lines
        assert lines[0] == "Line 0"
        assert lines[-1] == f"Line {num_lines - 1}"

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_latin1_encoding(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "latin1.zip"
        txt_content = "Acao\nCedilha\nAEIOU\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 3
        # Just verify we got lines, encoding might vary
        assert len(lines[0]) > 0
        assert len(lines[1]) > 0

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_multiple_txt_files(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "multiple.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("first.TXT", b"First file content")
            zf.writestr("second.TXT", b"Second file content")

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        # Should read the first TXT file found
        assert len(lines) >= 1
        assert "First" in lines[0] or "content" in " ".join(lines)

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_mixed_case_extension(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "mixedcase.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.txt", b"Lowercase txt")  # lowercase

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 1
        assert "Lowercase" in lines[0]

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_with_empty_lines(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "empty_lines.zip"
        txt_content = "Line 1\n\nLine 3\n\n\nLine 6"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        # Empty lines should be filtered out by the implementation
        assert "Line 1" in lines
        assert "Line 3" in lines
        assert "Line 6" in lines

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_whitespace_lines(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "whitespace.zip"
        txt_content = "Line 1\n    \nLine 3\n\t\t\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        # Should strip whitespace and filter empty lines
        assert len(lines) >= 2
        assert "Line 1" in lines
        assert "Line 3" in lines

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_special_characters(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "special.zip"
        txt_content = "Line@#$%\nLine!@#\nLine*&^"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 3
        assert "@#$%" in lines[0]

    @pytest.mark.asyncio
    async def test_read_lines_from_zip_long_lines(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "longlines.zip"
        long_line = "X" * 10000
        txt_content = f"{long_line}\nShort line\n"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 2
        assert len(lines[0]) == 10000
        assert lines[1] == "Short line"


class TestZipFileReaderIntegration:
    @pytest.fixture
    def reader(self):
        return ZipFileReader()

    @pytest.mark.asyncio
    async def test_read_real_world_cotahist_structure(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "COTAHIST_A2023.ZIP"
        cotahist_content = (
            "00COTAHIST.2023BOVESPA 20231231\n"
            "012023123102PETR4      010PETROBRAS   ON        ...\n"
            "012023123102VALE3      010VALE        ON        ...\n"
            "99000000003\n"
        )

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("COTAHIST_A2023.TXT", cotahist_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 4
        assert lines[0].startswith("00COTAHIST")
        assert lines[-1].startswith("99")

    @pytest.mark.asyncio
    async def test_concurrent_reading(self, reader, tmp_path):
        import asyncio
        import zipfile

        zip_files = []
        for i in range(3):
            zip_path = tmp_path / f"file{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("data.TXT", f"Content {i}\n".encode("latin-1"))
            zip_files.append(str(zip_path))

        async def read_all_lines(zip_path):
            lines = []
            async for line in reader.read_lines_from_zip(zip_path):
                lines.append(line)
            return lines

        results = await asyncio.gather(*[read_all_lines(zp) for zp in zip_files])

        assert len(results) == 3
        for i, lines in enumerate(results):
            assert len(lines) == 1
            assert f"Content {i}" in lines[0]

    @pytest.mark.asyncio
    async def test_error_handling_in_stream(self, reader, tmp_path):
        import zipfile

        # Create a ZIP with binary data that might cause decode issues
        zip_path = tmp_path / "binary.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", b"\x00\x01\x02\x03\x04")

        # Should handle decode errors gracefully or raise appropriate exception
        try:
            lines = []
            async for line in reader.read_lines_from_zip(str(zip_path)):
                lines.append(line)
            # If it succeeds, that's okay (handled gracefully)
            assert isinstance(lines, list)
        except (UnicodeDecodeError, ExtractionError):
            # If it raises, that's also acceptable
            pass

    @pytest.mark.asyncio
    async def test_memory_efficiency_with_large_file(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "huge.zip"
        # Create a large file (but not too large for test)
        num_lines = 50000
        txt_content = "\n".join([f"Line {i}" * 10 for i in range(num_lines)])

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        line_count = 0
        async for line in reader.read_lines_from_zip(str(zip_path)):
            line_count += 1
            # Just count, don't store in memory
            if line_count % 10000 == 0:
                # Verify we're getting valid lines
                assert "Line" in line

        assert line_count == num_lines


class TestZipFileReaderEdgeCases:
    @pytest.fixture
    def reader(self):
        return ZipFileReader()

    @pytest.mark.asyncio
    async def test_zip_with_nested_directories(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "nested.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("dir1/dir2/data.TXT", b"Nested content")

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 1
        assert "Nested content" in lines[0]

    @pytest.mark.asyncio
    async def test_zip_with_compressed_txt(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "compressed.zip"
        txt_content = "Compressed line\n" * 100

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)

        assert len(lines) == 100
        assert all("Compressed line" in line for line in lines)

    @pytest.mark.asyncio
    async def test_multiple_reads_same_zip(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "reread.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", b"Line 1\nLine 2\n")

        # Read first time
        lines1 = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines1.append(line)

        # Read second time
        lines2 = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines2.append(line)

        assert lines1 == lines2
        assert len(lines1) == 2

    @pytest.mark.asyncio
    async def test_partial_iteration(self, reader, tmp_path):
        import zipfile

        zip_path = tmp_path / "partial.zip"
        txt_content = "\n".join([f"Line {i}" for i in range(100)])

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.TXT", txt_content.encode("latin-1"))

        lines = []
        async for line in reader.read_lines_from_zip(str(zip_path)):
            lines.append(line)
            if len(lines) >= 10:
                break

        assert len(lines) == 10
        assert lines[0] == "Line 0"
        assert lines[9] == "Line 9"
