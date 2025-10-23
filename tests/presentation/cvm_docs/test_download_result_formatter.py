from src.brazil.cvm.fundamental_stocks_data import DownloadResult
from src.presentation.cvm_docs.download_result_formatter import DownloadResultFormatter


class TestDownloadResultFormatterWithFailures:
    def test_format_result_with_failures(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success("DFP_2023.zip")
        result.add_success("ITR_2023.zip")
        result.add_error("DFP_2022.zip", "Connection timeout after 3 retries")

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✗ FAILED DOWNLOADS (1)" in output
        assert "DFP_2022.zip" in output
        assert "Connection timeout after 3 retries" in output
        assert "SUMMARY: 2 succeeded, 1 failed out of 3 total" in output
        assert "✓ ALL SUCCESSFUL DOWNLOADS" not in output

    def test_format_result_only_failures(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_error("DFP_2023.zip", "Network error")
        result.add_error("ITR_2023.zip", "File not found")

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✗ FAILED DOWNLOADS (2)" in output
        assert "DFP_2023.zip" in output
        assert "ITR_2023.zip" in output
        assert "Network error" in output
        assert "File not found" in output
        assert "SUMMARY: 0 succeeded, 2 failed out of 2 total" in output


class TestDownloadResultFormatterPrintResult:
    def test_print_result(self, capsys):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success("DFP_2023.zip")
        result.add_error("ITR_2023.zip", "Error")

        formatter.print_result(result)
        captured = capsys.readouterr()

        assert "DOWNLOAD OPERATION COMPLETED" in captured.out
        assert "✗ FAILED DOWNLOADS" in captured.out


class TestDownloadResultFormatterColors:
    def test_colors_disabled(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()
        result.add_success("DFP_2023.zip")
        result.add_error("ITR_2023.zip", "Error")

        output = formatter.format_result(result)

        assert "\033[" not in output

    def test_colors_enabled(self):
        formatter = DownloadResultFormatter(use_colors=True)
        result = DownloadResult()
        result.add_success("DFP_2023.zip")

        output = formatter.format_result(result)

        assert "\033[" in output


class TestDownloadResultFormatterEmptyResult:
    def test_format_result_empty(self):
        formatter = DownloadResultFormatter(use_colors=False)
        result = DownloadResult()

        output = formatter.format_result(result)

        assert "DOWNLOAD OPERATION COMPLETED" in output
        assert "✓ ALL SUCCESSFUL DOWNLOADS (0)" in output
        assert "SUMMARY: 0 succeeded out of 0 total" in output
