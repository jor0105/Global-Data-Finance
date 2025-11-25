import zipfile
from io import BytesIO

import pandas as pd  # type: ignore

from ..core import get_logger
from ..macro_exceptions import ExtractionError

logger = get_logger(__name__)


class ReadFilesAdapter:
    @staticmethod
    def read_csv_test_encoding(zip_file: zipfile.ZipFile, csv_filename: str) -> str:
        """Detect correct encoding for CSV file.

        Args:
            zip_file: Open ZipFile object
            csv_filename: CSV filename

        Returns:
            Working encoding string

        Raises:
            ExtractionError: If no encoding works
        """
        encoding_csv = ["latin-1", "utf-8", "iso-8859-1", "cp1252"]
        for encoding in encoding_csv:
            try:
                with zip_file.open(csv_filename) as csv_file:
                    pd.read_csv(
                        BytesIO(csv_file.read(10000)),
                        encoding=encoding,
                        sep=";",
                        on_bad_lines="skip",
                        nrows=100,
                    )
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
            f"(tried {', '.join(encoding_csv)})",
        )

    @staticmethod
    def read_csv_chunk_size(text_wrapper, chunk_size) -> pd.DataFrame:
        return pd.read_csv(
            text_wrapper,
            sep=";",
            on_bad_lines="skip",
            chunksize=chunk_size,
        )
