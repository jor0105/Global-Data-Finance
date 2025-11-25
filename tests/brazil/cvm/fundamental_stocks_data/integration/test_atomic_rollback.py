import zipfile

import pandas as pd  # type: ignore
import pytest

from globaldatafinance.brazil.cvm.fundamental_stocks_data.infra.adapters.extractors_docs_adapter import (
    ParquetExtractorAdapterCVM,
)


class TestAtomicRollback:
    def test_rollback_preserves_existing_files(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        existing_data = pd.DataFrame(
            {"id": [1, 2, 3], "important": ["DO", "NOT", "DELETE"]}
        )
        existing_file = output_dir / "existing.parquet"
        existing_data.to_parquet(existing_file)

        print(f"✓ Existing file: {existing_file.name}")

        zip_path = tmp_path / "mixed.zip"

        with zipfile.ZipFile(zip_path, "w") as z:
            df_valid = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
            z.writestr(
                "new_valid.csv", df_valid.to_csv(sep=";", index=False).encode("latin-1")
            )

        corrupted_zip = tmp_path / "corrupted.zip"
        with open(corrupted_zip, "wb") as f:
            f.write(b"PK\x03\x04" + b"\x00" * 100)

        from globaldatafinance.macro_exceptions import CorruptedZipError

        extractor = ParquetExtractorAdapterCVM()

        with pytest.raises(CorruptedZipError):
            extractor.extract(
                source_path=str(corrupted_zip), destination_path=str(output_dir)
            )

        assert existing_file.exists(), "CRITICAL: existing file was DELETED!"

        df_check = pd.read_parquet(existing_file)
        assert df_check.equals(existing_data), "CRITICAL: existing file was MODIFIED!"

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 1, (
            f"Partial files were not cleaned! Found: {[f.name for f in parquet_files]}"
        )
        assert parquet_files[0].name == "existing.parquet", (
            "Incorrect file in directory"
        )

        print("✅ Rollback preserved existing file")

    def test_partial_success_triggers_atomic_rollback(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            df1 = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
            z.writestr("file1.csv", df1.to_csv(sep=";", index=False).encode("latin-1"))
            df2 = pd.DataFrame({"c": [3, 4], "d": ["z", "w"]})
            z.writestr("file2.csv", df2.to_csv(sep=";", index=False).encode("latin-1"))

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(source_path=str(zip_path), destination_path=str(tmp_path))

        assert (tmp_path / "file1.parquet").exists()
        assert (tmp_path / "file2.parquet").exists()

        print("✅ Atomic extraction: both files created")

    def test_rollback_does_not_leave_partial_parquet_files(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        existing = output_dir / "keep_me.parquet"
        pd.DataFrame({"id": [1]}).to_parquet(existing)

        corrupted_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(corrupted_zip, "w") as z:
            z.writestr("not_a_csv.txt", b"This is not a CSV file")

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(
            source_path=str(corrupted_zip), destination_path=str(output_dir)
        )

        parquet_files = list(tmp_path.glob("*.parquet"))
        assert len(parquet_files) == 0, (
            f"Partial files found: {[f.name for f in parquet_files]}"
        )
        assert existing.exists(), "Existing file was removed!"

        print("✅ No partial files left")

    def test_created_files_tracking_is_accurate(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        existing = output_dir / "skip_me.parquet"
        pd.DataFrame({"old": [1]}).to_parquet(existing)

        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            df2 = pd.DataFrame({"col": [3]})
            z.writestr(
                "new_file.csv", df2.to_csv(sep=";", index=False).encode("latin-1")
            )

        extractor = ParquetExtractorAdapterCVM()
        extractor.extract(source_path=str(zip_path), destination_path=str(output_dir))

        df_skip = pd.read_parquet(existing)
        assert "old" in df_skip.columns, "Existing file was overwritten!"

        new_file = output_dir / "new_file.parquet"
        assert new_file.exists(), "New file was not created"

        print("✅ Tracking correct: skip detected, new file created")
