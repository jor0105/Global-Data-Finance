"""Download result formatter for user-friendly output.

This module provides senior-level formatting for download results,
displaying successful and failed downloads in an organized manner.

Example:
    >>> from src.presentation.cvm_docs.download_result_formatter import DownloadResultFormatter
    >>> from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResult
    >>>
    >>> result = DownloadResult()
    >>> result.add_success_downloads("DFP_2023")
    >>> result.add_error_downloads("ITR_2023", "Network timeout")
    >>>
    >>> formatter = DownloadResultFormatter()
    >>> formatter.print_result(result)
"""

from src.brazil.cvm.fundamental_stocks_data import DownloadResult


class DownloadResultFormatter:
    """Senior-level formatter for download results.

    This class provides clean, organized, and easy-to-understand output
    for displaying download operation results to end users.

    The format automatically adapts based on the result:
    - If there are failures: Shows only the failures section
    - If all successful: Shows a success summary
    """

    # Color codes for terminal output
    _GREEN = "\033[92m"
    _RED = "\033[91m"
    _RESET = "\033[0m"
    _BOLD = "\033[1m"

    def __init__(self, use_colors: bool = True) -> None:
        """Initialize the formatter.

        Args:
            use_colors: Whether to use ANSI color codes in output.
                       Set to False for plain text output.
        """
        self.use_colors = use_colors

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled.

        Args:
            text: Text to colorize.
            color: Color code.

        Returns:
            Colorized text or plain text.
        """
        if not self.use_colors:
            return text
        return f"{color}{text}{self._RESET}"

    def format_result(self, result: DownloadResult) -> str:
        """Format download result with smart layout.

        Shows only relevant sections:
        - If there are failures: displays failures section only
        - If all successful: displays success summary only

        Args:
            result: DownloadResult object to format.

        Returns:
            Formatted output string.

        Example (with failures):
            >>> result = DownloadResult()
            >>> result.add_success_downloads("DFP_2023")
            >>> result.add_success_downloads("FRE_2023")
            >>> result.add_error_downloads("ITR_2023", "Connection timeout")
            >>> formatter = DownloadResultFormatter()
            >>> print(formatter.format_result(result))

            ╔════════════════════════════════════════╗
            ║    DOWNLOAD OPERATION COMPLETED        ║
            ╚════════════════════════════════════════╝

            ✗ FAILED DOWNLOADS (1)
            ────────────────────────────
              • ITR_2023
                └─ Error: Connection timeout

            SUMMARY: 2 succeeded, 1 failed out of 3 total

        Example (all successful):
            >>> result = DownloadResult()
            >>> result.add_success_downloads("DFP_2023")
            >>> result.add_success_downloads("FRE_2023")
            >>> formatter = DownloadResultFormatter()
            >>> print(formatter.format_result(result))

            ╔════════════════════════════════════════╗
            ║    DOWNLOAD OPERATION COMPLETED        ║
            ╚════════════════════════════════════════╝

            ✓ ALL SUCCESSFUL DOWNLOADS (2)
            ────────────────────────────

            SUMMARY: 2 succeeded out of 2 total
        """
        lines = []

        # Header
        lines.append("")
        lines.append(
            self._colorize(
                "╔════════════════════════════════════════╗",
                self._BOLD,
            )
        )
        lines.append(
            self._colorize(
                "║    DOWNLOAD OPERATION COMPLETED        ║",
                self._BOLD,
            )
        )
        lines.append(
            self._colorize(
                "╚════════════════════════════════════════╝",
                self._BOLD,
            )
        )

        # Failed downloads (only if there are failures)
        if result.failed_downloads:
            lines.append("")
            lines.append(
                self._colorize(
                    f"✗ FAILED DOWNLOADS ({result.error_count_downloads})",
                    self._RED,
                )
            )
            lines.append(self._colorize("────────────────────────────", self._RED))
            for item, error in result.failed_downloads.items():
                lines.append(f"  • {item}")
                lines.append(f"    └─ Error: {error}")
        else:
            # All successful
            lines.append("")
            lines.append(
                self._colorize(
                    f"✓ ALL SUCCESSFUL DOWNLOADS ({result.success_count_downloads})",
                    self._GREEN,
                )
            )
            lines.append(self._colorize("────────────────────────────", self._GREEN))

        # Summary line
        lines.append("")
        if result.failed_downloads:
            total = result.success_count_downloads + result.error_count_downloads
            summary = (
                f"SUMMARY: {result.success_count_downloads} succeeded, "
                f"{result.error_count_downloads} failed out of {total} total"
            )
        else:
            summary = f"SUMMARY: {result.success_count_downloads} succeeded out of {result.success_count_downloads} total"

        lines.append(self._colorize(summary, self._RESET))

        return "\n".join(lines)

    def print_result(self, result: DownloadResult) -> None:
        """Convenience method to directly print formatted result.

        Args:
            result: DownloadResult object to print.

        Example:
            >>> result = DownloadResult()
            >>> result.add_success_downloads("DFP_2023")
            >>> formatter = DownloadResultFormatter()
            >>> formatter.print_result(result)
        """
        print(self.format_result(result))
