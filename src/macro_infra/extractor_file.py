import asyncio
import zipfile
from io import BytesIO
from pathlib import Path
from typing import AsyncIterator

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
        created_files = []  # CRITICAL FIX: Track only files created in THIS extraction

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                csv_files = [name for name in z.namelist() if name.endswith(".csv")]

                if not csv_files:
                    logger.warning(f"No CSV files found in {zip_path}")
                    return

                for csv_filename in csv_files:
                    # Calculate expected parquet path
                    parquet_filename = Path(csv_filename).stem + ".parquet"
                    parquet_path = output_path / parquet_filename

                    try:
                        Extractor._extract_single_csv(
                            chunk_size, z, csv_filename, output_dir
                        )

                        # CRITICAL FIX: Register file ONLY if it exists after extraction
                        if parquet_path.exists():
                            created_files.append(parquet_path)
                            logger.debug(f"Registered created file: {parquet_filename}")

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
                        f"{len(failed_files)} failed). Rolling back {len(created_files)} files..."
                    )

                    cleanup_count = 0
                    cleanup_errors = []

                    # CRITICAL FIX: Only delete files created in THIS extraction
                    for parquet_file in created_files:
                        try:
                            # CRITICAL FIX: Re-check existence before delete
                            if parquet_file.exists():
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
            # CRITICAL FIX: Clean up only files created in THIS execution
            logger.error(
                f"Bad ZIP file detected: {zip_path}, cleaning up {len(created_files)} files"
            )
            for f in created_files:
                try:
                    if f.exists():
                        f.unlink()
                        logger.debug(f"Cleaned up {f.name} after ZIP error")
                except Exception as cleanup_err:
                    logger.error(f"Failed to cleanup {f.name}: {cleanup_err}")

            raise CorruptedZipError(zip_path, f"Invalid or corrupted ZIP file: {e}")
        except ExtractionError:
            raise  # Re-raise extraction errors as-is
        except DiskFullError:
            # CRITICAL FIX: Clean up files on disk full
            logger.error(
                f"Disk full during extraction, cleaning up {len(created_files)} files"
            )
            for f in created_files:
                try:
                    if f.exists():
                        f.unlink()
                except Exception:
                    pass  # Best effort cleanup
            raise  # Re-raise disk full errors as-is
        except Exception as e:
            # CRITICAL FIX: Clean up on any unexpected error
            logger.error(
                f"Unexpected error during extraction, cleaning up {len(created_files)} files"
            )
            for f in created_files:
                try:
                    if f.exists():
                        f.unlink()
                except Exception:
                    pass
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
        import pandas as pd     # type: ignore
        
        output_path = Path(output_dir)
        parquet_filename = Path(csv_filename).stem + ".parquet"
        parquet_path = output_path / parquet_filename

        # CRITICAL: Check if parquet file already exists to prevent data loss
        if parquet_path.exists():
            logger.warning(
                f"Parquet file already exists, skipping to prevent overwrite: {parquet_path}"
            )
            return  # Skip extraction to protect existing data

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
            writer_closed = False  # Track writer state to prevent double-close

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

                        # CRITICAL FIX: Close writer safely in success path
                        if writer is not None and not writer_closed:
                            writer.close()
                            writer_closed = True  # Mark BEFORE setting to None
                            writer = None
                            logger.debug(
                                f"Completed {csv_filename}: {total_rows} rows written to {parquet_filename}"
                            )

                    except Exception:
                        # CRITICAL FIX: Close writer only if not already closed
                        if writer is not None and not writer_closed:
                            try:
                                writer.close()
                                writer_closed = True
                                writer = None
                                logger.debug(
                                    f"Writer closed after error for {csv_filename}"
                                )
                            except Exception as close_err:
                                logger.error(
                                    f"CRITICAL: Failed to close writer for {csv_filename}: {close_err}"
                                )
                                # Don't raise here - original exception is more important

                        # Clean up partial file ALWAYS on error
                        if parquet_path.exists():
                            try:
                                parquet_path.unlink()
                                logger.debug(
                                    f"Cleaned up partial file after error: {parquet_filename}"
                                )
                            except Exception as cleanup_err:
                                logger.error(
                                    f"Failed to cleanup partial file {parquet_filename}: {cleanup_err}"
                                )

                        # Re-raise original error
                        raise

            finally:
                # CRITICAL FIX: Final safety net - only close if still open
                if writer is not None and not writer_closed:
                    try:
                        writer.close()
                        writer_closed = True
                        logger.warning(
                            f"Writer closed in finally block for {csv_filename} "
                            "(should have been closed earlier)"
                        )
                    except Exception as final_close_err:
                        logger.error(
                            f"CRITICAL: Failed to close writer in finally block: {final_close_err}"
                        )

                # CRITICAL FIX: Fallback with OOM protection
                if not writer_closed and parquet_path.exists():
                    # If we get here, chunked streaming failed
                    logger.error(
                        f"Chunked streaming failed for {csv_filename}, "
                        "attempting fallback with memory limit"
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

                    # CRITICAL: Verify partial file was deleted before fallback
                    if parquet_path.exists():
                        raise ExtractionError(
                            str(parquet_path),
                            f"CRITICAL: Failed to delete partial file before fallback. "
                            f"Cannot proceed to prevent data corruption: {parquet_path}. "
                            f"Manual intervention required.",
                        )

                    # CRITICAL FIX: Check file size BEFORE loading into memory
                    MAX_FALLBACK_SIZE_MB = 500  # Maximum 500MB for fallback

                    with zip_file.open(csv_filename) as csv_file_retry:
                        # Get file info to check size
                        info = zip_file.getinfo(csv_filename)
                        size_mb = info.file_size / 1024 / 1024

                        if size_mb > MAX_FALLBACK_SIZE_MB:
                            raise ExtractionError(
                                str(parquet_path),
                                f"File too large for fallback ({size_mb:.1f}MB > {MAX_FALLBACK_SIZE_MB}MB): {csv_filename}. "
                                f"Chunked read failed. Manual intervention required. "
                                f"Consider increasing available RAM or processing file separately.",
                            )

                        # Safe to load - file is under limit
                        try:
                            csv_content = csv_file_retry.read()
                            logger.warning(
                                f"Loaded entire file in memory (fallback): {csv_filename} "
                                f"({len(csv_content) / 1024 / 1024:.2f} MB)"
                            )
                        except MemoryError as mem_err:
                            raise ExtractionError(
                                str(parquet_path),
                                f"Memory exhausted loading {csv_filename} ({size_mb:.1f}MB): {mem_err}. "
                                f"Available RAM insufficient for fallback.",
                            )

                        df = pd.read_csv(
                            BytesIO(csv_content),
                            encoding=working_encoding,
                            sep=";",
                            on_bad_lines="skip",
                        )

                        # Write in smaller chunks using efficient ParquetWriter
                        fallback_writer = None
                        fallback_writer_closed = False

                        try:
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
                            if (
                                fallback_writer is not None
                                and not fallback_writer_closed
                            ):
                                fallback_writer.close()
                                fallback_writer_closed = True
                                logger.info(
                                    f"Fallback extraction completed successfully for {csv_filename}"
                                )

                        finally:
                            # Ensure fallback writer is closed
                            if (
                                fallback_writer is not None
                                and not fallback_writer_closed
                            ):
                                try:
                                    fallback_writer.close()
                                    fallback_writer_closed = True
                                except Exception as fb_close_err:
                                    logger.error(
                                        f"Failed to close fallback writer: {fb_close_err}"
                                    )

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
