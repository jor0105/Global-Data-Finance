from ...macro_exceptions import (
    DiskFullError,
    NetworkError,
    PathPermissionError,
    TimeoutError,
)


class RetryStrategy:
    """Handles retry logic and backoff calculations.

    This class determines which exceptions warrant a retry based on their type
    and error message patterns. It uses the application's standard exception
    hierarchy (macro_exceptions) to avoid dependencies on external libraries.
    """

    _RETRYABLE_KEYWORDS = [
        'timeout',
        'connection refused',
        'connection reset',
        'connection aborted',
        'temporarily',
        'unavailable',
        'try again',
    ]

    def __init__(
        self, initial_backoff: float, max_backoff: float, multiplier: float
    ):
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.multiplier = multiplier

    def is_retryable(self, exception: Exception) -> bool:
        """Determines if an exception warrants a retry.

        An exception is retryable if:
        - It is a NetworkError or TimeoutError (transient network issues)
        - Its error message contains retryable keywords

        Non-retryable exceptions: PathPermissionError, DiskFullError, ValueError

        Args:
            exception: The exception to evaluate

        Returns:
            True if the exception should trigger a retry, False otherwise
        """
        if isinstance(
            exception, (PathPermissionError, DiskFullError, ValueError)
        ):
            return False

        if isinstance(exception, (NetworkError, TimeoutError)):
            return True

        # Fallback: check error message for known retryable keywords
        error_msg = str(exception).lower()
        return any(kw in error_msg for kw in self._RETRYABLE_KEYWORDS)

    def calculate_backoff(self, retry_count: int) -> float:
        """Calculates the exponential backoff duration."""
        backoff = self.initial_backoff * (self.multiplier**retry_count)
        return min(backoff, self.max_backoff)
