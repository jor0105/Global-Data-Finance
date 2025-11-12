"""Simple pytest tests for fast mode extraction."""

import tempfile
from pathlib import Path

import pytest

from src.presentation import HistoricalQuotes


class TestFastModeExtraction:
    """Tests for fast mode extraction functionality."""

    @pytest.fixture
    def historical_quotes(self):
        """Fixture to create HistoricalQuotes instance."""
        return HistoricalQuotes()

    def test_initialization(self, historical_quotes):
        """Test that HistoricalQuotes can be initialized."""
        assert historical_quotes is not None

    def test_get_available_assets(self, historical_quotes):
        """Test that available assets can be retrieved."""
        assets = historical_quotes.get_available_assets()
        assert isinstance(assets, list)
        assert len(assets) > 0
        assert "ações" in assets

    def test_get_available_years(self, historical_quotes):
        """Test that available years can be retrieved."""
        years = historical_quotes.get_available_years()
        assert "minimal_year" in years
        assert "current_year" in years
        assert years["minimal_year"] == 1986
        assert years["current_year"] >= 2024

    def test_fast_mode_extraction(self, historical_quotes):
        """Test extraction with fast processing mode."""
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

            # Verify result structure
            assert "total_files" in result
            assert "success_count" in result
            assert "error_count" in result
            assert "total_records" in result
            assert "output_file" in result

            # Verify extraction worked (if files exist)
            if result["total_files"] > 0:
                assert result["success_count"] > 0
                assert result["total_records"] > 0

                output_file = Path(result["output_file"])
                assert output_file.exists()
                assert output_file.suffix == ".parquet"

    def test_slow_mode_extraction(self, historical_quotes):
        """Test extraction with slow processing mode."""
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

            # Verify result structure
            assert "total_files" in result
            assert "success_count" in result
            assert "error_count" in result
            assert "total_records" in result

            # Verify extraction worked (if files exist)
            if result["total_files"] > 0:
                assert result["success_count"] > 0
                assert result["total_records"] > 0

    def test_multiple_assets(self, historical_quotes):
        """Test extraction with multiple asset types."""
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

            assert "total_files" in result
            assert "total_records" in result

    def test_invalid_processing_mode(self, historical_quotes):
        """Test that invalid processing mode raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Invalid processing_mode"):
                historical_quotes.extract(
                    path_of_docs="/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST",
                    destination_path=temp_dir,
                    assets_list=["ações"],
                    initial_year=2024,
                    last_year=2024,
                    processing_mode="invalid_mode",
                )

    def test_output_filename_without_extension(self, historical_quotes):
        """Test that .parquet extension is added automatically."""
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

            if result["total_files"] > 0:
                assert result["output_file"].endswith(".parquet")

    def test_output_filename_with_extension(self, historical_quotes):
        """Test that existing .parquet extension is preserved."""
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

            if result["total_files"] > 0:
                assert result["output_file"].endswith("test_with_ext.parquet")
