from pathlib import Path
from unittest.mock import AsyncMock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from globaldatafinance.brazil.b3_data.historical_quotes.extraction_service import (
    temp_parquet_merge,
)
from globaldatafinance.macro_exceptions import (
    ExtractionError,
    ParquetWriteError,
)

pytestmark = pytest.mark.unit


def test_count_parquet_rows_success(tmp_path: Path) -> None:
    parquet_path = tmp_path / 'test.parquet'
    table = pa.table({'col': [1, 2, 3, 4, 5]})
    pq.write_table(table, str(parquet_path))

    rows = temp_parquet_merge.count_parquet_rows(parquet_path)
    assert rows == 5


def test_count_parquet_rows_raises_on_invalid_file(tmp_path: Path) -> None:
    bad_file = tmp_path / 'bad.parquet'
    bad_file.write_text('not a parquet file')

    with pytest.raises(ExtractionError) as exc_info:
        temp_parquet_merge.count_parquet_rows(bad_file)

    assert 'Failed to read rows count' in str(exc_info.value)


@pytest.mark.asyncio
async def test_merge_temp_files_streaming_empty_list(tmp_path: Path) -> None:
    output_path = tmp_path / 'out.parquet'
    check_resources = AsyncMock()

    total = await temp_parquet_merge.merge_temp_files_streaming(
        [], output_path, check_resources=check_resources
    )

    assert total == 0
    assert not output_path.exists()
    check_resources.assert_not_called()


@pytest.mark.asyncio
async def test_merge_temp_files_streaming_single_file(tmp_path: Path) -> None:
    temp_file = tmp_path / 'single.parquet'
    table = pa.table({'col': [10, 20, 30]})
    pq.write_table(table, str(temp_file))

    final_output = tmp_path / 'merged_single.parquet'
    check_resources = AsyncMock()

    total = await temp_parquet_merge.merge_temp_files_streaming(
        [temp_file], final_output, check_resources=check_resources
    )

    assert total == 3
    assert final_output.exists()
    assert not temp_file.exists()
    check_resources.assert_not_called()


@pytest.mark.asyncio
async def test_merge_temp_files_streaming_multiple_files(
    tmp_path: Path,
) -> None:
    schema = pa.schema([('id', pa.int64()), ('val', pa.string())])
    temp1 = tmp_path / 'temp_1.parquet'
    temp2 = tmp_path / 'temp_2.parquet'
    temp3 = tmp_path / 'temp_3.parquet'

    pq.write_table(
        pa.table({'id': [1, 2], 'val': ['a', 'b']}, schema=schema), str(temp1)
    )
    pq.write_table(
        pa.table({'id': [3], 'val': ['c']}, schema=schema), str(temp2)
    )
    pq.write_table(
        pa.table(
            {'id': [4, 5, 6, 7], 'val': ['d', 'e', 'f', 'g']}, schema=schema
        ),
        str(temp3),
    )

    final_output = tmp_path / 'merged_multi.parquet'
    check_resources = AsyncMock()

    total = await temp_parquet_merge.merge_temp_files_streaming(
        [temp1, temp2, temp3], final_output, check_resources=check_resources
    )

    assert total == 7
    assert final_output.exists()
    assert not temp1.exists()
    assert not temp2.exists()
    assert not temp3.exists()

    result_parquet = pq.ParquetFile(str(final_output))
    assert result_parquet.metadata.num_rows == 7


@pytest.mark.asyncio
async def test_merge_temp_files_streaming_triggers_resource_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    schema = pa.schema([('id', pa.int64())])
    temp1 = tmp_path / 't1.parquet'
    temp2 = tmp_path / 't2.parquet'

    pq.write_table(pa.table({'id': [1, 2]}, schema=schema), str(temp1))
    pq.write_table(pa.table({'id': [3, 4]}, schema=schema), str(temp2))

    final_output = tmp_path / 'merged_resource_check.parquet'
    check_resources = AsyncMock()

    # Temporarily adjust the condition or batch size check to verify check_resources call
    # The condition is: if total_rows % 500_000 == 0 and total_rows > 0: await check_resources()
    # We can create two files of 2 rows and mock total_rows modulo check
    class MockParquetFile(pq.ParquetFile):
        def iter_batches(self, batch_size=200_000):
            # Yield a batch with num_rows = 500_000
            batch = pa.record_batch({'id': pa.array(list(range(500_000)))})
            yield batch

    monkeypatch.setattr(pq, 'ParquetFile', MockParquetFile)

    total = await temp_parquet_merge.merge_temp_files_streaming(
        [temp1, temp2], final_output, check_resources=check_resources
    )

    assert total == 1_000_000
    assert check_resources.call_count == 2


@pytest.mark.asyncio
async def test_merge_temp_files_streaming_failure_cleans_up_and_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    schema = pa.schema([('id', pa.int64())])
    temp1 = tmp_path / 'fail_t1.parquet'
    temp2 = tmp_path / 'fail_t2.parquet'

    pq.write_table(pa.table({'id': [1]}, schema=schema), str(temp1))
    pq.write_table(pa.table({'id': [2]}, schema=schema), str(temp2))

    final_output = tmp_path / 'fail_merged.parquet'
    check_resources = AsyncMock()

    # Cause an error during write_batch
    class FailingWriter:
        def __init__(self, *args, **kwargs):
            pass

        def write_batch(self, batch):
            raise OSError('Disk write failure simulated')

        def close(self):
            pass

    monkeypatch.setattr(pq, 'ParquetWriter', FailingWriter)

    with pytest.raises(ParquetWriteError) as exc_info:
        await temp_parquet_merge.merge_temp_files_streaming(
            [temp1, temp2], final_output, check_resources=check_resources
        )

    assert 'Merge operation failed' in str(exc_info.value)
    # Temporary files should be cleaned up
    assert not temp1.exists()
    assert not temp2.exists()
    temp_merge = final_output.with_suffix('.parquet.merge_tmp')
    assert not temp_merge.exists()
