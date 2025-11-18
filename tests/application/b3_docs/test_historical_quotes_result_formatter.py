from datafinance.application.b3_docs.result_formatters import (
    HistoricalQuotesResultFormatter,
)


class TestHistoricalQuotesResultFormatter:
    def test_generate_message_success(self):
        result = {
            "error_count": 0,
            "total_records": 1000,
            "success_count": 5,
            "total_files": 5,
            "output_file": "/path/to/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "Successfully extracted" in message
        assert "1,000 records" in message
        assert "from 5 files" in message
        assert "/path/to/output.parquet" in message

    def test_generate_message_with_errors(self):
        result = {
            "error_count": 2,
            "total_records": 500,
            "success_count": 3,
            "total_files": 5,
            "output_file": "/path/to/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "completed with errors" in message
        assert "3/5 files" in message
        assert "500 records" in message
        assert "Errors: 2" in message

    def test_determine_success_no_errors(self):
        result = {"error_count": 0}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is True

    def test_determine_success_with_errors(self):
        result = {"error_count": 1}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is False

    def test_determine_success_missing_error_count(self):
        result = {}

        success = HistoricalQuotesResultFormatter.determine_success(result)

        assert success is True

    def test_enrich_result_success(self):
        result = {
            "error_count": 0,
            "total_records": 1000,
            "success_count": 5,
            "total_files": 5,
            "output_file": "/path/to/output.parquet",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert enriched["success"] is True
        assert "message" in enriched
        assert "Successfully extracted" in enriched["message"]
        assert enriched is result

    def test_enrich_result_with_errors(self):
        result = {
            "error_count": 2,
            "total_records": 500,
            "success_count": 3,
            "total_files": 5,
            "output_file": "/path/to/output.parquet",
        }

        enriched = HistoricalQuotesResultFormatter.enrich_result(result)

        assert enriched["success"] is False
        assert "message" in enriched
        assert "completed with errors" in enriched["message"]

    def test_message_formatting_large_numbers(self):
        result = {
            "error_count": 0,
            "total_records": 1234567,
            "success_count": 10,
            "total_files": 10,
            "output_file": "/path/to/output.parquet",
        }

        message = HistoricalQuotesResultFormatter.generate_message(result)

        assert "1,234,567 records" in message
