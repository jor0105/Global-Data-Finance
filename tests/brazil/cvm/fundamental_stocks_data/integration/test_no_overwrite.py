import zipfile

import pandas as pd  # type: ignore

from src.brazil.cvm.fundamental_stocks_data.infra.adapters.extractors_docs import (
    ParquetExtractor,
)


class TestNoOverwrite:
    def test_existing_parquet_is_never_overwritten(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        original_data = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "value": [100, 200, 300],
                "important": ["CRITICAL", "DATA", "HERE"],
            }
        )

        existing_file = output_dir / "data.parquet"
        original_data.to_parquet(existing_file)

        original_size = existing_file.stat().st_size

        print("✓ Original file created:")
        print(f"  Rows: {len(original_data)}")
        print(f"  Size: {original_size} bytes")

        zip_path = tmp_path / "new_data.zip"

        new_data = pd.DataFrame(
            {
                "id": [10, 20, 30, 40, 50],
                "value": [999, 888, 777, 666, 555],
                "important": ["NEW", "DATA", "SHOULD", "NOT", "APPEAR"],
            }
        )

        with zipfile.ZipFile(zip_path, "w") as z:
            csv_content = new_data.to_csv(sep=";", index=False)
            z.writestr("data.csv", csv_content.encode("latin-1"))

        print("✓ ZIP with new data created (should be ignored)")

        extractor = ParquetExtractor(chunk_size=50000)
        extractor.extract(source_path=str(zip_path), destination_dir=str(output_dir))

        assert existing_file.exists(), "CRITICAL: File was DELETED!"

        new_size = existing_file.stat().st_size
        assert (
            new_size == original_size
        ), f"CRITICAL: File was MODIFIED! Original size: {original_size}, new: {new_size}"

        df_after = pd.read_parquet(existing_file)

        assert (
            len(df_after) == len(original_data)
        ), f"CRITICAL: Number of rows changed! Original: {len(original_data)}, Current: {len(df_after)}"

        assert df_after.equals(
            original_data
        ), f"CRITICAL: DATA WAS OVERWRITTEN!\nOriginal:\n{original_data}\nCurrent:\n{df_after}"

        print("✅ Original file 100% preserved (extraction blocked)")

    def test_multiple_extraction_attempts_preserve_original(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        original_data = pd.DataFrame(
            {"counter": [1, 2, 3, 4, 5], "name": ["original"] * 5}
        )

        parquet_file = output_dir / "test.parquet"
        original_data.to_parquet(parquet_file)

        for i in range(5):
            new_data = pd.DataFrame(
                {"counter": [i * 10, i * 20], "name": [f"attempt_{i}"] * 2}
            )

            zip_path = tmp_path / f"attempt_{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as z:
                csv_content = new_data.to_csv(sep=";", index=False)
                z.writestr("test.csv", csv_content.encode("latin-1"))

            extractor = ParquetExtractor(chunk_size=50000)
            extractor.extract(
                source_path=str(zip_path), destination_dir=str(output_dir)
            )

        df_final = pd.read_parquet(parquet_file)

        assert df_final.equals(
            original_data
        ), f"CRITICAL: Data was corrupted after 5 attempts!\nOriginal:\n{original_data}\nFinal:\n{df_final}"

        print("✅ Data preserved after 5 extraction attempts")

    def test_concurrent_extractions_do_not_overwrite(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        data1 = pd.DataFrame({"id": [1], "source": ["first"]})
        data2 = pd.DataFrame({"id": [2], "source": ["second"]})

        zip1 = tmp_path / "zip1.zip"
        zip2 = tmp_path / "zip2.zip"

        for zip_path, data in [(zip1, data1), (zip2, data2)]:
            with zipfile.ZipFile(zip_path, "w") as z:
                csv_content = data.to_csv(sep=";", index=False)
                z.writestr("data.csv", csv_content.encode("latin-1"))

        extractor = ParquetExtractor(chunk_size=50000)
        extractor.extract(source_path=str(zip1), destination_dir=str(output_dir))

        extractor.extract(source_path=str(zip2), destination_dir=str(output_dir))

        df_result = pd.read_parquet(output_dir / "data.parquet")

        assert (
            df_result["source"].iloc[0] == "first"
        ), f"CRITICAL: Second file overwrote the first! Source: {df_result['source'].iloc[0]}"

        print("✅ First file preserved (second blocked)")

    def test_partial_extraction_does_not_corrupt_existing_files(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        existing_data = pd.DataFrame({"id": [1, 2, 3], "existing": [True] * 3})
        existing_file = output_dir / "file1.parquet"
        existing_data.to_parquet(existing_file)

        zip_path = tmp_path / "multi.zip"

        with zipfile.ZipFile(zip_path, "w") as z:
            df1 = pd.DataFrame({"id": [100, 200], "existing": [False] * 2})
            z.writestr("file1.csv", df1.to_csv(sep=";", index=False).encode("latin-1"))

            df2 = pd.DataFrame({"id": [10, 20], "new_file": [True] * 2})
            z.writestr("file2.csv", df2.to_csv(sep=";", index=False).encode("latin-1"))

        extractor = ParquetExtractor(chunk_size=50000)
        extractor.extract(source_path=str(zip_path), destination_dir=str(output_dir))

        df_file1 = pd.read_parquet(existing_file)
        assert df_file1.equals(existing_data), "CRITICAL: existing file1 was modified!"

        file2_path = output_dir / "file2.parquet"
        assert file2_path.exists(), "file2 was not created"

        df_file2 = pd.read_parquet(file2_path)
        assert len(df_file2) == 2, "file2 has incorrect data"

        print("✅ Partial extraction: file1 preserved, file2 created")
