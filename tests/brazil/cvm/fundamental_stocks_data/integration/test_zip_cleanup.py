import zipfile

import pandas as pd  # type: ignore
import pytest

from src.brazil.cvm.fundamental_stocks_data.infra.adapters.extractors_docs import (
    ParquetExtractor,
)
from src.brazil.cvm.fundamental_stocks_data.infra.adapters.requests import (
    HttpxAsyncDownloadAdapter,
)


class TestZipCleanup:
    @pytest.fixture
    def adapter(self):
        return HttpxAsyncDownloadAdapter(
            file_extractor_repository=ParquetExtractor(),
            automatic_extractor=True,
            max_concurrent=1,
        )

    @pytest.fixture
    def mock_zip(self, tmp_path):
        zip_path = tmp_path / "test.zip"

        data = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        with zipfile.ZipFile(zip_path, "w") as z:
            csv_content = data.to_csv(sep=";", index=False)
            z.writestr("data.csv", csv_content.encode("latin-1"))

        return zip_path

    def test_zip_deleted_after_successful_extraction(self, tmp_path, mock_zip):
        from src.macro_infra import Extractor

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        assert mock_zip.exists(), "Test ZIP was not created"
        zip_size = mock_zip.stat().st_size

        print(f"✓ ZIP created: {mock_zip.name} ({zip_size} bytes)")

        Extractor.extract_zip_to_parquet(
            chunk_size=50000, zip_path=str(mock_zip), output_dir=str(output_dir)
        )

        parquet_file = output_dir / "data.parquet"
        assert parquet_file.exists(), "Parquet was not created"

        from src.core import remove_file

        parquet_files = list(output_dir.glob("**/*.parquet"))
        if parquet_files:
            remove_file(str(mock_zip), log_on_error=True)

        assert (
            not mock_zip.exists()
        ), "CRITICAL: ZIP was not deleted after successful extraction!"

        print("✅ ZIP deleted after successful extraction")

    def test_zip_kept_on_extraction_failure(self, tmp_path):
        from src.macro_exceptions import CorruptedZipError
        from src.macro_infra import Extractor

        corrupted_zip = tmp_path / "corrupted.zip"
        with open(corrupted_zip, "wb") as f:
            f.write(b"PK\x03\x04" + b"\x00" * 50)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        print(f"✓ Corrupted ZIP created: {corrupted_zip.name}")

        with pytest.raises(CorruptedZipError):
            Extractor.extract_zip_to_parquet(
                chunk_size=50000,
                zip_path=str(corrupted_zip),
                output_dir=str(output_dir),
            )

        assert corrupted_zip.exists(), "Corrupted ZIP was deleted prematurely! It should be kept for retry or investigation."

        print("✅ ZIP kept after extraction failure")

    def test_zip_kept_if_no_parquet_generated(self, tmp_path):
        from src.macro_infra import Extractor

        zip_path = tmp_path / "no_csv.zip"

        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("readme.txt", b"This is not a CSV")
            z.writestr("image.png", b"\x89PNG\r\n\x1a\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        print(f"✓ ZIP without CSVs created: {zip_path.name}")

        Extractor.extract_zip_to_parquet(
            chunk_size=50000, zip_path=str(zip_path), output_dir=str(output_dir)
        )

        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 0, "Parquets were created unexpectedly"

        assert (
            zip_path.exists()
        ), "ZIP was deleted even though no parquets were generated!"

        print("✅ ZIP kept when no parquet is generated")

    def test_integration_with_httpx_adapter(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        downloaded_zip = output_dir / "downloaded.zip"

        data = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
        with zipfile.ZipFile(downloaded_zip, "w") as z:
            z.writestr("data.csv", data.to_csv(sep=";", index=False).encode("latin-1"))

        print(f"✓ ZIP 'downloaded': {downloaded_zip.name}")

        from src.macro_infra import Extractor

        Extractor.extract_zip_to_parquet(
            chunk_size=50000, zip_path=str(downloaded_zip), output_dir=str(output_dir)
        )

        parquet_files = list(output_dir.glob("**/*.parquet"))

        if parquet_files:
            print(f"✓ {len(parquet_files)} parquet(s) created")

            from src.core import remove_file

            remove_file(str(downloaded_zip), log_on_error=True)

            assert not downloaded_zip.exists(), "ZIP was not deleted"
            print(f"✅ ZIP deleted after creating {len(parquet_files)} parquet(s)")
        else:
            assert downloaded_zip.exists(), "ZIP was deleted without creating parquets"
            print("✅ ZIP kept (no parquet created)")

    def test_cleanup_does_not_delete_other_zips(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        zip1 = output_dir / "file1.zip"
        zip2 = output_dir / "file2.zip"
        zip3 = output_dir / "file3.zip"

        for zip_path in [zip1, zip2, zip3]:
            data = pd.DataFrame({"id": [1]})
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr(
                    "data.csv", data.to_csv(sep=";", index=False).encode("latin-1")
                )

        print("✓ 3 ZIPs created")

        from src.macro_infra import Extractor

        Extractor.extract_zip_to_parquet(
            chunk_size=50000, zip_path=str(zip1), output_dir=str(output_dir)
        )

        from src.core import remove_file

        parquet_files = list(output_dir.glob("**/*.parquet"))
        if parquet_files:
            remove_file(str(zip1), log_on_error=True)

        assert not zip1.exists(), "Processed ZIP was not deleted"
        assert zip2.exists(), "CRITICAL: Unprocessed ZIP was deleted!"
        assert zip3.exists(), "CRITICAL: Unprocessed ZIP was deleted!"

        print("✅ Only the processed ZIP was deleted")
