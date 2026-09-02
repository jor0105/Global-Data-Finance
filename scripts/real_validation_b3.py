"""Execute and validate one real COTAHIST case through the B3 facade."""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow.parquet as pq
from polars.testing import assert_frame_equal

from globaldatafinance import HistoricalQuotesB3
from globaldatafinance.brazil.b3_data.historical_quotes.catalog import (
    validate_cotahist_input,
)

from .real_validation_types import ValidationCase
from .real_validation_utils import failed_details, temporary_paths

B3_SCHEMA = {
    'data_pregao': pl.Date,
    'codigo_bdi': pl.String,
    'ticker': pl.String,
    'tipo_mercado': pl.String,
    'nome_resumido': pl.String,
    'especificacao_papel': pl.String,
    'preco_abertura': pl.Decimal(precision=38, scale=2),
    'preco_maximo': pl.Decimal(precision=38, scale=2),
    'preco_minimo': pl.Decimal(precision=38, scale=2),
    'preco_medio': pl.Decimal(precision=38, scale=2),
    'preco_fechamento': pl.Decimal(precision=38, scale=2),
    'melhor_oferta_compra': pl.Decimal(precision=38, scale=2),
    'melhor_oferta_venda': pl.Decimal(precision=38, scale=2),
    'numero_negocios': pl.Int64,
    'quantidade_total': pl.Int64,
    'volume_total': pl.Decimal(precision=38, scale=2),
    'data_vencimento': pl.Date,
    'fator_cotacao': pl.Int64,
    'codigo_isin': pl.String,
    'numero_distribuicao': pl.Int64,
}
_SORT_COLUMNS = list(B3_SCHEMA)
_FRAME_COMPARE_LIMIT = 256 * 1024 * 1024
_DIGEST_BATCH_SIZE = 100_000
_DIGEST_MODULUS = 1 << 256


def execute_cotahist_case(
    case: ValidationCase, workspace: Path
) -> dict[str, Any]:
    """Run fast or complete fast/slow parity for one annual archive."""
    input_path = Path(case.input_path)
    validate_cotahist_input(input_path)
    if case.mode == 'parity':
        return _execute_parity(case, input_path, workspace)
    result, details = _execute_mode(
        input_path, case.year, case.mode, workspace / 'fast'
    )
    if not details['valid']:
        return failed_details(result, details['message'])
    return _passed_details(result, details, 'COTAHIST fast extraction passed')


def _execute_mode(
    input_path: Path, year: int, mode: str, output_directory: Path
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    output_directory.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(
        HistoricalQuotesB3().extract_async(
            path_of_docs=str(input_path.parent),
            assets_list=['ações'],
            initial_year=year,
            last_year=year,
            destination_path=str(output_directory),
            output_filename='cotahist',
            processing_mode=mode,
            verbose=False,
        )
    )
    return result, _validate_result(result, output_directory, year)


def _execute_parity(
    case: ValidationCase, input_path: Path, workspace: Path
) -> dict[str, Any]:
    fast_result, fast_details = _execute_mode(
        input_path, case.year, 'fast', workspace / 'fast'
    )
    slow_result, slow_details = _execute_mode(
        input_path, case.year, 'slow', workspace / 'slow'
    )
    public_result = {'fast': fast_result, 'slow': slow_result}
    if not fast_details['valid']:
        return failed_details(public_result, fast_details['message'])
    if not slow_details['valid']:
        return failed_details(public_result, slow_details['message'])
    if fast_details['record_count'] != slow_details['record_count']:
        return failed_details(public_result, 'fast/slow row count mismatch')
    if fast_details['schema'] != slow_details['schema']:
        return failed_details(public_result, 'fast/slow schema mismatch')
    if fast_details['date_range'] != slow_details['date_range']:
        return failed_details(public_result, 'fast/slow date range mismatch')
    try:
        comparison_method = _compare_content(
            Path(fast_result['output_file']),
            Path(slow_result['output_file']),
        )
    except (AssertionError, OSError, RuntimeError, ValueError) as error:
        return failed_details(public_result, f'fast/slow mismatch: {error}')
    artifacts = [
        *[dict(item, mode='fast') for item in fast_details['artifacts']],
        *[dict(item, mode='slow') for item in slow_details['artifacts']],
    ]
    return {
        'status': 'passed',
        'message': (
            f'COTAHIST full fast/slow parity passed ({comparison_method})'
        ),
        'publicResult': public_result,
        'published': True,
        'artifactCount': len(artifacts),
        'artifacts': artifacts,
        'recordCount': fast_details['record_count'],
        'schema': fast_details['schema'],
        'dateRange': fast_details['date_range'],
        'comparisonMethod': comparison_method,
    }


def _validate_result(
    result: Mapping[str, Any], output_directory: Path, year: int
) -> dict[str, Any]:
    public_error = _validate_public_result(result)
    if public_error:
        return {'valid': False, 'message': public_error}
    output_path = Path(str(result['output_file']))
    if not output_path.is_file() or output_path.stat().st_size == 0:
        return {
            'valid': False,
            'message': 'B3 Parquet output is missing or empty',
        }
    if output_path.parent != output_directory.resolve():
        return {'valid': False, 'message': 'B3 output escaped its directory'}
    parquet_files = sorted(output_directory.glob('*.parquet'))
    if parquet_files != [output_path]:
        return {'valid': False, 'message': 'B3 output file count is not one'}
    frame_error = _validate_frame(output_path, result, year)
    if frame_error:
        return {'valid': False, 'message': frame_error}
    metadata_error = _validate_metadata(output_path)
    if metadata_error:
        return {'valid': False, 'message': metadata_error}
    temporary = temporary_paths(output_directory)
    if temporary:
        return {
            'valid': False,
            'message': f'B3 temporary files leaked: {temporary}',
        }
    try:
        date_range = _date_range(output_path)
    except (OSError, RuntimeError, ValueError, TypeError) as error:
        return {
            'valid': False,
            'message': f'B3 date validation failed: {error}',
        }
    return {
        'valid': True,
        'message': '',
        'record_count': int(result['total_records']),
        'schema': {name: str(dtype) for name, dtype in B3_SCHEMA.items()},
        'date_range': date_range,
        'artifacts': [
            {
                'path': output_path.name,
                'sizeBytes': output_path.stat().st_size,
                'rows': int(result['total_records']),
                'pyarrowReadable': True,
                'metadataPresent': True,
            }
        ],
    }


def _validate_public_result(result: Mapping[str, Any]) -> str | None:
    """Validate the public B3 result counters before inspecting its file."""
    required = (
        result.get('success') is True,
        result.get('total_files') == 1,
        result.get('success_count') == 1,
        result.get('error_count') == 0,
        result.get('total_records', 0) > 0,
        result.get('errors') == {},
    )
    if not all(required):
        return 'public B3 result is unsuccessful'
    return None


def _validate_frame(
    output_path: Path, result: Mapping[str, Any], year: int
) -> str | None:
    """Validate schema, content counters, dates, tickers, and markets."""
    try:
        scan = pl.scan_parquet(output_path)
        if scan.collect_schema() != B3_SCHEMA:
            return 'B3 schema mismatch'
        observed = scan.select(
            pl.len().alias('row_count'),
            pl.col('data_pregao').min().alias('first_date'),
            pl.col('data_pregao').max().alias('last_date'),
            pl.col('ticker').str.len_chars().min().alias('shortest_ticker'),
            pl.col('tipo_mercado')
            .is_in(['010', '020'])
            .sum()
            .alias('markets'),
        ).collect(engine='streaming')
        if observed['row_count'][0] != result['total_records']:
            return 'B3 row count mismatch'
        first_date = observed['first_date'][0]
        last_date = observed['last_date'][0]
        if first_date is None or last_date is None:
            return 'B3 date range is empty'
        if first_date.year != year or last_date.year != year:
            return 'B3 dates have wrong year'
        if observed['shortest_ticker'][0] <= 0 or observed['markets'][0] <= 0:
            return 'B3 ticker or market validation failed'
    except (OSError, RuntimeError, ValueError, TypeError) as error:
        return f'B3 artifact validation failed: {error}'
    return None


def _validate_metadata(output_path: Path) -> str | None:
    """Validate positive row metadata through PyArrow."""
    try:
        metadata = pq.ParquetFile(output_path).metadata
    except (OSError, RuntimeError, ValueError, TypeError) as error:
        return f'B3 Parquet metadata validation failed: {error}'
    if metadata is None or metadata.num_rows <= 0:
        return 'B3 Parquet metadata is invalid'
    return None


def _date_range(output_path: Path) -> tuple[str, str]:
    """Return the complete output date range in a report-safe form."""
    observed = (
        pl.scan_parquet(output_path)
        .select(
            pl.col('data_pregao').min().alias('first_date'),
            pl.col('data_pregao').max().alias('last_date'),
        )
        .collect(engine='streaming')
    )
    first_date = observed['first_date'][0]
    last_date = observed['last_date'][0]
    if first_date is None or last_date is None:
        raise ValueError('B3 date range is empty')
    return first_date.isoformat(), last_date.isoformat()


def _passed_details(
    result: Mapping[str, Any], details: Mapping[str, Any], message: str
) -> dict[str, Any]:
    return {
        'status': 'passed',
        'message': message,
        'publicResult': dict(result),
        'published': True,
        'artifactCount': len(details['artifacts']),
        'artifacts': details['artifacts'],
        'recordCount': details['record_count'],
        'schema': details['schema'],
        'dateRange': details['date_range'],
    }


def _compare_content(fast_path: Path, slow_path: Path) -> str:
    if max(fast_path.stat().st_size, slow_path.stat().st_size) <= (
        _FRAME_COMPARE_LIMIT
    ):
        assert_frame_equal(
            _canonical_frame(fast_path),
            _canonical_frame(slow_path),
            check_dtypes=True,
        )
        return 'full_frame'
    if _canonical_digest(fast_path) != _canonical_digest(slow_path):
        raise AssertionError('canonical content digest mismatch')
    return 'order_independent_batch_digest'


def _canonical_frame(path: Path) -> pl.DataFrame:
    return (
        pl.scan_parquet(path).sort(_SORT_COLUMNS).collect(engine='streaming')
    )


def _canonical_digest(path: Path) -> str:
    """Hash all rows in bounded batches without depending on row order."""
    parquet = pq.ParquetFile(path)
    schema = '|'.join(
        f'{field.name}:{field.type}' for field in parquet.schema_arrow
    )
    row_count = 0
    xor_state = 0
    sum_state = 0
    square_state = 0
    for batch in parquet.iter_batches(batch_size=_DIGEST_BATCH_SIZE):
        for row in batch.to_pylist():
            encoded = json.dumps(
                row,
                default=str,
                ensure_ascii=True,
                sort_keys=True,
                separators=(',', ':'),
            ).encode('utf-8')
            row_value = int.from_bytes(hashlib.sha256(encoded).digest())
            xor_state ^= row_value
            sum_state = (sum_state + row_value) % _DIGEST_MODULUS
            square_state = (
                square_state + row_value * row_value
            ) % _DIGEST_MODULUS
            row_count += 1
    digest = hashlib.sha256()
    digest.update(schema.encode('utf-8'))
    digest.update(
        f'|{row_count}|{xor_state}|{sum_state}|{square_state}'.encode()
    )
    return digest.hexdigest()
