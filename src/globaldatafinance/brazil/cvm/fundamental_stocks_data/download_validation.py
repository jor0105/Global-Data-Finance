"""Validation helpers for CVM downloaded files."""

import zipfile
from pathlib import Path

from ....core import get_logger

logger = get_logger(__name__)


def validate_downloaded_file(
    filepath: str, expected_size: int | None = None
) -> bool:
    """Validate that a downloaded ZIP is present, complete, and readable."""
    try:
        path = Path(filepath)

        if not path.exists():
            logger.error(f'Downloaded file does not exist: {filepath}')
            return False

        if expected_size is not None and not _has_valid_size(
            path, expected_size
        ):
            return False

        return _has_valid_zip_contents(filepath)

    except Exception as e:
        logger.error(f'Error validating file {filepath}: {e}')
        return False


def find_parquet_files(dest_path: str) -> list[Path]:
    return list(Path(dest_path).glob('**/*.parquet'))


def validate_parquet_files(
    parquet_files: list[Path], doc_name: str, year: str
) -> bool:
    """Validate that parquet files are readable and contain data."""
    try:
        import pyarrow.parquet as pq

        valid_files = 0
        for parquet_file in parquet_files:
            try:
                file_size = parquet_file.stat().st_size
                if file_size == 0:
                    logger.error(
                        f'Empty parquet file (0 bytes): {parquet_file} '
                        f'for {doc_name}_{year}'
                    )
                    return False

                table = pq.read_table(str(parquet_file))

                if table.num_rows == 0:
                    logger.warning(
                        f'Parquet file has no data rows: {parquet_file} '
                        f'for {doc_name}_{year}'
                    )

                valid_files += 1
                logger.debug(
                    f'Parquet validated: {parquet_file.name} '
                    f'({table.num_rows:,} rows, {file_size:,} bytes)'
                )

            except Exception as e:
                logger.error(
                    f'Invalid parquet {parquet_file} for {doc_name}_{year}: '
                    f'{type(e).__name__}: {e}'
                )
                return False

        logger.info(
            f'All {valid_files} parquet files validated for {doc_name}_{year}'
        )
        return True

    except ImportError:
        logger.warning(
            'pyarrow not available for parquet validation, '
            'skipping content check'
        )
        return True
    except Exception as e:
        logger.error(f'Unexpected error validating parquets: {e}')
        return False


def _has_valid_size(path: Path, expected_size: int) -> bool:
    actual_size = path.stat().st_size
    size_diff = abs(actual_size - expected_size)
    size_diff_pct = (
        (size_diff / expected_size) * 100 if expected_size > 0 else 0
    )

    if size_diff_pct > 5.0:
        logger.error(
            f'File size mismatch for {path}: '
            f'expected {expected_size:,} bytes, '
            f'got {actual_size:,} bytes '
            f'({size_diff_pct:.1f}% difference)'
        )
        return False

    logger.debug(
        f'File size validation passed: {actual_size:,} bytes '
        f'(expected {expected_size:,}, diff {size_diff_pct:.2f}%)'
    )
    return True


def _has_valid_zip_contents(filepath: str) -> bool:
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_file:
            bad_file = zip_file.testzip()
            if bad_file:
                logger.error(f'Corrupted file in ZIP: {bad_file} ({filepath})')
                return False

            namelist = zip_file.namelist()
            if not namelist:
                logger.error(f'Empty ZIP file: {filepath}')
                return False

            csv_files = [n for n in namelist if n.lower().endswith('.csv')]
            if not csv_files:
                logger.warning(
                    f'No CSV files in ZIP: {filepath}. '
                    f'Files found: {", ".join(namelist[:5])}'
                    f'{"..." if len(namelist) > 5 else ""}'
                )

    except zipfile.BadZipFile as e:
        logger.error(f'Invalid ZIP file: {filepath} - {e}')
        return False

    logger.debug(f'File validation passed: {filepath} ')
    return True
