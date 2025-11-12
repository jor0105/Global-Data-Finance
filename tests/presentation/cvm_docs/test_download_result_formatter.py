"""Tests for DownloadResultFormatter."""

from src.brazil.cvm.fundamental_stocks_data import DownloadResult
from src.presentation.cvm_docs.download_result_formatter import DownloadResultFormatter


class TestDownloadResultFormatter:
    """Test suite for DownloadResultFormatter."""

    def test_initialization_with_colors_enabled(self):
        """Test initialization with colors enabled."""
        formatter = DownloadResultFormatter(use_colors=True)
        assert formatter.use_colors is True

    def test_initialization_with_colors_disabled(self):
        """Test initialization with colors disabled."""
        formatter = DownloadResultFormatter(use_colors=False)
        assert formatter.use_colors is False

    def test_initialization_default_colors_enabled(self):
        """Test default initialization has colors enabled."""
        formatter = DownloadResultFormatter()
        assert formatter.use_colors is True

    def test_colorize_applies_color_when_enabled(self):
        """Test colorize applies color when enabled."""
        formatter = DownloadResultFormatter(use_colors=True)
        result = formatter._colorize("test", formatter.GREEN)
        assert formatter.GREEN in result
        assert formatter.RESET in result
        assert "test" in result

    def test_colorize_returns_plain_text_when_disabled(self):
        """Test colorize returns plain text when disabled."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = formatter._colorize("test", formatter.GREEN)
        assert result == "test"
        assert formatter.GREEN not in result

    def test_format_result_all_successful(self):
        """Test formatting when all downloads are successful."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_success_downloads("ITR_2023.zip")
        output = formatter.format_result(result)
        assert "ALL SUCCESSFUL DOWNLOADS (2)" in output
        assert "SUMMARY: 2 succeeded out of 2 total" in output
        assert "DOWNLOAD OPERATION COMPLETED" in output

    def test_format_result_with_failures(self):
        """Test formatting when some downloads failed."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_error_downloads("ITR_2023.zip", "Connection timeout")
        output = formatter.format_result(result)
        assert "FAILED DOWNLOADS (1)" in output
        assert "ITR_2023.zip" in output
        assert "Connection timeout" in output
        assert "SUMMARY: 1 succeeded, 1 failed out of 2 total" in output

    def test_format_result_only_failures(self):
        """Test formatting when all downloads failed."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_error_downloads("DFP_2023.zip", "Network error")
        result.add_error_downloads("ITR_2023.zip", "File not found")
        output = formatter.format_result(result)
        assert "FAILED DOWNLOADS (2)" in output
        assert "DFP_2023.zip" in output
        assert "ITR_2023.zip" in output
        assert "Network error" in output
        assert "File not found" in output
        assert "SUMMARY: 0 succeeded, 2 failed out of 2 total" in output

    def test_format_result_displays_header(self):
        """Test that format_result displays proper header."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        output = formatter.format_result(result)
        assert "╔════════════════════════════════════════╗" in output
        assert "║    DOWNLOAD OPERATION COMPLETED        ║" in output
        assert "╚════════════════════════════════════════╝" in output

    def test_format_result_empty_result(self):
        """Test formatting with empty result."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        output = formatter.format_result(result)
        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "ALL SUCCESSFUL DOWNLOADS (0)" in output

    def test_format_result_multiple_failures(self):
        """Test formatting with multiple failures."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2022.zip")
        result.add_error_downloads("ITR_2022.zip", "Network error")
        result.add_error_downloads("FCA_2022.zip", "File corrupted")
        result.add_error_downloads("FRE_2022.zip", "Timeout")
        output = formatter.format_result(result)
        assert "FAILED DOWNLOADS (3)" in output
        assert "ITR_2022.zip" in output
        assert "Network error" in output
        assert "FCA_2022.zip" in output
        assert "File corrupted" in output
        assert "FRE_2022.zip" in output
        assert "Timeout" in output

    def test_format_result_with_colors_contains_ansi_codes(self):
        """Test formatting with colors contains ANSI codes."""
        formatter = DownloadResultFormatter(use_colors=True)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        output = formatter.format_result(result)
        assert "\033[" in output

    def test_format_result_without_colors_no_ansi_codes(self):
        """Test formatting without colors has no ANSI codes."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        output = formatter.format_result(result)
        assert "\033[" not in output

    def test_print_result_calls_format_and_prints(self, capsys):
        """Test that print_result formats and prints the result."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        formatter.print_result(result)
        captured = capsys.readouterr()
        assert "DOWNLOAD OPERATION COMPLETED" in captured.out

    def test_print_result_with_errors(self, capsys):
        """Test print_result with errors."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_error_downloads("ITR_2023.zip", "Error")
        formatter.print_result(result)
        captured = capsys.readouterr()
        assert "DOWNLOAD OPERATION COMPLETED" in captured.out
        assert "FAILED DOWNLOADS" in captured.out

    def test_color_constants_are_defined(self):
        """Test that color constants are properly defined."""
        formatter = DownloadResultFormatter()
        assert hasattr(formatter, "GREEN")
        assert hasattr(formatter, "RED")
        assert hasattr(formatter, "YELLOW")
        assert hasattr(formatter, "BLUE")
        assert hasattr(formatter, "CYAN")
        assert hasattr(formatter, "BOLD")
        assert hasattr(formatter, "RESET")

    def test_format_result_preserves_newlines(self):
        """Test that formatted result contains proper newlines."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("file.zip")
        output = formatter.format_result(result)
        assert "\n" in output
        assert output.count("\n") > 3

    def test_format_result_summary_calculation_accuracy(self):
        """Test that summary calculations are accurate."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        for i in range(7):
            result.add_success_downloads(f"success_{i}.zip")
        for i in range(3):
            result.add_error_downloads(f"error_{i}.zip", f"Error {i}")
        output = formatter.format_result(result)
        assert "7 succeeded, 3 failed out of 10 total" in output

    def test_format_result_displays_error_indicators(self):
        """Test that error indicators are displayed correctly."""
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_error_downloads("file.zip", "Test error")
        output = formatter.format_result(result)
        assert "•" in output
