"""Validation helpers for CVM downloaded files."""

import zipfile
from pathlib import Path

try:
    import pyarrow.parquet as pq
except ImportError:
    pq = None  # type: ignore[assignment]

from ....core import get_logger

logger = get_logger(__name__)


def validate_downloaded_file(
    filepath: str, expected_size: int | None = None
) -> bool:
    """Validate that a downloaded ZIP is present, complete, and readable."""
    try:
        path = Path(filepath)

        if not path.exists():
            logger.error('Downloaded file does not exist: %s', filepath)
            return False

        if expected_size is not None and not _has_valid_size(
            path, expected_size
        ):
            return False

        return _has_valid_zip_contents(filepath)

    except Exception as e:
        logger.error('Error validating file %s: %s', filepath, e)
        return False


def find_parquet_files(dest_path: str) -> list[Path]:
    return list(Path(dest_path).glob('**/*.parquet'))


def validate_parquet_files(
    parquet_files: list[Path], doc_name: str, year: str
) -> bool:
    """Validate that parquet files are readable and contain data."""
    if pq is None:
        logger.warning(
            'pyarrow not available for parquet validation, '
            'skipping content check'
        )
        return True

    try:
        valid_files = 0
        for parquet_file in parquet_files:
            try:
                file_size = parquet_file.stat().st_size
                if file_size == 0:
                    logger.error(
                        'Empty parquet file (0 bytes): %s for %s_%s',
                        parquet_file,
                        doc_name,
                        year,
                    )
                    return False

                table = pq.read_table(str(parquet_file))

                if table.num_rows == 0:
                    logger.warning(
                        'Parquet file has no data rows: %s for %s_%s',
                        parquet_file,
                        doc_name,
                        year,
                    )

                valid_files += 1
                logger.debug(
                    'Parquet validated: %s (%d rows, %d bytes)',
                    parquet_file.name,
                    table.num_rows,
                    file_size,
                )

            except Exception as e:
                logger.error(
                    'Invalid parquet %s for %s_%s: %s: %s',
                    parquet_file,
                    doc_name,
                    year,
                    type(e).__name__,
                    e,
                )
                return False

        logger.info(
            'All %d parquet files validated for %s_%s',
            valid_files,
            doc_name,
            year,
        )
        return True

    except Exception as e:
        logger.error('Unexpected error validating parquets: %s', e)
        return False


def _has_valid_size(path: Path, expected_size: int) -> bool:
    actual_size = path.stat().st_size
    size_diff = abs(actual_size - expected_size)
    size_diff_pct = (
        (size_diff / expected_size) * 100 if expected_size > 0 else 0
    )

    if size_diff_pct > 5.0:
        logger.error(
            'File size mismatch for %s: expected %d bytes, got %d bytes (%.1f%% difference)',
            path,
            expected_size,
            actual_size,
            size_diff_pct,
        )
        return False

    logger.debug(
        'File size validation passed: %d bytes (expected %d, diff %.2f%%)',
        actual_size,
        expected_size,
        size_diff_pct,
    )
    return True


def _has_valid_zip_contents(filepath: str) -> bool:
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_file:
            bad_file = zip_file.testzip()
            if bad_file:
                logger.error(
                    'Corrupted file in ZIP: %s (%s)', bad_file, filepath
                )
                return False

            namelist = zip_file.namelist()
            if not namelist:
                logger.error('Empty ZIP file: %s', filepath)
                return False

            csv_files = [n for n in namelist if n.lower().endswith('.csv')]
            if not csv_files:
                logger.warning(
                    'No CSV files in ZIP: %s. Files found: %s%s',
                    filepath,
                    ', '.join(namelist[:5]),
                    '...' if len(namelist) > 5 else '',
                )

    except zipfile.BadZipFile as e:
        logger.error('Invalid ZIP file: %s - %s', filepath, e)
        return False

    logger.debug('File validation passed: %s', filepath)
    return True
