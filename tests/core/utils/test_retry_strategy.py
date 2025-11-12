"""Tests for RetryStrategy."""

import requests

from src.core.utils.retry_strategy import RetryStrategy
from src.macro_exceptions import (
    DiskFullError,
    NetworkError,
    PathPermissionError,
    TimeoutError,
)


class TestRetryStrategy:
    """Test suite for RetryStrategy."""

    def test_initialization_with_default_values(self):
        """Test initialization with custom backoff parameters."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        assert strategy.initial_backoff == 1.0
        assert strategy.max_backoff == 60.0
        assert strategy.multiplier == 2.0

    def test_initialization_with_custom_values(self):
        """Test initialization with custom values."""
        strategy = RetryStrategy(initial_backoff=0.5, max_backoff=30.0, multiplier=1.5)

        assert strategy.initial_backoff == 0.5
        assert strategy.max_backoff == 30.0
        assert strategy.multiplier == 1.5

    def test_is_retryable_with_network_error(self):
        """Test that NetworkError is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = NetworkError("Connection failed")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_timeout_error(self):
        """Test that TimeoutError is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = TimeoutError("Request timed out")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_requests_timeout(self):
        """Test that requests.exceptions.Timeout is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = requests.exceptions.Timeout("Request timed out")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_requests_connection_error(self):
        """Test that requests.exceptions.ConnectionError is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = requests.exceptions.ConnectionError("Connection refused")
        assert strategy.is_retryable(error) is True

    def test_is_not_retryable_with_path_permission_error(self):
        """Test that PathPermissionError is not retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = PathPermissionError("Permission denied")
        assert strategy.is_retryable(error) is False

    def test_is_not_retryable_with_disk_full_error(self):
        """Test that DiskFullError is not retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = DiskFullError("No space left on device")
        assert strategy.is_retryable(error) is False

    def test_is_not_retryable_with_value_error(self):
        """Test that ValueError is not retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = ValueError("Invalid value")
        assert strategy.is_retryable(error) is False

    def test_is_retryable_with_timeout_keyword(self):
        """Test that error message with 'timeout' keyword is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Operation timeout occurred")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_connection_refused_keyword(self):
        """Test that error message with 'connection refused' is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Connection refused by server")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_connection_reset_keyword(self):
        """Test that error message with 'connection reset' is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Connection reset by peer")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_connection_aborted_keyword(self):
        """Test that error message with 'connection aborted' is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Connection aborted")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_temporarily_keyword(self):
        """Test that error message with 'temporarily' is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Service temporarily unavailable")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_unavailable_keyword(self):
        """Test that error message with 'unavailable' is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Service unavailable")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_try_again_keyword(self):
        """Test that error message with 'try again' is retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Please try again later")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error1 = Exception("TIMEOUT occurred")
        error2 = Exception("Timeout occurred")
        error3 = Exception("timeout occurred")

        assert strategy.is_retryable(error1) is True
        assert strategy.is_retryable(error2) is True
        assert strategy.is_retryable(error3) is True

    def test_is_not_retryable_with_unrelated_error(self):
        """Test that unrelated error message is not retryable."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Something completely different")
        assert strategy.is_retryable(error) is False

    def test_calculate_backoff_first_retry(self):
        """Test backoff calculation for first retry."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(retry_count=0)
        assert backoff == 1.0

    def test_calculate_backoff_second_retry(self):
        """Test backoff calculation for second retry."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(retry_count=1)
        assert backoff == 2.0

    def test_calculate_backoff_third_retry(self):
        """Test backoff calculation for third retry."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(retry_count=2)
        assert backoff == 4.0

    def test_calculate_backoff_exponential_growth(self):
        """Test exponential backoff growth pattern."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoffs = [strategy.calculate_backoff(i) for i in range(5)]
        assert backoffs == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_calculate_backoff_respects_max_backoff(self):
        """Test that backoff never exceeds max_backoff."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=10.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(retry_count=10)
        assert backoff == 10.0

    def test_calculate_backoff_with_high_retry_count(self):
        """Test backoff calculation with high retry count."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(retry_count=100)
        assert backoff == 60.0

    def test_calculate_backoff_with_custom_multiplier(self):
        """Test backoff calculation with custom multiplier."""
        strategy = RetryStrategy(initial_backoff=2.0, max_backoff=100.0, multiplier=3.0)

        backoffs = [strategy.calculate_backoff(i) for i in range(4)]
        assert backoffs == [2.0, 6.0, 18.0, 54.0]

    def test_calculate_backoff_with_fractional_multiplier(self):
        """Test backoff calculation with fractional multiplier."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=100.0, multiplier=1.5)

        backoff0 = strategy.calculate_backoff(retry_count=0)
        backoff1 = strategy.calculate_backoff(retry_count=1)
        backoff2 = strategy.calculate_backoff(retry_count=2)

        assert backoff0 == 1.0
        assert backoff1 == 1.5
        assert backoff2 == 2.25

    def test_calculate_backoff_zero_retry_count(self):
        """Test backoff calculation with zero retry count."""
        strategy = RetryStrategy(initial_backoff=5.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(retry_count=0)
        assert backoff == 5.0

    def test_calculate_backoff_with_small_initial_backoff(self):
        """Test backoff calculation with small initial backoff."""
        strategy = RetryStrategy(initial_backoff=0.1, max_backoff=10.0, multiplier=2.0)

        backoffs = [strategy.calculate_backoff(i) for i in range(4)]
        assert backoffs == [0.1, 0.2, 0.4, 0.8]

    def test_calculate_backoff_reaches_max_gradually(self):
        """Test that backoff reaches max backoff gradually."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=5.0, multiplier=2.0)

        backoff2 = strategy.calculate_backoff(retry_count=2)
        backoff3 = strategy.calculate_backoff(retry_count=3)

        assert backoff2 == 4.0
        assert backoff3 == 5.0

    def test_retryable_keywords_constant_exists(self):
        """Test that retryable keywords constant is defined."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        assert hasattr(strategy, "_RETRYABLE_KEYWORDS")
        assert isinstance(strategy._RETRYABLE_KEYWORDS, list)
        assert len(strategy._RETRYABLE_KEYWORDS) > 0

    def test_retryable_keywords_contains_expected_values(self):
        """Test that retryable keywords contain expected values."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        keywords = strategy._RETRYABLE_KEYWORDS
        assert "timeout" in keywords
        assert "connection refused" in keywords
        assert "connection reset" in keywords
        assert "connection aborted" in keywords
        assert "temporarily" in keywords
        assert "unavailable" in keywords
        assert "try again" in keywords

    def test_multiple_keywords_in_single_message(self):
        """Test error message containing multiple retryable keywords."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("Connection timeout and temporarily unavailable")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_empty_exception_message(self):
        """Test is_retryable with empty exception message."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        error = Exception("")
        assert strategy.is_retryable(error) is False

    def test_calculate_backoff_sequence_consistency(self):
        """Test that backoff calculation is consistent across calls."""
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff1_first = strategy.calculate_backoff(retry_count=1)
        backoff1_second = strategy.calculate_backoff(retry_count=1)

        assert backoff1_first == backoff1_second
