from io import BytesIO

import pandas as pd  # type: ignore


class ReadFilesAdapter:
    @staticmethod
    def read_csv_test_encoding(csv_file, encoding) -> None:
        pd.read_csv(
            BytesIO(csv_file.read(10000)),
            encoding=encoding,
            sep=";",
            on_bad_lines="skip",
            nrows=100,
        )

    @staticmethod
    def read_csv_encoding_2(csv_content, encoding) -> pd.DataFrame:
        pd.read_csv(
            BytesIO(csv_content),
            encoding=encoding,
            sep=";",
            on_bad_lines="skip",
        )

    @staticmethod
    def read_csv_chunk_size(text_wrapper, chunk_size) -> pd.DataFrame:
        return pd.read_csv(
            text_wrapper,
            sep=";",
            on_bad_lines="skip",
            chunksize=chunk_size,
        )
