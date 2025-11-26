import tempfile
from pathlib import Path

import polars as pl
import pytest

from globaldatafinance.application import HistoricalQuotesB3
from globaldatafinance.brazil.b3_data.historical_quotes.exceptions import (
    InvalidProcessingMode,
)


@pytest.mark.integration
class TestFastModeExtraction:
    @pytest.fixture
    def historical_quotes(self):
        return HistoricalQuotesB3()

    def test_initialization(self, historical_quotes):
        assert historical_quotes is not None
        assert isinstance(historical_quotes, HistoricalQuotesB3)

    def test_get_available_assets(self, historical_quotes):
        assets = historical_quotes.get_available_assets()
        assert isinstance(assets, list), "Assets should be a list"
        assert len(assets) > 0, "Assets list should not be empty"
        assert "ações" in assets, "ações should be in available assets"
        assert all(isinstance(asset, str) for asset in assets), (
            "All assets should be strings"
        )

    def test_get_available_years(self, historical_quotes):
        years = historical_quotes.get_available_years()
        assert isinstance(years, dict), "Years should be a dictionary"
        assert "minimal_year" in years, "minimal_year key should exist"
        assert "current_year" in years, "current_year key should exist"
        assert isinstance(years["minimal_year"], int), (
            "minimal_year should be an integer"
        )
        assert isinstance(years["current_year"], int), (
            "current_year should be an integer"
        )
        assert years["minimal_year"] == 1986, "minimal_year should be 1986"
        assert years["current_year"] >= 2024, "current_year should be >= 2024"
        assert years["minimal_year"] <= years["current_year"], (
            "minimal_year should be <= current_year"
        )

    def test_fast_mode_extraction(self, historical_quotes):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = historical_quotes.extract(
                path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                destination_path=temp_dir,
                assets_list=["ações"],
                initial_year=2024,
                last_year=2024,
                output_filename="test_fast",
                processing_mode="fast",
            )

            # Validar estrutura do resultado
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "total_files" in result, "total_files key should exist"
            assert "success_count" in result, "success_count key should exist"
            assert "error_count" in result, "error_count key should exist"
            assert "total_records" in result, "total_records key should exist"
            assert "output_file" in result, "output_file key should exist"

            # Validar tipos de dados
            assert isinstance(result["total_files"], int), (
                "total_files should be an integer"
            )
            assert isinstance(result["success_count"], int), (
                "success_count should be an integer"
            )
            assert isinstance(result["error_count"], int), (
                "error_count should be an integer"
            )
            assert isinstance(result["total_records"], int), (
                "total_records should be an integer"
            )
            assert isinstance(result["output_file"], str), (
                "output_file should be a string"
            )

            # Validar valores lógicos
            assert result["total_files"] >= 0, "total_files should be non-negative"
            assert result["success_count"] >= 0, "success_count should be non-negative"
            assert result["error_count"] >= 0, "error_count should be non-negative"
            assert result["total_records"] >= 0, "total_records should be non-negative"
            assert (
                result["success_count"] + result["error_count"] <= result["total_files"]
            ), "success + error should not exceed total"

            if result["total_files"] > 0:
                assert result["success_count"] > 0, (
                    "success_count should be > 0 if files were found"
                )
                assert result["total_records"] > 0, (
                    "total_records should be > 0 if files were found"
                )

                output_file = Path(result["output_file"])
                assert output_file.exists(), (
                    f"Output file should exist at {output_file}"
                )
                assert output_file.suffix == ".parquet", (
                    "Output file should be a parquet file"
                )
                assert output_file.stat().st_size > 0, "Output file should not be empty"

                df = pl.read_parquet(output_file)
                assert isinstance(df, pl.DataFrame), (
                    "Output file should contain a valid Polars DataFrame"
                )
                assert len(df) == result["total_records"], (
                    "DataFrame rows should match total_records"
                )
                assert len(df.columns) > 0, "DataFrame should have columns"

    def test_slow_mode_extraction(self, historical_quotes):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = historical_quotes.extract(
                path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                destination_path=temp_dir,
                assets_list=["ações"],
                initial_year=2024,
                last_year=2024,
                output_filename="test_slow",
                processing_mode="slow",
            )

            # Validar estrutura do resultado
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "total_files" in result, "total_files key should exist"
            assert "success_count" in result, "success_count key should exist"
            assert "error_count" in result, "error_count key should exist"
            assert "total_records" in result, "total_records key should exist"
            assert isinstance(result["total_files"], int), (
                "total_files should be an integer"
            )
            assert isinstance(result["success_count"], int), (
                "success_count should be an integer"
            )
            assert isinstance(result["error_count"], int), (
                "error_count should be an integer"
            )
            assert isinstance(result["total_records"], int), (
                "total_records should be an integer"
            )
            assert result["total_files"] >= 0, "total_files should be non-negative"
            assert result["success_count"] >= 0, "success_count should be non-negative"
            assert result["error_count"] >= 0, "error_count should be non-negative"
            assert result["total_records"] >= 0, "total_records should be non-negative"

            if result["total_files"] > 0:
                assert result["success_count"] > 0, (
                    "success_count should be > 0 if files were found"
                )
                assert result["total_records"] > 0, (
                    "total_records should be > 0 if files were found"
                )

    def test_multiple_assets(self, historical_quotes):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = historical_quotes.extract(
                path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                destination_path=temp_dir,
                assets_list=["ações", "etf"],
                initial_year=2024,
                last_year=2024,
                output_filename="test_multi_assets",
                processing_mode="fast",
            )

            assert isinstance(result, dict), "Result should be a dictionary"
            assert "total_files" in result, "total_files key should exist"
            assert "total_records" in result, "total_records key should exist"
            assert isinstance(result["total_files"], int), (
                "total_files should be an integer"
            )
            assert isinstance(result["total_records"], int), (
                "total_records should be an integer"
            )
            assert result["total_files"] >= 0, "total_files should be non-negative"
            assert result["total_records"] >= 0, "total_records should be non-negative"

    def test_multiple_years_and_assets(self, historical_quotes):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = historical_quotes.extract(
                path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                destination_path=temp_dir,
                assets_list=["ações", "etf"],
                initial_year=2023,
                last_year=2024,
                output_filename="test_multi_years_assets",
                processing_mode="fast",
            )

            assert isinstance(result, dict), "Result should be a dictionary"
            assert "total_files" in result, "total_files key should exist"
            assert "total_records" in result, "total_records key should exist"
            assert isinstance(result["total_files"], int), (
                "total_files should be an integer"
            )
            assert isinstance(result["total_records"], int), (
                "total_records should be an integer"
            )
            assert result["total_files"] >= 0, "total_files should be non-negative"
            assert result["total_records"] >= 0, "total_records should be non-negative"
            assert result["total_files"] >= 0, "Multiple years should process files"

    def test_invalid_processing_mode(self, historical_quotes):
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(InvalidProcessingMode, match="Invalid processing_mode"):
                historical_quotes.extract(
                    path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                    destination_path=temp_dir,
                    assets_list=["ações"],
                    initial_year=2024,
                    last_year=2024,
                    processing_mode="invalid_mode",
                )

    def test_output_filename_without_extension(self, historical_quotes):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = historical_quotes.extract(
                path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                destination_path=temp_dir,
                assets_list=["ações"],
                initial_year=2024,
                last_year=2024,
                output_filename="test_no_ext",
                processing_mode="fast",
            )

            assert isinstance(result, dict), "Result should be a dictionary"
            assert "output_file" in result, "output_file key should exist"
            assert isinstance(result["output_file"], str), (
                "output_file should be a string"
            )

            if result["total_files"] > 0:
                assert result["output_file"].endswith(".parquet"), (
                    "Output file should end with .parquet"
                )
                output_path = Path(result["output_file"])
                assert output_path.exists(), (
                    f"Output file should exist at {output_path}"
                )
                assert output_path.stat().st_size > 0, "Output file should not be empty"

    def test_output_filename_with_extension(self, historical_quotes):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = historical_quotes.extract(
                path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                destination_path=temp_dir,
                assets_list=["ações"],
                initial_year=2024,
                last_year=2024,
                output_filename="test_with_ext.parquet",
                processing_mode="fast",
            )

            assert isinstance(result, dict), "Result should be a dictionary"
            assert "output_file" in result, "output_file key should exist"
            assert isinstance(result["output_file"], str), (
                "output_file should be a string"
            )

            if result["total_files"] > 0:
                assert result["output_file"].endswith("test_with_ext.parquet"), (
                    "Output file should preserve .parquet extension"
                )
                output_path = Path(result["output_file"])
                assert output_path.exists(), (
                    f"Output file should exist at {output_path}"
                )
                assert output_path.stat().st_size > 0, "Output file should not be empty"
