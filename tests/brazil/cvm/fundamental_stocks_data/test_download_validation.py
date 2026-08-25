import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    download_validation,
)

pytestmark = pytest.mark.unit


def test_find_parquet_files(tmp_path: Path) -> None:
    sub_dir = tmp_path / 'nested' / 'dir'
    sub_dir.mkdir(parents=True)

    file1 = tmp_path / 'top.parquet'
    file2 = sub_dir / 'nested.parquet'
    file3 = tmp_path / 'other.txt'

    file1.touch()
    file2.touch()
    file3.touch()

    found = download_validation.find_parquet_files(str(tmp_path))
    assert len(found) == 2
    assert file1 in found
    assert file2 in found


def test_validate_parquet_files_valid_files(tmp_path: Path) -> None:
    p1 = tmp_path / 'file1.parquet'
    p2 = tmp_path / 'file2.parquet'

    pq.write_table(pa.table({'col': [1, 2, 3]}), str(p1))
    pq.write_table(pa.table({'col': [4, 5]}), str(p2))

    assert (
        download_validation.validate_parquet_files([p1, p2], 'dfp', '2023')
        is True
    )


def test_validate_parquet_files_empty_zero_bytes(tmp_path: Path) -> None:
    empty_file = tmp_path / 'zero_bytes.parquet'
    empty_file.touch()

    assert (
        download_validation.validate_parquet_files([empty_file], 'dfp', '2023')
        is False
    )


def test_validate_parquet_files_zero_rows_logs_warning_and_returns_true(
    tmp_path: Path,
) -> None:
    p = tmp_path / 'zero_rows.parquet'
    pq.write_table(pa.table({'col': pa.array([], type=pa.int64())}), str(p))

    assert (
        download_validation.validate_parquet_files([p], 'dfp', '2023') is True
    )


def test_validate_parquet_files_corrupted_file(tmp_path: Path) -> None:
    corrupt = tmp_path / 'corrupt.parquet'
    corrupt.write_text('not a real parquet')

    assert (
        download_validation.validate_parquet_files([corrupt], 'dfp', '2023')
        is False
    )


def test_validate_parquet_files_when_pyarrow_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(download_validation, 'pq', None)
    file = tmp_path / 'dummy.parquet'
    file.touch()

    # When pq is None, content validation is skipped and returns True
    assert (
        download_validation.validate_parquet_files([file], 'dfp', '2023')
        is True
    )


def test_validate_parquet_files_unexpected_outer_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Pass an object where iterating over parquet_files raises an exception
    bad_list = MagicMock()
    bad_list.__iter__.side_effect = RuntimeError(
        'Unexpected error in validation loop'
    )

    assert (
        download_validation.validate_parquet_files(bad_list, 'dfp', '2023')
        is False
    )


def test_has_valid_zip_contents_corrupt_zip(tmp_path: Path) -> None:
    corrupt_zip = tmp_path / 'bad.zip'
    corrupt_zip.write_text('not a zip')

    assert (
        download_validation._has_valid_zip_contents(str(corrupt_zip)) is False
    )


def test_has_valid_zip_contents_empty_zip(tmp_path: Path) -> None:
    empty_zip = tmp_path / 'empty.zip'
    with zipfile.ZipFile(empty_zip, 'w'):
        pass

    assert download_validation._has_valid_zip_contents(str(empty_zip)) is False


def test_has_valid_zip_contents_no_csv(tmp_path: Path) -> None:
    no_csv_zip = tmp_path / 'no_csv.zip'
    with zipfile.ZipFile(no_csv_zip, 'w') as zf:
        zf.writestr('doc.txt', 'hello')

    # Logs warning but returns True because it is a valid zip
    assert download_validation._has_valid_zip_contents(str(no_csv_zip)) is True


def test_validate_downloaded_file_nonexistent() -> None:
    assert (
        download_validation.validate_downloaded_file(
            '/path/that/does/not/exist.zip'
        )
        is False
    )


def test_validate_downloaded_file_size_check_fail(tmp_path: Path) -> None:
    zip_path = tmp_path / 'test.zip'
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('file.csv', 'a;b\n1;2\n')

    actual_size = zip_path.stat().st_size
    # Size difference > 5%
    assert (
        download_validation.validate_downloaded_file(
            str(zip_path), expected_size=int(actual_size * 1.5)
        )
        is False
    )
