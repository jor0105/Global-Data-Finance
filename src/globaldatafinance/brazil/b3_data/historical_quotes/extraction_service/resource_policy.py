import asyncio
import gc

from .....core import ResourceMonitor, ResourceState, get_logger
from ..processing import ProcessingModeEnumB3

logger = get_logger(__name__)


class ResourcePolicyB3:
    """Own resource-aware sizing and throttling for B3 extraction."""

    FLUSH_BATCH_SIZE = 500_000
    PARSE_BATCH_SIZE = 50_000

    MIN_FLUSH_BATCH = 50_000
    MIN_PARSE_BATCH = 10_000

    def __init__(self, processing_mode: ProcessingModeEnumB3) -> None:
        self.processing_mode = processing_mode
        self.resource_monitor = ResourceMonitor()

        desired_concurrent_files = processing_mode.desired_concurrent_files
        desired_workers = processing_mode.desired_workers
        self.use_parallel_parsing = processing_mode.use_parallel_parsing

        self.max_concurrent_files = min(
            desired_concurrent_files,
            self.resource_monitor.get_safe_worker_count(
                desired_concurrent_files
            ),
        )

        if self.use_parallel_parsing:
            self.max_workers = self.resource_monitor.get_safe_worker_count(
                desired_workers
            )
        else:
            self.max_workers = 1

        self.flush_batch_size = self.FLUSH_BATCH_SIZE
        self.parse_batch_size = self.PARSE_BATCH_SIZE

    async def check_and_wait_for_resources(self) -> None:
        """Wait for resource recovery when the monitor reports pressure."""
        resource_state = self.resource_monitor.check_resources()

        if resource_state == ResourceState.CRITICAL:
            await asyncio.sleep(0.1)
            gc.collect()
        elif resource_state == ResourceState.EXHAUSTED:
            logger.warning('Resources exhausted, waiting for recovery...')
            if not await self.wait_for_resources(timeout_seconds=30):
                raise MemoryError('Unable to recover from resource exhaustion')

    def adjust_batch_sizes(self) -> None:
        """Adjust batch sizes based on current memory state."""
        memory_state = self.resource_monitor.check_resources()

        base_flush_size = self.FLUSH_BATCH_SIZE
        new_flush_size = self.resource_monitor.get_safe_batch_size(
            base_flush_size
        )

        if new_flush_size != self.flush_batch_size:
            logger.info(
                f'Adjusted flush batch size: {self.flush_batch_size} -> {new_flush_size} '
                f'(memory state: {memory_state.value})'
            )
            self.flush_batch_size = max(new_flush_size, self.MIN_FLUSH_BATCH)

        ratio = self.PARSE_BATCH_SIZE / base_flush_size
        new_parse_size = int(self.flush_batch_size * ratio)
        if new_parse_size != self.parse_batch_size:
            self.parse_batch_size = max(new_parse_size, self.MIN_PARSE_BATCH)

    def should_flush_by_memory(self) -> bool:
        """Return True if process memory usage exceeds mode threshold."""
        process_memory_mb = self.resource_monitor.get_process_memory_mb()
        threshold_mb = self.processing_mode.memory_threshold_mb

        should_flush = process_memory_mb >= threshold_mb

        if should_flush:
            logger.info(
                'Memory threshold reached for flush',
                extra={
                    'process_memory_mb': f'{process_memory_mb:.2f}',
                    'threshold_mb': threshold_mb,
                    'mode': str(self.processing_mode),
                },
            )

        return should_flush

    async def wait_for_resources(self, timeout_seconds: int = 30) -> bool:
        """Wait for resources to become available, up to timeout."""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            self.resource_monitor.wait_for_resources,
            ResourceState.WARNING,
            timeout_seconds,
        )
        return bool(result)
