"""Download result formatter for user-friendly output.

This module provides senior-level formatting for download results,
displaying successful and failed downloads in an organized manner.

Example:
    >>> from src.presentation.cvm_docs.download_result_formatter import DownloadResultFormatter
    >>> from src.brazil.cvm.fundamental_stocks_data.domain import DownloadResultCVM
    >>>
    >>> result = DownloadResultCVM()
    >>> result.add_success_downloads("DFP_2023")
    >>> result.add_error_downloads("ITR_2023", "Network timeout")
    >>>
    >>> formatter = DownloadResultFormatter()
    >>> formatter.print_result(result)
"""

from ...brazil import DownloadResultCVM


class DownloadResultFormatter:
    """Senior-level formatter for download results.

    This class provides clean, organized, and easy-to-understand output
    for displaying download operation results to end users.

    The format automatically adapts based on the result:
    - If there are failures: Shows only the failures section
    - If all successful: Shows a success summary
    """

    # ANSI color codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    def __init__(self, use_colors: bool = True) -> None:
        """
        Initializes the formatter.

        Args:
            use_colors: Whether to use ANSI color codes in the output.
                        Set to False for plain text output.
        """
        self.use_colors = use_colors

    def _colorize(self, text: str, color: str) -> str:
        """
        Applies color to text if colors are enabled.

        Args:
            text: The text to colorize.
            color: The color code.

        Returns:
            The colorized text or plain text.
        """
        if not self.use_colors:
            return text
        return f'{color}{text}{self.RESET}'

    def format_result(self, result: DownloadResultCVM) -> str:
        """
        Formats the download result with a smart layout.

        It shows only relevant sections:
        - If there are failures, it displays the failures section only.
        - If all successful, it displays a success summary only.

        Args:
            result: The DownloadResultCVM object to format.

        Returns:
            A formatted output string.

        Example (with failures):
            >>> result = DownloadResultCVM()
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
            >>> result = DownloadResultCVM()
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
        lines.append('')
        lines.append(self._colorize('📥 CVM Documents Download', self.BOLD))
        lines.append(
            self._colorize(
                '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
                self.BOLD,
            )
        )

        # Status message
        if (
            result.error_count_downloads == 0
            and result.success_count_downloads > 0
        ):
            lines.append(
                self._colorize(
                    '✓ Documents downloaded successfully!', self.GREEN
                )
            )
        elif (
            result.success_count_downloads > 0
            and result.error_count_downloads > 0
        ):
            lines.append(
                self._colorize(
                    '⚠ Download completed with some errors.', self.YELLOW
                )
            )
        else:
            lines.append(
                self._colorize('✗ Document download failed.', self.RED)
            )

        lines.append('')

        # Summary Section
        total = result.success_count_downloads + result.error_count_downloads
        lines.append(self._colorize('📊 Summary:', self.BOLD))
        lines.append(f'  • Total files: {total}')
        lines.append(
            f'  • Success: {self._colorize(str(result.success_count_downloads), self.GREEN)}'
        )
        lines.append(
            f'  • Errors: {self._colorize(str(result.error_count_downloads), self.RED if result.error_count_downloads > 0 else self.RESET)}'
        )
        lines.append(f'  • Elapsed time: {result.elapsed_time:.1f}s')

        lines.append('')

        # Files Section
        if result.successful_downloads:
            lines.append(self._colorize('📁 Downloaded files:', self.BOLD))
            for item in result.successful_downloads:
                # Clean up item name if needed (e.g., remove full path if present, though usually it's just doc_year)
                display_name = item.replace('_', ' - ')
                lines.append(
                    f'  {self._colorize("✓", self.GREEN)} {display_name}'
                )

        # Errors Section (if any)
        if result.failed_downloads:
            lines.append('')
            lines.append(self._colorize('❌ Errors:', self.BOLD))
            for item, error in result.failed_downloads.items():
                display_name = item.replace('_', ' - ')
                lines.append(
                    f'  {self._colorize("✗", self.RED)} {display_name}'
                )
                lines.append(f'    └─ Error: {error}')

        return '\n'.join(lines)

    def print_result(self, result: DownloadResultCVM) -> None:
        """
        A convenience method to directly print the formatted result.

        Args:
            result: The DownloadResultCVM object to print.

        Example:
            >>> result = DownloadResultCVM()
            >>> result.add_success_downloads("DFP_2023")
            >>> formatter = DownloadResultFormatter()
            >>> formatter.print_result(result)
        """
        print(self.format_result(result))
