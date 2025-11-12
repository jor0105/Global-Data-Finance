from typing import AsyncIterator

from src.macro_infra import Extractor


class ZipFileReader:
    """Reader for ZIP files that streams TXT content in memory.

    Uses the centralized Extractor from macro_infra.
    """

    async def read_lines_from_zip(self, zip_path: str) -> AsyncIterator[str]:
        """Read lines from TXT file inside ZIP without extracting to disk.

        Args:
            zip_path: Path to the ZIP file

        Yields:
            Lines from the TXT file inside the ZIP (decoded as latin-1)

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If file is not a valid ZIP
            ExtractionError: If no TXT file found in ZIP
        """
        async for line in Extractor.read_txt_from_zip_async(zip_path):
            yield line
