import asyncio
import gc
from pathlib import Path
from typing import Protocol

from .....core import get_logger
from .resource_policy import ResourcePolicyB3
from .types import ParsedRecord

logger = get_logger(__name__)


class _ParquetWriter(Protocol):
    async def write_to_parquet(
        self,
        data: list[ParsedRecord],
        output_path: Path,
        mode: str,
    ) -> None: ...


class BufferedParquetWriterB3:
    """Flush parsed records to Parquet with bounded retry behavior."""

    MAX_WRITE_RETRIES = 3

    def __init__(
        self,
        data_writer: _ParquetWriter,
        resource_policy: ResourcePolicyB3,
    ) -> None:
        self.data_writer = data_writer
        self.resource_policy = resource_policy

    async def flush_if_needed(
        self,
        buffer: list[ParsedRecord],
        output_path: Path,
        *,
        is_first_write: bool,
    ) -> tuple[int, bool]:
        """Flush buffered records when size or memory thresholds are reached."""
        should_flush = (
            len(buffer) >= self.resource_policy.flush_batch_size
            or self.resource_policy.should_flush_by_memory()
        )

        if not should_flush or not buffer:
            return 0, is_first_write

        return await self.flush_to_disk(
            buffer,
            output_path,
            is_first_write=is_first_write,
        )

    async def flush_to_disk(
        self,
        buffer: list[ParsedRecord],
        output_path: Path,
        *,
        is_first_write: bool,
        collect_garbage: bool = True,
    ) -> tuple[int, bool]:
        """Flush buffered records and return written count plus next state."""
        if not buffer:
            return 0, is_first_write

        records_written = len(buffer)
        write_mode = 'overwrite' if is_first_write else 'append'

        await self.write_buffer_to_disk(buffer, output_path, write_mode)
        buffer.clear()

        if collect_garbage:
            gc.collect()

        return records_written, False

    async def write_buffer_to_disk(
        self, buffer: list[ParsedRecord], output_path: Path, mode: str
    ) -> None:
        """Write buffer to Parquet file with retries on failure."""
        if not buffer:
            return

        logger.debug(
            f'Writing buffer to disk: {len(buffer)} records (mode: {mode})',
            extra={'output_path': str(output_path)},
        )

        for attempt in range(self.MAX_WRITE_RETRIES):
            try:
                await self.data_writer.write_to_parquet(
                    data=buffer,
                    output_path=output_path,
                    mode=mode,
                )
                return
            except Exception as e:
                if attempt < self.MAX_WRITE_RETRIES - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f'Write failed (attempt {attempt + 1}/{self.MAX_WRITE_RETRIES}), '
                        f'retrying in {wait_time}s: {e}',
                        extra={'output_path': str(output_path)},
                    )
                    await asyncio.sleep(wait_time)
                    continue

                logger.error(
                    f'Write failed after {self.MAX_WRITE_RETRIES} attempts',
                    extra={
                        'output_path': str(output_path),
                        'buffer_size': len(buffer),
                        'error': str(e),
                    },
                    exc_info=True,
                )
                raise
