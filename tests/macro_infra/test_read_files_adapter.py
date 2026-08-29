import io
import zipfile

import pandas as pd
import pytest

from globaldatafinance.macro_infra import ReadFilesAdapter


@pytest.mark.unit
class TestReadFilesAdapter:
    @pytest.mark.parametrize(
        'content',
        [
            b'col1;col2\n1;2\n3;4\n',
            'col1;col2\n1;2\n3;4\n'.encode('latin-1'),
            'col1;col2\n1;2\n3;4\n'.encode('iso-8859-1'),
            'col1;col2\n1;2\n3;4\n'.encode('cp1252'),
        ],
    )
    def test_read_csv_test_encoding_detects_any_supported_encoding(
        self, tmp_path, content
    ):
        csv_name = 'test.csv'
        zip_path = tmp_path / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(csv_name, content)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            detected = ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)
        assert detected in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    def test_read_csv_test_encoding_detects_supported_encoding_with_non_ascii(
        self, tmp_path
    ):
        csv_content = 'col1;col2\n1;2\n3;á\n'.encode()
        csv_name = 'test.csv'
        zip_path = tmp_path / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(csv_name, csv_content)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            detected = ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)
        assert detected in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    def test_read_csv_test_encoding_logs_and_skips_bad_encoding(
        self, tmp_path, caplog
    ):
        csv_name = 'test.csv'
        zip_path = tmp_path / 'test.zip'
        content = 'col1;col2\n1;2\n3;á\n'.encode()
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(csv_name, content)
        with (
            zipfile.ZipFile(zip_path, 'r') as zf,
            caplog.at_level('DEBUG'),
        ):
            detected = ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)
        assert detected in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        assert any(
            'Validated' in r.message or 'Test read failed' in r.message
            for r in caplog.records
        )

    def test_read_csv_chunk_size_yields_correct_chunks(self):
        csv_content = 'col1;col2\n1;2\n3;4\n'
        wrapper = io.StringIO(csv_content)
        chunks = list(
            ReadFilesAdapter.read_csv_chunk_size(wrapper, chunk_size=1)
        )
        assert len(chunks) == 2
        assert all(isinstance(chunk, pd.DataFrame) for chunk in chunks)

    def test_read_csv_test_encoding_raises_when_all_fail(
        self, tmp_path, monkeypatch
    ):
        import globaldatafinance.macro_infra.read_files as read_files_mod
        from globaldatafinance.macro_exceptions import ExtractionError

        csv_name = 'unreadable.csv'
        zip_path = tmp_path / 'bad.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(csv_name, b'some content')

        def mock_failing_read_csv(*_args, **_kwargs):
            raise UnicodeDecodeError('utf-8', b'', 0, 1, 'decoding failed')

        monkeypatch.setattr(
            read_files_mod.pd, 'read_csv', mock_failing_read_csv
        )

        with (
            zipfile.ZipFile(zip_path, 'r') as zf,
            pytest.raises(ExtractionError) as exc_info,
        ):
            ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)

        assert 'Could not read unreadable.csv with any encoding' in str(
            exc_info.value
        )
        assert isinstance(exc_info.value.__cause__, UnicodeDecodeError)

    def test_read_csv_test_encoding_continues_after_expected_parser_error(
        self, tmp_path, monkeypatch
    ):
        import globaldatafinance.macro_infra.read_files as read_files_mod

        csv_name = 'retry.csv'
        zip_path = tmp_path / 'retry.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(csv_name, b'col1;col2\n1;2\n')

        calls = 0

        def parse_after_retry(*_args, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise pd.errors.ParserError('malformed row')
            return pd.DataFrame({'col1': [1]})

        monkeypatch.setattr(read_files_mod.pd, 'read_csv', parse_after_retry)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            encoding = ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)

        assert encoding == 'utf-8'
        assert calls == 2

    def test_read_csv_test_encoding_propagates_unexpected_error(
        self, tmp_path, monkeypatch
    ):
        import globaldatafinance.macro_infra.read_files as read_files_mod

        csv_name = 'unexpected.csv'
        zip_path = tmp_path / 'unexpected.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(csv_name, b'col1;col2\n1;2\n')

        def fail_unexpectedly(*_args, **_kwargs):
            raise RuntimeError('unexpected parser defect')

        monkeypatch.setattr(read_files_mod.pd, 'read_csv', fail_unexpectedly)

        with (
            zipfile.ZipFile(zip_path, 'r') as zf,
            pytest.raises(RuntimeError, match='unexpected parser defect'),
        ):
            ReadFilesAdapter.read_csv_test_encoding(zf, csv_name)
