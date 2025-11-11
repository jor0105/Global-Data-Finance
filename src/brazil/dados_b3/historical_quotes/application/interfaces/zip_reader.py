from typing import AsyncIterator, Protocol


class IZipReader(Protocol):
    """Interface for reading ZIP files in memory."""

    async def read_lines_from_zip(self, zip_path: str) -> AsyncIterator[str]:
        """Read lines from TXT file inside ZIP without extracting to disk.

        Args:
            zip_path: Path to the ZIP file

        Yields:
            Lines from the TXT file inside the ZIP

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            zipfile.BadZipFile: If file is not a valid ZIP
        """
        ...
