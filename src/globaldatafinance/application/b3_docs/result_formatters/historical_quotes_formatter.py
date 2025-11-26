from typing import Any, Dict


class HistoricalQuotesResultFormatter:
    """Formats and generates messages for historical quotes extraction results.

    This class is responsible for:
    - Generating user-friendly messages from extraction results
    - Determining success/failure status
    - Formatting statistics and summaries

    This follows Single Responsibility Principle by moving presentation
    logic out of the Use Case layer.
    """

    @staticmethod
    def generate_message(result: Dict[str, Any]) -> str:
        """Generate a user-friendly message from extraction results.

        Args:
            result: Dictionary containing extraction results with keys:
                   - error_count (int): Number of errors
                   - total_records (int): Total records extracted
                   - success_count (int): Number of successful files
                   - total_files (int): Total files processed
                   - output_file (str): Path to output file

        Returns:
            Formatted message string describing the extraction results
        """
        if result["error_count"] == 0:
            return (
                f"Successfully extracted {result['total_records']:,} records "
                f"from {result['success_count']} files. "
                f"Saved to: {result['output_file']}"
            )
        else:
            return (
                f"Extraction completed with errors. "
                f"Processed {result['success_count']}/{result['total_files']} files. "
                f"Extracted {result['total_records']:,} records. "
                f"Errors: {result['error_count']}"
            )

    @staticmethod
    def determine_success(result: Dict[str, Any]) -> bool:
        """Determine if extraction was successful based on error count.

        Args:
            result: Dictionary containing extraction results

        Returns:
            True if no errors occurred, False otherwise
        """
        result_bool: bool = result.get("error_count", 0) == 0
        return result_bool

    @staticmethod
    def enrich_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich extraction result with success flag and message.

        This method adds presentation-layer information to the result
        dictionary returned by the extraction service.

        Args:
            result: Raw extraction result from service layer

        Returns:
            Enriched result with 'success' and 'message' fields
        """
        result["success"] = HistoricalQuotesResultFormatter.determine_success(result)
        result["message"] = HistoricalQuotesResultFormatter.generate_message(result)
        return result
