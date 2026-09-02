"""Real-engine integration tests for B3 Parquet persistence semantics."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pyarrow.parquet as pq
import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer import (
    ParquetWriterB3,
)
from globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer import (
    disk as parquet_writer_disk,
)
from globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer import (
    writer as writer_module,
)
from globaldatafinance.core import ResourceState
from globaldatafinance.macro_exceptions import DiskFullError

pytestmark = pytest.mark.integration


class _ResourceMonitor:
    """Small fake used only to select writer resource states."""

    def __init__(self, states: list[ResourceState]) -> None:
        self._states = states
        self._index = 0

    def check_resources(self) -> ResourceState:
        """Return deterministic resource states without replacing engines."""
        index = min(self._index, len(self._states) - 1)
        self._index += 1
        return self._states[index]


def _records(*identifiers: int) -> list[dict[str, object]]:
    """Build B3-shaped rows covering decimals, dates, strings, and ints."""
    return [
        {
            'data_pregao': date(2024, 1, identifier),
            'codigo_bdi': '02',
            'ticker': f'TEST{identifier}',
            'tipo_mercado': '010',
            'nome_resumido': 'TESTE',
            'especificacao_papel': 'ON',
            'preco_abertura': Decimal('10.10'),
            'preco_maximo': Decimal('11.10'),
            'preco_minimo': Decimal('9.10'),
            'preco_medio': Decimal('10.20'),
            'preco_fechamento': Decimal('10.30'),
            'melhor_oferta_compra': Decimal('10.00'),
            'melhor_oferta_venda': Decimal('10.40'),
            'numero_negocios': identifier,
            'quantidade_total': identifier * 100,
            'volume_total': Decimal('1000.00'),
            'data_vencimento': date(2024, 12, 31),
            'fator_cotacao': 1,
            'codigo_isin': 'BRTESTACNPR0',
            'numero_distribuicao': identifier,
        }
        for identifier in identifiers
    ]


@pytest.mark.asyncio
async def test_writer_creates_readable_real_parquet_with_full_schema(
    tmp_path: Path,
) -> None:
    """Polars and PyArrow read the same ordered rows and physical artifact."""
    output_path = tmp_path / 'quotes.parquet'
    await ParquetWriterB3(
        resource_monitor=_ResourceMonitor([ResourceState.HEALTHY])
    ).write_to_parquet(_records(1, 2), output_path)

    raw_bytes = output_path.read_bytes()
    polars_frame = pl.read_parquet(output_path)
    arrow_file = pq.ParquetFile(output_path)
    metadata = arrow_file.metadata

    assert raw_bytes[:4] == b'PAR1'
    assert raw_bytes[-4:] == b'PAR1'
    assert metadata is not None
    assert metadata.num_rows == 2
    assert polars_frame['ticker'].to_list() == ['TEST1', 'TEST2']
    assert polars_frame.schema['data_pregao'] == pl.Date
    assert polars_frame.schema['preco_fechamento'] == pl.Decimal(38, 2)
    assert polars_frame.schema['numero_negocios'] == pl.Int64
    assert polars_frame['preco_fechamento'].to_list() == [
        Decimal('10.30'),
        Decimal('10.30'),
    ]
    assert arrow_file.read().num_rows == polars_frame.height
    column = metadata.row_group(0).column(0)
    assert column.compression == 'ZSTD'
    assert column.statistics is not None


@pytest.mark.asyncio
async def test_writer_append_preserves_existing_rows_and_order(
    tmp_path: Path,
) -> None:
    """Append streams the original Parquet then adds rows without loss."""
    output_path = tmp_path / 'append.parquet'
    writer = ParquetWriterB3(
        resource_monitor=_ResourceMonitor([ResourceState.HEALTHY])
    )
    await writer.write_to_parquet(_records(1, 2), output_path)
    await writer.write_to_parquet(_records(3), output_path, mode='append')

    frame = pl.read_parquet(output_path)

    assert frame['ticker'].to_list() == ['TEST1', 'TEST2', 'TEST3']
    assert pq.ParquetFile(output_path).metadata.num_rows == 3
    assert not output_path.with_suffix('.parquet.tmp').exists()


@pytest.mark.asyncio
async def test_writer_overwrite_replaces_data_without_duplication(
    tmp_path: Path,
) -> None:
    """Overwrite atomically replaces an old valid file with only new rows."""
    output_path = tmp_path / 'overwrite.parquet'
    writer = ParquetWriterB3(
        resource_monitor=_ResourceMonitor([ResourceState.HEALTHY])
    )
    await writer.write_to_parquet(_records(1, 2), output_path)
    await writer.write_to_parquet(_records(3), output_path, mode='overwrite')

    frame = pl.read_parquet(output_path)

    assert frame['ticker'].to_list() == ['TEST3']
    assert pq.ParquetFile(output_path).metadata.num_rows == 1
    assert not output_path.with_suffix('.parquet.tmp').exists()


@pytest.mark.asyncio
async def test_writer_merges_real_chunks_without_temporary_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chunk mode uses real temporary Parquets and leaves a clean directory."""
    monkeypatch.setattr(writer_module, 'MEMORY_SPLIT_RECORD_THRESHOLD', 2)
    monkeypatch.setattr(writer_module, 'CHUNK_RECORD_COUNT', 2)
    output_path = tmp_path / 'chunked.parquet'
    writer = ParquetWriterB3(
        resource_monitor=_ResourceMonitor([ResourceState.CRITICAL])
    )

    await writer.write_to_parquet(_records(1, 2, 3, 4, 5), output_path)

    frame = pl.read_parquet(output_path)
    assert frame['ticker'].to_list() == [
        'TEST1',
        'TEST2',
        'TEST3',
        'TEST4',
        'TEST5',
    ]
    assert pq.ParquetFile(output_path).metadata.num_rows == 5
    assert list(tmp_path.glob('*_chunks')) == []
    assert not output_path.with_suffix('.parquet.tmp').exists()


@pytest.mark.asyncio
async def test_writer_disk_failure_keeps_no_partial_parquet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed low-level write cleans temp output before DiskFullError."""
    output_path = tmp_path / 'disk-full.parquet'
    writer = ParquetWriterB3(
        resource_monitor=_ResourceMonitor([ResourceState.HEALTHY])
    )

    def write_partial_then_fail(_df: pl.DataFrame, target: Path) -> None:
        target.write_bytes(b'not a valid parquet')
        raise OSError('No space left on device')

    monkeypatch.setattr(writer, '_write_dataframe', write_partial_then_fail)

    with pytest.raises(DiskFullError):
        await writer.write_to_parquet(_records(1), output_path)

    assert not output_path.exists()
    assert not output_path.with_suffix('.parquet.tmp').exists()


def test_writer_check_disk_space_translates_insufficient_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The disk seam translates a low-capacity filesystem error."""
    free_space = (ParquetWriterB3.MIN_FREE_SPACE_MB - 10) * 1024 * 1024
    monkeypatch.setattr(
        parquet_writer_disk.shutil,
        'disk_usage',
        lambda _path: SimpleNamespace(free=free_space),
    )

    with pytest.raises(DiskFullError):
        ParquetWriterB3._check_disk_space(tmp_path / 'file.parquet')
