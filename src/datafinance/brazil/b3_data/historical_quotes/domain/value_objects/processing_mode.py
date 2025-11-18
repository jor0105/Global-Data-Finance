from enum import Enum


class ProcessingModeEnumB3(str, Enum):
    FAST = "fast"
    SLOW = "slow"

    # FAST mode configuration: High concurrency for maximum performance
    FAST_DESIRED_CONCURRENT_FILES = (
        15  # Process 15 files in parallel to maximize throughput on multi-core systems
    )
    FAST_DESIRED_WORKERS = None  # Use default CPU count for thread pool executor
    FAST_USE_PARALLEL_PARSING = (
        True  # Enable parallel parsing with ThreadPoolExecutor for faster processing
    )
    FAST_MEMORY_THRESHOLD_MB = (
        3500  # Flush buffer at 3.5GB to leave 500MB margin for 4.5GB total target
    )

    # SLOW mode configuration: Conservative resource usage for low-end systems
    SLOW_DESIRED_CONCURRENT_FILES = (
        3  # Limit to 3 concurrent files to minimize memory usage
    )
    SLOW_DESIRED_WORKERS = 2  # Use only 2 workers to approach sequential processing
    SLOW_USE_PARALLEL_PARSING = False  # Disable parallel parsing for lower CPU overhead
    SLOW_MEMORY_THRESHOLD_MB = (
        1000  # Flush buffer at 1GB to leave 200MB margin for 1.5GB total target
    )

    @property
    def desired_concurrent_files(self) -> int:
        return int(
            self.FAST_DESIRED_CONCURRENT_FILES
            if self == ProcessingModeEnumB3.FAST
            else self.SLOW_DESIRED_CONCURRENT_FILES
        )

    @property
    def desired_workers(self):
        # Pode ser int ou None
        return (
            self.FAST_DESIRED_WORKERS
            if self == ProcessingModeEnumB3.FAST
            else self.SLOW_DESIRED_WORKERS
        )

    @property
    def use_parallel_parsing(self) -> bool:
        return bool(
            self.FAST_USE_PARALLEL_PARSING
            if self == ProcessingModeEnumB3.FAST
            else self.SLOW_USE_PARALLEL_PARSING
        )

    @property
    def memory_threshold_mb(self) -> int:
        return int(
            self.FAST_MEMORY_THRESHOLD_MB
            if self == ProcessingModeEnumB3.FAST
            else self.SLOW_MEMORY_THRESHOLD_MB
        )
