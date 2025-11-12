"""Tests for SimpleProgressBar utility."""

import io
from unittest.mock import patch

from src.core.utils.progress import SimpleProgressBar


class TestSimpleProgressBar:
    """Test suite for SimpleProgressBar."""

    def test_initialization_with_positive_total(self):
        """Test initialization with positive total."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=100, desc="Test", width=40)

            assert bar.total == 100
            assert bar.desc == "Test"
            assert bar.width == 40
            assert bar.current == 0

    def test_initialization_with_zero_total(self):
        """Test initialization with zero total."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=0, desc="Empty", width=40)

            assert bar.total == 0
            assert bar.current == 0

    def test_initialization_with_negative_total(self):
        """Test initialization with negative total converts to zero."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=-10, desc="Negative", width=40)

            assert bar.total == 0

    def test_initialization_prints_starting_message(self):
        """Test that initialization prints starting message for non-zero total."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            SimpleProgressBar(total=50, desc="Download", width=40)

            output = mock_stdout.getvalue()
            assert "Download: Starting download of 50 files" in output

    def test_initialization_no_print_for_zero_total(self):
        """Test that initialization doesn't print for zero total."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            SimpleProgressBar(total=0, desc="Empty", width=40)

            output = mock_stdout.getvalue()
            assert output == ""

    def test_update_increments_current(self):
        """Test that update increments current counter."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(1)
            assert bar.current == 1

            bar.update(3)
            assert bar.current == 4

    def test_update_with_custom_amount(self):
        """Test update with custom amount."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=100, desc="Test", width=40)

            bar.update(25)
            assert bar.current == 25

    def test_update_with_zero_amount(self):
        """Test update with zero amount."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(0)
            assert bar.current == 0

    def test_update_with_negative_amount(self):
        """Test update with negative amount."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.current = 5
            bar.update(-2)
            assert bar.current == 3

    def test_update_does_not_print_too_frequently(self):
        """Test that update respects print throttling."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=100, desc="Test", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar._last_print_time = 0.0
            with patch("time.time", return_value=0.05):
                bar.update(1)
                first_output = mock_stdout.getvalue()

            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            with patch("time.time", return_value=0.25):
                bar.update(1)
                second_output = mock_stdout.getvalue()

            assert first_output == ""
            assert second_output != ""

    def test_update_always_prints_at_completion(self):
        """Test that update always prints when reaching total."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=10, desc="Test", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.update(10)
            output = mock_stdout.getvalue()

            assert "10/10" in output
            assert "100%" in output

    def test_print_with_zero_total_does_nothing(self):
        """Test that _print does nothing with zero total."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=0, desc="Test", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar._print()
            output = mock_stdout.getvalue()

            assert output == ""

    def test_print_displays_correct_format(self):
        """Test that _print displays correct format."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=100, desc="Download", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.current = 50
            bar._print()
            output = mock_stdout.getvalue()

            assert "Download" in output
            assert "50/100" in output
            assert "50%" in output

    def test_print_displays_progress_bar_characters(self):
        """Test that _print displays progress bar with filled/empty characters."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=100, desc="Test", width=10)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.current = 50
            bar._print()
            output = mock_stdout.getvalue()

            assert "█" in output
            assert "░" in output

    def test_close_prints_final_state(self):
        """Test that close prints final state."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=10, desc="Test", width=40)
            bar.current = 10
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.close()
            output = mock_stdout.getvalue()

            assert "10/10" in output

    def test_close_prints_newline(self):
        """Test that close prints newline at end."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=10, desc="Test", width=40)
            bar.current = 5
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.close()
            output = mock_stdout.getvalue()

            assert output.endswith("\n")

    def test_close_with_zero_total_does_nothing(self):
        """Test that close does nothing with zero total."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=0, desc="Test", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.close()
            output = mock_stdout.getvalue()

            assert output == ""

    def test_full_workflow_with_updates(self):
        """Test complete workflow with multiple updates."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=5, desc="Process", width=20)

            for _ in range(5):
                bar.update(1)

            bar.close()

            assert bar.current == 5

    def test_exceeding_total_still_works(self):
        """Test that exceeding total doesn't break the bar."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(15)

            assert bar.current == 15

    def test_progress_calculation_accuracy(self):
        """Test progress percentage calculation accuracy."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=3, desc="Test", width=10)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.current = 1
            bar._print()
            output = mock_stdout.getvalue()

            assert "33%" in output

    def test_width_parameter_affects_bar_size(self):
        """Test that width parameter affects the bar size."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar_small = SimpleProgressBar(total=100, desc="Test", width=10)
            bar_large = SimpleProgressBar(total=100, desc="Test", width=50)

            assert bar_small.width == 10
            assert bar_large.width == 50

    def test_float_total_converts_to_int(self):
        """Test that float total is converted to int."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10.7, desc="Test", width=40)

            assert isinstance(bar.total, int)
            assert bar.total == 10

    def test_float_amount_converts_to_int(self):
        """Test that float amount is converted to int."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(2.9)

            assert isinstance(bar.current, int)
            assert bar.current == 2

    def test_desc_parameter_is_stored(self):
        """Test that desc parameter is properly stored."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Custom Description", width=40)

            assert bar.desc == "Custom Description"

    def test_empty_desc_works(self):
        """Test that empty description works."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="", width=40)

            assert bar.desc == ""

    def test_concurrent_updates_maintain_consistency(self):
        """Test that rapid consecutive updates maintain consistency."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=1000, desc="Test", width=40)

            for _ in range(100):
                bar.update(1)

            assert bar.current == 100

    def test_last_print_time_initialization(self):
        """Test that last print time is initialized."""
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            assert hasattr(bar, "_last_print_time")
            assert bar._last_print_time == 0.0

    def test_full_bar_display_at_50_percent(self):
        """Test bar display at exactly 50 percent."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=100, desc="Test", width=10)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.current = 50
            bar._print()
            output = mock_stdout.getvalue()

            filled_count = output.count("█")
            empty_count = output.count("░")

            assert filled_count == 5
            assert empty_count == 5

    def test_full_bar_display_at_100_percent(self):
        """Test bar display at 100 percent."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=100, desc="Test", width=10)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.current = 100
            bar._print()
            output = mock_stdout.getvalue()

            filled_count = output.count("█")
            empty_count = output.count("░")

            assert filled_count == 10
            assert empty_count == 0

    def test_full_bar_display_at_0_percent(self):
        """Test bar display at 0 percent."""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=100, desc="Test", width=10)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.current = 0
            bar._print()
            output = mock_stdout.getvalue()

            filled_count = output.count("█")
            empty_count = output.count("░")

            assert filled_count == 0
            assert empty_count == 10
