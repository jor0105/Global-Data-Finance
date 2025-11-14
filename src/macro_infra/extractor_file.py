import asyncio
import zipfile
from io import BytesIO
from pathlib import Path
from typing import AsyncIterator, List

import pandas as pd  # type: ignore
import pyarrow as pa  # type: ignore
import pyarrow.parquet as pq  # type: ignore

from src.core import get_logger
from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
)

logger = get_logger(__name__)


class Extractor:
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
    def _read_txt_from_zip_sync(zip_path: str) -> List[str]:
        """Synchronous helper to read TXT file content from ZIP.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            List of lines from the TXT file

        Raises:
            CorruptedZipError: If ZIP is invalid
            ExtractionError: If no TXT file found
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Get first .TXT file in the archive
                txt_files = [
                    name for name in zip_ref.namelist() if name.upper().endswith(".TXT")
                ]

                if not txt_files:
                    raise ExtractionError(zip_path, "No .TXT file found in ZIP")

                # Read the first TXT file
                with zip_ref.open(txt_files[0]) as txt_file:
                    # B3 files use latin-1 encoding
                    content = txt_file.read().decode("latin-1")
                    lines = content.splitlines()

            return lines

        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, str(e))
        except Exception as e:
            if isinstance(e, (ExtractionError, CorruptedZipError)):
                raise
            raise ExtractionError(zip_path, f"Error reading TXT from ZIP: {e}")

    @staticmethod
    def read_txt_from_zip(zip_path: str) -> List[str]:
        """Read lines from TXT file inside ZIP synchronously.

        Convenience method for synchronous code.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            List of lines from the TXT file

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            CorruptedZipError: If ZIP file is invalid
            ExtractionError: If no TXT file found
        """
        path = Path(zip_path)
        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        return Extractor._read_txt_from_zip_sync(zip_path)

    @staticmethod
    def extract_zip_to_parquet(chunk_size: int, zip_path: str, output_dir: str) -> None:
        """Extract CSV files from ZIP and save as Parquet with memory optimization.

        Args:
            zip_path: Path to the ZIP file
            output_dir: Directory where Parquet files will be saved

        Raises:
            InvalidDestinationPathError: If output_dir doesn't exist or isn't writable
            CorruptedZipError: If ZIP is corrupted or can't be read
            ExtractionError: For other extraction failures (CSV read, Parquet write, etc.)
            DiskFullError: If insufficient disk space
        """
        output_path = Path(output_dir)
        try:
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")

            if not output_path.is_dir():
                raise InvalidDestinationPathError(f"'{output_dir}' is not a directory")

            test_file = output_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except PermissionError as e:
            raise InvalidDestinationPathError(
                f"No write permission for '{output_dir}': {e}"
            )
        except Exception as e:
            raise InvalidDestinationPathError(f"Invalid path '{output_dir}': {e}")

        zip_path_obj = Path(zip_path)
        if not zip_path_obj.exists():
            raise ExtractionError(zip_path, f"ZIP file not found: {zip_path}")

        extracted_count = 0
        failed_files = []

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                csv_files = [name for name in z.namelist() if name.endswith(".csv")]

                if not csv_files:
                    logger.warning(f"No CSV files found in {zip_path}")
                    return

                for csv_filename in csv_files:
                    try:
                        Extractor._extract_single_csv(
                            chunk_size, z, csv_filename, output_dir
                        )
                        extracted_count += 1
                    except DiskFullError:
                        raise  # Re-raise disk full errors immediately
                    except Exception as e:
                        logger.error(f"Failed to extract {csv_filename}: {e}")
                        failed_files.append((csv_filename, str(e)))
                        continue

                # CRITICAL FIX: Extraction must be atomic (all-or-nothing)
                # If ANY file fails, we must rollback to prevent data loss
                if failed_files:
                    failed_list = "; ".join([f"{f[0]}: {f[1]}" for f in failed_files])

                    # Clean up any partially extracted parquet files
                    logger.warning(
                        f"Partial extraction detected ({extracted_count} succeeded, "
                        f"{len(failed_files)} failed). Rolling back..."
                    )

                    cleanup_count = 0
                    cleanup_errors = []
                    for parquet_file in Path(output_dir).glob("*.parquet"):
                        try:
                            parquet_file.unlink()
                            cleanup_count += 1
                            logger.debug(
                                f"Cleaned up partial file: {parquet_file.name}"
                            )
                        except Exception as cleanup_err:
                            cleanup_errors.append(f"{parquet_file.name}: {cleanup_err}")
                            logger.error(
                                f"Failed to cleanup {parquet_file.name}: {cleanup_err}"
                            )

                    logger.info(
                        f"Rollback complete: {cleanup_count} partial files removed"
                    )

                    if cleanup_errors:
                        cleanup_msg = "; ".join(cleanup_errors)
                        logger.error(
                            f"WARNING: Some partial files could not be removed: {cleanup_msg}"
                        )

                    # Always raise error if any extraction failed (atomic behavior)
                    raise ExtractionError(
                        zip_path,
                        f"Atomic extraction failed: {extracted_count} succeeded but "
                        f"{len(failed_files)} failed. All partial data rolled back. "
                        f"Failures: {failed_list}",
                    )

        except zipfile.BadZipFile as e:
            raise CorruptedZipError(zip_path, f"Invalid or corrupted ZIP file: {e}")
        except ExtractionError:
            raise  # Re-raise extraction errors as-is
        except DiskFullError:
            raise  # Re-raise disk full errors as-is
        except Exception as e:
            raise ExtractionError(zip_path, f"Unexpected error during extraction: {e}")

        logger.info(
            f"Successfully extracted {extracted_count} CSV files from {zip_path}"
        )

    @staticmethod
    def _extract_single_csv(
        chunk_size: int, zip_file: zipfile.ZipFile, csv_filename: str, output_dir: str
    ) -> None:
        """Extract a single CSV file from ZIP and convert to Parquet with memory safety.

        Uses streaming processing to avoid loading entire CSV into memory.

        Args:
            chunk_size: Number of rows per chunk for processing
            zip_file: Open ZipFile object
            csv_filename: Name of CSV file inside ZIP
            output_dir: Output directory for Parquet file

        Raises:
            ExtractionError: If CSV can't be read
            DiskFullError: If insufficient disk space
        """
        output_path = Path(output_dir)
        parquet_filename = Path(csv_filename).stem + ".parquet"
        parquet_path = output_path / parquet_filename

        # Reduce chunk size further for memory safety
        safe_chunk_size = min(chunk_size, 50_000)

        # List of encodings to try in order (latin-1 first for CVM files)
        encodings_to_try = ["latin-1", "utf-8", "iso-8859-1", "cp1252"]

        logger.debug(f"Processing {csv_filename} with chunk size {safe_chunk_size}")

        try:
            # Find working encoding first (read just first chunk)
            working_encoding = None
            for encoding in encodings_to_try:
                try:
                    with zip_file.open(csv_filename) as csv_file:
                        # Test read with pandas
                        pd.read_csv(
                            BytesIO(csv_file.read(10000)),  # Read first 10KB to test
                            encoding=encoding,
                            sep=";",
                            on_bad_lines="skip",
                            nrows=100,
                        )
                        working_encoding = encoding
                        logger.debug(
                            f"Successfully validated {csv_filename} with encoding {encoding}"
                        )
                        break
                except (UnicodeDecodeError, LookupError):
                    continue
                except Exception as e:
                    logger.debug(f"Test read failed for {csv_filename}: {e}")
                    continue

            if working_encoding is None:
                raise ExtractionError(
                    str(parquet_path),
                    f"Could not read {csv_filename} with any encoding "
                    f"(tried {', '.join(encodings_to_try)})",
                )

            # Now process file in chunks using pandas
            total_rows = 0
            writer = None  # Will hold ParquetWriter for append mode

            try:
                with zip_file.open(csv_filename) as csv_file:
                    try:
                        # Use TextIOWrapper to stream decode without loading full content
                        import io

                        text_wrapper = io.TextIOWrapper(
                            csv_file, encoding=working_encoding, newline=""
                        )

                        # Read CSV in chunks - now truly streaming!
                        csv_reader = pd.read_csv(
                            text_wrapper,
                            sep=";",
                            on_bad_lines="skip",
                            chunksize=safe_chunk_size,
                        )

                        for chunk_df in csv_reader:
                            if len(chunk_df) > 0:
                                try:
                                    # Convert to Arrow table
                                    table = pa.Table.from_pandas(chunk_df)

                                    # Use ParquetWriter for true append (more efficient)
                                    if writer is None:
                                        # First chunk: create writer
                                        writer = pq.ParquetWriter(
                                            parquet_path,
                                            table.schema,
                                            compression="zstd",
                                            compression_level=3,
                                        )
                                        logger.debug(f"Created {parquet_filename}")

                                    # Write chunk to file (true append, no re-read)
                                    writer.write_table(table)
                                    total_rows += len(chunk_df)
                                    logger.debug(
                                        f"Wrote {len(chunk_df)} rows to {parquet_filename}"
                                    )

                                except OSError as e:
                                    if "No space left on device" in str(e):
                                        raise DiskFullError(str(parquet_path))
                                    raise

                        # CRITICAL FIX: Close writer in success path
                        if writer is not None:
                            writer.close()
                            writer = None  # Mark as closed
                            logger.debug(
                                f"Completed {csv_filename}: {total_rows} rows written to {parquet_filename}"
                            )

                    except Exception as e:
                        # CRITICAL FIX: Always close writer on any error
                        if writer is not None:
                            try:
                                writer.close()
                                writer = None
                                logger.debug(
                                    f"Writer closed after error for {csv_filename}"
                                )
                            except Exception as close_err:
                                logger.error(
                                    f"CRITICAL: Failed to close writer for {csv_filename}: {close_err}"
                                )
                                # Raise compound exception to signal both failures
                                raise ExtractionError(
                                    str(parquet_path),
                                    f"Extraction failed AND writer close failed: {e} | {close_err}",
                                )

                        # Re-raise original error
                        raise

            finally:
                # CRITICAL FIX: Final safety net to ensure writer is closed
                if writer is not None:
                    try:
                        writer.close()
                        logger.warning(
                            f"Writer closed in finally block for {csv_filename} "
                            "(should have been closed earlier)"
                        )
                    except Exception as final_close_err:
                        logger.error(
                            f"CRITICAL: Failed to close writer in finally block: {final_close_err}"
                        )
                        # Don't raise here as we're already handling an exception

                        # Fallback to loading entire file if chunking fails
                        logger.warning(
                            f"Chunked read failed for {csv_filename}, loading entire file: {final_close_err}"
                        )

                    # CRITICAL FIX: Clean up partial file with robust error handling
                    if parquet_path.exists():
                        cleanup_attempt = 0
                        max_cleanup_attempts = 3
                        cleanup_success = False

                        while (
                            cleanup_attempt < max_cleanup_attempts
                            and not cleanup_success
                        ):
                            try:
                                parquet_path.unlink()
                                cleanup_success = True
                                logger.debug(
                                    f"Cleaned up partial file: {parquet_filename} "
                                    f"(attempt {cleanup_attempt + 1})"
                                )
                            except Exception as cleanup_error:
                                cleanup_attempt += 1
                                if cleanup_attempt >= max_cleanup_attempts:
                                    logger.error(
                                        f"CRITICAL: Failed to delete partial file {parquet_path} "
                                        f"after {max_cleanup_attempts} attempts. "
                                        f"Cannot proceed with fallback extraction to avoid data corruption. "
                                        f"Error: {cleanup_error}"
                                    )
                                    # Re-raise to prevent writing over corrupted file
                                    raise ExtractionError(
                                        str(parquet_path),
                                        f"Cannot cleanup partial file before retry: {cleanup_error}. "
                                        f"Manual intervention required to remove: {parquet_path}",
                                    )
                                else:
                                    # Wait a bit before retry (file might be locked)
                                    import time

                                    time.sleep(0.1 * cleanup_attempt)
                                    logger.debug(
                                        f"Retrying cleanup of {parquet_filename} "
                                        f"(attempt {cleanup_attempt + 1}/{max_cleanup_attempts})"
                                    )

                    # Retry with entire file (CAUTION: loads full file in memory)
                    with zip_file.open(csv_filename) as csv_file_retry:
                        try:
                            csv_content = csv_file_retry.read()
                            logger.warning(
                                f"Loaded entire file in memory: {csv_filename} "
                                f"({len(csv_content) / 1024 / 1024:.2f} MB)"
                            )
                        except MemoryError as mem_err:
                            raise ExtractionError(
                                str(parquet_path),
                                f"File too large to load in memory: {csv_filename}. "
                                f"Consider increasing chunk_size or available RAM: {mem_err}",
                            )

                        df = pd.read_csv(
                            BytesIO(csv_content),
                            encoding=working_encoding,
                            sep=";",
                            on_bad_lines="skip",
                        )

                        # Write in smaller chunks using efficient ParquetWriter
                        fallback_writer = None
                        for chunk_start in range(0, len(df), safe_chunk_size):
                            chunk_df = df.iloc[
                                chunk_start : chunk_start + safe_chunk_size
                            ]
                            table = pa.Table.from_pandas(chunk_df)

                            if fallback_writer is None:
                                # First chunk: create writer
                                fallback_writer = pq.ParquetWriter(
                                    parquet_path,
                                    table.schema,
                                    compression="zstd",
                                    compression_level=3,
                                )

                            # Write chunk (true append)
                            fallback_writer.write_table(table)

                        # Close writer to finalize
                        if fallback_writer is not None:
                            fallback_writer.close()

        except DiskFullError:
            # Clean up partial file on disk full
            if parquet_path.exists():
                try:
                    parquet_path.unlink()
                    logger.warning(
                        f"Removed partial file due to disk full: {parquet_path}"
                    )
                except Exception as cleanup_err:
                    logger.error(
                        f"Failed to remove partial file {parquet_path}: {cleanup_err}"
                    )
            raise  # Re-raise disk full errors
        except Exception as e:
            # Clean up partial file if it exists
            if parquet_path.exists():
                try:
                    parquet_path.unlink()
                    logger.warning(f"Removed partial file due to error: {parquet_path}")
                except Exception as cleanup_err:
                    logger.error(
                        f"Failed to remove partial file {parquet_path}: {cleanup_err}"
                    )
            raise ExtractionError(
                str(parquet_path),
                f"Error converting {csv_filename} to Parquet: {e}",
            )
