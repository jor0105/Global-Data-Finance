"""End-to-end checks for public B3 ZIP/TXT extraction contracts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from globaldatafinance import HistoricalQuotesB3
from tests.support.builders import (
    build_cotahist_record,
    write_cotahist_txt,
    write_cotahist_zip,
)

pytestmark = pytest.mark.integration
# allow-assertion-reduction: Shared builders own record-shape checks.


def _write_plain_txt(directory: Path, ticker: str) -> Path:
    return write_cotahist_txt(
        directory,
        year=2024,
        records=[build_cotahist_record(ticker=ticker)],
    )


def _write_zip(directory: Path, ticker: str) -> Path:
    return write_cotahist_zip(
        directory,
        year=2024,
        records=[build_cotahist_record(ticker=ticker)],
    )


@pytest.mark.parametrize('processing_mode', ['fast', 'slow'])
def test_public_extract_processes_plain_txt_and_writes_expected_schema(
    tmp_path: Path, processing_mode: str
) -> None:
    input_directory = tmp_path / 'input'
    output_directory = tmp_path / 'output'
    input_directory.mkdir()
    _write_plain_txt(input_directory, 'TXTPETR4')

    result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        destination_path=str(output_directory),
        output_filename='quotes',
        processing_mode=processing_mode,
        verbose=False,
    )

    expected_columns = [
        'data_pregao',
        'codigo_bdi',
        'ticker',
        'tipo_mercado',
        'nome_resumido',
        'especificacao_papel',
        'preco_abertura',
        'preco_maximo',
        'preco_minimo',
        'preco_medio',
        'preco_fechamento',
        'melhor_oferta_compra',
        'melhor_oferta_venda',
        'numero_negocios',
        'quantidade_total',
        'volume_total',
        'data_vencimento',
        'fator_cotacao',
        'codigo_isin',
        'numero_distribuicao',
    ]
    expected_decimal = pl.Decimal(precision=38, scale=2)
    expected_types = {
        'data_pregao': pl.Date,
        'codigo_bdi': pl.String,
        'ticker': pl.String,
        'tipo_mercado': pl.String,
        'nome_resumido': pl.String,
        'especificacao_papel': pl.String,
        'preco_abertura': expected_decimal,
        'preco_maximo': expected_decimal,
        'preco_minimo': expected_decimal,
        'preco_medio': expected_decimal,
        'preco_fechamento': expected_decimal,
        'melhor_oferta_compra': expected_decimal,
        'melhor_oferta_venda': expected_decimal,
        'numero_negocios': pl.Int64,
        'quantidade_total': pl.Int64,
        'volume_total': expected_decimal,
        'data_vencimento': pl.Date,
        'fator_cotacao': pl.Int64,
        'codigo_isin': pl.String,
        'numero_distribuicao': pl.Int64,
    }

    assert result['success'] is True
    assert result['message']
    assert result['total_files'] == 1
    assert result['success_count'] == 1
    assert result['error_count'] == 0
    assert result['total_records'] == 1
    assert result['errors'] == {}
    assert result['assets'] == ['ações']
    assert result['processing_mode'] == processing_mode
    assert result['elapsed_time'] >= 0

    output_path = Path(result['output_file'])
    assert output_path == output_directory / 'quotes.parquet'
    assert output_path.is_file()

    frame = pl.read_parquet(output_path)
    assert frame.height == 1
    assert frame.columns == expected_columns
    assert {name: frame.schema[name] for name in expected_columns} == (
        expected_types
    )
    assert frame['data_pregao'][0] == date(2024, 1, 15)
    assert frame['ticker'].to_list() == ['TXTPETR4']
    assert frame['tipo_mercado'].to_list() == ['010']
    assert frame['preco_fechamento'][0] == Decimal('123.45')
    assert frame['volume_total'][0] == Decimal('1234.56')


def test_public_extract_returns_empty_for_nonmatching_directory(
    tmp_path: Path,
) -> None:
    """A nonempty directory without COTAHIST files returns an empty result."""
    input_directory = tmp_path / 'input'
    input_directory.mkdir()
    (input_directory / 'README.txt').write_text(
        'This file is intentionally not a COTAHIST input.\n', encoding='utf-8'
    )

    result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        verbose=False,
    )

    assert set(result) == {
        'success',
        'message',
        'total_files',
        'success_count',
        'error_count',
        'total_records',
        'output_file',
        'errors',
        'assets',
        'processing_mode',
        'elapsed_time',
    }
    assert result['success'] is True
    assert result['total_files'] == 0
    assert result['success_count'] == 0
    assert result['error_count'] == 0
    assert result['total_records'] == 0
    assert result['output_file'] == ''
    assert result['errors'] == {}


@pytest.mark.parametrize(
    ('payload', 'reason'),
    [
        (b'', 'empty'),
        (b'00HEADER\n99TRAILER\n', 'no type-01 quote data record'),
    ],
)
def test_public_extract_rejects_selected_txt_without_quote_records(
    tmp_path: Path, payload: bytes, reason: str
) -> None:
    """A selected TXT cannot report success when it has no quote records."""
    input_directory = tmp_path / 'input'
    output_directory = tmp_path / 'output'
    input_directory.mkdir()
    (input_directory / 'COTAHIST_A2024.TXT').write_bytes(payload)

    result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        destination_path=str(output_directory),
        output_filename='quotes',
        verbose=False,
    )

    assert result['success'] is False
    assert result['total_files'] == 1
    assert result['success_count'] == 0
    assert result['error_count'] == 1
    assert result['total_records'] == 0
    assert result['output_file'] == ''
    assert (
        reason in result['errors'][str(input_directory / 'COTAHIST_A2024.TXT')]
    )
    assert list(output_directory.glob('*.parquet')) == []


def test_public_extract_reports_selected_input_without_matching_assets(
    tmp_path: Path,
) -> None:
    """Valid inputs with no requested assets have explicit no-data results."""
    input_directory = tmp_path / 'input'
    output_directory = tmp_path / 'output'
    input_directory.mkdir()
    write_cotahist_txt(
        input_directory,
        year=2024,
        records=[build_cotahist_record(market='070')],
    )

    result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        destination_path=str(output_directory),
        output_filename='quotes',
        verbose=False,
    )

    assert result['success'] is False
    assert result['total_files'] == 1
    assert result['success_count'] == 0
    assert result['error_count'] == 1
    assert result['total_records'] == 0
    assert result['output_file'] == ''
    assert result['errors'] == {
        str(input_directory / 'COTAHIST_A2024.TXT'): (
            'No COTAHIST records matched the requested assets'
        )
    }
    assert list(output_directory.glob('*.parquet')) == []


def test_public_extract_accepts_explicit_parquet_suffix_without_duplication(
    tmp_path: Path,
) -> None:
    """An explicit Parquet suffix must occur once in the output path."""
    input_directory = tmp_path / 'input'
    output_directory = tmp_path / 'output'
    input_directory.mkdir()
    _write_plain_txt(input_directory, 'EXPLICIT4')

    result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        destination_path=str(output_directory),
        output_filename='quotes.parquet',
        verbose=False,
    )

    output_path = output_directory / 'quotes.parquet'
    assert result['success'] is True
    assert result['output_file'] == str(output_path)
    assert output_path.is_file()
    assert not (output_directory / 'quotes.parquet.parquet').exists()


def test_public_extract_prefers_zip_when_zip_and_txt_share_a_year(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / 'input'
    output_directory = tmp_path / 'output'
    input_directory.mkdir()
    _write_zip(input_directory, 'ZIPPETR4')
    _write_plain_txt(input_directory, 'TXTPETR4')

    result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        destination_path=str(output_directory),
        output_filename='preferred',
        processing_mode='fast',
        verbose=False,
    )

    assert result['success'] is True
    assert result['total_files'] == 1
    assert result['success_count'] == 1
    assert result['error_count'] == 0
    assert result['total_records'] == 1

    frame = pl.read_parquet(result['output_file'])
    assert frame['ticker'].to_list() == ['ZIPPETR4']


def test_public_extract_accepts_historical_cotahist_member(
    tmp_path: Path,
) -> None:
    """The public B3 flow accepts the extensionless historical layout."""
    input_directory = tmp_path / 'input'
    output_directory = tmp_path / 'output'
    input_directory.mkdir()
    write_cotahist_zip(
        input_directory,
        year=2001,
        records=[build_cotahist_record(year=2001, ticker='HIST2001')],
        member_name='COTAHIST_A2001',
    )

    result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2001,
        last_year=2001,
        destination_path=str(output_directory),
        output_filename='historical',
        verbose=False,
    )

    frame = pl.read_parquet(result['output_file'])
    assert result['success'] is True
    assert result['total_records'] == 1
    assert frame['ticker'].to_list() == ['HIST2001']


def test_public_fast_and_slow_are_equal_for_all_parquet_columns(
    tmp_path: Path,
) -> None:
    """Synthetic integration compares all 20 fields, not a projection."""
    input_directory = tmp_path / 'input'
    input_directory.mkdir()
    write_cotahist_zip(
        input_directory,
        year=2024,
        records=[
            build_cotahist_record(ticker='FASTSLOW1'),
            build_cotahist_record(ticker='FASTSLOW2', market='020'),
        ],
    )

    fast_result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        destination_path=str(tmp_path / 'fast'),
        output_filename='quotes',
        processing_mode='fast',
        verbose=False,
    )
    slow_result = HistoricalQuotesB3().extract(
        path_of_docs=str(input_directory),
        assets_list=['ações'],
        initial_year=2024,
        last_year=2024,
        destination_path=str(tmp_path / 'slow'),
        output_filename='quotes',
        processing_mode='slow',
        verbose=False,
    )

    fast_frame = pl.read_parquet(fast_result['output_file']).sort(
        pl.all(), nulls_last=True
    )
    slow_frame = pl.read_parquet(slow_result['output_file']).sort(
        pl.all(), nulls_last=True
    )
    assert fast_result['success'] is True
    assert slow_result['success'] is True
    assert_frame_equal(fast_frame, slow_frame, check_dtypes=True)
