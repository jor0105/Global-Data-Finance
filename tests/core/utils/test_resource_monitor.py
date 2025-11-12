"""Tests for ResourceMonitor - memory and CPU monitoring with circuit breaker."""

import time
from unittest.mock import Mock, patch

from src.core.utils import ResourceLimits, ResourceMonitor, ResourceState


class TestResourceMonitor:
    """Test suite for ResourceMonitor with various resource states."""

    def setup_method(self):
        """Reset singleton before each test."""
        ResourceMonitor._instance = None

    def test_singleton_pattern(self):
        """Test that ResourceMonitor follows singleton pattern."""
        monitor1 = ResourceMonitor()
        monitor2 = ResourceMonitor()
        assert monitor1 is monitor2

    def test_initialization_with_default_limits(self):
        """Test initialization with default resource limits."""
        monitor = ResourceMonitor()
        assert monitor.limits is not None
        assert monitor.limits.memory_warning_threshold == 70.0
        assert monitor.limits.memory_critical_threshold == 85.0

    def test_initialization_with_custom_limits(self):
        """Test initialization with custom resource limits."""
        custom_limits = ResourceLimits(
            memory_warning_threshold=60.0,
            memory_critical_threshold=80.0,
            min_free_memory_mb=200,
        )
        monitor = ResourceMonitor(limits=custom_limits)
        assert monitor.limits.memory_warning_threshold == 60.0
        assert monitor.limits.min_free_memory_mb == 200

    @patch("src.core.utils.resource_monitor.psutil")
    def test_check_resources_healthy(self, mock_psutil):
        """Test resource check returns HEALTHY for good conditions."""
        mock_memory = Mock()
        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3  # 2GB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 30.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.HEALTHY

    @patch("src.core.utils.resource_monitor.psutil")
    def test_check_resources_warning(self, mock_psutil):
        """Test resource check returns WARNING at threshold."""
        mock_memory = Mock()
        mock_memory.percent = 75.0
        mock_memory.available = 500 * 1024**2  # 500MB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.WARNING

    @patch("src.core.utils.resource_monitor.psutil")
    def test_check_resources_critical(self, mock_psutil):
        """Test resource check returns CRITICAL for high usage."""
        mock_memory = Mock()
        mock_memory.percent = 90.0
        mock_memory.available = 200 * 1024**2  # 200MB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.CRITICAL

    @patch("src.core.utils.resource_monitor.psutil")
    def test_check_resources_exhausted(self, mock_psutil):
        """Test resource check returns EXHAUSTED and triggers circuit breaker."""
        mock_memory = Mock()
        mock_memory.percent = 96.0
        mock_memory.available = 50 * 1024**2  # 50MB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.EXHAUSTED
        assert monitor.is_circuit_breaker_active()

    @patch("src.core.utils.resource_monitor.psutil")
    def test_circuit_breaker_cooldown(self, mock_psutil):
        """Test circuit breaker resets after cooldown period."""
        mock_memory = Mock()
        mock_memory.percent = 96.0
        mock_memory.available = 50 * 1024**2
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        # Use very short cooldown for testing
        custom_limits = ResourceLimits(circuit_breaker_cooldown_seconds=1)
        monitor = ResourceMonitor(limits=custom_limits)

        # Trigger circuit breaker
        state = monitor.check_resources()
        assert state == ResourceState.EXHAUSTED
        assert monitor.is_circuit_breaker_active()

        # Wait for cooldown
        time.sleep(1.1)

        # Memory improved
        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3

        # Check again - should reset
        state = monitor.check_resources()
        assert state == ResourceState.HEALTHY
        assert not monitor.is_circuit_breaker_active()

    @patch("src.core.utils.resource_monitor.psutil")
    def test_get_safe_worker_count_reduces_on_pressure(self, mock_psutil):
        """Test worker count is reduced under memory pressure."""
        mock_memory = Mock()
        mock_psutil.virtual_memory.return_value = mock_memory

        monitor = ResourceMonitor()

        # Healthy state - full workers
        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3
        workers = monitor.get_safe_worker_count(8)
        assert workers == min(8, mock_psutil.cpu_count.return_value or 1)

        # Warning state - reduced workers
        mock_memory.percent = 75.0
        mock_memory.available = 500 * 1024**2
        workers = monitor.get_safe_worker_count(8)
        assert workers == 4  # Half of requested

        # Critical state - minimal workers
        mock_memory.percent = 90.0
        mock_memory.available = 200 * 1024**2
        workers = monitor.get_safe_worker_count(8)
        assert workers == 2  # Max 2 workers

        # Exhausted state - single worker
        mock_memory.percent = 96.0
        mock_memory.available = 50 * 1024**2
        workers = monitor.get_safe_worker_count(8)
        assert workers == 1

    @patch("src.core.utils.resource_monitor.psutil")
    def test_get_safe_batch_size_reduces_on_pressure(self, mock_psutil):
        """Test batch size is reduced under memory pressure."""
        mock_memory = Mock()
        mock_psutil.virtual_memory.return_value = mock_memory

        monitor = ResourceMonitor()

        # Healthy state - full batch size
        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3
        batch_size = monitor.get_safe_batch_size(100_000)
        assert batch_size == 100_000

        # Warning state - reduced
        mock_memory.percent = 75.0
        mock_memory.available = 500 * 1024**2
        batch_size = monitor.get_safe_batch_size(100_000)
        assert batch_size == 50_000

        # Critical state - heavily reduced
        mock_memory.percent = 90.0
        mock_memory.available = 200 * 1024**2
        batch_size = monitor.get_safe_batch_size(100_000)
        assert batch_size == 25_000

        # Exhausted state - minimum
        mock_memory.percent = 96.0
        mock_memory.available = 50 * 1024**2
        batch_size = monitor.get_safe_batch_size(100_000)
        assert batch_size == 1_000

    @patch("src.core.utils.resource_monitor.psutil")
    def test_wait_for_resources_success(self, mock_psutil):
        """Test waiting for resources to become available."""
        mock_memory = Mock()
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()

        # Start in critical state
        mock_memory.percent = 90.0
        mock_memory.available = 200 * 1024**2

        # After short delay, improve to healthy
        def side_effect(*args, **kwargs):
            mock_memory.percent = 50.0
            mock_memory.available = 2 * 1024**3
            return mock_memory

        mock_psutil.virtual_memory.side_effect = [mock_memory, side_effect()]

        # Should succeed
        result = monitor.wait_for_resources(
            required_state=ResourceState.WARNING, timeout_seconds=2
        )
        assert result is True

    @patch("src.core.utils.resource_monitor.psutil")
    def test_wait_for_resources_timeout(self, mock_psutil):
        """Test timeout when resources don't become available."""
        mock_memory = Mock()
        mock_memory.percent = 96.0  # Exhausted
        mock_memory.available = 50 * 1024**2
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()

        # Should timeout
        result = monitor.wait_for_resources(
            required_state=ResourceState.WARNING, timeout_seconds=1
        )
        assert result is False

    @patch("src.core.utils.resource_monitor.psutil", None)
    def test_no_psutil_fallback(self):
        """Test graceful degradation when psutil is not available."""
        monitor = ResourceMonitor()

        # Should return HEALTHY (conservative fallback)
        state = monitor.check_resources()
        assert state == ResourceState.HEALTHY

        # Memory info should indicate unavailable
        memory_info = monitor.get_memory_info()
        assert memory_info["available"] is False

    @patch("src.core.utils.resource_monitor.psutil")
    def test_minimum_free_memory_threshold(self, mock_psutil):
        """Test absolute minimum free memory trigger."""
        mock_memory = Mock()
        mock_memory.percent = 80.0  # Below exhausted threshold
        mock_memory.available = 50 * 1024**2  # 50MB - below minimum
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        # Should be exhausted due to absolute minimum
        assert state == ResourceState.EXHAUSTED
