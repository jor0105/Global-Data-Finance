import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    ParquetExtractorAdapterCVM,
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    extract as extract_module,
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    transaction as transaction_module,
)
from globaldatafinance.macro_exceptions import (
    CorruptedZipError,
    ExtractionError,
    SecurityError,
)


@pytest.mark.unit
class TestParquetExtractorInitialization:
    def test_init_creates_extractor_adapter(self):
        extractor = ParquetExtractorAdapterCVM()
        assert extractor.extractor_adapter is not None


@pytest.mark.integration
class TestParquetExtractorErrorHandling:
    def test_extract_raises_error_on_nonexistent_zip(self, tmp_path):
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / 'nonexistent.zip'

        with pytest.raises(ExtractionError):
            extractor.extract(str(zip_path), str(tmp_path))

    def test_extract_raises_corrupted_zip_error(self, tmp_path):
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / 'corrupted.zip'
        zip_path.write_text('Not a ZIP')

        with pytest.raises(CorruptedZipError):
            extractor.extract(str(zip_path), str(tmp_path))

    @pytest.mark.parametrize(
        'destination_path', ['/', 'D:\\', '\\\\server\\share\\output']
    )
    def test_extract_rejects_unsafe_destination_before_staging(
        self, tmp_path, destination_path
    ):
        """Direct extraction never creates unsafe staging paths."""
        zip_path = tmp_path / 'input.zip'
        with zipfile.ZipFile(zip_path, 'w') as archive:
            archive.writestr('input.csv', 'first;second\n1;2\n')

        with (
            patch.object(Path, 'mkdir') as mkdir,
            pytest.raises(SecurityError),
        ):
            ParquetExtractorAdapterCVM().extract(
                str(zip_path), destination_path
            )

        mkdir.assert_not_called()

    @pytest.mark.parametrize(
        'member_name',
        [
            'dir/payload:secret.csv',
            'dir/CON.csv',
            'dir/file.csv.',
        ],
    )
    def test_extract_rejects_win32_member_before_staging(
        self, tmp_path, member_name
    ):
        """Unsafe Win32 names are rejected before staging or output writes."""
        zip_path = tmp_path / 'unsafe-member.zip'
        with zipfile.ZipFile(zip_path, 'w') as archive:
            archive.writestr(member_name, 'first;second\n1;2\n')

        with (
            patch.object(transaction_module.tempfile, 'mkdtemp') as mkdtemp,
            pytest.raises(
                CorruptedZipError, match='unsafe Windows ZIP member'
            ),
        ):
            ParquetExtractorAdapterCVM().extract(str(zip_path), str(tmp_path))

        mkdtemp.assert_not_called()
        assert not list(tmp_path.glob('*.parquet'))

    def test_extract_rejects_file_ancestor_before_staging(self, tmp_path):
        """An archive file cannot also be a parent of another member."""
        zip_path = tmp_path / 'ancestor-member.zip'
        with zipfile.ZipFile(zip_path, 'w') as archive:
            archive.writestr('dir', 'not a directory')
            archive.writestr('dir/file.csv', 'first;second\n1;2\n')

        with (
            patch.object(transaction_module.tempfile, 'mkdtemp') as mkdtemp,
            pytest.raises(
                CorruptedZipError, match='file ZIP member is an ancestor'
            ),
        ):
            ParquetExtractorAdapterCVM().extract(str(zip_path), str(tmp_path))

        mkdtemp.assert_not_called()
        assert not list(tmp_path.glob('*.parquet'))

    def test_extract_wraps_unexpected_exception(self, tmp_path, monkeypatch):
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / 'test.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.csv', 'col1;col2\n1;2\n')

        def fail_transaction(*_args, **_kwargs):
            raise RuntimeError('Unexpected error')

        monkeypatch.setattr(
            extract_module,
            'CvmFailureAtomicBatchCommit',
            fail_transaction,
        )

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(str(zip_path), str(tmp_path))

        assert 'Unexpected extraction error' in str(exc_info.value)
        assert 'Unexpected error' in str(exc_info.value)


@pytest.mark.integration
class TestParquetExtractorSuccessfulExtraction:
    def test_extract_real_zip_file(self, tmp_path):
        zip_path = tmp_path / 'test_data.zip'

        csv_content = 'col1;col2;col3\n1;2;3\n4;5;6\n'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test.csv', csv_content)

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob('*.parquet'))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == 'test.parquet'

    def test_extract_multiple_csv_files(self, tmp_path):
        zip_path = tmp_path / 'multi_data.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(3):
                csv_content = f'col1;col2\n{i};{i + 1}\n'
                zf.writestr(f'test_{i}.csv', csv_content)

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob('*.parquet'))
        assert len(parquet_files) == 3

    def test_extract_nonexistent_zip_raises_error(self, tmp_path):
        extractor = ParquetExtractorAdapterCVM()
        nonexistent_zip = tmp_path / 'nonexistent.zip'

        with pytest.raises(ExtractionError):
            extractor.extract(str(nonexistent_zip), str(tmp_path))

    def test_extract_empty_zip_is_rejected_without_outputs(self, tmp_path):
        zip_path = tmp_path / 'empty.zip'

        with zipfile.ZipFile(zip_path, 'w'):
            pass

        extractor = ParquetExtractorAdapterCVM()
        with pytest.raises(ExtractionError, match='does not contain any CSV'):
            extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob('*.parquet'))
        assert len(parquet_files) == 0

    def test_extract_zip_with_non_csv_files(self, tmp_path):
        zip_path = tmp_path / 'mixed.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('data.csv', 'col1;col2\n1;2\n')
            zf.writestr('readme.txt', 'This is a readme')
            zf.writestr('image.png', b'\x89PNG\r\n')

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(str(zip_path), str(tmp_path))

        parquet_files = list(tmp_path.glob('*.parquet'))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == 'data.parquet'


@pytest.mark.unit
class TestParquetExtractorFileExtractorInterface:
    def test_implements_extract_method(self):
        extractor = ParquetExtractorAdapterCVM()
        assert hasattr(extractor, 'extract')
        assert callable(extractor.extract)


@pytest.mark.integration
class TestParquetExtractorRollbackAndTransactionalBehavior:
    def test_extract_partial_failure_triggers_atomic_rollback(
        self, tmp_path, monkeypatch
    ):
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / 'partial_fail.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('good.csv', 'col1;col2\n1;2\n')
            zf.writestr('bad.csv', 'col1;col2\n3;4\n')

        orig_extract_csv = (
            extractor.extractor_adapter.extract_csv_from_zip_to_parquet
        )

        def mock_extract_csv(z, parquet_path, parquet_filename, csv_filename):
            if csv_filename == 'bad.csv':
                raise ValueError('Malformed CSV data in bad.csv')
            return orig_extract_csv(
                z, parquet_path, parquet_filename, csv_filename
            )

        monkeypatch.setattr(
            extractor.extractor_adapter,
            'extract_csv_from_zip_to_parquet',
            mock_extract_csv,
        )

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(str(zip_path), str(tmp_path))

        assert 'Unexpected extraction error' in str(exc_info.value)
        assert 'bad.csv' in str(exc_info.value)
        # Ensure that good.parquet was rolled back and deleted
        remaining_parquets = list(tmp_path.glob('*.parquet'))
        assert len(remaining_parquets) == 0

    def test_extract_disk_full_error_propagates_and_cleans_up(
        self, tmp_path, monkeypatch
    ):
        from globaldatafinance.macro_exceptions import DiskFullError

        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / 'disk_full.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('doc.csv', 'a;b\n1;2\n')

        def mock_extract_disk_full(*_args, **_kwargs):
            raise DiskFullError('No space left on device')

        monkeypatch.setattr(
            extractor.extractor_adapter,
            'extract_csv_from_zip_to_parquet',
            mock_extract_disk_full,
        )

        with pytest.raises(DiskFullError):
            extractor.extract(str(zip_path), str(tmp_path))

        assert len(list(tmp_path.glob('*.parquet'))) == 0

    def test_extract_staging_failure_cleans_transaction_directory(
        self, tmp_path, monkeypatch
    ):
        """The public adapter does not leak hidden staging after failure."""
        extractor = ParquetExtractorAdapterCVM()
        zip_path = tmp_path / 'staging_cleanup.zip'

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('good.csv', 'col1;col2\n1;2\n')
            zf.writestr('bad.csv', 'col1;col2\n3;4\n')

        orig_extract_csv = (
            extractor.extractor_adapter.extract_csv_from_zip_to_parquet
        )

        def mock_extract_csv(z, parquet_path, parquet_filename, csv_filename):
            if csv_filename == 'bad.csv':
                raise ValueError('Forced error on bad.csv')
            return orig_extract_csv(
                z, parquet_path, parquet_filename, csv_filename
            )

        monkeypatch.setattr(
            extractor.extractor_adapter,
            'extract_csv_from_zip_to_parquet',
            mock_extract_csv,
        )

        with pytest.raises(ExtractionError) as exc_info:
            extractor.extract(str(zip_path), str(tmp_path))

        assert 'Unexpected extraction error' in str(exc_info.value)
        assert 'Forced error on bad.csv' in str(exc_info.value)
        assert list(tmp_path.glob('*.parquet')) == []
        assert list(tmp_path.glob('.globaldatafinance-cvm-staging-*')) == []
