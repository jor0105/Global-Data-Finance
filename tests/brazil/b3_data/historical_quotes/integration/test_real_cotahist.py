"""Opt-in tests for caller-owned real COTAHIST inputs without network use."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow.parquet as pq
import pytest
from polars.testing import assert_frame_equal

from globaldatafinance import ExtractionResultB3, HistoricalQuotesB3
from globaldatafinance.brazil.b3_data.historical_quotes.zip_reader import (
    ZipFileReaderB3,
)
from tests.support.builders import write_cotahist_zip

pytestmark = [pytest.mark.integration, pytest.mark.real_data]

_SAMPLE_RECORD_COUNT = 20_000
_FULL_FRAME_COMPARE_LIMIT_BYTES = 256 * 1024 * 1024
_DIGEST_BATCH_SIZE = 100_000
_DIGEST_MODULUS = 1 << 256

EXPECTED_SCHEMA = {
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


async def _extract_local_data(
    input_directory: Path,
    output_directory: Path,
    year: int,
    mode: str,
    output_name: str,
) -> ExtractionResultB3:
    """Run one explicitly selected local year through the async facade."""
    return await HistoricalQuotesB3().extract_async(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=year,
        last_year=year,
        destination_path=str(output_directory),
        output_filename=output_name,
        processing_mode=mode,
        verbose=False,
    )


def _assert_successful_result(
    result: ExtractionResultB3, output_directory: Path, output_name: str
) -> Path:
    """Assert the stable public result and return its verified output path."""
    assert result['success'] is True
    assert result['total_files'] == 1
    assert result['success_count'] == 1
    assert result['error_count'] == 0
    assert result['total_records'] > 0
    assert result['errors'] == {}

    output_path = Path(result['output_file'])
    assert output_path == output_directory / f'{output_name}.parquet'
    assert output_path.is_file()
    assert output_path.stat().st_size > 0
    return output_path


@pytest.mark.asyncio
async def test_real_cotahist_catalog_validates_every_available_archive(
    local_cotahist_catalog: dict[int, list[Path]],
) -> None:
    """Inspect names and member resolution without reading every row."""
    reader = ZipFileReaderB3()
    inspected_inputs = 0
    for year, paths in sorted(local_cotahist_catalog.items()):
        for path in paths:
            assert path.name.casefold().startswith(
                f'cotahist_a{year}'.casefold()
            )
            assert path.stat().st_size > 0
            if path.suffix.casefold() == '.zip':
                async for _line in reader.read_lines_from_zip(str(path)):
                    break
            else:
                assert path.suffix.casefold() == '.txt'
            inspected_inputs += 1

    assert inspected_inputs >= 1


@pytest.mark.asyncio
@pytest.mark.slow
async def test_real_cotahist_limited_sample_has_fast_slow_parity(
    local_cotahist: tuple[Path, int], tmp_path: Path
) -> None:
    """A bounded real sample compares every column with exact dtypes."""
    input_file, year = local_cotahist
    sample_records = await _collect_quote_sample(input_file)
    sample_input = tmp_path / 'sample-input'
    sample_input.mkdir()
    write_cotahist_zip(
        sample_input,
        year=year,
        records=sample_records,
        compression=zipfile.ZIP_STORED,
    )

    fast_result = await _extract_local_data(
        sample_input, tmp_path / 'fast', year, 'fast', 'sample'
    )
    slow_result = await _extract_local_data(
        sample_input, tmp_path / 'slow', year, 'slow', 'sample'
    )
    fast_path = _assert_successful_result(
        fast_result, tmp_path / 'fast', 'sample'
    )
    slow_path = _assert_successful_result(
        slow_result, tmp_path / 'slow', 'sample'
    )
    sort_columns = list(EXPECTED_SCHEMA)
    fast_frame = pl.read_parquet(fast_path).sort(sort_columns, nulls_last=True)
    slow_frame = pl.read_parquet(slow_path).sort(sort_columns, nulls_last=True)

    assert fast_frame.schema == EXPECTED_SCHEMA
    assert slow_frame.schema == EXPECTED_SCHEMA
    assert fast_frame.height <= _SAMPLE_RECORD_COUNT
    assert fast_frame.height > 0
    assert_frame_equal(fast_frame, slow_frame, check_dtypes=True)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_real_cotahist_full_year_fast_has_stable_contract(
    local_cotahist: tuple[Path, int], tmp_path: Path
) -> None:
    """Process the selected annual input once, in fast mode only."""
    input_file, year = local_cotahist
    output_directory = tmp_path / 'annual-fast'
    result = await _extract_local_data(
        input_file.parent,
        output_directory,
        year,
        'fast',
        'annual_fast',
    )
    output_path = _assert_successful_result(
        result, output_directory, 'annual_fast'
    )
    lazy_frame = pl.scan_parquet(output_path)
    observed = lazy_frame.select(
        pl.len().alias('row_count'),
        pl.col('data_pregao').min().alias('first_date'),
        pl.col('data_pregao').max().alias('last_date'),
        pl.col('ticker').str.len_chars().min().alias('shortest_ticker'),
        pl.col('tipo_mercado').is_in(['010', '020']).sum().alias('markets'),
    ).collect()

    assert lazy_frame.collect_schema() == EXPECTED_SCHEMA
    assert observed['row_count'][0] == result['total_records']
    assert observed['first_date'][0].year == year
    assert observed['last_date'][0].year == year
    assert observed['shortest_ticker'][0] > 0
    assert observed['markets'][0] > 0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_real_cotahist_full_year_fast_slow_parity(
    local_cotahist: tuple[Path, int], tmp_path: Path
) -> None:
    """Compare complete fast and slow outputs independent of row order."""
    input_file, year = local_cotahist
    fast_result = await _extract_local_data(
        input_file.parent,
        tmp_path / 'full-fast',
        year,
        'fast',
        'full_fast',
    )
    slow_result = await _extract_local_data(
        input_file.parent,
        tmp_path / 'full-slow',
        year,
        'slow',
        'full_slow',
    )
    fast_path = _assert_successful_result(
        fast_result, tmp_path / 'full-fast', 'full_fast'
    )
    slow_path = _assert_successful_result(
        slow_result, tmp_path / 'full-slow', 'full_slow'
    )

    assert fast_result['total_records'] == slow_result['total_records']
    fast_scan = pl.scan_parquet(fast_path)
    slow_scan = pl.scan_parquet(slow_path)
    assert fast_scan.collect_schema() == EXPECTED_SCHEMA
    assert slow_scan.collect_schema() == EXPECTED_SCHEMA

    fast_summary = _full_output_summary(fast_scan)
    slow_summary = _full_output_summary(slow_scan)
    assert fast_summary == slow_summary
    assert fast_summary['row_count'] == fast_result['total_records']
    assert fast_summary['first_date'].year == year
    assert fast_summary['last_date'].year == year

    if max(fast_path.stat().st_size, slow_path.stat().st_size) <= (
        _FULL_FRAME_COMPARE_LIMIT_BYTES
    ):
        fast_frame = _canonical_frame(fast_path)
        slow_frame = _canonical_frame(slow_path)
        assert_frame_equal(fast_frame, slow_frame, check_dtypes=True)
    else:
        assert _canonical_digest(fast_path) == _canonical_digest(slow_path)


async def _collect_quote_sample(input_file: Path) -> list[str]:
    """Read a non-empty bounded set of real type-01 records for parity."""
    records: list[str] = []
    async for line in ZipFileReaderB3().read_lines_from_zip(str(input_file)):
        if line.startswith('01'):
            records.append(line)
            if len(records) == _SAMPLE_RECORD_COUNT:
                break

    assert records, f'{input_file} contains no type-01 records for parity'
    return records


def _full_output_summary(scan: pl.LazyFrame) -> dict[str, Any]:
    """Collect bounded metadata shared by both complete output checks."""
    observed = scan.select(
        pl.len().alias('row_count'),
        pl.col('data_pregao').min().alias('first_date'),
        pl.col('data_pregao').max().alias('last_date'),
    ).collect(engine='streaming')
    return {
        key: observed[key][0]
        for key in ('row_count', 'first_date', 'last_date')
    }


def _canonical_frame(path: Path) -> pl.DataFrame:
    """Materialize a small complete output in deterministic row order."""
    return (
        pl.scan_parquet(path)
        .sort(list(EXPECTED_SCHEMA))
        .collect(engine='streaming')
    )


def _canonical_digest(path: Path) -> str:
    """Hash bounded row batches without depending on row order."""
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
            row_value = _row_digest_value(row)
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


def _row_digest_value(row: dict[str, Any]) -> int:
    """Return a stable integer digest for one complete Parquet row."""
    encoded = json.dumps(
        row,
        default=str,
        ensure_ascii=True,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return int.from_bytes(hashlib.sha256(encoded).digest())
