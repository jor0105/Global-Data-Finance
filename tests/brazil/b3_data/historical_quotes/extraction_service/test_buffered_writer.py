from importlib import import_module
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

buffered_writer_module = import_module(
    'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.buffered_writer'
)
BufferedParquetWriterB3 = buffered_writer_module.BufferedParquetWriterB3

pytestmark = pytest.mark.unit


class StubResourcePolicy:
    flush_batch_size = 2

    def should_flush_by_memory(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_flush_success_retries_with_backoff_and_clears_buffer():
    data_writer = AsyncMock()
    data_writer.write_to_parquet.side_effect = [
        OSError('temporary failure'),
        OSError('second failure'),
        None,
    ]
    buffered_writer = BufferedParquetWriterB3(
        data_writer=data_writer, resource_policy=StubResourcePolicy()
    )
    records = [{'id': 1}, {'id': 2}]

    with (
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.buffered_writer.asyncio.sleep',
            new_callable=AsyncMock,
        ) as sleep,
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.buffered_writer.gc.collect'
        ) as collect,
    ):
        written, is_first_write = await buffered_writer.flush_to_disk(
            records,
            Path('quotes.parquet'),
            is_first_write=True,
        )

    assert (written, is_first_write) == (2, False)
    assert data_writer.write_to_parquet.call_count == 3
    assert [call.args[0] for call in sleep.await_args_list] == [1, 2]
    assert data_writer.write_to_parquet.call_args_list[0].kwargs['mode'] == (
        'overwrite'
    )
    assert all(
        call.kwargs['mode'] == 'overwrite'
        for call in data_writer.write_to_parquet.call_args_list
    )
    assert records == []
    collect.assert_called_once_with()


@pytest.mark.asyncio
async def test_flush_exhaustion_preserves_buffer_and_final_exception():
    data_writer = AsyncMock()
    failure = OSError('permanent failure')
    data_writer.write_to_parquet.side_effect = failure
    buffered_writer = BufferedParquetWriterB3(
        data_writer=data_writer, resource_policy=StubResourcePolicy()
    )
    records = [{'id': 1}]

    with (
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.buffered_writer.asyncio.sleep',
            new_callable=AsyncMock,
        ) as sleep,
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.buffered_writer.gc.collect'
        ) as collect,
        pytest.raises(OSError, match='permanent failure'),
    ):
        await buffered_writer.flush_to_disk(
            records,
            Path('quotes.parquet'),
            is_first_write=False,
        )

    assert data_writer.write_to_parquet.call_count == (
        BufferedParquetWriterB3.MAX_WRITE_RETRIES
    )
    assert [call.args[0] for call in sleep.await_args_list] == [1, 2]
    assert records == [{'id': 1}]
    collect.assert_not_called()


@pytest.mark.asyncio
async def test_flush_if_needed_does_not_flush_small_buffer():
    data_writer = AsyncMock()
    buffered_writer = BufferedParquetWriterB3(
        data_writer=data_writer, resource_policy=StubResourcePolicy()
    )
    records = [{'id': 1}]

    written, is_first_write = await buffered_writer.flush_if_needed(
        records,
        Path('quotes.parquet'),
        is_first_write=True,
    )

    assert (written, is_first_write) == (0, True)
    assert records == [{'id': 1}]
    data_writer.write_to_parquet.assert_not_awaited()
