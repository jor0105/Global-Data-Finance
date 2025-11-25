import io
from unittest.mock import patch

from globaldatafinance.core.utils import SimpleProgressBar


class TestSimpleProgressBar:
    def test_initialization_with_positive_total(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=100, desc="Test", width=40)

            assert bar.total == 100
            assert bar.desc == "Test"
            assert bar.width == 40
            assert bar.current == 0

    def test_initialization_with_zero_total(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=0, desc="Empty", width=40)

            assert bar.total == 0
            assert bar.current == 0

    def test_initialization_with_negative_total(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=-10, desc="Negative", width=40)

            assert bar.total == 0

    def test_initialization_prints_starting_message(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            SimpleProgressBar(total=50, desc="Download", width=40)

            output = mock_stdout.getvalue()
            assert "Download: Starting download of 50 files" in output

    def test_initialization_no_print_for_zero_total(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            SimpleProgressBar(total=0, desc="Empty", width=40)

            output = mock_stdout.getvalue()
            assert output == ""

    def test_update_increments_current(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(1)
            assert bar.current == 1

            bar.update(3)
            assert bar.current == 4

    def test_update_with_custom_amount(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=100, desc="Test", width=40)

            bar.update(25)
            assert bar.current == 25

    def test_update_with_zero_amount(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(0)
            assert bar.current == 0

    def test_update_with_negative_amount(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.current = 5
            bar.update(-2)
            assert bar.current == 3

    def test_update_does_not_print_too_frequently(self):
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
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=10, desc="Test", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.update(10)
            output = mock_stdout.getvalue()

            assert "10/10" in output
            assert "100%" in output

    def test_print_with_zero_total_does_nothing(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=0, desc="Test", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar._print()
            output = mock_stdout.getvalue()

            assert output == ""

    def test_print_displays_correct_format(self):
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
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=10, desc="Test", width=40)
            bar.current = 10
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.close()
            output = mock_stdout.getvalue()

            assert "10/10" in output

    def test_close_prints_newline(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=10, desc="Test", width=40)
            bar.current = 5
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.close()
            output = mock_stdout.getvalue()

            assert output.endswith("\n")

    def test_close_with_zero_total_does_nothing(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=0, desc="Test", width=40)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.close()
            output = mock_stdout.getvalue()

            assert output == ""

    def test_full_workflow_with_updates(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=5, desc="Process", width=20)

            for _ in range(5):
                bar.update(1)

            bar.close()

            assert bar.current == 5

    def test_exceeding_total_still_works(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(15)

            assert bar.current == 15

    def test_progress_calculation_accuracy(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            bar = SimpleProgressBar(total=3, desc="Test", width=10)
            mock_stdout.truncate(0)
            mock_stdout.seek(0)

            bar.current = 1
            bar._print()
            output = mock_stdout.getvalue()

            assert "33%" in output

    def test_width_parameter_affects_bar_size(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar_small = SimpleProgressBar(total=100, desc="Test", width=10)
            bar_large = SimpleProgressBar(total=100, desc="Test", width=50)

            assert bar_small.width == 10
            assert bar_large.width == 50

    def test_float_total_converts_to_int(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10.7, desc="Test", width=40)

            assert isinstance(bar.total, int)
            assert bar.total == 10

    def test_float_amount_converts_to_int(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            bar.update(2.9)

            assert isinstance(bar.current, int)
            assert bar.current == 2

    def test_desc_parameter_is_stored(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Custom Description", width=40)

            assert bar.desc == "Custom Description"

    def test_empty_desc_works(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="", width=40)

            assert bar.desc == ""

    def test_concurrent_updates_maintain_consistency(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=1000, desc="Test", width=40)

            for _ in range(100):
                bar.update(1)

            assert bar.current == 100

    def test_last_print_time_initialization(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            bar = SimpleProgressBar(total=10, desc="Test", width=40)

            assert hasattr(bar, "_last_print_time")
            assert bar._last_print_time == 0.0

    def test_full_bar_display_at_50_percent(self):
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
