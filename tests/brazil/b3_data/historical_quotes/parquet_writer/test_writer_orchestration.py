"""Unit-level writer orchestration tests using only project-owned seams."""

from pathlib import Path

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.parquet_writer import (
    ParquetWriterB3,
)
from globaldatafinance.core import ResourceState

pytestmark = pytest.mark.unit


class _ResourceMonitor:
    """Controlled resource collaborator, not a replacement for Polars/Arrow."""

    def __init__(self, states: list[ResourceState]) -> None:
        self.states = states
        self.calls = 0

    def check_resources(self) -> ResourceState:
        """Return the configured state and record orchestration."""
        state = self.states[min(self.calls, len(self.states) - 1)]
        self.calls += 1
        return state


@pytest.mark.asyncio
async def test_writer_skips_empty_data_before_resource_or_engine_work(
    tmp_path: Path,
) -> None:
    """An empty batch exits before touching its resource collaborator."""
    monitor = _ResourceMonitor([ResourceState.HEALTHY])

    await ParquetWriterB3(resource_monitor=monitor).write_to_parquet(
        [], tmp_path / 'empty.parquet'
    )

    assert monitor.calls == 0
    assert not (tmp_path / 'empty.parquet').exists()


@pytest.mark.asyncio
async def test_writer_fails_when_resource_recovery_remains_exhausted(
    tmp_path: Path,
) -> None:
    """The resource policy stops before a real engine allocates data."""
    monitor = _ResourceMonitor(
        [ResourceState.EXHAUSTED, ResourceState.EXHAUSTED]
    )

    with pytest.raises(MemoryError, match='Insufficient memory'):
        await ParquetWriterB3(resource_monitor=monitor).write_to_parquet(
            [{'ticker': 'TEST'}], tmp_path / 'memory.parquet'
        )

    assert monitor.calls == 3
    assert not (tmp_path / 'memory.parquet').exists()
