from src.brazil.cvm.fundamental_stocks_data import DownloadResult
from src.presentation.cvm_docs.download_result_formatter import DownloadResultFormatter


class TestDownloadResultFormatterInitialization:
    def test_initialization_default_colors_enabled(self):
        formatter = DownloadResultFormatter()
        assert formatter.use_colors is True

    def test_initialization_with_colors_disabled(self):
        formatter = DownloadResultFormatter(use_colors=False)
        assert formatter.use_colors is False

    def test_initialization_with_colors_enabled(self):
        formatter = DownloadResultFormatter(use_colors=True)
        assert formatter.use_colors is True

    def test_formatter_has_color_constants(self):
        formatter = DownloadResultFormatter()
        assert hasattr(formatter, "_GREEN")
        assert hasattr(formatter, "_RED")
        assert hasattr(formatter, "_RESET")
        assert hasattr(formatter, "_BOLD")

    def test_color_constants_are_strings(self):
        formatter = DownloadResultFormatter()
        assert isinstance(formatter._GREEN, str)
        assert isinstance(formatter._RED, str)
        assert isinstance(formatter._RESET, str)
        assert isinstance(formatter._BOLD, str)


class TestDownloadResultFormatterWithSuccessfulDownloads:
    def test_format_result_all_successful_single_file(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✓ ALL SUCCESSFUL DOWNLOADS (1)" in output
        assert "SUMMARY: 1 succeeded out of 1 total" in output
        assert "✗ FAILED DOWNLOADS" not in output

    def test_format_result_all_successful_multiple_files(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_success_downloads("ITR_2023.zip")
        result.add_success_downloads("FCA_2023.zip")

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✓ ALL SUCCESSFUL DOWNLOADS (3)" in output
        assert "SUMMARY: 3 succeeded out of 3 total" in output
        assert "✗ FAILED DOWNLOADS" not in output

    def test_format_result_successful_contains_separator(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "────────────────────────────" in output

    def test_format_result_successful_contains_header_box(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "╔════════════════════════════════════════╗" in output
        assert "║    DOWNLOAD OPERATION COMPLETED        ║" in output
        assert "╚════════════════════════════════════════╝" in output


class TestDownloadResultFormatterWithFailures:
    def test_format_result_with_single_failure(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_success_downloads("ITR_2023.zip")
        result.add_error_downloads("DFP_2022.zip", "Connection timeout after 3 retries")

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✗ FAILED DOWNLOADS (1)" in output
        assert "DFP_2022.zip" in output
        assert "Connection timeout after 3 retries" in output
        assert "SUMMARY: 2 succeeded, 1 failed out of 3 total" in output
        assert "✓ ALL SUCCESSFUL DOWNLOADS" not in output

    def test_format_result_with_multiple_failures(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_error_downloads("ITR_2023.zip", "Network error")
        result.add_error_downloads("FCA_2023.zip", "File not found")
        result.add_error_downloads("FRE_2023.zip", "Permission denied")

        output = formatter.format_result(result)

        assert "✗ FAILED DOWNLOADS (3)" in output
        assert "ITR_2023.zip" in output
        assert "FCA_2023.zip" in output
        assert "FRE_2023.zip" in output
        assert "Network error" in output
        assert "File not found" in output
        assert "Permission denied" in output
        assert "SUMMARY: 1 succeeded, 3 failed out of 4 total" in output

    def test_format_result_only_failures(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_error_downloads("DFP_2023.zip", "Network error")
        result.add_error_downloads("ITR_2023.zip", "File not found")

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✗ FAILED DOWNLOADS (2)" in output
        assert "DFP_2023.zip" in output
        assert "ITR_2023.zip" in output
        assert "Network error" in output
        assert "File not found" in output
        assert "SUMMARY: 0 succeeded, 2 failed out of 2 total" in output

    def test_format_result_failure_displays_error_tree(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_error_downloads("DFP_2023.zip", "Connection timeout")

        output = formatter.format_result(result)

        assert "• DFP_2023.zip" in output
        assert "└─ Error: Connection timeout" in output

    def test_format_result_failure_with_long_error_message(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        long_error = (
            "Connection timeout after 3 retries. "
            "The server did not respond within the allocated time. "
            "Please check your network connection and try again."
        )
        result.add_error_downloads("DFP_2023.zip", long_error)

        output = formatter.format_result(result)

        assert "DFP_2023.zip" in output
        assert long_error in output


class TestDownloadResultFormatterEmptyResult:
    def test_format_result_empty(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✓ ALL SUCCESSFUL DOWNLOADS (0)" in output
        assert "SUMMARY: 0 succeeded out of 0 total" in output
        assert "✗ FAILED DOWNLOADS" not in output

    def test_format_result_empty_has_header(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()

        output = formatter.format_result(result)

        assert "╔════════════════════════════════════════╗" in output
        assert "║    DOWNLOAD OPERATION COMPLETED        ║" in output
        assert "╚════════════════════════════════════════╝" in output


class TestDownloadResultFormatterPrintResult:
    def test_print_result_outputs_to_stdout(self, capsys):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        formatter.print_result(result)
        captured = capsys.readouterr()

        assert "DOWNLOAD OPERATION COMPLETED" in captured.out
        assert "✓ ALL SUCCESSFUL DOWNLOADS" in captured.out

    def test_print_result_with_failures(self, capsys):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_error_downloads("ITR_2023.zip", "Error")

        formatter.print_result(result)
        captured = capsys.readouterr()

        assert "DOWNLOAD OPERATION COMPLETED" in captured.out
        assert "✗ FAILED DOWNLOADS" in captured.out

    def test_print_result_with_empty_result(self, capsys):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()

        formatter.print_result(result)
        captured = capsys.readouterr()

        assert "DOWNLOAD OPERATION COMPLETED" in captured.out
        assert "✓ ALL SUCCESSFUL DOWNLOADS (0)" in captured.out

    def test_print_result_returns_none(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()

        return_value = formatter.print_result(result)

        assert return_value is None


class TestDownloadResultFormatterColorsEnabled:
    def test_colors_enabled_contains_ansi_codes(self):
        formatter = DownloadResultFormatter(use_colors=True)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "\033[" in output

    def test_colors_enabled_green_for_success(self):
        formatter = DownloadResultFormatter(use_colors=True)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "\033[92m" in output  # GREEN

    def test_colors_enabled_red_for_failures(self):
        formatter = DownloadResultFormatter(use_colors=True)
        result = DownloadResult()
        result.add_error_downloads("DFP_2023.zip", "Error")

        output = formatter.format_result(result)

        assert "\033[91m" in output  # RED

    def test_colors_enabled_bold_for_header(self):
        formatter = DownloadResultFormatter(use_colors=True)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "\033[1m" in output  # BOLD

    def test_colors_enabled_reset_code_present(self):
        formatter = DownloadResultFormatter(use_colors=True)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "\033[0m" in output  # RESET


class TestDownloadResultFormatterColorsDisabled:
    def test_colors_disabled_no_ansi_codes(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_error_downloads("ITR_2023.zip", "Error")

        output = formatter.format_result(result)

        assert "\033[" not in output

    def test_colors_disabled_with_failures_no_ansi(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_error_downloads("DFP_2023.zip", "Network error")

        output = formatter.format_result(result)

        assert "\033[" not in output

    def test_colors_disabled_with_empty_result_no_ansi(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()

        output = formatter.format_result(result)

        assert "\033[" not in output


class TestDownloadResultFormatterColorizeMethod:
    def test_colorize_with_colors_enabled(self):
        formatter = DownloadResultFormatter(use_colors=True)
        text = "Test text"

        result = formatter._colorize(text, formatter._GREEN)

        assert result.startswith("\033[92m")  # GREEN
        assert result.endswith("\033[0m")  # RESET
        assert "Test text" in result

    def test_colorize_with_colors_disabled(self):
        formatter = DownloadResultFormatter(use_colors=False)
        text = "Test text"

        result = formatter._colorize(text, formatter._GREEN)

        assert result == "Test text"
        assert "\033[" not in result

    def test_colorize_preserves_text_content(self):
        formatter = DownloadResultFormatter(use_colors=True)
        text = "Important message with special chars: !@#$%"

        result = formatter._colorize(text, formatter._RED)

        assert "Important message with special chars: !@#$%" in result

    def test_colorize_with_empty_string(self):
        formatter = DownloadResultFormatter(use_colors=True)

        result = formatter._colorize("", formatter._GREEN)

        assert "\033[92m" in result
        assert "\033[0m" in result


class TestDownloadResultFormatterOutputStructure:
    def test_output_contains_newlines(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "\n" in output
        assert output.count("\n") > 5  # Should have multiple lines

    def test_output_starts_with_newline(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert output.startswith("\n")

    def test_output_ends_with_summary(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "SUMMARY:" in output
        assert output.strip().endswith("total")

    def test_output_sections_ordered_correctly(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        result.add_error_downloads("ITR_2023.zip", "Error")

        output = formatter.format_result(result)

        header_pos = output.find("DOWNLOAD OPERATION COMPLETED")
        failed_pos = output.find("✗ FAILED DOWNLOADS")
        summary_pos = output.find("SUMMARY:")

        assert header_pos < failed_pos < summary_pos


class TestDownloadResultFormatterEdgeCases:
    def test_format_result_with_special_characters_in_filename(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023 (final).zip")
        result.add_error_downloads("ITR_2023[updated].zip", "Error occurred")

        output = formatter.format_result(result)

        assert "ITR_2023[updated].zip" in output
        assert "Error occurred" in output

    def test_format_result_with_unicode_characters(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023_测试.zip")
        result.add_error_downloads("ITR_2023_тест.zip", "Ошибка соединения")

        output = formatter.format_result(result)

        assert "ITR_2023_тест.zip" in output
        assert "Ошибка соединения" in output

    def test_format_result_with_very_long_filename(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        long_filename = "DFP_" + "a" * 200 + ".zip"
        result.add_success_downloads(long_filename)

        output = formatter.format_result(result)

        assert "✓ ALL SUCCESSFUL DOWNLOADS (1)" in output
        assert "SUMMARY: 1 succeeded out of 1 total" in output

    def test_format_result_with_empty_error_message(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_error_downloads("DFP_2023.zip", "")

        output = formatter.format_result(result)

        assert "DFP_2023.zip" in output
        assert "└─ Error:" in output

    def test_format_result_preserves_error_message_whitespace(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        error_msg = "Error: Line 1\n    Line 2 indented"
        result.add_error_downloads("DFP_2023.zip", error_msg)

        output = formatter.format_result(result)

        assert error_msg in output


class TestDownloadResultFormatterMultipleResults:
    def test_format_result_large_number_of_successes(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        for i in range(100):
            result.add_success_downloads(f"DFP_202{i}.zip")

        output = formatter.format_result(result)

        assert "✓ ALL SUCCESSFUL DOWNLOADS (100)" in output
        assert "SUMMARY: 100 succeeded out of 100 total" in output

    def test_format_result_large_number_of_failures(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("DFP_2023.zip")
        for i in range(50):
            result.add_error_downloads(f"ITR_202{i}.zip", f"Error {i}")

        output = formatter.format_result(result)

        assert "✗ FAILED DOWNLOADS (50)" in output
        assert "SUMMARY: 1 succeeded, 50 failed out of 51 total" in output

    def test_format_result_balanced_success_and_failures(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        for i in range(5):
            result.add_success_downloads(f"DFP_202{i}.zip")
            result.add_error_downloads(f"ITR_202{i}.zip", "Error")

        output = formatter.format_result(result)

        assert "✗ FAILED DOWNLOADS (5)" in output
        assert "SUMMARY: 5 succeeded, 5 failed out of 10 total" in output


class TestDownloadResultFormatterIntegrationWithDownloadResult:
    def test_formatter_handles_download_result_correctly(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("File1.zip")
        result.add_success_downloads("File2.zip")
        result.add_error_downloads("File3.zip", "Error 1")

        output = formatter.format_result(result)

        assert result.success_count_downloads == 2
        assert result.error_count_downloads == 1
        assert "2 succeeded, 1 failed out of 3 total" in output

    def test_formatter_uses_download_result_methods(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success_downloads("A.zip")
        result.add_success_downloads("B.zip")

        output = formatter.format_result(result)

        assert f"({result.success_count_downloads})" in output
        assert str(result.success_count_downloads) in output
