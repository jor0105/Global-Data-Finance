"""Stream COTAHIST lines from ZIP archives and plain TXT files."""

import asyncio
import zipfile
from collections.abc import AsyncIterator
from pathlib import Path

from ....macro_exceptions import CorruptedZipError, ExtractionError
from ....macro_infra import ExtractorAdapter


class ZipFileReaderB3:
    """Reader for ZIP and plain TXT files that streams content in memory.

    Uses the centralized ExtractorAdapter for ZIP archives, and direct
    streaming for uncompressed COTAHIST TXT files.
    """

    async def read_lines_from_zip(self, zip_path: str) -> AsyncIterator[str]:
        """Read TXT lines directly or from ZIP without extracting to disk.

        Args:
            zip_path: Path to the ZIP archive or uncompressed TXT file

        Yields:
            Lines from the file (decoded as latin-1)

        Raises:
            FileNotFoundError: If the file doesn't exist
            CorruptedZipError: If file is not a valid ZIP archive
            ExtractionError: If no TXT file found in ZIP
        """
        if isinstance(zip_path, str) and not zip_path:
            raise ValueError('zip_path cannot be empty')

        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f'File not found: {zip_path}')

        member_name = self._validate_cotahist_input(path)
        if path.suffix.lower() == '.txt':
            async for line in self._read_lines_from_txt(path):
                yield line
            return

        if member_name is None:
            raise ExtractionError(str(path), 'COTAHIST ZIP member is missing')
        extractor = ExtractorAdapter()
        async for line in extractor.extract_txt_from_zip_async(
            zip_path, member_name=member_name
        ):
            yield line

    @staticmethod
    def _validate_cotahist_input(path: Path) -> str | None:
        """Reuse the catalog contract before an input reaches the parser."""
        from .catalog import CotahistCatalogError, validate_cotahist_input

        try:
            return validate_cotahist_input(path)
        except CotahistCatalogError as error:
            if isinstance(error.__cause__, CorruptedZipError):
                raise error.__cause__ from error
            if isinstance(error.__cause__, zipfile.BadZipFile):
                raise CorruptedZipError(
                    str(path), str(error.__cause__)
                ) from error
            raise ExtractionError(str(path), str(error)) from error

    async def _read_lines_from_txt(self, txt_path: Path) -> AsyncIterator[str]:
        with txt_path.open(encoding='latin-1', errors='replace') as f:
            for line_count, line in enumerate(f, start=1):
                yield line.rstrip('\r\n')
                if line_count % ExtractorAdapter.CHUNK_SIZE_TXT == 0:
                    await asyncio.sleep(0)
