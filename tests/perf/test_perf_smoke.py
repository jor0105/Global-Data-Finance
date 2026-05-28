"""Perf smoke benchmarks (opt-in via ``-m perf``).

Estes benchmarks estabelecem uma regua reprodutivel para duas operacoes
hot path da lib:

1. Geracao de URLs de download CVM (`generate_urls`) - compute
   puro, sem rede.
2. Parsing positional de linhas COTAHIST B3 (`CotahistParserB3.parse_line`)
   - compute puro, sem I/O.

Para rodar e salvar baseline::

    uv run pytest tests/perf -m perf --benchmark-save=baseline_v1

Para comparar contra o baseline::

    uv run pytest tests/perf -m perf --benchmark-compare=baseline_v1
"""

from __future__ import annotations

from typing import Any

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.cotahist_parser import (
    CotahistParserB3,
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data.client import (
    generate_urls,
)


def _synthetic_cotahist_line() -> str:
    """Build a synthetic but valid-looking COTAHIST type-01 record.

    The exact content does not need to be a real B3 sample - the parser
    operates by fixed-width slicing, so a 245-char string with realistic
    field positions is enough to exercise every branch of `_parse_quote_record`.
    """
    parts = [
        '01',  # tipreg (1-2)
        '20240115',  # data_pregao (3-10)
        '02',  # codigo_bdi (11-12)
        'PETR4       ',  # ticker (13-24)
        '010',  # tpmerc (25-27)
        'PETROBRAS   ',  # nome_resumido (28-39)
        'PN        ',  # especificacao (40-49)
        '       ',  # padding to position 56
        '0000000123456',  # preco_abertura (57-69)
        '0000000125000',  # preco_maximo (70-82)
        '0000000122000',  # preco_minimo (83-95)
        '0000000124000',  # preco_medio (96-108)
        '0000000124500',  # preco_fechamento (109-121)
        '0000000124400',  # melhor_oferta_compra (122-134)
        '0000000124600',  # melhor_oferta_venda (135-147)
        '12345',  # numero_negocios (148-152)
        '000000001234567890',  # quantidade_total (153-170)
        '000000000001234567',  # volume_total (171-188)
        '              ',  # filler/preco_exercicio (189-202)
        '00000000',  # data_vencimento (203-210)
        '0000001',  # fator_cotacao (211-217)
        '             ',  # filler (218-230)
        'BRPETRACNPR6',  # codigo_isin (231-242)
        '100',  # numero_distribuicao (243-245)
    ]
    line = ''.join(parts)
    # Pad/truncate to exactly 245 chars.
    line = line.ljust(245)[:245]
    return line


@pytest.mark.perf
def test_benchmark_cvm_url_generation(benchmark) -> None:
    """Benchmark generating CVM download URLs for a 3-year DFP range.

    Pure-compute path: hits `DictZipsToDownloadCVM` value object logic
    without touching the network.
    """

    def _run() -> int:
        dict_zips, _ = generate_urls(
            list_docs=['DFP'],
            initial_year=2020,
            last_year=2022,
        )
        return sum(len(urls) for urls in dict_zips.values())

    total_urls = benchmark(_run)
    assert total_urls > 0


@pytest.mark.perf
def test_benchmark_b3_cotahist_parse_line(benchmark) -> None:
    """Benchmark parsing a single COTAHIST line through the full pipeline.

    Pure-compute path: exercises slicing, decimal parsing and date parsing.
    """
    parser = CotahistParserB3()
    line = _synthetic_cotahist_line()
    target_codes = {'010', '020'}

    def _run() -> dict[str, Any] | None:
        return parser.parse_line(line, target_codes)

    parsed = benchmark(_run)
    assert parsed is not None
    assert parsed['ticker'] == 'PETR4'
