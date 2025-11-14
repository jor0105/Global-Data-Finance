import asyncio
import zipfile
from pathlib import Path
from typing import IO, AsyncIterator, Iterator

from src.core import get_logger
from src.macro_exceptions import CorruptedZipError, ExtractionError

logger = get_logger(__name__)


class Extractor:
    """Generic file extraction utilities for ZIP archives.

    This class provides low-level, reusable extraction methods that can be
    used across different parts of the application. Domain-specific logic
    (like CSV to Parquet conversion) should be implemented in dedicated
    modules within their respective domains.
    """

    @staticmethod
    async def read_txt_from_zip_async(zip_path: str) -> AsyncIterator[str]:
        """Read lines from TXT file inside ZIP asynchronously with true streaming.

        This method is designed for COTAHIST files from B3 and uses
        true streaming without loading entire file into memory.

        Args:
            zip_path: Path to the ZIP file

        Yields:
            Lines from the TXT file (decoded as latin-1)

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If ZIP file is invalid or corrupted
            ExtractionError: If no TXT file found in ZIP
        """
        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        # Use streaming approach with limited buffer
        loop = asyncio.get_event_loop()

        try:
            # Open ZIP in executor (blocking operation)
            zip_file = await loop.run_in_executor(None, zipfile.ZipFile, zip_path, "r")

            try:
                # Get first .TXT file in the archive
                txt_files = [
                    name
                    for name in zip_file.namelist()
                    if name.upper().endswith(".TXT")
                ]

                if not txt_files:
                    raise ExtractionError(zip_path, "No .TXT file found in ZIP")

                # Open the TXT file for streaming
                txt_file_handle = await loop.run_in_executor(
                    None, zip_file.open, txt_files[0]
                )

                try:
                    # Read in chunks to avoid memory issues
                    CHUNK_SIZE = 8192  # 8KB chunks
                    buffer = b""

                    while True:
                        # Read chunk in executor
                        chunk = await loop.run_in_executor(
                            None, txt_file_handle.read, CHUNK_SIZE
                        )

                        if not chunk:
                            # Process remaining buffer
                            if buffer:
                                try:
                                    line = buffer.decode("latin-1")
                                    if line.strip():
                                        yield line.strip()
                                except UnicodeDecodeError:
                                    logger.warning(
                                        f"Failed to decode final buffer in {zip_path}"
                                    )
                            break

                        buffer += chunk

                        # Process complete lines from buffer
                        while b"\n" in buffer:
                            line_bytes, buffer = buffer.split(b"\n", 1)

                            try:
                                line = line_bytes.decode("latin-1").strip()
                                if line:  # Skip empty lines
                                    yield line
                            except UnicodeDecodeError:
                                logger.warning(
                                    f"Failed to decode line in {zip_path}, skipping"
                                )
                                continue

                finally:
                    # Cleanup file handle
                    await loop.run_in_executor(None, txt_file_handle.close)

            finally:
                # Cleanup ZIP file
                await loop.run_in_executor(None, zip_file.close)

        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, str(e))
        except Exception as e:
            if isinstance(e, (ExtractionError, CorruptedZipError, FileNotFoundError)):
                raise
            raise ExtractionError(zip_path, f"Error reading TXT from ZIP: {e}")

    @staticmethod
    def list_files_in_zip(zip_path: str, extension: str = "") -> list[str]:
        """List files in ZIP archive with optional extension filter.

        Args:
            zip_path: Path to the ZIP file
            extension: Optional file extension to filter (e.g., '.csv', '.txt')

        Returns:
            List of filenames in the ZIP

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If ZIP file is invalid or corrupted
        """
        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                if extension:
                    return [
                        name
                        for name in z.namelist()
                        if name.lower().endswith(extension)
                    ]
                return z.namelist()
        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, str(e))

    @staticmethod
    def extract_file_from_zip(
        zip_path: str, filename: str, destination_path: str
    ) -> None:
        """Extract a single file from ZIP archive.

        Args:
            zip_path: Path to the ZIP file
            filename: Name of the file inside the ZIP to extract
            destination_path: Path where the extracted file will be saved

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If ZIP file is invalid or corrupted
            ExtractionError: If file not found in ZIP or extraction fails
        """
        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                if filename not in z.namelist():
                    raise ExtractionError(
                        zip_path, f"File '{filename}' not found in ZIP"
                    )

                z.extract(filename, destination_path)
                logger.debug(f"Extracted {filename} to {destination_path}")

        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, str(e))
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(zip_path, f"Error extracting file: {e}")

    @staticmethod
    def read_file_from_zip(zip_path: str, filename: str) -> bytes:
        """Read file content from ZIP archive without extracting to disk.

        Args:
            zip_path: Path to the ZIP file
            filename: Name of the file inside the ZIP to read

        Returns:
            Raw bytes content of the file

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If ZIP file is invalid or corrupted
            ExtractionError: If file not found in ZIP or read fails
        """
        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                if filename not in z.namelist():
                    raise ExtractionError(
                        zip_path, f"File '{filename}' not found in ZIP"
                    )

                return z.read(filename)

        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, str(e))
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(zip_path, f"Error reading file from ZIP: {e}")

    @staticmethod
    def open_file_from_zip(zip_file: zipfile.ZipFile, filename: str) -> IO[bytes]:
        """Open a file handle from an already-opened ZIP archive.

        This is useful for streaming large files without loading them entirely
        into memory. The caller is responsible for closing the returned handle.

        Args:
            zip_file: Already opened ZipFile object
            filename: Name of the file inside the ZIP to open

        Returns:
            File handle that can be read in chunks

        Raises:
            ExtractionError: If file not found in ZIP
        """
        if filename not in zip_file.namelist():
            raise ExtractionError(
                zip_file.filename or "unknown", f"File '{filename}' not found in ZIP"
            )

        return zip_file.open(filename)

    @staticmethod
    def iterate_files_in_zip(
        zip_path: str, extension: str = ""
    ) -> Iterator[tuple[str, zipfile.ZipFile]]:
        """Iterate over files in ZIP archive, yielding filename and open ZIP handle.

        This is useful for processing multiple files from the same ZIP without
        repeatedly opening/closing the archive.

        Args:
            zip_path: Path to the ZIP file
            extension: Optional file extension to filter

        Yields:
            Tuple of (filename, open_zipfile) for each matching file

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If ZIP file is invalid or corrupted

        Example:
            >>> for filename, zip_handle in Extractor.iterate_files_in_zip("data.zip", ".csv"):
            ...     with zip_handle.open(filename) as f:
            ...         process_file(f)
        """
        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                files = Extractor.list_files_in_zip(zip_path, extension)
                for filename in files:
                    yield filename, z
        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, str(e))
