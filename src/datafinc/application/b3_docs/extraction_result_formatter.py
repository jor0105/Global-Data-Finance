"""Formatter for extraction results display.

This module provides formatted output for B3 historical quotes extraction results,
making it easy for users to understand what happened during the extraction process.
"""

from typing import Any, Dict


class ExtractionResultFormatter:
    """Formats extraction results for user-friendly display.

    Provides colored, organized output showing:
    - Extraction summary
    - Success/error statistics
    - Output file location
    - Record counts
    - Error details if any
    """

    # ANSI color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        """Initialize the formatter.

        Args:
            use_colors: Whether to use ANSI colors in output (default: True)
        """
        self.use_colors = use_colors

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_colors:
            return f"{color}{text}{self.RESET}"
        return text

    def print_result(self, result: Dict[str, Any]) -> None:
        """Print formatted extraction results.

        Args:
            result: Dictionary containing extraction results with keys:
                   - success (bool)
                   - message (str)
                   - total_files (int)
                   - success_count (int)
                   - error_count (int)
                   - total_records (int)
                   - output_file (str)
                   - errors (list, optional)
        """
        print("\n" + "=" * 70)
        print(
            self._colorize(
                "  B3 HISTORICAL QUOTES EXTRACTION RESULTS", self.BOLD + self.CYAN
            )
        )
        print("=" * 70)

        # Status
        if result.get("success", False):
            status_text = "✓ SUCCESS"
            status_color = self.GREEN
        else:
            status_text = "✗ COMPLETED WITH ERRORS"
            status_color = self.YELLOW if result.get("error_count", 0) > 0 else self.RED

        print(f"\n{self._colorize(status_text, self.BOLD + status_color)}")

        # Summary message
        if "message" in result:
            print(f"\n{result['message']}")

        # Statistics
        print(f"\n{self._colorize('Extraction Statistics:', self.BOLD + self.BLUE)}")
        print(f"  Total ZIP files processed: {result.get('total_files', 0)}")
        success_msg = f"✓ Successfully processed: {result.get('success_count', 0)}"
        print(f"  {self._colorize(success_msg, self.GREEN)}")

        if result.get("error_count", 0) > 0:
            error_msg = f"✗ Failed to process: {result.get('error_count', 0)}"
            print(f"  {self._colorize(error_msg, self.RED)}")

        total_records = result.get("total_records", 0)
        records_msg = f"Total records extracted: {total_records:,}"
        print(f"  {self._colorize(records_msg, self.BOLD)}")

        # Output file
        if "output_file" in result:
            print(
                f"\n{self._colorize('Output File:', self.BOLD + self.BLUE)} {result['output_file']}"
            )

        # Error details
        if result.get("error_count", 0) > 0 and "errors" in result:
            print(f"\n{self._colorize('Error Details:', self.BOLD + self.RED)}")
            errors = result["errors"]
            if isinstance(errors, dict):
                for file_path, error_msg in errors.items():
                    print(f"  • {file_path}")
                    print(f"    {self._colorize('Error:', self.RED)} {error_msg}")
            else:
                for error in errors:
                    print(f"  • {error}")

        print("\n" + "=" * 70 + "\n")
