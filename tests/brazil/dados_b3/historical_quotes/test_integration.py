"""
Integration test for Historical Quotes extraction module.

This test validates the entire flow without real file I/O.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.brazil.dados_b3.historical_quotes.domain import (
    AvailableAssets,
    DocsToExtractor,
)
from src.brazil.dados_b3.historical_quotes.infra import (
    CotahistParser,
    ExtractionService,
    ProcessingMode,
)


class TestAvailableAssets:
    """Test asset class mapping and validation."""

    def test_create_set_assets_valid(self):
        """Valid asset list should be converted to set."""
        assets = AvailableAssets.create_set_assets(["ações", "etf"])
        assert assets == {"ações", "etf"}

    def test_get_target_tmerc_codes(self):
        """Asset classes should map to correct TPMERC codes."""
        assets = {"ações", "etf"}
        codes = AvailableAssets.get_target_tmerc_codes(assets)
        assert codes == {"010", "020"}

    def test_get_target_tmerc_codes_options(self):
        """Options should map to correct codes."""
        assets = {"opções"}
        codes = AvailableAssets.get_target_tmerc_codes(assets)
        assert codes == {"070", "080"}


class TestDocsToExtractor:
    """Test DocsToExtractor entity."""

    def test_entity_creation(self):
        """Entity should be created with all required fields."""
        entity = DocsToExtractor(
            set_assets={"ações"},
            range_years=range(2023, 2025),
            path_of_docs="/path",
            destination_path="/output",
            set_documents_to_download={"/path/file1.zip"},
        )

        assert entity.set_assets == {"ações"}
        assert list(entity.range_years) == [2023, 2024]
        assert entity.path_of_docs == "/path"
        assert entity.destination_path == "/output"
        assert len(entity.set_documents_to_download) == 1


class TestCotahistParserIntegration:
    """Integration tests for COTAHIST parser."""

    @pytest.fixture
    def parser(self):
        return CotahistParser()

    @pytest.fixture
    def sample_quote_line(self):
        """Create a realistic COTAHIST line."""
        line = "01"  # TIPREG
        line += "20231215"  # DATA
        line += "02"  # CODBDI
        line += "PETR4       "  # CODNEG (12 chars)
        line += "010"  # TPMERC
        line += "PETROBRAS   "  # NOMRES (12 chars)
        line += "ON        "  # ESPECI (10 chars)
        line += " " * 7  # PRAZOT
        line += "BRL"  # MODREF
        line += "0000000003150"  # PREABE = 31.50
        line += "0000000003200"  # PREMAX = 32.00
        line += "0000000003100"  # PREMIN = 31.00
        line += "0000000003150"  # PREMED = 31.50
        line += "0000000003180"  # PREULT = 31.80
        line += "0000000003179"  # PREOFC = 31.79
        line += "0000000003181"  # PREOFV = 31.81
        line += "12345"  # TOTNEG
        line += "000000000100000000"  # QUATOT
        line += "000000003180000000"  # VOLTOT
        line += "0000000003180"  # PREEXE
        line += "1"  # INDOPC
        line += "00000000"  # DATVEN
        line += "0000001"  # FATCOT
        line += "0000000003185"  # PTOEXE
        line += "BRPETRACNOR9"  # CODISI (12 chars)
        line += "123"  # DISMES

        return line.ljust(245)

    def test_full_parsing_flow(self, parser, sample_quote_line):
        """Test complete parsing with filtering."""
        target_codes = {"010", "020"}
        result = parser.parse_line(sample_quote_line, target_codes)

        assert result is not None
        assert result["codneg"] == "PETR4"
        assert result["tpmerc"] == "010"
        assert result["data_pregao"] == date(2023, 12, 15)
        assert result["preult"] == Decimal("31.80")
        assert result["premax"] == Decimal("32.00")
        assert result["premin"] == Decimal("31.00")
        assert result["totneg"] == 12345
        assert result["codisi"] == "BRPETRACNOR9"

    def test_filtering_by_tpmerc(self, parser, sample_quote_line):
        """Lines with non-matching TPMERC should be filtered out."""
        target_codes = {"070", "080"}  # Options only
        result = parser.parse_line(sample_quote_line, target_codes)

        assert result is None


class TestExtractionServiceIntegration:
    """Integration tests for extraction service."""

    @pytest.mark.asyncio
    async def test_extraction_service_creation(self):
        """Service should be created with proper configuration."""
        mock_reader = Mock()
        mock_parser = Mock()
        mock_writer = Mock()

        service = ExtractionService(
            zip_reader=mock_reader,
            parser=mock_parser,
            data_writer=mock_writer,
            processing_mode=ProcessingMode.FAST,
        )

        assert service.max_concurrent_files == 10

    @pytest.mark.asyncio
    async def test_extraction_service_slow_mode(self):
        """Slow mode should limit concurrency."""
        mock_reader = Mock()
        mock_parser = Mock()
        mock_writer = Mock()

        service = ExtractionService(
            zip_reader=mock_reader,
            parser=mock_parser,
            data_writer=mock_writer,
            processing_mode=ProcessingMode.SLOW,
        )

        assert service.max_concurrent_files == 2


class TestEndToEndFlow:
    """End-to-end integration test."""

    def test_complete_flow_validation(self):
        """Validate that all components can work together."""
        # 1. Create asset set
        assets = AvailableAssets.create_set_assets(["ações", "etf"])
        assert assets == {"ações", "etf"}

        # 2. Map to TPMERC codes
        codes = AvailableAssets.get_target_tmerc_codes(assets)
        assert codes == {"010", "020"}

        # 3. Create entity
        docs = DocsToExtractor(
            set_assets=assets,
            range_years=range(2023, 2025),
            path_of_docs="/test",
            destination_path="/output",
            set_documents_to_download={"/test/COTAHIST.2023.ZIP"},
        )

        assert docs.set_assets == assets
        assert list(docs.range_years) == [2023, 2024]

        # 4. Verify parser can handle the codes
        parser = CotahistParser()
        line = "01202312150210PETR4       010" + " " * 213
        result = parser.parse_line(line, codes)

        assert result is not None
        assert result["tpmerc"] == "010"
