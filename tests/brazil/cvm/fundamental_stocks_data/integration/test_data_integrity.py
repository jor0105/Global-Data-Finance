import zipfile

import pandas as pd  # type: ignore
import pytest

from datafinance.brazil.cvm.fundamental_stocks_data.infra.adapters.extractors_docs import (
    ParquetExtractorAdapterCVM,
)


class TestDataIntegrity:
    @pytest.fixture
    def sample_data(self):
        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
                "value": [10.5, 20.3, 30.7, 40.2, 50.9],
                "category": ["A", "B", "A", "C", "B"],
            }
        )

    @pytest.fixture
    def csv_zip(self, tmp_path, sample_data):
        zip_path = tmp_path / "data.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            csv_content = sample_data.to_csv(sep=";", index=False)
            z.writestr("data.csv", csv_content.encode("latin-1"))
        return zip_path

    def test_no_data_loss_during_extraction(self, csv_zip, tmp_path, sample_data):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        extractor = ParquetExtractorAdapterCVM(chunk_size=50000)
        extractor.extract(source_path=str(csv_zip), destination_path=str(output_dir))

        parquet_file = output_dir / "data.parquet"
        assert parquet_file.exists(), "Parquet was not created"
        df_result = pd.read_parquet(parquet_file)
        assert len(df_result) == len(sample_data), (
            f"DATA LOSS! Original: {len(sample_data)} rows, "
            f"Result: {len(df_result)} rows"
        )
        assert list(df_result.columns) == list(sample_data.columns), (
            f"Different columns! Original: {list(sample_data.columns)}, "
            f"Result: {list(df_result.columns)}"
        )
        for col in sample_data.columns:
            assert df_result[col].equals(
                sample_data[col]
            ), f"DATA CORRUPTION in column '{col}'!"
        print(f"✅ Integrity 100%: {len(df_result)} rows preserved")

    def test_no_data_loss_with_special_characters(self, tmp_path):
        special_data = pd.DataFrame(
            {
                "name": ["João", "José", "María", "François", "Ñoño"],
                "city": ["São Paulo", "Brasília", "Río", "Montréal", "España"],
                "description": [
                    "Ação da empresa",
                    "Título público",
                    "Índice",
                    "Câmbio",
                    "Opção",
                ],
            }
        )
        zip_path = tmp_path / "special.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            csv_content = special_data.to_csv(sep=";", index=False)
            z.writestr("special.csv", csv_content.encode("latin-1"))
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        extractor = ParquetExtractorAdapterCVM(chunk_size=50000)
        extractor.extract(source_path=str(zip_path), destination_path=str(output_dir))

        df_result = pd.read_parquet(output_dir / "special.parquet")
        for col in special_data.columns:
            for i, (original, result) in enumerate(
                zip(special_data[col], df_result[col])
            ):
                assert original == result, (
                    f"Corrupted character at line {i}, column '{col}': "
                    f"'{original}' -> '{result}'"
                )
        print(f"✅ Special characters preserved: {len(df_result)} rows")

    def test_no_data_loss_with_large_numbers(self, tmp_path):
        numeric_data = pd.DataFrame(
            {
                "big_int": [9999999999999999, 1234567890123456, -9876543210987654],
                "float_precision": [
                    1.234567890123456,
                    9.876543210987654,
                    3.141592653589793,
                ],
                "scientific": [1.23e15, 4.56e-10, 7.89e20],
            }
        )
        zip_path = tmp_path / "numeric.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            csv_content = numeric_data.to_csv(sep=";", index=False)
            z.writestr("numeric.csv", csv_content.encode("latin-1"))
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        extractor = ParquetExtractorAdapterCVM(chunk_size=50000)
        extractor.extract(source_path=str(zip_path), destination_path=str(output_dir))

        df_result = pd.read_parquet(output_dir / "numeric.parquet")
        for col in numeric_data.columns:
            if numeric_data[col].dtype == "float64":
                assert (
                    numeric_data[col] - df_result[col]
                ).abs().max() < 1e-10, f"Loss of precision in column '{col}'"
            else:
                assert (
                    numeric_data[col] == df_result[col]
                ).all(), f"Integer corruption in column '{col}'"
        print(f"✅ Numeric precision preserved: {len(df_result)} rows")

    def test_empty_csv_does_not_cause_data_loss(self, tmp_path):
        zip_path = tmp_path / "mixed.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("empty.csv", b"col1;col2\n")
            valid_data = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
            csv_content = valid_data.to_csv(sep=";", index=False)
            z.writestr("valid.csv", csv_content.encode("latin-1"))
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        extractor = ParquetExtractorAdapterCVM(chunk_size=50000)
        extractor.extract(source_path=str(zip_path), destination_path=str(output_dir))

        valid_parquet = output_dir / "valid.parquet"
        assert valid_parquet.exists(), "Valid CSV was not processed"
        df_result = pd.read_parquet(valid_parquet)
        assert len(df_result) == 2, "Valid CSV data was lost"
        print("✅ Empty CSV did not affect other data")
