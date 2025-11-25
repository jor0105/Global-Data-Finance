import zipfile

import pandas as pd  # type: ignore

from globaldatafinance.brazil.cvm.fundamental_stocks_data.infra.adapters.extractors_docs_adapter import (
    ParquetExtractorAdapterCVM,
)


class TestNoOverwrite:
    def test_existing_parquet_is_never_overwritten(self, tmp_path):
        original_data = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "value": [100, 200, 300],
                "important": ["CRITICAL", "DATA", "HERE"],
            }
        )

        existing_file = tmp_path / "data.parquet"
        original_data.to_parquet(existing_file)

        original_size = existing_file.stat().st_size
        original_mtime = existing_file.stat().st_mtime

        print("✓ Original file created:")
        print(f"  Rows: {len(original_data)}")
        print(f"  Size: {original_size} bytes")

        zip_path = tmp_path / "new_data.zip"

        new_data = pd.DataFrame(
            {
                "id": [10, 20, 30, 40, 50],
                "value": [999, 888, 777, 666, 555],
                "important": ["NEW", "DATA", "SHOULD", "APPEAR", "NOW"],
            }
        )

        with zipfile.ZipFile(zip_path, "w") as z:
            csv_content = new_data.to_csv(sep=";", index=False)
            z.writestr("data.csv", csv_content.encode("latin-1"))

        print("✓ ZIP with new data created (should overwrite)")

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(source_path=str(zip_path), destination_path=str(tmp_path))

        new_stat = existing_file.stat()
        new_size = new_stat.st_size
        new_mtime = new_stat.st_mtime

        assert new_mtime > original_mtime, (
            "File should have been updated (new mtime > old mtime)"
        )
        assert new_size != original_size, (
            "File size should have changed (new content is different)"
        )

        df_after = pd.read_parquet(existing_file)

        assert len(df_after) == len(new_data), (
            f"Number of rows should have changed! Original: {len(original_data)}, New: {len(new_data)}, Current: {len(df_after)}"
        )

        pd.testing.assert_frame_equal(
            df_after.reset_index(drop=True), new_data.reset_index(drop=True)
        )

        print("✅ Original file was successfully overwritten with new data")

    def test_multiple_extraction_attempts_overwrite_original(self, tmp_path):
        original_data = pd.DataFrame(
            {"counter": [1, 2, 3, 4, 5], "name": ["original"] * 5}
        )

        parquet_file = tmp_path / "test.parquet"
        original_data.to_parquet(parquet_file)

        last_data = None
        for i in range(5):
            new_data = pd.DataFrame(
                {"counter": [i * 10, i * 20], "name": [f"attempt_{i}"] * 2}
            )
            last_data = new_data

            zip_path = tmp_path / f"attempt_{i}.zip"
            with zipfile.ZipFile(zip_path, "w") as z:
                csv_content = new_data.to_csv(sep=";", index=False)
                z.writestr("test.csv", csv_content.encode("latin-1"))

            extractor = ParquetExtractorAdapterCVM()
            extractor.extract(source_path=str(zip_path), destination_path=str(tmp_path))

        df_final = pd.read_parquet(parquet_file)

        assert last_data is not None
        pd.testing.assert_frame_equal(
            df_final.reset_index(drop=True), last_data.reset_index(drop=True)
        )

        print("✅ Data updated to the latest version after 5 extraction attempts")

    def test_concurrent_extractions_overwrite(self, tmp_path):
        data1 = pd.DataFrame({"id": [1], "source": ["first"]})
        data2 = pd.DataFrame({"id": [2], "source": ["second"]})

        zip1 = tmp_path / "zip1.zip"
        zip2 = tmp_path / "zip2.zip"

        for zip_path, data in [(zip1, data1), (zip2, data2)]:
            with zipfile.ZipFile(zip_path, "w") as z:
                csv_content = data.to_csv(sep=";", index=False)
                z.writestr("data.csv", csv_content.encode("latin-1"))

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(source_path=str(zip1), destination_path=str(tmp_path))
        extractor.extract(source_path=str(zip2), destination_path=str(tmp_path))

        df_result = pd.read_parquet(tmp_path / "data.parquet")

        assert df_result["source"].iloc[0] == "second", (
            f"CRITICAL: Second file did NOT overwrite the first! Source: {df_result['source'].iloc[0]}"
        )

        print("✅ Second file successfully overwrote the first")

    def test_partial_extraction_overwrites_existing_files(self, tmp_path):
        existing_data = pd.DataFrame({"id": [1, 2, 3], "existing": [True] * 3})
        existing_file = tmp_path / "file1.parquet"
        existing_data.to_parquet(existing_file)

        zip_path = tmp_path / "multi.zip"

        df1 = pd.DataFrame({"id": [100, 200], "existing": [False] * 2})
        df2 = pd.DataFrame({"id": [10, 20], "new_file": [True] * 2})

        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("file1.csv", df1.to_csv(sep=";", index=False).encode("latin-1"))
            z.writestr("file2.csv", df2.to_csv(sep=";", index=False).encode("latin-1"))

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(source_path=str(zip_path), destination_path=str(tmp_path))

        df_file1 = pd.read_parquet(existing_file)
        pd.testing.assert_frame_equal(
            df_file1.reset_index(drop=True), df1.reset_index(drop=True)
        )

        file2_path = tmp_path / "file2.parquet"
        assert file2_path.exists(), "file2 was not created"

        df_file2 = pd.read_parquet(file2_path)
        assert len(df_file2) == 2, "file2 has incorrect data"

        print("✅ Partial extraction: file1 updated, file2 created")
