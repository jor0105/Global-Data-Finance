"""Read CSV members from ZIP archives using a compatible text encoding."""

import zipfile
from io import BytesIO
from typing import IO

import pandas as pd  # type: ignore

from ..core import get_logger
from ..macro_exceptions import ExtractionError

logger = get_logger(__name__)


class ReadFilesAdapter:
    """Provide low-level CSV reading helpers for archive adapters."""

    @staticmethod
    def read_csv_test_encoding(
        zip_file: zipfile.ZipFile, csv_filename: str
    ) -> str:
        """Detect correct encoding for CSV file.

        Args:
            zip_file: Open ZipFile object
            csv_filename: CSV filename

        Returns:
            Working encoding string

        Raises:
            ExtractionError: If no encoding works
        """
        encoding_csv = ['latin-1', 'utf-8', 'iso-8859-1', 'cp1252']
        last_error: Exception | None = None
        for encoding in encoding_csv:
            try:
                with zip_file.open(csv_filename) as csv_file:
                    pd.read_csv(
                        BytesIO(csv_file.read(10000)),
                        encoding=encoding,
                        sep=';',
                        on_bad_lines='skip',
                        nrows=100,
                    )
                    logger.debug(
                        f'Validated {csv_filename} with encoding {encoding}'
                    )
                    return encoding
            except (UnicodeDecodeError, LookupError) as err:
                last_error = err
                continue
            except (
                OSError,
                KeyError,
                EOFError,
                zipfile.BadZipFile,
                zipfile.LargeZipFile,
                pd.errors.ParserError,
                pd.errors.EmptyDataError,
            ) as err:
                last_error = err
                logger.debug('Test read failed for %s: %s', csv_filename, err)
                continue
        raise ExtractionError(
            csv_filename,
            f'Could not read {csv_filename} with any encoding '
            f'(tried {", ".join(encoding_csv)})',
        ) from last_error

    @staticmethod
    def read_csv_chunk_size(
        text_wrapper: IO[str], chunk_size: int
    ) -> pd.DataFrame:
        """Read a CSV stream in pandas chunks using the project delimiter."""
        return pd.read_csv(
            text_wrapper,
            sep=';',
            on_bad_lines='skip',
            chunksize=chunk_size,
        )
