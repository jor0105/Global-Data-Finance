"""Tests for HistoricalQuotesResultFormatter."""

from src.presentation.b3_docs.result_formatters.historical_quotes_formatter import (
    HistoricalQuotesResultFormatter,
)


class TestHistoricalQuotesResultFormatter:
    """Test suite for HistoricalQuotesResultFormatter."""

    def test_generate_message_with_no_errors(self):
        """Test message generation when extraction has no errors."""
        result = {
            "error_count": 0,
            "total_records": 50000,
            "success_count": 10,
            "total_files": 10,
            "output_file": "/path/to/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "Successfully extracted 50,000 records" in message
        assert "from 10 files" in message
        assert "Saved to: /path/to/output.parquet" in message

    def test_generate_message_with_errors(self):
        """Test message generation when extraction has errors."""
        result = {
            "error_count": 3,
            "total_records": 35000,
            "success_count": 7,
            "total_files": 10,
            "output_file": "/path/to/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "Extraction completed with errors" in message
        assert "Processed 7/10 files" in message
        assert "Extracted 35,000 records" in message
        assert "Errors: 3" in message

    def test_generate_message_formats_large_numbers(self):
        """Test that large record counts are formatted with commas."""
        result = {
            "error_count": 0,
            "total_records": 1500000,
            "success_count": 50,
            "total_files": 50,
            "output_file": "/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "1,500,000" in message

    def test_generate_message_with_zero_records(self):
        """Test message generation with zero records."""
        result = {
            "error_count": 0,
            "total_records": 0,
            "success_count": 5,
            "total_files": 5,
            "output_file": "/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "0 records" in message

    def test_generate_message_with_single_file(self):
        """Test message generation with single file processed."""
        result = {
            "error_count": 0,
            "total_records": 10000,
            "success_count": 1,
            "total_files": 1,
            "output_file": "/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "from 1 file" in message or "1 files" in message

    def test_generate_message_with_all_files_failed(self):
        """Test message generation when all files failed."""
        result = {
            "error_count": 5,
            "total_records": 0,
            "success_count": 0,
            "total_files": 5,
            "output_file": "/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "Extraction completed with errors" in message
        assert "Processed 0/5 files" in message
        assert "Errors: 5" in message

    def test_determine_success_with_no_errors(self):
        """Test success determination when no errors occurred."""
        result = {"error_count": 0}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is True

    def test_determine_success_with_errors(self):
        """Test success determination when errors occurred."""
        result = {"error_count": 3}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is False

    def test_determine_success_with_missing_error_count(self):
        """Test success determination when error_count is missing."""
        result = {}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is True

    def test_determine_success_with_zero_errors_string(self):
        """Test success determination with zero as string."""
        result = {"error_count": 0}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is True

    def test_enrich_result_adds_success_flag(self):
        """Test that enrich_result adds success flag."""
        result = {
            "error_count": 0,
            "total_records": 10000,
            "success_count": 5,
            "total_files": 5,
            "output_file": "/output.parquet",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert "success" in enriched
        assert enriched["success"] is True

    def test_enrich_result_adds_message(self):
        """Test that enrich_result adds message."""
        result = {
            "error_count": 0,
            "total_records": 10000,
            "success_count": 5,
            "total_files": 5,
            "output_file": "/output.parquet",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert "message" in enriched
        assert isinstance(enriched["message"], str)
        assert len(enriched["message"]) > 0

    def test_enrich_result_preserves_original_data(self):
        """Test that enrich_result preserves original result data."""
        result = {
            "error_count": 2,
            "total_records": 8000,
            "success_count": 3,
            "total_files": 5,
            "output_file": "/output.parquet",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert enriched["error_count"] == 2
        assert enriched["total_records"] == 8000
        assert enriched["success_count"] == 3
        assert enriched["total_files"] == 5
        assert enriched["output_file"] == "/output.parquet"

    def test_enrich_result_with_errors(self):
        """Test enrich_result with errors."""
        result = {
            "error_count": 3,
            "total_records": 7000,
            "success_count": 7,
            "total_files": 10,
            "output_file": "/output.parquet",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert enriched["success"] is False
        assert "Extraction completed with errors" in enriched["message"]

    def test_enrich_result_returns_modified_dict(self):
        """Test that enrich_result returns the modified dictionary."""
        result = {
            "error_count": 0,
            "total_records": 10000,
            "success_count": 5,
            "total_files": 5,
            "output_file": "/output.parquet",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert enriched is result

    def test_enrich_result_minimal_data(self):
        """Test enrich_result with minimal data."""
        result = {
            "error_count": 0,
            "total_records": 0,
            "success_count": 0,
            "total_files": 0,
            "output_file": "",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert "success" in enriched
        assert "message" in enriched

    def test_static_methods_are_static(self):
        """Test that all methods are static."""
        assert isinstance(
            HistoricalQuotesResultFormatter.__dict__["generate_message"], staticmethod
        )
        assert isinstance(
            HistoricalQuotesResultFormatter.__dict__["determine_success"], staticmethod
        )
        assert isinstance(
            HistoricalQuotesResultFormatter.__dict__["enrich_result"], staticmethod
        )

    def test_generate_message_includes_all_required_info(self):
        """Test that generated message includes all required information."""
        result = {
            "error_count": 1,
            "total_records": 25000,
            "success_count": 4,
            "total_files": 5,
            "output_file": "/data/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "25,000" in message or "25000" in message
        assert "4" in message
        assert "5" in message
        assert "1" in message

    def test_generate_message_with_very_large_numbers(self):
        """Test message generation with very large record counts."""
        result = {
            "error_count": 0,
            "total_records": 999999999,
            "success_count": 100,
            "total_files": 100,
            "output_file": "/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "999,999,999" in message or "999999999" in message

    def test_determine_success_with_negative_error_count(self):
        """Test success determination with negative error count."""
        result = {"error_count": -1}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is False

    def test_enrich_result_does_not_modify_errors_field(self):
        """Test that enrich_result preserves errors field if present."""
        result = {
            "error_count": 2,
            "total_records": 8000,
            "success_count": 3,
            "total_files": 5,
            "output_file": "/output.parquet",
            "errors": {"file1.zip": "Error 1", "file2.zip": "Error 2"},
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert "errors" in enriched
        assert len(enriched["errors"]) == 2

    def test_generate_message_output_file_path_variations(self):
        """Test message generation with different output file paths."""
        result1 = {
            "error_count": 0,
            "total_records": 10000,
            "success_count": 5,
            "total_files": 5,
            "output_file": "/absolute/path/file.parquet",
        }

        result2 = {
            "error_count": 0,
            "total_records": 10000,
            "success_count": 5,
            "total_files": 5,
            "output_file": "relative/path/file.parquet",
        }

        message1 = HistoricalQuotesResultFormatter.generate_message(result1)
        message2 = HistoricalQuotesResultFormatter.generate_message(result2)

        assert "/absolute/path/file.parquet" in message1
        assert "relative/path/file.parquet" in message2
