from unittest.mock import patch

from src.brazil.cvm.fundamental_stocks_data.utils.progress import SimpleProgressBar


class TestSimpleProgressBar:
    def test_init_with_positive_total(self, capsys):
        bar = SimpleProgressBar(total=10, desc="Test", width=40)

        assert bar.total == 10
        assert bar.desc == "Test"
        assert bar.width == 40
        assert bar.current == 0
        assert bar._last_print_time == 0.0

        captured = capsys.readouterr()
        assert "Test: Starting download of 10 files..." in captured.out

    def test_init_with_zero_total(self, capsys):
        bar = SimpleProgressBar(total=0, desc="Test")

        assert bar.total == 0
        assert bar.current == 0

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_init_with_negative_total_converted_to_zero(self, capsys):
        bar = SimpleProgressBar(total=-5, desc="Test")

        assert bar.total == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_init_with_custom_width(self, capsys):
        bar = SimpleProgressBar(total=10, desc="Test", width=20)

        assert bar.width == 20

    def test_init_with_string_total_converted_to_int(self, capsys):
        bar = SimpleProgressBar(total="10", desc="Test")

        assert bar.total == 10
        assert isinstance(bar.total, int)

    def test_init_with_string_width_converted_to_int(self, capsys):
        bar = SimpleProgressBar(total=10, width="50")

        assert bar.width == 50
        assert isinstance(bar.width, int)

    def test_init_with_float_total_converted_to_int(self, capsys):
        bar = SimpleProgressBar(total=10.7, desc="Test")

        assert bar.total == 10
        assert isinstance(bar.total, int)

    def test_update_increments_current(self):
        bar = SimpleProgressBar(total=10)

        bar.update(1)
        assert bar.current == 1

        bar.update(2)
        assert bar.current == 3

        bar.update(5)
        assert bar.current == 8

    def test_update_with_string_amount_converted_to_int(self):
        bar = SimpleProgressBar(total=10)

        bar.update("3")
        assert bar.current == 3

    def test_update_with_float_amount_converted_to_int(self):
        bar = SimpleProgressBar(total=10)

        bar.update(2.7)
        assert bar.current == 2

    def test_update_with_zero_total_does_not_print(self, capsys):
        bar = SimpleProgressBar(total=0)

        with patch("time.time", return_value=100.0):
            bar.update(1)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_update_prints_only_when_time_threshold_exceeded(self, capsys):
        bar = SimpleProgressBar(total=10, desc="Test")
        capsys.readouterr()  # Clear initial output

        with patch("time.time") as mock_time:
            mock_time.return_value = 0.0
            bar._last_print_time = 0.0

            # Update without crossing threshold
            bar.update(1)
            mock_time.return_value = 0.05  # Less than 0.1s
            bar.update(1)

            captured = capsys.readouterr()
            assert captured.out == ""

            # Update crossing threshold
            mock_time.return_value = 0.15  # More than 0.1s
            bar.update(1)

            captured = capsys.readouterr()
            assert "Test" in captured.out
            assert "[" in captured.out
            assert "]" in captured.out

    def test_update_prints_when_current_reaches_total(self, capsys):
        bar = SimpleProgressBar(total=5, desc="Test")
        capsys.readouterr()  # Clear initial output

        with patch("time.time", return_value=0.0):
            bar._last_print_time = 0.0
            bar.update(5)  # Reach total immediately

        captured = capsys.readouterr()
        assert "Test" in captured.out

    def test_print_shows_correct_percentage(self, capsys):
        bar = SimpleProgressBar(total=100, desc="Test")
        capsys.readouterr()  # Clear initial output

        bar.current = 50
        bar._print()

        captured = capsys.readouterr()
        assert "50/100" in captured.out
        assert "50%" in captured.out

    def test_print_shows_full_bar_at_100_percent(self, capsys):
        bar = SimpleProgressBar(total=100, desc="Test", width=10)
        capsys.readouterr()  # Clear initial output

        bar.current = 100
        bar._print()

        captured = capsys.readouterr()
        assert "█" * 10 in captured.out

    def test_print_shows_empty_bar_at_0_percent(self, capsys):
        bar = SimpleProgressBar(total=100, desc="Test", width=10)
        capsys.readouterr()  # Clear initial output

        bar.current = 0
        bar._print()

        captured = capsys.readouterr()
        assert "░" * 10 in captured.out

    def test_print_with_zero_total_returns_early(self, capsys):
        bar = SimpleProgressBar(total=0)

        bar._print()

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_partial_progress(self, capsys):
        bar = SimpleProgressBar(total=10, desc="Test", width=10)
        capsys.readouterr()  # Clear initial output

        bar.current = 5
        bar._print()

        captured = capsys.readouterr()
        assert "5/10" in captured.out
        assert "50%" in captured.out
        # Should have 5 filled and 5 empty blocks
        assert captured.out.count("█") == 5
        assert captured.out.count("░") == 5

    def test_close_with_positive_total(self, capsys):
        bar = SimpleProgressBar(total=10, desc="Test")
        capsys.readouterr()  # Clear initial output

        bar.current = 10
        bar.close()

        captured = capsys.readouterr()
        assert "Test" in captured.out
        assert "\n" in captured.out

    def test_close_with_zero_total(self, capsys):
        bar = SimpleProgressBar(total=0)
        capsys.readouterr()

        bar.close()

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_close_prints_final_state(self, capsys):
        bar = SimpleProgressBar(total=20, desc="Final", width=20)
        capsys.readouterr()  # Clear initial output

        bar.current = 15

        with patch("time.time", return_value=0.0):
            bar._last_print_time = 1000.0  # Ensure time threshold is passed
            bar.close()

        captured = capsys.readouterr()
        assert "Final" in captured.out
        assert "15/20" in captured.out

    def test_complete_workflow(self, capsys):
        bar = SimpleProgressBar(total=5, desc="Download")
        capsys.readouterr()  # Clear initial output

        with patch("time.time") as mock_time:
            mock_time.return_value = 0.0
            bar._last_print_time = 0.0

            for i in range(1, 6):
                mock_time.return_value = i * 0.02
                bar.update(1)

            bar.close()

        captured = capsys.readouterr()
        assert "Download" in captured.out
        assert "5/5" in captured.out

    def test_default_width_is_40(self, capsys):
        bar = SimpleProgressBar(total=10)

        assert bar.width == 40

    def test_default_desc_is_empty_string(self, capsys):
        bar = SimpleProgressBar(total=10)

        assert bar.desc == ""

    def test_multiple_instances_independent(self, capsys):
        bar1 = SimpleProgressBar(total=10, desc="Bar1")
        bar2 = SimpleProgressBar(total=20, desc="Bar2")
        capsys.readouterr()

        bar1.update(5)
        bar2.update(10)

        assert bar1.current == 5
        assert bar2.current == 10
        assert bar1.total == 10
        assert bar2.total == 20

    def test_large_total(self, capsys):
        bar = SimpleProgressBar(total=1000000, desc="Large")
        capsys.readouterr()

        bar.current = 500000
        bar._print()

        captured = capsys.readouterr()
        assert "500000/1000000" in captured.out
        assert "50%" in captured.out

    def test_edge_case_one_percent(self, capsys):
        bar = SimpleProgressBar(total=100, desc="Test", width=100)
        capsys.readouterr()

        bar.current = 1
        bar._print()

        captured = capsys.readouterr()
        assert "1/100" in captured.out
        assert "1%" in captured.out
        assert captured.out.count("█") == 1
        assert captured.out.count("░") == 99

    def test_current_exceeds_total(self, capsys):
        bar = SimpleProgressBar(total=10, desc="Test", width=10)
        capsys.readouterr()

        bar.current = 15
        bar._print()

        captured = capsys.readouterr()
        assert "15/10" in captured.out
        # Percentage should be > 100%
        assert "150%" in captured.out

    def test_update_negative_amount(self):
        bar = SimpleProgressBar(total=10)

        bar.current = 5
        bar.update(-2)

        assert bar.current == 3

    def test_bar_visual_correctness(self, capsys):
        bar = SimpleProgressBar(total=100, desc="Test", width=10)
        capsys.readouterr()

        test_cases = [
            (0, 0, 10),  # 0% filled, 10 empty
            (25, 2, 8),  # 25% filled, ~2-3 filled
            (50, 5, 5),  # 50% filled, 5 filled
            (75, 7, 3),  # 75% filled, ~7-8 filled
            (100, 10, 0),  # 100% filled, 10 filled
        ]

        for current, min_filled, min_empty in test_cases:
            bar.current = current
            bar._print()

            captured = capsys.readouterr()
            filled_count = captured.out.count("█")
            empty_count = captured.out.count("░")

            assert (
                filled_count + empty_count == 10
            ), f"Total bars should be 10 at {current}%"
            assert (
                filled_count == (bar.width * current) // 100
            ), f"Filled count mismatch at {current}%"
