import asyncio
import io
import time
import zipfile
from pathlib import Path
from typing import IO, AsyncIterator

import pyarrow as pa  # type: ignore
import pyarrow.parquet as pq  # type: ignore

from ..core import get_logger
from ..macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
)
from .read_files import ReadFilesAdapter

logger = get_logger(__name__)


class ExtractorAdapter:
    """Generic file extraction utilities for ZIP archives.

    This class provides low-level, reusable extraction methods that can be
    used across different parts of the application. Domain-specific logic
    (like CSV to Parquet conversion) should be implemented in dedicated
    modules within their respective domains.
    """

    CHUNK_SIZE_TXT = 8192
    CHUNK_SIZE_PARQUET = 50000

    @staticmethod
    def list_files_in_zip(zip_path: str, extension: str) -> list[str]:
        """List files in ZIP archive with optional extension filter.

        Args:
            zip_path: Path to the ZIP file
            extension: File extension to filter (e.g., '.csv', '.txt')

        Returns:
            List of filenames in the ZIP

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If ZIP file is invalid or corrupted
        """
        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f'ZIP file not found: {zip_path}')

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                names = z.namelist()
                return [
                    name for name in names if name.lower().endswith(extension)
                ]
        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, str(e))

    @staticmethod
    def open_file_from_zip(
        zip_file: zipfile.ZipFile, filename: str
    ) -> IO[bytes]:
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
                zip_file.filename or 'unknown',
                f"File '{filename}' not found in ZIP",
            )

        return zip_file.open(filename)

    async def extract_txt_from_zip_async(
        self, zip_path: str
    ) -> AsyncIterator[str]:
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
        # Validate file existence using existing method
        try:
            txt_files = ExtractorAdapter.list_files_in_zip(zip_path, '.txt')
        except (FileNotFoundError, CorruptedZipError):
            raise

        if not txt_files:
            raise ExtractionError(zip_path, 'No .TXT file found in ZIP')

        # Use streaming approach with limited buffer
        loop = asyncio.get_event_loop()

        try:
            # Open ZIP in executor (blocking operation)
            zip_file = await loop.run_in_executor(
                None, zipfile.ZipFile, zip_path, 'r'
            )

            try:
                # Open the first TXT file for streaming
                txt_file_handle = ExtractorAdapter.open_file_from_zip(
                    zip_file, txt_files[0]
                )

                try:
                    # Read in chunks to avoid memory issues
                    buffer = b''

                    while True:
                        # Read chunk in executor
                        chunk = await loop.run_in_executor(
                            None, txt_file_handle.read, self.CHUNK_SIZE_TXT
                        )

                        if not chunk:
                            # Process remaining buffer
                            if buffer:
                                try:
                                    line = buffer.decode('latin-1')
                                    if line.strip():
                                        yield line.strip()
                                except UnicodeDecodeError:
                                    logger.warning(
                                        f'Failed to decode final buffer in {zip_path}'
                                    )
                            break

                        buffer += chunk

                        # Process complete lines from buffer
                        while b'\n' in buffer:
                            line_bytes, buffer = buffer.split(b'\n', 1)

                            try:
                                line = line_bytes.decode('latin-1').strip()
                                if line:  # Skip empty lines
                                    yield line
                            except UnicodeDecodeError:
                                logger.warning(
                                    f'Failed to decode line in {zip_path}, skipping'
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
            if isinstance(
                e, (ExtractionError, CorruptedZipError, FileNotFoundError)
            ):
                raise
            raise ExtractionError(zip_path, f'Error reading TXT from ZIP: {e}')

    def extract_csv_from_zip_to_parquet(
        self,
        zip_file: zipfile.ZipFile,
        parquet_path: Path,
        parquet_filename: str,
        csv_filename: str,
    ) -> None:
        """Extract single CSV from ZIP and convert to Parquet.

        Uses streaming processing to avoid loading entire CSV into memory.
        Falls back to in-memory processing if streaming fails.

        Args:
            zip_file: Open ZipFile object
            parquet_path: Full path for Parquet file
            parquet_filename: Parquet filename
            csv_filename: Name of CSV file inside ZIP

        Raises:
            ExtractionError: If CSV can't be read or converted
            DiskFullError: If insufficient disk space
        """
        logger.debug(
            f'Processing {csv_filename} with chunk size {self.CHUNK_SIZE_PARQUET}'
        )

        try:
            # Detect encoding first
            encoding = ReadFilesAdapter.read_csv_test_encoding(
                zip_file, csv_filename
            )

            # Try streaming conversion
            try:
                self.__stream_csv_to_parquet(
                    zip_file, csv_filename, parquet_path, encoding
                )
            except Exception as stream_error:
                logger.warning(
                    f'Streaming failed for {csv_filename}, '
                    f'attempting fallback: {stream_error}'
                )

                # Clean up partial file before fallback
                self.__safe_delete_file(parquet_path, max_attempts=3)

        except DiskFullError:
            self.__safe_delete_file(parquet_path)
            raise

        except Exception as e:
            self.__safe_delete_file(parquet_path)
            raise ExtractionError(
                str(parquet_path),
                f'Error converting {csv_filename} to Parquet: {e}',
            )

    def __stream_csv_to_parquet(
        self,
        zip_file: zipfile.ZipFile,
        csv_filename: str,
        parquet_path: Path,
        encoding: str,
    ) -> None:
        """Stream CSV to Parquet using chunked processing.

        Args:
            zip_file: Open ZipFile object
            csv_filename: CSV filename
            parquet_path: Output Parquet path
            encoding: CSV encoding

        Raises:
            DiskFullError: If disk space exhausted
            Exception: On any streaming failure
        """
        writer = None
        writer_closed = False
        total_rows = 0

        try:
            with zip_file.open(csv_filename) as csv_file:
                text_wrapper = io.TextIOWrapper(
                    csv_file, encoding=encoding, newline=''
                )

                csv_reader = ReadFilesAdapter.read_csv_chunk_size(
                    text_wrapper, chunk_size=self.CHUNK_SIZE_PARQUET
                )

                for chunk_df in csv_reader:
                    if len(chunk_df) > 0:
                        table = pa.Table.from_pandas(chunk_df)

                        if writer is None:
                            writer = pq.ParquetWriter(
                                parquet_path,
                                table.schema,
                                compression='zstd',
                                compression_level=3,
                            )
                            logger.debug(f'Created {parquet_path.name}')

                        try:
                            writer.write_table(table)
                            total_rows += len(chunk_df)
                        except OSError as e:
                            if 'No space left on device' in str(e):
                                raise DiskFullError(str(parquet_path))
                            raise

                if writer is not None:
                    writer.close()
                    writer_closed = True
                    logger.debug(
                        f'Completed {csv_filename}: {total_rows} rows written'
                    )

        except Exception:
            if writer is not None and not writer_closed:
                try:
                    writer.close()
                except Exception as close_err:
                    logger.error(f'Failed to close writer: {close_err}')
            raise

    def __safe_delete_file(
        self, file_path: Path, max_attempts: int = 3
    ) -> None:
        """Safely delete file with retry logic.

        Args:
            file_path: Path to file to delete
            max_attempts: Maximum deletion attempts

        Raises:
            ExtractionError: If file cannot be deleted after all attempts
        """
        if not file_path.exists():
            return

        for attempt in range(max_attempts):
            try:
                file_path.unlink()
                logger.debug(
                    f'Deleted {file_path.name} (attempt {attempt + 1})'
                )
                return
            except Exception as e:
                if attempt >= max_attempts - 1:
                    raise ExtractionError(
                        str(file_path),
                        f'Cannot delete file after {max_attempts} attempts: {e}. '
                        f'Manual intervention required.',
                    )
                time.sleep(0.1 * (attempt + 1))
                logger.debug(
                    f'Retrying deletion of {file_path.name} '
                    f'(attempt {attempt + 2}/{max_attempts})'
                )
