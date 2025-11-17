import io
import time
import zipfile
from pathlib import Path
from typing import List, cast

import pyarrow as pa  # type: ignore
import pyarrow.parquet as pq  # type: ignore

from .......core import get_logger
from .......macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
)
from .......macro_infra import ExtractorAdapter, ReadFilesAdapter
from ....application import FileExtractorRepositoryCVM

logger = get_logger(__name__)


class ParquetExtractorCVM(FileExtractorRepositoryCVM):
    """Extracts ZIP files containing CSVs and converts to Parquet format.

    This extractor is specifically designed for CVM data, handling:
    - CSV files with semicolon delimiters
    - Latin-1 encoding (common in Brazilian financial data)
    - Large files through chunked processing
    - Atomic transactions (all-or-nothing extraction)
    - Automatic cleanup on failures

    Attributes:
        chunk_size: Number of rows per chunk for memory optimization during conversion
        encodings: List of encodings to try (latin-1 first for CVM compatibility)
        max_fallback_size_mb: Maximum file size (MB) for in-memory fallback processing

    Example:
        >>> extractor = ParquetExtractorCVM(chunk_size=50000)
        >>> extractor.extract("/tmp/dfp_2023.zip", "/tmp/output")
        # Creates Parquet files with efficient compression
    """

    def __init__(
        self,
        chunk_size: int = 50000,
        encodings: list[str] | None = None,
        max_fallback_size_mb: int = 500,
    ):
        """Initialize ParquetExtractorCVM.

        Args:
            chunk_size: Rows per chunk for streaming processing
            encodings: Ordered list of encodings to try (default: latin-1, utf-8, iso-8859-1, cp1252)
            max_fallback_size_mb: Max file size for in-memory fallback when streaming fails
        """
        self.chunk_size = min(chunk_size, 50000)  # Safety cap
        self.encodings = encodings or ["latin-1", "utf-8", "iso-8859-1", "cp1252"]
        self.max_fallback_size_mb = max_fallback_size_mb
        logger.debug(
            f"ParquetExtractorCVM initialized with chunk_size={self.chunk_size}"
        )

    def extract(self, source_path: str, destination_dir: str) -> None:
        """Extract ZIP to Parquet files with atomic transaction guarantee.

        Processes all CSV files found in the ZIP archive and converts them
        to Parquet format. If ANY file fails, all changes are rolled back.

        Args:
            source_path: Path to ZIP file containing CSV files
            destination_dir: Directory where Parquet files will be saved

        Raises:
            ExtractionError: If ZIP is invalid or CSV conversion fails
            CorruptedZipError: If ZIP file is corrupted or cannot be read
            DiskFullError: If insufficient disk space is available
            InvalidDestinationPathError: If destination path is invalid or not writable

        Note:
            - Automatically creates destination directory if it doesn't exist
            - Cleans up ALL partial Parquet files if ANY extraction fails (atomic)
            - Skips existing files to prevent data loss

        Example:
            >>> extractor = ParquetExtractorCVM()
            >>> extractor.extract("/data/dfp_2023.zip", "/data/output")
            # Creates /data/output/file1.parquet, /data/output/file2.parquet, etc.
        """
        try:
            logger.info(f"Starting Parquet extraction from {source_path}")

            # Validate and prepare destination
            self._validate_destination(destination_dir)

            # Validate source
            zip_path = Path(source_path)
            if not zip_path.exists():
                raise ExtractionError(source_path, f"ZIP file not found: {source_path}")

            # Process with atomic transaction
            self._extract_with_transaction(source_path, destination_dir)

            logger.info(f"Parquet extraction completed successfully: {source_path}")

        except (
            ExtractionError,
            CorruptedZipError,
            DiskFullError,
            InvalidDestinationPathError,
        ):
            raise

        except Exception as e:
            logger.error(f"Unexpected error during extraction of {source_path}: {e}")
            raise ExtractionError(
                source_path, f"Unexpected extraction error: {type(e).__name__}: {e}"
            )

    def _validate_destination(self, destination_dir: str) -> None:
        """Validate and prepare destination directory.

        Args:
            destination_dir: Directory path to validate

        Raises:
            InvalidDestinationPathError: If path is invalid or not writable
        """
        output_path = Path(destination_dir)

        try:
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created output directory: {destination_dir}")

            if not output_path.is_dir():
                raise InvalidDestinationPathError(
                    f"'{destination_dir}' is not a directory"
                )

            # Test write permission
            test_file = output_path / ".write_test"
            test_file.touch()
            test_file.unlink()

        except PermissionError as e:
            raise InvalidDestinationPathError(
                f"No write permission for '{destination_dir}': {e}"
            )
        except Exception as e:
            raise InvalidDestinationPathError(f"Invalid path '{destination_dir}': {e}")

    def _extract_with_transaction(self, zip_path: str, output_dir: str) -> None:
        """Extract with atomic transaction (all-or-nothing).

        Args:
            zip_path: Path to ZIP file
            output_dir: Output directory

        Raises:
            CorruptedZipError: If ZIP is corrupted
            ExtractionError: If extraction fails (triggers rollback)
            DiskFullError: If disk space exhausted (triggers rollback)
        """
        extracted_count = 0
        failed_files = []
        created_files = []  # Track files created in THIS extraction only

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                csv_files = ExtractorAdapter.list_files_in_zip(zip_path, ".csv")

                if not csv_files:
                    logger.warning(f"No CSV files found in {zip_path}")
                    return

                for csv_filename in csv_files:
                    output_path = Path(output_dir)
                    parquet_filename = Path(csv_filename).stem + ".parquet"
                    parquet_path = output_path / parquet_filename

                    try:
                        self._extract_single_csv(z, csv_filename, output_dir)

                        # Register file ONLY if it exists after extraction
                        if parquet_path.exists():
                            created_files.append(parquet_path)
                            logger.debug(f"Registered created file: {parquet_filename}")

                        extracted_count += 1

                    except DiskFullError:
                        raise  # Immediate escalation
                    except Exception as e:
                        logger.error(f"Failed to extract {csv_filename}: {e}")
                        failed_files.append((csv_filename, str(e)))
                        continue

                # Atomic check: if ANY file failed, rollback ALL
                if failed_files:
                    self._rollback_extraction(created_files, failed_files, zip_path)

        except zipfile.BadZipFile as e:
            self._cleanup_files(created_files, "ZIP corruption")
            raise CorruptedZipError(zip_path, f"Invalid or corrupted ZIP file: {e}")

        except ExtractionError:
            self._cleanup_files(created_files, "extraction error")
            raise

        except DiskFullError:
            self._cleanup_files(created_files, "disk full")
            raise

        except Exception as e:
            self._cleanup_files(created_files, "unexpected error")
            raise ExtractionError(zip_path, f"Unexpected error during extraction: {e}")

        logger.info(
            f"Successfully extracted {extracted_count} CSV files from {zip_path}"
        )

    def _rollback_extraction(
        self,
        created_files: list[Path],
        failed_files: list[tuple[str, str]],
        zip_path: str,
    ) -> None:
        """Rollback partial extraction (atomic behavior).

        Args:
            created_files: List of files created in this extraction
            failed_files: List of (filename, error) tuples for failed files
            zip_path: Original ZIP path (for error message)

        Raises:
            ExtractionError: Always raised after rollback
        """
        failed_list = "; ".join([f"{f[0]}: {f[1]}" for f in failed_files])

        logger.warning(
            f"Partial extraction detected. Rolling back {len(created_files)} files..."
        )

        result = self._cleanup_files(created_files, "rollback", return_stats=True)
        cleanup_count, cleanup_errors = cast(tuple[int, List[str]], result)

        logger.info(f"Rollback complete: {cleanup_count} partial files removed")

        if cleanup_errors:
            cleanup_msg = "; ".join(cleanup_errors)
            logger.error(f"WARNING: Some files could not be removed: {cleanup_msg}")

        raise ExtractionError(
            zip_path,
            f"Atomic extraction failed: {len(failed_files)} files failed. "
            f"All partial data rolled back. Failures: {failed_list}",
        )

    def _cleanup_files(
        self,
        files: list[Path],
        reason: str,
        return_stats: bool = False,
    ) -> tuple[int, List[str]] | None:
        """Clean up files with error tracking.

        Args:
            files: List of file paths to delete
            reason: Reason for cleanup (for logging)
            return_stats: If True, return (count, errors) instead of None

        Returns:
            If return_stats=True: tuple of (cleanup_count, cleanup_errors)
            Otherwise: None
        """
        cleanup_count = 0
        cleanup_errors: List[str] = []

        logger.info(f"Cleaning up {len(files)} files due to: {reason}")

        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    cleanup_count += 1
                    logger.debug(f"Cleaned up: {file_path.name}")
            except Exception as err:
                error_msg = f"{file_path.name}: {err}"
                cleanup_errors.append(error_msg)
                logger.error(f"Failed to cleanup {file_path.name}: {err}")

        if return_stats:
            return cleanup_count, cleanup_errors
        return None

    def _extract_single_csv(
        self, zip_file: zipfile.ZipFile, csv_filename: str, output_dir: str
    ) -> None:
        """Extract single CSV from ZIP and convert to Parquet.

        Uses streaming processing to avoid loading entire CSV into memory.
        Falls back to in-memory processing if streaming fails.

        Args:
            zip_file: Open ZipFile object
            csv_filename: Name of CSV file inside ZIP
            output_dir: Output directory for Parquet file

        Raises:
            ExtractionError: If CSV can't be read or converted
            DiskFullError: If insufficient disk space
        """
        output_path = Path(output_dir)
        parquet_filename = Path(csv_filename).stem + ".parquet"
        parquet_path = output_path / parquet_filename

        # Skip if file already exists (protect existing data)
        if parquet_path.exists():
            logger.warning(
                f"Parquet file already exists, skipping: {parquet_path.name}"
            )
            return

        logger.debug(f"Processing {csv_filename} with chunk size {self.chunk_size}")

        try:
            # Detect encoding first
            encoding = self._detect_encoding(zip_file, csv_filename)

            # Try streaming conversion
            try:
                self._stream_csv_to_parquet(
                    zip_file, csv_filename, parquet_path, encoding
                )
            except Exception as stream_error:
                logger.warning(
                    f"Streaming failed for {csv_filename}, "
                    f"attempting fallback: {stream_error}"
                )

                # Clean up partial file before fallback
                self._safe_delete_file(parquet_path, max_attempts=3)

                # Try fallback (in-memory)
                self._fallback_csv_to_parquet(
                    zip_file, csv_filename, parquet_path, encoding
                )

        except DiskFullError:
            self._safe_delete_file(parquet_path)
            raise

        except Exception as e:
            self._safe_delete_file(parquet_path)
            raise ExtractionError(
                str(parquet_path), f"Error converting {csv_filename} to Parquet: {e}"
            )

    def _detect_encoding(self, zip_file: zipfile.ZipFile, csv_filename: str) -> str:
        """Detect correct encoding for CSV file.

        Args:
            zip_file: Open ZipFile object
            csv_filename: CSV filename

        Returns:
            Working encoding string

        Raises:
            ExtractionError: If no encoding works
        """
        for encoding in self.encodings:
            try:
                with zip_file.open(csv_filename) as csv_file:
                    ReadFilesAdapter.read_csv_test_encoding(csv_file, encoding)
                    logger.debug(f"Validated {csv_filename} with encoding {encoding}")
                    return encoding
            except (UnicodeDecodeError, LookupError):
                continue
            except Exception as e:
                logger.debug(f"Test read failed for {csv_filename}: {e}")
                continue

        raise ExtractionError(
            csv_filename,
            f"Could not read {csv_filename} with any encoding "
            f"(tried {', '.join(self.encodings)})",
        )

    def _stream_csv_to_parquet(
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
                text_wrapper = io.TextIOWrapper(csv_file, encoding=encoding, newline="")

                csv_reader = ReadFilesAdapter.read_csv_chunk_size(
                    text_wrapper, chunk_size=self.chunk_size
                )

                for chunk_df in csv_reader:
                    if len(chunk_df) > 0:
                        table = pa.Table.from_pandas(chunk_df)

                        if writer is None:
                            writer = pq.ParquetWriter(
                                parquet_path,
                                table.schema,
                                compression="zstd",
                                compression_level=3,
                            )
                            logger.debug(f"Created {parquet_path.name}")

                        try:
                            writer.write_table(table)
                            total_rows += len(chunk_df)
                        except OSError as e:
                            if "No space left on device" in str(e):
                                raise DiskFullError(str(parquet_path))
                            raise

                if writer is not None:
                    writer.close()
                    writer_closed = True
                    logger.debug(f"Completed {csv_filename}: {total_rows} rows written")

        except Exception:
            if writer is not None and not writer_closed:
                try:
                    writer.close()
                except Exception as close_err:
                    logger.error(f"Failed to close writer: {close_err}")
            raise

    def _fallback_csv_to_parquet(
        self,
        zip_file: zipfile.ZipFile,
        csv_filename: str,
        parquet_path: Path,
        encoding: str,
    ) -> None:
        """Fallback: load entire CSV into memory and convert.

        Args:
            zip_file: Open ZipFile object
            csv_filename: CSV filename
            parquet_path: Output Parquet path
            encoding: CSV encoding

        Raises:
            ExtractionError: If file too large or memory insufficient
            DiskFullError: If disk space exhausted
        """
        # Check file size before loading
        info = zip_file.getinfo(csv_filename)
        size_mb = info.file_size / 1024 / 1024

        if size_mb > self.max_fallback_size_mb:
            raise ExtractionError(
                str(parquet_path),
                f"File too large for fallback ({size_mb:.1f}MB > "
                f"{self.max_fallback_size_mb}MB): {csv_filename}",
            )

        logger.warning(
            f"Loading entire file in memory (fallback): {csv_filename} "
            f"({size_mb:.2f} MB)"
        )

        try:
            with zip_file.open(csv_filename) as csv_file:
                csv_content = csv_file.read()
        except MemoryError as mem_err:
            raise ExtractionError(
                str(parquet_path),
                f"Memory exhausted loading {csv_filename} ({size_mb:.1f}MB): {mem_err}",
            )

        df = ReadFilesAdapter.read_csv_encoding_2(
            csv_content,
            encoding,
        )

        # Write in chunks
        writer = None
        writer_closed = False

        try:
            for chunk_start in range(0, len(df), self.chunk_size):
                chunk_df = df.iloc[chunk_start : chunk_start + self.chunk_size]
                table = pa.Table.from_pandas(chunk_df)

                if writer is None:
                    writer = pq.ParquetWriter(
                        parquet_path,
                        table.schema,
                        compression="zstd",
                        compression_level=3,
                    )

                try:
                    writer.write_table(table)
                except OSError as e:
                    if "No space left on device" in str(e):
                        raise DiskFullError(str(parquet_path))
                    raise

            if writer is not None:
                writer.close()
                writer_closed = True
                logger.info(f"Fallback extraction completed for {csv_filename}")

        finally:
            if writer is not None and not writer_closed:
                try:
                    writer.close()
                except Exception as close_err:
                    logger.error(f"Failed to close fallback writer: {close_err}")

    def _safe_delete_file(self, file_path: Path, max_attempts: int = 3) -> None:
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
                logger.debug(f"Deleted {file_path.name} (attempt {attempt + 1})")
                return
            except Exception as e:
                if attempt >= max_attempts - 1:
                    raise ExtractionError(
                        str(file_path),
                        f"Cannot delete file after {max_attempts} attempts: {e}. "
                        f"Manual intervention required.",
                    )
                time.sleep(0.1 * (attempt + 1))
                logger.debug(
                    f"Retrying deletion of {file_path.name} "
                    f"(attempt {attempt + 2}/{max_attempts})"
                )
