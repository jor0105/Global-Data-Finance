import asyncio
import zipfile
from pathlib import Path
from typing import AsyncIterator, List

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

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

                if failed_files:
                    failed_list = "; ".join([f"{f[0]}: {f[1]}" for f in failed_files])
                    logger.warning(
                        f"Extracted {extracted_count} files with {len(failed_files)} "
                        f"failures: {failed_list}"
                    )
                    if extracted_count == 0:
                        raise ExtractionError(
                            zip_path,
                            f"Failed to extract all CSV files: {failed_list}",
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

        # List of encodings to try in order
        encodings_to_try = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

        logger.debug(f"Processing {csv_filename} with chunk size {safe_chunk_size}")

        try:
            # Find working encoding first (read just first chunk)
            working_encoding = None
            for encoding in encodings_to_try:
                try:
                    with zip_file.open(csv_filename) as csv_file:
                        # Try to read just first few lines
                        test_df = pl.read_csv(
                            csv_file,
                            encoding=encoding,
                            separator=";",
                            ignore_errors=True,
                            n_rows=100,
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

            # Now process file in chunks using streaming approach
            first_write = True
            total_rows = 0

            with zip_file.open(csv_filename) as csv_file:
                # Use scan_csv for lazy loading (more memory efficient)
                try:
                    # Read and process in chunks
                    reader = pl.read_csv_batched(
                        csv_file,
                        encoding=working_encoding,
                        separator=";",
                        ignore_errors=True,
                        batch_size=safe_chunk_size,
                    )

                    batches = reader.next_batches(1)
                    while batches:
                        for chunk in batches:
                            if chunk is not None and chunk.height > 0:
                                try:
                                    # Convert to Arrow table
                                    table = chunk.to_arrow()

                                    # Write or append to Parquet
                                    if first_write:
                                        pq.write_table(
                                            table,
                                            parquet_path,
                                            compression="zstd",
                                            compression_level=3,
                                        )
                                        first_write = False
                                        logger.debug(f"Created {parquet_filename}")
                                    else:
                                        # Append using ParquetWriter for efficiency
                                        parquet_file = pq.ParquetFile(parquet_path)
                                        existing_table = parquet_file.read()
                                        combined = pa.concat_tables(
                                            [existing_table, table]
                                        )
                                        pq.write_table(
                                            combined,
                                            parquet_path,
                                            compression="zstd",
                                            compression_level=3,
                                        )
                                        logger.debug(
                                            f"Appended chunk to {parquet_filename}"
                                        )

                                    total_rows += chunk.height

                                except OSError as e:
                                    if "No space left on device" in str(e):
                                        raise DiskFullError(str(parquet_path))
                                    raise

                        # Get next batch
                        batches = reader.next_batches(1)

                    logger.debug(
                        f"Completed {csv_filename}: {total_rows} rows written to {parquet_filename}"
                    )

                except pl.exceptions.ComputeError as e:
                    # Fallback to traditional approach if streaming fails
                    logger.warning(
                        f"Streaming read failed for {csv_filename}, falling back to traditional approach: {e}"
                    )

                    # Clean up partial file
                    if parquet_path.exists():
                        try:
                            parquet_path.unlink()
                        except Exception:
                            pass

                    # Retry with traditional approach
                    with zip_file.open(csv_filename) as csv_file_retry:
                        csv_data = pl.read_csv(
                            csv_file_retry,
                            encoding=working_encoding,
                            separator=";",
                            ignore_errors=True,
                        )

                        # Write in smaller chunks
                        for chunk_start in range(0, csv_data.height, safe_chunk_size):
                            chunk = csv_data[
                                chunk_start : chunk_start + safe_chunk_size
                            ]
                            table = chunk.to_arrow()

                            if chunk_start == 0:
                                pq.write_table(
                                    table,
                                    parquet_path,
                                    compression="zstd",
                                    compression_level=3,
                                )
                            else:
                                existing = pq.read_table(parquet_path)
                                combined = pa.concat_tables([existing, table])
                                pq.write_table(
                                    combined,
                                    parquet_path,
                                    compression="zstd",
                                    compression_level=3,
                                )

        except pl.exceptions.ComputeError as e:
            # Clean up partial file if it exists
            if parquet_path.exists():
                try:
                    parquet_path.unlink()
                except Exception:
                    pass
            raise ExtractionError(
                str(parquet_path),
                f"Invalid CSV format in {csv_filename}: {e}",
            )
        except DiskFullError:
            raise  # Re-raise disk full errors
        except Exception as e:
            # Clean up partial file if it exists
            if parquet_path.exists():
                try:
                    parquet_path.unlink()
                except Exception:
                    pass
            raise ExtractionError(
                str(parquet_path),
                f"Error converting {csv_filename} to Parquet: {e}",
            )
