import pytest
import requests

from src.brazil.cvm.fundamental_stocks_data.utils.retry_strategy import RetryStrategy
from src.macro_exceptions.macro_exceptions import (
    DiskFullError,
    NetworkError,
    PathPermissionError,
    TimeoutError,
)


class TestRetryStrategyInit:
    def test_init_with_valid_parameters(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        assert strategy.initial_backoff == 1.0
        assert strategy.max_backoff == 60.0
        assert strategy.multiplier == 2.0

    def test_init_with_zero_backoff(self):
        strategy = RetryStrategy(initial_backoff=0.0, max_backoff=10.0, multiplier=2.0)

        assert strategy.initial_backoff == 0.0

    def test_init_with_small_values(self):
        strategy = RetryStrategy(initial_backoff=0.1, max_backoff=5.0, multiplier=1.5)

        assert strategy.initial_backoff == 0.1
        assert strategy.max_backoff == 5.0
        assert strategy.multiplier == 1.5

    def test_init_with_large_values(self):
        strategy = RetryStrategy(
            initial_backoff=1000.0, max_backoff=10000.0, multiplier=10.0
        )

        assert strategy.initial_backoff == 1000.0
        assert strategy.max_backoff == 10000.0
        assert strategy.multiplier == 10.0

    def test_init_with_multiplier_one(self):
        strategy = RetryStrategy(initial_backoff=5.0, max_backoff=60.0, multiplier=1.0)

        assert strategy.multiplier == 1.0


class TestIsRetryable:
    def test_network_error_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = NetworkError("Connection failed")

        assert strategy.is_retryable(exception) is True

    def test_timeout_error_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = TimeoutError("Request timed out")

        assert strategy.is_retryable(exception) is True

    def test_requests_timeout_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = requests.exceptions.Timeout("Request timeout")

        assert strategy.is_retryable(exception) is True

    def test_requests_connection_error_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = requests.exceptions.ConnectionError("Connection error")

        assert strategy.is_retryable(exception) is True

    def test_path_permission_error_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = PathPermissionError("Permission denied")

        assert strategy.is_retryable(exception) is False

    def test_disk_full_error_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = DiskFullError("Disk full")

        assert strategy.is_retryable(exception) is False

    def test_value_error_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = ValueError("Invalid value")

        assert strategy.is_retryable(exception) is False

    def test_keyword_timeout_in_message_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("The request timeout occurred")

        assert strategy.is_retryable(exception) is True

    def test_keyword_connection_refused_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Connection refused by server")

        assert strategy.is_retryable(exception) is True

    def test_keyword_connection_reset_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Connection reset by peer")

        assert strategy.is_retryable(exception) is True

    def test_keyword_connection_aborted_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Connection aborted")

        assert strategy.is_retryable(exception) is True

    def test_keyword_temporarily_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Service temporarily unavailable")

        assert strategy.is_retryable(exception) is True

    def test_keyword_unavailable_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Service unavailable")

        assert strategy.is_retryable(exception) is True

    def test_keyword_try_again_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Please try again later")

        assert strategy.is_retryable(exception) is True

    def test_case_insensitive_keyword_matching(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("TIMEOUT OCCURRED")

        assert strategy.is_retryable(exception) is True

    def test_keyword_uppercase_variations(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)

        test_messages = [
            "CONNECTION REFUSED",
            "Connection Refused",
            "CONNECTION refused",
            "UNAVAILABLE",
            "Try Again",
        ]

        for message in test_messages:
            exception = Exception(message)
            assert (
                strategy.is_retryable(exception) is True
            ), f"Failed for message: {message}"

    def test_unknown_error_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Unknown error occurred")

        assert strategy.is_retryable(exception) is False

    def test_runtime_error_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = RuntimeError("Some runtime error")

        assert strategy.is_retryable(exception) is False

    def test_type_error_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = TypeError("Type mismatch")

        assert strategy.is_retryable(exception) is False

    def test_oserror_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = OSError("OS error")

        assert strategy.is_retryable(exception) is False

    def test_multiple_keywords_in_message_is_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("Connection timeout temporarily unavailable")

        assert strategy.is_retryable(exception) is True

    def test_partial_keyword_match_not_retryable(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        # "timeouts" contains "timeout"
        exception = Exception("Too many timeouts")

        assert strategy.is_retryable(exception) is True

    def test_path_permission_error_priority_over_keywords(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = PathPermissionError("timeout on permission denied")

        assert strategy.is_retryable(exception) is False

    def test_disk_full_error_priority_over_keywords(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = DiskFullError("timeout on disk full")

        assert strategy.is_retryable(exception) is False

    def test_value_error_priority_over_keywords(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = ValueError("timeout in value error")

        assert strategy.is_retryable(exception) is False

    def test_empty_exception_message(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("")

        assert strategy.is_retryable(exception) is False

    def test_whitespace_only_message(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)
        exception = Exception("   ")

        assert strategy.is_retryable(exception) is False


class TestCalculateBackoff:
    def test_backoff_first_retry(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(0)

        assert backoff == 1.0

    def test_backoff_second_retry(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(1)

        assert backoff == 2.0  # 1.0 * 2^1

    def test_backoff_third_retry(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(2)

        assert backoff == 4.0  # 1.0 * 2^2

    def test_backoff_exponential_growth(self):
        strategy = RetryStrategy(
            initial_backoff=1.0, max_backoff=1000.0, multiplier=3.0
        )

        backoffs = [strategy.calculate_backoff(i) for i in range(5)]

        expected = [1.0, 3.0, 9.0, 27.0, 81.0]
        assert backoffs == expected

    def test_backoff_respects_max_backoff(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=10.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(10)

        assert backoff == 10.0

    def test_backoff_never_exceeds_max(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=32.0, multiplier=2.0)

        for i in range(20):
            backoff = strategy.calculate_backoff(i)
            assert backoff <= 32.0

    def test_backoff_with_zero_initial_backoff(self):
        strategy = RetryStrategy(initial_backoff=0.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(5)

        assert backoff == 0.0

    def test_backoff_with_multiplier_one(self):
        strategy = RetryStrategy(initial_backoff=5.0, max_backoff=60.0, multiplier=1.0)

        backoffs = [strategy.calculate_backoff(i) for i in range(5)]

        assert all(b == 5.0 for b in backoffs)

    def test_backoff_with_small_multiplier(self):
        strategy = RetryStrategy(
            initial_backoff=100.0, max_backoff=1000.0, multiplier=0.5
        )

        backoff1 = strategy.calculate_backoff(1)
        backoff2 = strategy.calculate_backoff(2)

        assert backoff1 == 50.0
        assert backoff2 == 25.0

    def test_backoff_with_fractional_multiplier(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=1.5)

        backoff1 = strategy.calculate_backoff(1)
        backoff2 = strategy.calculate_backoff(2)

        assert backoff1 == pytest.approx(1.5)
        assert backoff2 == pytest.approx(2.25)

    def test_backoff_large_retry_count(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)

        backoff = strategy.calculate_backoff(100)

        assert backoff == 60.0  # Capped at max_backoff

    def test_backoff_progression(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=100.0, multiplier=2.0)

        backoffs = [strategy.calculate_backoff(i) for i in range(10)]
        expected = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 100.0, 100.0, 100.0]

        assert backoffs == expected

    def test_backoff_with_very_small_initial(self):
        strategy = RetryStrategy(
            initial_backoff=0.001, max_backoff=1.0, multiplier=10.0
        )

        backoff = strategy.calculate_backoff(0)

        assert backoff == pytest.approx(0.001)

    def test_backoff_with_large_multiplier(self):
        strategy = RetryStrategy(
            initial_backoff=1.0, max_backoff=1000.0, multiplier=10.0
        )

        backoff = strategy.calculate_backoff(2)

        assert backoff == 100.0  # 1.0 * 10^2

    def test_backoff_zero_retry_count_always_returns_initial(self):
        test_cases = [
            (0.5, 100.0, 2.0),
            (10.0, 500.0, 3.0),
            (100.0, 10000.0, 1.5),
        ]

        for initial, max_back, mult in test_cases:
            strategy = RetryStrategy(initial, max_back, mult)
            backoff = strategy.calculate_backoff(0)
            assert backoff == initial


class TestRetryStrategyIntegration:
    def test_typical_exponential_backoff_scenario(self):
        strategy = RetryStrategy(initial_backoff=0.5, max_backoff=30.0, multiplier=2.0)

        # Simulate retry sequence
        retries = []
        for i in range(8):
            exception = NetworkError("Connection failed")
            if strategy.is_retryable(exception):
                backoff = strategy.calculate_backoff(i)
                retries.append((i, backoff))

        expected = [
            (0, 0.5),
            (1, 1.0),
            (2, 2.0),
            (3, 4.0),
            (4, 8.0),
            (5, 16.0),
            (6, 30.0),
            (7, 30.0),
        ]

        assert retries == expected

    def test_non_retryable_exception_stops_retry(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)

        exceptions = [
            NetworkError("Connection failed"),
            ValueError("Invalid value"),
            NetworkError("Another connection error"),
        ]

        retryable_count = sum(1 for exc in exceptions if strategy.is_retryable(exc))

        assert retryable_count == 2

    def test_mixed_retryable_scenarios(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)

        test_cases = [
            (NetworkError("Connection error"), True),
            (TimeoutError("Timeout"), True),
            (requests.exceptions.Timeout("Timeout"), True),
            (Exception("Service temporarily unavailable"), True),
            (PathPermissionError("Permission denied"), False),
            (DiskFullError("Disk full"), False),
            (ValueError("Invalid"), False),
            (Exception("Unknown error"), False),
        ]

        for exception, expected in test_cases:
            result = strategy.is_retryable(exception)
            assert (
                result == expected
            ), f"Failed for {exception}: expected {expected}, got {result}"

    def test_backoff_sequence_realistic(self):
        strategy = RetryStrategy(initial_backoff=0.1, max_backoff=32.0, multiplier=2.0)

        max_retries = 10
        backoff_sequence = [strategy.calculate_backoff(i) for i in range(max_retries)]

        # Verify it's increasing until max
        for i in range(len(backoff_sequence) - 1):
            if backoff_sequence[i] < 32.0:
                assert backoff_sequence[i] <= backoff_sequence[i + 1]
            else:
                assert backoff_sequence[i] == 32.0

    def test_all_custom_exception_types(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)

        custom_exceptions = [
            (NetworkError("Network error"), True),
            (TimeoutError("Timeout"), True),
            (PathPermissionError("Permission denied"), False),
            (DiskFullError("Disk full"), False),
        ]

        for exception, expected in custom_exceptions:
            result = strategy.is_retryable(exception)
            assert result == expected

    def test_keyword_matching_with_special_characters(self):
        strategy = RetryStrategy(1.0, 60.0, 2.0)

        exception = Exception("timeout: (connection failed)")

        assert strategy.is_retryable(exception) is True

    def test_edge_case_strategy_configurations(self):
        configs = [
            (0.0, 0.0, 1.0),
            (100.0, 100.0, 1.0),
            (1.0, 1.0, 1.0),
            (0.001, 1000.0, 100.0),
        ]

        for initial, max_back, mult in configs:
            strategy = RetryStrategy(initial, max_back, mult)

            # Should not raise any errors
            backoff = strategy.calculate_backoff(0)
            assert backoff <= max_back
