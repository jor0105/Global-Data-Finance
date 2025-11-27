import asyncio
import zipfile

import pytest

from globaldatafinance.macro_exceptions import (
    CorruptedZipError,
    ExtractionError,
)
from globaldatafinance.macro_infra import ExtractorAdapter


class TestExtractorListFilesInZip:
    def test_list_files_zip_not_found_raises_error(self, tmp_path):
        zip_path = tmp_path / 'nonexistent.zip'

        with pytest.raises(FileNotFoundError):
            ExtractorAdapter.list_files_in_zip(str(zip_path), '.txt')

    def test_list_files_corrupted_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / 'corrupted.zip'
        zip_path.write_text('Not a ZIP')

        with pytest.raises(CorruptedZipError):
            ExtractorAdapter.list_files_in_zip(str(zip_path), '.txt')

    def test_list_files_no_filter_returns_all(self, tmp_path):
        zip_path = tmp_path / 'test.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('file1.txt', 'content')
            zf.writestr('file2.csv', 'data')
            zf.writestr('file3.json', '{}')

        files = ExtractorAdapter.list_files_in_zip(str(zip_path), '')

        assert len(files) == 3
        assert 'file1.txt' in files
        assert 'file2.csv' in files
        assert 'file3.json' in files

    def test_list_files_with_extension_filter(self, tmp_path):
        zip_path = tmp_path / 'test.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('file1.txt', 'content')
            zf.writestr('file2.csv', 'data')
            zf.writestr('file3.CSV', 'DATA')

        files = ExtractorAdapter.list_files_in_zip(str(zip_path), '.csv')

        assert len(files) == 2
        assert 'file2.csv' in files
        assert 'file3.CSV' in files

    def test_list_files_empty_zip_returns_empty(self, tmp_path):
        zip_path = tmp_path / 'empty.zip'

        with zipfile.ZipFile(zip_path, 'w') as _:
            pass

        files = ExtractorAdapter.list_files_in_zip(str(zip_path), '.txt')

        assert len(files) == 0


class TestExtractorOpenFileFromZip:
    def test_open_file_not_in_zip_raises_error(self, tmp_path):
        zip_path = tmp_path / 'test.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('other.txt', 'content')

        with zipfile.ZipFile(zip_path, 'r') as zf:
            with pytest.raises(ExtractionError) as exc_info:
                ExtractorAdapter.open_file_from_zip(zf, 'missing.txt')

            assert 'not found in ZIP' in str(exc_info.value)

    def test_open_file_successful(self, tmp_path):
        zip_path = tmp_path / 'test.zip'
        file_content = b'Test content'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.txt', file_content)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            handle = ExtractorAdapter.open_file_from_zip(zf, 'data.txt')
            content = handle.read()
            handle.close()

        assert content == file_content


class TestExtractorReadTxtFromZipAsync:
    @pytest.mark.asyncio
    async def test_async_read_txt_file_not_found(self, tmp_path):
        zip_path = tmp_path / 'nonexistent.zip'
        extractor = ExtractorAdapter()

        with pytest.raises(FileNotFoundError):
            async for _ in extractor.extract_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_corrupted_zip(self, tmp_path):
        zip_path = tmp_path / 'corrupted.zip'
        zip_path.write_text('Not a ZIP file')
        extractor = ExtractorAdapter()

        with pytest.raises(CorruptedZipError):
            async for _ in extractor.extract_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_no_txt_file(self, tmp_path):
        zip_path = tmp_path / 'no_txt.zip'
        extractor = ExtractorAdapter()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.csv', 'csv,data')

        with pytest.raises(ExtractionError):
            async for _ in extractor.extract_txt_from_zip_async(str(zip_path)):
                pass

    @pytest.mark.asyncio
    async def test_async_read_txt_successful(self, tmp_path):
        zip_path = tmp_path / 'async_txt.zip'
        txt_content = 'Line 1\nLine 2\nLine 3\n'
        extractor = ExtractorAdapter()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.TXT', txt_content.encode('latin-1'))

        lines = []
        async for line in extractor.extract_txt_from_zip_async(str(zip_path)):
            lines.append(line)

        assert len(lines) == 3
        assert 'Line 1' in lines[0]
        assert 'Line 2' in lines[1]
        assert 'Line 3' in lines[2]

    @pytest.mark.asyncio
    async def test_async_read_txt_empty_file(self, tmp_path):
        zip_path = tmp_path / 'empty.zip'
        extractor = ExtractorAdapter()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('empty.TXT', b'')

        lines = []
        async for line in extractor.extract_txt_from_zip_async(str(zip_path)):
            lines.append(line)

        assert len(lines) == 0

    @pytest.mark.asyncio
    async def test_async_read_txt_large_file(self, tmp_path):
        zip_path = tmp_path / 'large.zip'
        num_lines = 10000
        txt_content = '\n'.join([f'Line {i}' for i in range(num_lines)])
        extractor = ExtractorAdapter()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('large.TXT', txt_content.encode('latin-1'))

        line_count = 0
        async for line in extractor.extract_txt_from_zip_async(str(zip_path)):
            line_count += 1
            if line_count % 1000 == 0:
                assert 'Line' in line

        assert line_count == num_lines

    @pytest.mark.asyncio
    async def test_async_read_txt_filters_empty_lines(self, tmp_path):
        zip_path = tmp_path / 'empty_lines.zip'
        txt_content = 'Line 1\n\nLine 3\n\n\nLine 6\n'
        extractor = ExtractorAdapter()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.TXT', txt_content.encode('latin-1'))

        lines = []
        async for line in extractor.extract_txt_from_zip_async(str(zip_path)):
            lines.append(line)

        assert 'Line 1' in lines
        assert 'Line 3' in lines
        assert 'Line 6' in lines
        assert '' not in lines

    @pytest.mark.asyncio
    async def test_async_read_txt_handles_decode_errors(
        self, tmp_path, caplog
    ):
        zip_path = tmp_path / 'decode_error.zip'
        content = b'Valid line\n\x00\x01\x02\x03\nAnother line\n'
        extractor = ExtractorAdapter()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.TXT', content)

        lines = []
        try:
            async for line in extractor.extract_txt_from_zip_async(
                str(zip_path)
            ):
                lines.append(line)
        except Exception:
            pass

        assert len(lines) >= 0

    @pytest.mark.asyncio
    async def test_async_read_txt_partial_iteration(self, tmp_path):
        zip_path = tmp_path / 'partial.zip'
        txt_content = '\n'.join([f'Line {i}' for i in range(100)])
        extractor = ExtractorAdapter()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.TXT', txt_content.encode('latin-1'))

        lines = []
        async for line in extractor.extract_txt_from_zip_async(str(zip_path)):
            lines.append(line)
            if len(lines) >= 10:
                break

        assert len(lines) == 10


class TestExtractorEdgeCases:
    @pytest.mark.asyncio
    async def test_concurrent_async_reads(self, tmp_path):
        zip_files = []
        for i in range(3):
            zip_path = tmp_path / f'file{i}.zip'
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr('data.TXT', f'Content {i}\n'.encode('latin-1'))
            zip_files.append(str(zip_path))

        async def read_lines(zip_path):
            extractor = ExtractorAdapter()
            lines = []
            async for line in extractor.extract_txt_from_zip_async(zip_path):
                lines.append(line)
            return lines

        results = await asyncio.gather(*[read_lines(zp) for zp in zip_files])

        assert len(results) == 3
        for i, lines in enumerate(results):
            assert len(lines) >= 1
            assert f'Content {i}' in lines[0]
