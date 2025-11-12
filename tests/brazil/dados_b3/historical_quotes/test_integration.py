"""Integration tests for historical_quotes module.

These tests verify the complete end-to-end flow:
1. Creating DocsToExtractor with validated parameters
2. Extracting data from mock ZIP files
3. Verifying output Parquet files
4. Testing error handling and edge cases
"""

from pathlib import Path

import polars as pl
import pytest

from src.brazil.dados_b3.historical_quotes import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)
from src.presentation.b3_docs.result_formatters import HistoricalQuotesResultFormatter
from tests.fixtures import MockZipFiles


class TestHistoricalQuotesIntegration:
    """Integration tests for complete historical quotes extraction flow."""

    @pytest.fixture
    def source_dir_with_zips(self, tmp_path):
        """Create a source directory with multiple COTAHIST ZIP files."""
        source_dir = tmp_path / "cotahist_source"
        source_dir.mkdir()

        # Create ZIP files for multiple years
        MockZipFiles.create_multiple_cotahist_zips(source_dir, 2022, 2023)

        return source_dir

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create an output directory for extracted files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    def test_full_extraction_flow_fast_mode(self, source_dir_with_zips, output_dir):
        """Test complete extraction flow in fast mode."""
        # Step 1: Create DocsToExtractor entity
        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir_with_zips),
            assets_list=["ações"],
            initial_year=2022,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        # Verify entity was created correctly
        assert docs_to_extract.path_of_docs == str(source_dir_with_zips)
        assert "ações" in docs_to_extract.set_assets
        assert len(docs_to_extract.set_documents_to_download) == 2  # 2022 and 2023

        # Step 2: Extract data
        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            processing_mode="fast",
            output_filename="test_output.parquet",
        )

        # Step 3: Enrich result with presentation data
        result = HistoricalQuotesResultFormatter.enrich_result(result)

        # Step 4: Verify results
        assert result["success"] is True
        assert result["total_files"] == 2
        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert result["total_records"] > 0
        assert "message" in result
        assert "Successfully extracted" in result["message"]

        # Step 5: Verify output file exists and is valid
        output_file = Path(result["output_file"])
        assert output_file.exists()
        assert output_file.suffix == ".parquet"

        # Step 6: Verify Parquet content
        df = pl.read_parquet(output_file)
        assert len(df) > 0
        assert "codneg" in df.columns
        assert "preult" in df.columns
        assert "data_pregao" in df.columns

    def test_full_extraction_flow_slow_mode(self, source_dir_with_zips, output_dir):
        """Test complete extraction flow in slow mode."""
        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir_with_zips),
            assets_list=["ações", "etf"],
            initial_year=2022,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            processing_mode="slow",
            output_filename="slow_mode_output.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        assert result["success"] is True
        assert result["total_records"] > 0

        output_file = Path(result["output_file"])
        assert output_file.exists()

        df = pl.read_parquet(output_file)
        assert len(df) > 0

    def test_extraction_with_single_year(self, tmp_path):
        """Test extraction with just one year."""
        source_dir = tmp_path / "single_year"
        source_dir.mkdir()
        MockZipFiles.create_cotahist_zip(source_dir, 2023)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir),
            assets_list=["ações"],
            initial_year=2023,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            output_filename="single_year.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        assert result["success"] is True
        assert result["total_files"] == 1
        assert result["success_count"] == 1

    def test_extraction_with_multiple_asset_classes(
        self, source_dir_with_zips, output_dir
    ):
        """Test extraction filtering multiple asset classes."""
        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir_with_zips),
            assets_list=["ações", "etf", "opções"],
            initial_year=2022,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            output_filename="multi_asset.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        assert result["success"] is True
        assert result["total_records"] > 0

        # Verify output contains different asset types
        df = pl.read_parquet(Path(result["output_file"]))
        assert len(df) > 0
        # Should have records from different TPMERC codes
        assert df["tpmerc"].n_unique() >= 1

    def test_extraction_with_empty_zip(self, tmp_path):
        """Test extraction with ZIP containing no matching records."""
        source_dir = tmp_path / "empty_data"
        source_dir.mkdir()
        MockZipFiles.create_empty_cotahist_zip(source_dir, 2023)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir),
            assets_list=["ações"],
            initial_year=2023,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            output_filename="empty_output.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        assert result["success"] is True
        assert result["total_records"] == 0

    def test_extraction_with_no_zip_files(self, tmp_path):
        """Test extraction when no ZIP files match the year range."""
        source_dir = tmp_path / "no_files"
        source_dir.mkdir()
        # Create a ZIP for 2020, but request 2023
        MockZipFiles.create_cotahist_zip(source_dir, 2020)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir),
            assets_list=["ações"],
            initial_year=2023,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        # Should have no documents to download
        assert len(docs_to_extract.set_documents_to_download) == 0

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            output_filename="no_files_output.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        # Should succeed but with 0 records
        assert result["total_files"] == 0
        assert result["total_records"] == 0

    def test_extraction_destination_defaults_to_source(self, tmp_path):
        """Test that destination path defaults to source path."""
        source_dir = tmp_path / "source_and_dest"
        source_dir.mkdir()
        MockZipFiles.create_cotahist_zip(source_dir, 2023)

        # Don't specify destination_path
        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir),
            assets_list=["ações"],
            initial_year=2023,
            last_year=2023,
            # destination_path not specified
        ).execute()

        # Destination should default to source
        assert docs_to_extract.destination_path == str(source_dir)

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            output_filename="default_dest.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        assert result["success"] is True

        # Output file should be in source directory
        output_file = Path(result["output_file"])
        assert output_file.parent == source_dir

    def test_extraction_with_custom_output_filename(
        self, source_dir_with_zips, output_dir
    ):
        """Test extraction with custom output filename."""
        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir_with_zips),
            assets_list=["ações"],
            initial_year=2022,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = extract_use_case.execute_sync(
            docs_to_extract=docs_to_extract,
            output_filename="custom_name.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        assert result["success"] is True

        output_file = Path(result["output_file"])
        assert output_file.name == "custom_name.parquet"
        assert output_file.exists()

    @pytest.mark.asyncio
    async def test_async_extraction_flow(self, source_dir_with_zips, output_dir):
        """Test async extraction flow."""
        docs_to_extract = CreateDocsToExtractUseCase(
            path_of_docs=str(source_dir_with_zips),
            assets_list=["ações"],
            initial_year=2022,
            last_year=2023,
            destination_path=str(output_dir),
        ).execute()

        extract_use_case = ExtractHistoricalQuotesUseCase()
        result = await extract_use_case.execute(
            docs_to_extract=docs_to_extract,
            output_filename="async_output.parquet",
        )

        result = HistoricalQuotesResultFormatter.enrich_result(result)

        assert result["success"] is True
        assert result["total_records"] > 0

        output_file = Path(result["output_file"])
        assert output_file.exists()
