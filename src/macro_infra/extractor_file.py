import logging
import zipfile
from pathlib import Path

import pandas as pd  # type: ignore
import pyarrow as pa  # type: ignore
import pyarrow.parquet as pq  # type: ignore

from src.macro_exceptions import (
    CorruptedZipError,
    DiskFullError,
    ExtractionError,
    InvalidDestinationPathError,
)

logger = logging.getLogger(__name__)


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
    def _extract_single_csv(
        chunk_size: int, zip_file: zipfile.ZipFile, csv_filename: str, output_dir: str
    ) -> None:
        """Extract a single CSV file from ZIP and convert to Parquet.

        Args:
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

        # List of encodings to try in order
        encodings_to_try = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

        try:
            # Read CSV and convert to Parquet in chunks to save memory
            csv_data = None
            last_encoding_error = None

            # Try different encodings
            for encoding in encodings_to_try:
                try:
                    with zip_file.open(csv_filename) as csv_file:
                        csv_data = pd.read_csv(
                            csv_file,
                            encoding=encoding,
                            sep=";",  # CVM uses a semicolon as a delimiter
                            dtype_backend="numpy_nullable",
                            on_bad_lines="skip",  # Skip malformed lines
                            engine="python",  # More flexible parser
                            skipinitialspace=True,  # Strip whitespace after the delimiter
                        )
                    logger.debug(
                        f"Successfully read {csv_filename} with encoding {encoding}"
                    )
                    break
                except (UnicodeDecodeError, LookupError) as e:
                    last_encoding_error = e
                    logger.debug(
                        f"Failed to read {csv_filename} with encoding {encoding}: {e}"
                    )
                    continue

            if csv_data is None:
                raise ExtractionError(
                    str(parquet_path),
                    f"Could not read {csv_filename} with any encoding "
                    f"(tried {', '.join(encodings_to_try)}): {last_encoding_error}",
                )

            # Process data in chunks for memory optimization
            first_chunk = True
            for chunk_start in range(0, len(csv_data), chunk_size):
                chunk = csv_data.iloc[chunk_start : chunk_start + chunk_size]

                try:
                    # Convert to Arrow table
                    table = pa.Table.from_pandas(chunk)

                    # Write or append to Parquet
                    if first_chunk:
                        pq.write_table(table, parquet_path)
                        first_chunk = False
                        logger.debug(f"Created {parquet_filename}")
                    else:
                        # Append mode: read existing, concatenate, and rewrite
                        existing_table = pq.read_table(parquet_path)
                        combined = pa.concat_tables([existing_table, table])
                        pq.write_table(combined, parquet_path)
                        logger.debug(f"Appended chunk to {parquet_filename}")

                except OSError as e:
                    if "No space left on device" in str(e):
                        raise DiskFullError(str(parquet_path))
                    raise

        except pd.errors.ParserError as e:
            # Clean up the partial file if it exists
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
            # Clean up the partial file if it exists
            if parquet_path.exists():
                try:
                    parquet_path.unlink()
                except Exception:
                    pass
            raise ExtractionError(
                str(parquet_path),
                f"Error converting {csv_filename} to Parquet: {e}",
            )
