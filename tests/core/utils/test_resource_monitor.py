import time
from unittest.mock import Mock, patch

from datafinc.core.utils import ResourceLimits, ResourceMonitor, ResourceState


class TestResourceMonitor:
    def setup_method(self):
        ResourceMonitor._instance = None

    def test_singleton_pattern(self):
        monitor1 = ResourceMonitor()
        monitor2 = ResourceMonitor()
        assert monitor1 is monitor2

    def test_initialization_with_default_limits(self):
        monitor = ResourceMonitor()
        assert monitor.limits is not None
        assert monitor.limits.memory_warning_threshold == 70.0
        assert monitor.limits.memory_critical_threshold == 85.0

    def test_initialization_with_custom_limits(self):
        custom_limits = ResourceLimits(
            memory_warning_threshold=60.0,
            memory_critical_threshold=80.0,
            min_free_memory_mb=200,
        )
        monitor = ResourceMonitor(limits=custom_limits)
        assert monitor.limits.memory_warning_threshold == 60.0
        assert monitor.limits.min_free_memory_mb == 200

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_check_resources_healthy(self, mock_psutil):
        mock_memory = Mock()
        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3
        mock_memory.total = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 30.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.HEALTHY

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_check_resources_warning(self, mock_psutil):
        mock_memory = Mock()
        mock_memory.percent = 75.0
        mock_memory.available = 500 * 1024**2
        mock_memory.total = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.WARNING

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_check_resources_critical(self, mock_psutil):
        mock_memory = Mock()
        mock_memory.percent = 90.0
        mock_memory.available = 200 * 1024**2
        mock_memory.total = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.CRITICAL

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_check_resources_exhausted(self, mock_psutil):
        mock_memory = Mock()
        mock_memory.percent = 96.0
        mock_memory.available = 50 * 1024**2
        mock_memory.total = 8 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.EXHAUSTED

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_circuit_breaker_cooldown(self, mock_psutil):
        mock_memory = Mock()
        mock_memory.total = 8 * 1024**3
        mock_memory.percent = 96.0
        mock_memory.available = 50 * 1024**2
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        custom_limits = ResourceLimits(circuit_breaker_cooldown_seconds=1)
        monitor = ResourceMonitor(limits=custom_limits)

        state = monitor.check_resources()
        assert state == ResourceState.EXHAUSTED

        time.sleep(1.1)

        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3

        state = monitor.check_resources()
        assert state == ResourceState.HEALTHY

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_get_safe_worker_count_reduces_on_pressure(self, mock_psutil):
        ResourceMonitor._instance = None

        mock_memory = Mock()
        mock_memory.total = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 30.0

        monitor = ResourceMonitor()

        mock_memory.percent = 75.0
        mock_memory.available = 500 * 1024**2
        workers = monitor.get_safe_worker_count(8)
        assert workers == 4

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_get_safe_batch_size_reduces_on_pressure(self, mock_psutil):
        ResourceMonitor._instance = None

        mock_memory = Mock()
        mock_memory.total = 8 * 1024**3
        mock_memory.percent = 75.0
        mock_memory.available = 500 * 1024**2
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 30.0

        monitor = ResourceMonitor()

        batch_size = monitor.get_safe_batch_size(100_000)
        assert batch_size == 50_000

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_wait_for_resources_success(self, mock_psutil):
        ResourceMonitor._instance = None

        mock_memory = Mock()
        mock_memory.total = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_memory.available = 2 * 1024**3
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()

        result = monitor.wait_for_resources(
            required_state=ResourceState.WARNING, timeout_seconds=2
        )
        assert result is True

    @patch("datafinc.core.utils.resource_monitor.psutil", None)
    def test_no_psutil_fallback(self):
        ResourceMonitor._instance = None
        monitor = ResourceMonitor()

        state = monitor.check_resources()
        assert state == ResourceState.HEALTHY

    @patch("datafinc.core.utils.resource_monitor.psutil")
    def test_minimum_free_memory_threshold(self, mock_psutil):
        mock_memory = Mock()
        mock_memory.total = 8 * 1024**3
        mock_memory.percent = 80.0
        mock_memory.available = 50 * 1024**2
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 50.0

        monitor = ResourceMonitor()
        state = monitor.check_resources()

        assert state == ResourceState.EXHAUSTED
