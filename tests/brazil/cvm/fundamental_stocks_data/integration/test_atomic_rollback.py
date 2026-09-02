"""Failure-atomic CVM batch extraction regressions with real Parquet files."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data import transaction
from globaldatafinance.brazil.cvm.fundamental_stocks_data.extract import (
    ParquetExtractorAdapterCVM,
)
from globaldatafinance.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
)
from tests.support.builders import csv_bytes, write_zip

pytestmark = pytest.mark.integration


def _write_csv_archive(
    archive_path: Path, members: dict[str, list[str]]
) -> Path:
    """Create a deterministic CSV ZIP from named semicolon-delimited rows."""
    return write_zip(
        archive_path,
        {
            filename: csv_bytes(rows, encoding='latin-1')
            for filename, rows in members.items()
        },
    )


def _parquet_bytes(path: Path) -> bytes:
    """Read bytes so rollback assertions prove exact existing-file recovery."""
    return path.read_bytes()


def _transaction_dirs(destination: Path) -> list[Path]:
    """Return any leaked normal or recovery transaction directories."""
    return sorted(destination.glob('.globaldatafinance-cvm-staging-*'))


def test_corrupted_input_preserves_existing_output(tmp_path: Path) -> None:
    """An invalid ZIP changes neither old data nor transaction state."""
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    sentinel = output_dir / 'sentinel.parquet'
    pd.DataFrame({'id': [1], 'state': ['keep']}).to_parquet(sentinel)
    expected_bytes = _parquet_bytes(sentinel)
    corrupted_input = tmp_path / 'corrupted.zip'
    corrupted_input.write_bytes(b'not a ZIP archive')

    with pytest.raises(CorruptedZipError):
        ParquetExtractorAdapterCVM().extract(
            source_path=str(corrupted_input), destination_path=str(output_dir)
        )

    assert _parquet_bytes(sentinel) == expected_bytes
    assert _transaction_dirs(output_dir) == []


def test_staging_failure_does_not_publish_first_member_or_modify_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A later conversion failure leaves all final paths exactly untouched."""
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    existing = output_dir / 'first.parquet'
    pd.DataFrame({'version': ['old']}).to_parquet(existing)
    expected_bytes = _parquet_bytes(existing)
    archive_path = _write_csv_archive(
        tmp_path / 'staging-failure.zip',
        {
            'first.csv': ['version', 'new'],
            'second.csv': ['version', 'second'],
        },
    )
    extractor = ParquetExtractorAdapterCVM()
    original_extract = (
        extractor.extractor_adapter.extract_csv_from_zip_to_parquet
    )

    def fail_second_csv(
        archive: zipfile.ZipFile,
        parquet_path: Path,
        parquet_filename: str,
        csv_filename: str,
    ) -> None:
        if csv_filename == 'second.csv':
            assert not (output_dir / 'second.parquet').exists()
            raise ExtractionError(str(archive_path), 'second CSV is invalid')
        original_extract(archive, parquet_path, parquet_filename, csv_filename)

    monkeypatch.setattr(
        extractor.extractor_adapter,
        'extract_csv_from_zip_to_parquet',
        fail_second_csv,
    )

    with pytest.raises(ExtractionError, match='second CSV is invalid'):
        extractor.extract(str(archive_path), str(output_dir))

    assert _parquet_bytes(existing) == expected_bytes
    assert not (output_dir / 'second.parquet').exists()
    assert _transaction_dirs(output_dir) == []


def test_disk_full_during_staging_preserves_existing_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disk exhaustion before commit cannot delete or overwrite old Parquet."""
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    existing = output_dir / 'data.parquet'
    pd.DataFrame({'version': ['old']}).to_parquet(existing)
    expected_bytes = _parquet_bytes(existing)
    archive_path = _write_csv_archive(
        tmp_path / 'disk-full.zip', {'data.csv': ['version', 'new']}
    )
    extractor = ParquetExtractorAdapterCVM()

    def fail_disk(*_args: object, **_kwargs: object) -> None:
        raise DiskFullError(str(output_dir))

    monkeypatch.setattr(
        extractor.extractor_adapter,
        'extract_csv_from_zip_to_parquet',
        fail_disk,
    )

    with pytest.raises(DiskFullError):
        extractor.extract(str(archive_path), str(output_dir))

    assert _parquet_bytes(existing) == expected_bytes
    assert _transaction_dirs(output_dir) == []


@pytest.mark.parametrize('failure_call', [1, 2])
def test_commit_replace_failure_restores_all_preexisting_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_call: int,
) -> None:
    """First and later replacement failures restore byte-identical old data."""
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    first = output_dir / 'first.parquet'
    second = output_dir / 'second.parquet'
    pd.DataFrame({'version': ['first-old']}).to_parquet(first)
    pd.DataFrame({'version': ['second-old']}).to_parquet(second)
    expected_first = _parquet_bytes(first)
    expected_second = _parquet_bytes(second)
    archive_path = _write_csv_archive(
        tmp_path / 'replace-failure.zip',
        {
            'first.csv': ['version', 'first-new'],
            'second.csv': ['version', 'second-new'],
        },
    )
    original_replace = os.replace
    replace_calls = 0

    def fail_selected_replace(
        source: str | os.PathLike[str],
        destination: str | os.PathLike[str],
    ) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == failure_call:
            raise OSError('simulated replace failure')
        original_replace(source, destination)

    monkeypatch.setattr(transaction.os, 'replace', fail_selected_replace)

    with pytest.raises(
        ExtractionError, match='all modified outputs were restored'
    ):
        ParquetExtractorAdapterCVM().extract(
            str(archive_path), str(output_dir)
        )

    assert _parquet_bytes(first) == expected_first
    assert _parquet_bytes(second) == expected_second
    assert _transaction_dirs(output_dir) == []


def test_commit_replaces_conflicts_and_creates_new_outputs(
    tmp_path: Path,
) -> None:
    """A successful batch commits old conflicts and new files together."""
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    pd.DataFrame({'version': ['old']}).to_parquet(output_dir / 'first.parquet')
    archive_path = _write_csv_archive(
        tmp_path / 'success.zip',
        {
            'first.csv': ['version', 'new'],
            'second.csv': ['version', 'created'],
        },
    )

    ParquetExtractorAdapterCVM().extract(str(archive_path), str(output_dir))

    assert pd.read_parquet(output_dir / 'first.parquet')[
        'version'
    ].tolist() == ['new']
    assert pd.read_parquet(output_dir / 'second.parquet')[
        'version'
    ].tolist() == ['created']
    assert _transaction_dirs(output_dir) == []


def test_basename_collision_is_rejected_before_staging(tmp_path: Path) -> None:
    """Two CSV paths mapping to one output cannot partially publish."""
    archive_path = _write_csv_archive(
        tmp_path / 'collision.zip',
        {
            'one/data.csv': ['version', 'one'],
            'two/data.csv': ['version', 'two'],
        },
    )

    with pytest.raises(ExtractionError, match='collide after basename'):
        ParquetExtractorAdapterCVM().extract(str(archive_path), str(tmp_path))

    assert not (tmp_path / 'data.parquet').exists()
    assert _transaction_dirs(tmp_path) == []


def test_failed_restore_preserves_recovery_directory(
    tmp_path: Path, monkeypatch
) -> None:
    """A failed rollback reports its retained backup path safely."""
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    first = output_dir / 'first.parquet'
    second = output_dir / 'second.parquet'
    pd.DataFrame({'version': ['first-old']}).to_parquet(first)
    pd.DataFrame({'version': ['second-old']}).to_parquet(second)
    archive_path = _write_csv_archive(
        tmp_path / 'restore-failure.zip',
        {
            'first.csv': ['version', 'first-new'],
            'second.csv': ['version', 'second-new'],
        },
    )
    original_replace = os.replace
    replace_calls = 0

    def fail_commit_and_restore(
        source: str | os.PathLike[str],
        destination: str | os.PathLike[str],
    ) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls in {2, 3}:
            raise OSError('simulated restore failure')
        original_replace(source, destination)

    monkeypatch.setattr(transaction.os, 'replace', fail_commit_and_restore)

    with pytest.raises(
        ExtractionError, match='Recovery directory preserved'
    ) as error:
        ParquetExtractorAdapterCVM().extract(
            str(archive_path), str(output_dir)
        )

    recovery_dirs = _transaction_dirs(output_dir)
    assert len(recovery_dirs) == 1
    assert (recovery_dirs[0] / 'backups' / 'first.parquet').exists()
    assert str(recovery_dirs[0]) in str(error.value)
