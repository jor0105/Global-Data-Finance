"""End-to-end checks for public B3 ZIP/TXT extraction contracts."""

from __future__ import annotations

import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import polars as pl
import pytest

from globaldatafinance import HistoricalQuotesB3

pytestmark = pytest.mark.integration


def _put_field(line: list[str], start: int, end: int, value: str) -> None:
    width = end - start
    assert len(value) <= width
    line[start:end] = list(value.ljust(width))


def _put_number(line: list[str], start: int, end: int, value: int) -> None:
    width = end - start
    _put_field(line, start, end, str(value).rjust(width, '0'))


def _build_cotahist_record(ticker: str) -> str:
    """Build one valid 245-character type-01 COTAHIST record."""
    line = [' '] * 245
    _put_field(line, 0, 2, '01')
    _put_field(line, 2, 10, '20240115')
    _put_field(line, 10, 12, '02')
    _put_field(line, 12, 24, ticker)
    _put_field(line, 24, 27, '010')
    _put_field(line, 27, 39, 'PETROBRAS')
    _put_field(line, 39, 49, 'ON')
    for start, end in (
        (56, 69),
        (69, 82),
        (82, 95),
        (95, 108),
        (108, 121),
        (121, 134),
        (134, 147),
    ):
        _put_number(line, start, end, 12345)
    _put_number(line, 147, 152, 1)
    _put_number(line, 152, 170, 100)
    _put_number(line, 170, 188, 123456)
    _put_field(line, 202, 210, '20241231')
    _put_number(line, 210, 217, 1)
    _put_field(line, 230, 242, 'BRPETRACNPR6')
    _put_number(line, 242, 245, 1)
    record = ''.join(line)
    assert len(record) == 245
    assert record[0:2] == '01'
    assert record[2:10] == '20240115'
    assert record[12:24].strip() == ticker
    assert record[24:27] == '010'
    return record


def _write_plain_txt(directory: Path, ticker: str) -> Path:
    path = directory / 'COTAHIST_A2024.TXT'
    path.write_text(_build_cotahist_record(ticker) + '\n', encoding='latin-1')
    return path


def _write_zip(directory: Path, ticker: str) -> Path:
    path = directory / 'COTAHIST_A2024.ZIP'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(
            'COTAHIST_A2024.TXT',
            (_build_cotahist_record(ticker) + '\n').encode('latin-1'),
        )
    return path


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
