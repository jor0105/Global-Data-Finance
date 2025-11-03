import pytest
import requests

from src.core.utils import RetryStrategy
from src.macro_exceptions import (
    DiskFullError,
    NetworkError,
    PathPermissionError,
    TimeoutError,
)


@pytest.mark.unit
class TestRetryStrategyInitialization:
    def test_init_with_valid_parameters(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        assert strategy.initial_backoff == 1.0
        assert strategy.max_backoff == 60.0
        assert strategy.multiplier == 2.0

    def test_init_with_custom_values(self):
        strategy = RetryStrategy(initial_backoff=2.5, max_backoff=120.0, multiplier=3.0)
        assert strategy.initial_backoff == 2.5
        assert strategy.max_backoff == 120.0
        assert strategy.multiplier == 3.0

    def test_init_with_small_values(self):
        strategy = RetryStrategy(initial_backoff=0.1, max_backoff=5.0, multiplier=1.5)
        assert strategy.initial_backoff == 0.1
        assert strategy.max_backoff == 5.0
        assert strategy.multiplier == 1.5

    def test_init_with_large_values(self):
        strategy = RetryStrategy(
            initial_backoff=10.0, max_backoff=3600.0, multiplier=5.0
        )
        assert strategy.initial_backoff == 10.0
        assert strategy.max_backoff == 3600.0
        assert strategy.multiplier == 5.0


@pytest.mark.unit
class TestRetryStrategyIsRetryable:
    def test_network_error_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = NetworkError("DRE", "Connection refused")
        assert strategy.is_retryable(error) is True

    def test_timeout_error_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = TimeoutError("DRE", 30.0)
        assert strategy.is_retryable(error) is True

    def test_requests_timeout_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = requests.exceptions.Timeout("Request timed out")
        assert strategy.is_retryable(error) is True

    def test_requests_connection_error_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = requests.exceptions.ConnectionError("Connection failed")
        assert strategy.is_retryable(error) is True

    def test_path_permission_error_not_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = PathPermissionError("/path")
        assert strategy.is_retryable(error) is False

    def test_disk_full_error_not_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = DiskFullError("/path")
        assert strategy.is_retryable(error) is False

    def test_value_error_not_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = ValueError("Invalid value")
        assert strategy.is_retryable(error) is False

    def test_generic_exception_with_timeout_keyword_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Request timeout occurred")
        assert strategy.is_retryable(error) is True

    def test_generic_exception_with_connection_refused_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Connection refused by server")
        assert strategy.is_retryable(error) is True

    def test_generic_exception_with_connection_reset_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Connection reset by peer")
        assert strategy.is_retryable(error) is True

    def test_generic_exception_with_connection_aborted_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Connection aborted")
        assert strategy.is_retryable(error) is True

    def test_generic_exception_with_temporarily_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Service temporarily unavailable")
        assert strategy.is_retryable(error) is True

    def test_generic_exception_with_unavailable_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Service unavailable")
        assert strategy.is_retryable(error) is True

    def test_generic_exception_with_try_again_is_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Please try again later")
        assert strategy.is_retryable(error) is True

    def test_generic_exception_without_keywords_not_retryable(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Something went wrong")
        assert strategy.is_retryable(error) is False

    def test_is_retryable_case_insensitive(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        test_cases = [
            "TIMEOUT occurred",
            "Connection REFUSED",
            "Temporarily UNAVAILABLE",
            "TRY AGAIN",
        ]
        for msg in test_cases:
            error = Exception(msg)
            assert strategy.is_retryable(error) is True

    def test_is_retryable_with_multiple_keywords(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("Connection timeout, please try again")
        assert strategy.is_retryable(error) is True

    def test_is_retryable_with_empty_message(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception("")
        assert strategy.is_retryable(error) is False


@pytest.mark.unit
class TestRetryStrategyCalculateBackoff:
    def test_calculate_backoff_first_retry(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        backoff = strategy.calculate_backoff(0)
        assert backoff == 1.0

    def test_calculate_backoff_second_retry(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        backoff = strategy.calculate_backoff(1)
        assert backoff == 2.0

    def test_calculate_backoff_third_retry(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        backoff = strategy.calculate_backoff(2)
        assert backoff == 4.0

    def test_calculate_backoff_exponential_growth(self):
        strategy = RetryStrategy(
            initial_backoff=1.0, max_backoff=1000.0, multiplier=2.0
        )
        backoffs = [strategy.calculate_backoff(i) for i in range(5)]
        assert backoffs == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_calculate_backoff_respects_max_backoff(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=10.0, multiplier=2.0)
        backoff = strategy.calculate_backoff(10)
        assert backoff == 10.0

    def test_calculate_backoff_with_different_multiplier(self):
        strategy = RetryStrategy(
            initial_backoff=1.0, max_backoff=1000.0, multiplier=3.0
        )
        backoffs = [strategy.calculate_backoff(i) for i in range(4)]
        assert backoffs == [1.0, 3.0, 9.0, 27.0]

    def test_calculate_backoff_with_fractional_initial_backoff(self):
        strategy = RetryStrategy(initial_backoff=0.5, max_backoff=60.0, multiplier=2.0)
        backoffs = [strategy.calculate_backoff(i) for i in range(4)]
        assert backoffs == [0.5, 1.0, 2.0, 4.0]

    def test_calculate_backoff_with_large_retry_count(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        backoff = strategy.calculate_backoff(100)
        assert backoff == 60.0

    def test_calculate_backoff_with_zero_retry_count(self):
        strategy = RetryStrategy(initial_backoff=5.0, max_backoff=60.0, multiplier=2.0)
        backoff = strategy.calculate_backoff(0)
        assert backoff == 5.0

    def test_calculate_backoff_with_multiplier_one(self):
        strategy = RetryStrategy(initial_backoff=2.0, max_backoff=60.0, multiplier=1.0)
        backoffs = [strategy.calculate_backoff(i) for i in range(5)]
        assert backoffs == [2.0, 2.0, 2.0, 2.0, 2.0]

    def test_calculate_backoff_never_exceeds_max(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=15.0, multiplier=2.0)
        for retry_count in range(20):
            backoff = strategy.calculate_backoff(retry_count)
            assert backoff <= 15.0


@pytest.mark.unit
class TestRetryStrategyEdgeCases:
    def test_is_retryable_with_none_exception_message(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error = Exception()
        result = strategy.is_retryable(error)
        assert isinstance(result, bool)

    def test_calculate_backoff_with_negative_retry_count(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        backoff = strategy.calculate_backoff(-1)
        assert backoff >= 0

    def test_retryable_keywords_constant(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        assert hasattr(strategy, "_RETRYABLE_KEYWORDS")
        assert isinstance(strategy._RETRYABLE_KEYWORDS, list)
        assert len(strategy._RETRYABLE_KEYWORDS) > 0

    def test_all_retryable_keywords_are_lowercase(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        for keyword in strategy._RETRYABLE_KEYWORDS:
            assert keyword == keyword.lower()


@pytest.mark.unit
class TestRetryStrategyIntegration:
    def test_realistic_retry_scenario(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        error1 = Exception("Network timeout")
        assert strategy.is_retryable(error1) is True
        backoff1 = strategy.calculate_backoff(0)
        assert backoff1 == 1.0

        error2 = Exception("Connection refused")
        assert strategy.is_retryable(error2) is True
        backoff2 = strategy.calculate_backoff(1)
        assert backoff2 == 2.0

        error3 = Exception("Service temporarily unavailable")
        assert strategy.is_retryable(error3) is True
        backoff3 = strategy.calculate_backoff(2)
        assert backoff3 == 4.0

        error4 = PathPermissionError("/path")
        assert strategy.is_retryable(error4) is False

    def test_multiple_strategies_independent(self):
        strategy1 = RetryStrategy(initial_backoff=1.0, max_backoff=30.0, multiplier=2.0)
        strategy2 = RetryStrategy(initial_backoff=2.0, max_backoff=60.0, multiplier=3.0)
        backoff1 = strategy1.calculate_backoff(2)
        backoff2 = strategy2.calculate_backoff(2)
        assert backoff1 == 4.0
        assert backoff2 == 18.0

    def test_retry_with_various_network_errors(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        retryable_messages = [
            "Connection timeout",
            "Network is temporarily unavailable",
            "Please try again",
            "Connection refused by host",
            "Connection reset by peer",
            "Connection aborted",
            "Read timeout",
            "Write timeout",
        ]
        for msg in retryable_messages:
            error = Exception(msg)
            assert strategy.is_retryable(error) is True, f"Failed for: {msg}"

    def test_retry_with_non_retryable_errors(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=60.0, multiplier=2.0)
        non_retryable_errors = [
            PathPermissionError("/path"),
            DiskFullError("/path"),
            ValueError("Invalid input"),
            KeyError("missing_key"),
            Exception("Fatal error occurred"),
        ]
        for error in non_retryable_errors:
            assert (
                strategy.is_retryable(error) is False
            ), f"Should not retry: {type(error).__name__}"

    def test_backoff_progression_with_cap(self):
        strategy = RetryStrategy(initial_backoff=1.0, max_backoff=20.0, multiplier=2.0)
        backoffs = []
        for i in range(10):
            backoff = strategy.calculate_backoff(i)
            backoffs.append(backoff)
        assert backoffs[0] == 1.0
        assert backoffs[1] == 2.0
        assert backoffs[2] == 4.0
        assert backoffs[3] == 8.0
        assert backoffs[4] == 16.0
        assert all(b == 20.0 for b in backoffs[5:])

    def test_custom_configuration_for_fast_retries(self):
        strategy = RetryStrategy(initial_backoff=0.1, max_backoff=2.0, multiplier=1.5)
        backoffs = [strategy.calculate_backoff(i) for i in range(5)]
        assert all(b <= 2.0 for b in backoffs)
        assert backoffs[0] == 0.1

    def test_custom_configuration_for_slow_retries(self):
        strategy = RetryStrategy(initial_backoff=5.0, max_backoff=300.0, multiplier=2.0)
        backoffs = [strategy.calculate_backoff(i) for i in range(5)]
        assert backoffs[0] == 5.0
        assert backoffs[1] == 10.0
        assert backoffs[2] == 20.0
