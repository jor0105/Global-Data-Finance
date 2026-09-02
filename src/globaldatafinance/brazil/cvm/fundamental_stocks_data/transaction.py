"""Failure-atomic batch commit for CVM CSV-to-Parquet extraction.

Multiple output files cannot become visible in one filesystem operation. This
module instead guarantees a recoverable batch: every input is converted in a
hidden staging directory, existing outputs are backed up before commit, and a
failed replacement restores earlier targets in reverse order.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ....core import get_logger
from ....core.archive_safety import (
    validate_zip_archive,
    validate_zip_crc_with_limits,
)
from ....core.utils import assert_path_not_sensitive
from ....macro_exceptions import CorruptedZipError, ExtractionError
from ....macro_infra import ExtractorAdapter
from .download_validation import validate_parquet_files

logger = get_logger(__name__)


@dataclass(frozen=True)
class _StagedOutput:
    """One source CSV and its staged and final Parquet locations."""

    csv_filename: str
    parquet_filename: str
    staged_path: Path
    destination_path: Path


class CvmFailureAtomicBatchCommit:
    """Convert a validated CVM archive and commit all outputs recoverably."""

    _STAGING_PREFIX = '.globaldatafinance-cvm-staging-'

    def __init__(
        self,
        source_path: str,
        destination_path: str,
        extractor_adapter: ExtractorAdapter,
    ) -> None:
        """Store the already-owned generic converter and target boundary."""
        self.source_path = source_path
        self._raw_destination_path = destination_path
        self.destination_dir = Path(destination_path)
        self.extractor_adapter = extractor_adapter

    def execute(self, zip_file: zipfile.ZipFile) -> int:
        """Stage and commit one validated archive deterministically."""
        self._validate_destination()
        outputs = self._build_outputs(zip_file)
        staging_dir = Path(
            tempfile.mkdtemp(
                prefix=self._STAGING_PREFIX,
                dir=self.destination_dir,
            )
        )
        preserve_staging = False

        try:
            staged_outputs = self._stage_outputs(
                zip_file, outputs, staging_dir
            )
            self._validate_staged_outputs(staged_outputs)
            self._commit_outputs(staged_outputs, staging_dir)
        except Exception as error:
            preserve_staging = isinstance(error, _RecoveryPreservedError)
            if preserve_staging:
                raise ExtractionError(
                    self.source_path,
                    str(error),
                ) from error.__cause__
            raise
        finally:
            if not preserve_staging:
                self._cleanup_staging(staging_dir)

        return len(outputs)

    def _validate_destination(self) -> None:
        """Require a caller-approved directory before creating state."""
        self.destination_dir = self.destination_dir.expanduser().resolve()
        assert_path_not_sensitive(
            self.destination_dir,
            raw_input=self._raw_destination_path,
        )
        if (
            not self.destination_dir.exists()
            or not self.destination_dir.is_dir()
        ):
            raise ExtractionError(
                self.source_path,
                'Destination directory does not exist or is not a directory: '
                f'{self.destination_dir}',
            )

    def _build_outputs(self, zip_file: zipfile.ZipFile) -> list[_StagedOutput]:
        """Validate every CSV member and reject collisions before any write."""
        try:
            infos = validate_zip_archive(self.source_path, zip_file)
            validate_zip_crc_with_limits(
                self.source_path, zip_file, infos=infos
            )
        except zipfile.BadZipFile as error:
            raise CorruptedZipError(self.source_path, str(error)) from error

        csv_members = [
            info.filename
            for info in infos
            if not info.is_dir() and info.filename.lower().endswith('.csv')
        ]
        if not csv_members:
            raise ExtractionError(
                self.source_path, 'Archive does not contain any CSV members'
            )

        output_names: set[str] = set()
        outputs: list[_StagedOutput] = []
        for csv_filename in sorted(csv_members, key=str.casefold):
            parquet_filename = self._parquet_basename(csv_filename)
            normalized_name = parquet_filename.casefold()
            if normalized_name in output_names:
                raise ExtractionError(
                    self.source_path,
                    'CSV members collide after basename normalization: '
                    f'{csv_filename!r} -> {parquet_filename!r}',
                )
            output_names.add(normalized_name)
            outputs.append(
                _StagedOutput(
                    csv_filename=csv_filename,
                    parquet_filename=parquet_filename,
                    staged_path=Path(),
                    destination_path=self.destination_dir / parquet_filename,
                )
            )
        return outputs

    @staticmethod
    def _parquet_basename(csv_filename: str) -> str:
        """Derive the established basename-only Parquet output name."""
        posix_name = PurePosixPath(csv_filename.replace('\\', '/')).name
        return f'{PurePosixPath(posix_name).stem}.parquet'

    def _stage_outputs(
        self,
        zip_file: zipfile.ZipFile,
        outputs: list[_StagedOutput],
        staging_dir: Path,
    ) -> list[_StagedOutput]:
        """Convert every CSV only inside the hidden transaction directory."""
        staged_outputs: list[_StagedOutput] = []
        for output in outputs:
            staged_path = staging_dir / output.parquet_filename
            self.extractor_adapter.extract_csv_from_zip_to_parquet(
                zip_file,
                staged_path,
                output.parquet_filename,
                output.csv_filename,
            )
            staged_outputs.append(
                _StagedOutput(
                    csv_filename=output.csv_filename,
                    parquet_filename=output.parquet_filename,
                    staged_path=staged_path,
                    destination_path=output.destination_path,
                )
            )
        return staged_outputs

    def _validate_staged_outputs(self, outputs: list[_StagedOutput]) -> None:
        """Require nonempty Parquet footers before final targets can change."""
        parquet_files = [output.staged_path for output in outputs]
        if not validate_parquet_files(
            parquet_files, 'staged_cvm_batch', 'transaction'
        ):
            raise ExtractionError(
                self.source_path,
                'Staged Parquet validation failed before batch commit',
            )

    def _commit_outputs(
        self,
        outputs: list[_StagedOutput],
        staging_dir: Path,
    ) -> None:
        """Backup old targets then replace outputs in deterministic order."""
        ordered_outputs = sorted(
            outputs, key=lambda output: output.parquet_filename.casefold()
        )
        backup_dir = staging_dir / 'backups'
        backups = self._create_backups(ordered_outputs, backup_dir)
        committed: list[_StagedOutput] = []

        try:
            for output in ordered_outputs:
                output.staged_path.replace(output.destination_path)
                committed.append(output)
        except Exception as original_error:
            restoration_errors = self._restore_outputs(committed, backups)
            if restoration_errors:
                raise _RecoveryPreservedError(
                    staging_dir=staging_dir,
                    original_error=original_error,
                    restoration_errors=restoration_errors,
                ) from original_error
            raise ExtractionError(
                self.source_path,
                'Failure-atomic batch commit failed and all modified outputs '
                f'were restored: {type(original_error).__name__}: '
                f'{original_error}',
            ) from original_error

    def _create_backups(
        self,
        outputs: list[_StagedOutput],
        backup_dir: Path,
    ) -> dict[Path, Path]:
        """Create hard-link backups and copy only when linking fails."""
        existing_outputs = [
            output for output in outputs if output.destination_path.exists()
        ]
        if not existing_outputs:
            return {}

        backup_dir.mkdir()
        backups: dict[Path, Path] = {}
        for output in existing_outputs:
            backup_path = backup_dir / output.parquet_filename
            try:
                os.link(output.destination_path, backup_path)
            except OSError:
                shutil.copy2(output.destination_path, backup_path)
            backups[output.destination_path] = backup_path
        return backups

    def _restore_outputs(
        self,
        committed: list[_StagedOutput],
        backups: dict[Path, Path],
    ) -> list[str]:
        """Restore committed targets in reverse order and collect failures."""
        restoration_errors: list[str] = []
        for output in reversed(committed):
            try:
                backup_path = backups.get(output.destination_path)
                if backup_path is not None:
                    backup_path.replace(output.destination_path)
                elif output.destination_path.exists():
                    output.destination_path.unlink()
            except OSError as error:
                restoration_errors.append(
                    f'{output.destination_path}: '
                    f'{type(error).__name__}: {error}'
                )
        return restoration_errors

    @staticmethod
    def _cleanup_staging(staging_dir: Path) -> None:
        """Remove transaction state after normal success or rollback."""
        try:
            shutil.rmtree(staging_dir)
        except OSError as error:
            logger.error(
                'Could not remove completed CVM transaction directory %s: %s',
                staging_dir,
                error,
                exc_info=True,
            )


class _RecoveryPreservedError(Exception):
    """Internal signal that a recovery directory is the remaining safe copy."""

    def __init__(
        self,
        *,
        staging_dir: Path,
        original_error: Exception,
        restoration_errors: list[str],
    ) -> None:
        """Describe the committed failure without losing recovery evidence."""
        details = '; '.join(restoration_errors)
        super().__init__(
            'Failure-atomic batch commit could not fully restore outputs. '
            f'Recovery directory preserved at {staging_dir}. '
            f'Original error: {type(original_error).__name__}: '
            f'{original_error}. Restoration errors: {details}'
        )
