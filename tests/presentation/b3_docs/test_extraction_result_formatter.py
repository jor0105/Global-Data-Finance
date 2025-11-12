"""Tests for ExtractionResultFormatter."""

from src.presentation.b3_docs.extraction_result_formatter import (
    ExtractionResultFormatter,
)


class TestExtractionResultFormatter:
    """Test suite for ExtractionResultFormatter class."""

    def test_initialization_with_colors(self):
        """Test formatter initialization with colors enabled."""
        formatter = ExtractionResultFormatter(use_colors=True)
        assert formatter.use_colors is True

    def test_initialization_without_colors(self):
        """Test formatter initialization with colors disabled."""
        formatter = ExtractionResultFormatter(use_colors=False)
        assert formatter.use_colors is False

    def test_colorize_with_colors_enabled(self):
        """Test text colorization when colors are enabled."""
        formatter = ExtractionResultFormatter(use_colors=True)
        colored_text = formatter._colorize("test", formatter.GREEN)
        assert formatter.GREEN in colored_text
        assert formatter.RESET in colored_text
        assert "test" in colored_text

    def test_colorize_with_colors_disabled(self):
        """Test text colorization when colors are disabled."""
        formatter = ExtractionResultFormatter(use_colors=False)
        colored_text = formatter._colorize("test", formatter.GREEN)
        assert colored_text == "test"
        assert formatter.GREEN not in colored_text

    def test_print_result_success(self, capsys):
        """Test printing successful extraction results."""
        formatter = ExtractionResultFormatter(use_colors=False)

        result = {
            "success": True,
            "message": "Successfully extracted data",
            "total_files": 3,
            "success_count": 3,
            "error_count": 0,
            "total_records": 15000,
            "output_file": "/output/test.parquet",
        }

        formatter.print_result(result)
        captured = capsys.readouterr()

        assert "SUCCESS" in captured.out
        assert "Successfully extracted data" in captured.out
        assert "Total ZIP files processed: 3" in captured.out
        assert "Successfully processed: 3" in captured.out
        assert "Total records extracted: 15,000" in captured.out
        assert "/output/test.parquet" in captured.out

    def test_print_result_with_errors(self, capsys):
        """Test printing extraction results with errors."""
        formatter = ExtractionResultFormatter(use_colors=False)

        result = {
            "success": False,
            "message": "Extraction completed with errors",
            "total_files": 3,
            "success_count": 2,
            "error_count": 1,
            "total_records": 10000,
            "output_file": "/output/test.parquet",
            "errors": ["Error processing file3.zip: File corrupted"],
        }

        formatter.print_result(result)
        captured = capsys.readouterr()

        assert "ERRORS" in captured.out or "COMPLETED" in captured.out
        assert "Extraction completed with errors" in captured.out
        assert "Total ZIP files processed: 3" in captured.out
        assert "Successfully processed: 2" in captured.out
        assert "Failed to process: 1" in captured.out
        assert "Total records extracted: 10,000" in captured.out
        assert "Error processing file3.zip: File corrupted" in captured.out

    def test_print_result_minimal(self, capsys):
        """Test printing minimal extraction results."""
        formatter = ExtractionResultFormatter(use_colors=False)

        result = {
            "success": True,
            "total_files": 0,
            "success_count": 0,
            "error_count": 0,
            "total_records": 0,
        }

        formatter.print_result(result)
        captured = capsys.readouterr()

        assert "SUCCESS" in captured.out
        assert "Total ZIP files processed: 0" in captured.out
        assert "Total records extracted: 0" in captured.out
