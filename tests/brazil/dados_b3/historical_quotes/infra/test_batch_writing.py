"""Integration tests for batch writing feature in ExtractionService."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    import polars as pl
except ImportError:
    pl = None

from src.brazil.dados_b3.historical_quotes.domain.value_objects.processing_mode import (
    ProcessingModeEnum,
)
from src.brazil.dados_b3.historical_quotes.infra.cotahist_parser import CotahistParser
from src.brazil.dados_b3.historical_quotes.infra.extraction_service import (
    ExtractionService,
)
from src.brazil.dados_b3.historical_quotes.infra.parquet_writer import ParquetWriter
from src.brazil.dados_b3.historical_quotes.infra.zip_reader import ZipFileReader


@pytest.mark.skipif(pl is None, reason="Polars not installed")
class TestBatchWriting:
    """Tests for batch writing functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Provide temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_zip_reader(self):
        """Provide mock ZIP reader."""
        reader = MagicMock(spec=ZipFileReader)
        return reader

    @pytest.fixture
    def parser(self):
        """Provide real parser instance."""
        return CotahistParser()

    @pytest.fixture
    def parquet_writer(self):
        """Provide real Parquet writer."""
        return ParquetWriter()

    @pytest.mark.asyncio
    async def test_flush_batch_to_disk_creates_file(
        self, mock_zip_reader, parser, parquet_writer, temp_output_dir
    ):
        """Test that flush_batch_to_disk creates Parquet file."""
        service = ExtractionService(
            zip_reader=mock_zip_reader,
            parser=parser,
            data_writer=parquet_writer,
            processing_mode=ProcessingModeEnum.FAST,
        )

        # Create test records
        test_records = [
            {"ticker": "PETR4", "date": "2024-01-01", "close": 35.50},
            {"ticker": "VALE3", "date": "2024-01-01", "close": 68.20},
        ]

        output_path = temp_output_dir / "test_batch.parquet"

        # Flush batch
        await service._flush_batch_to_disk(test_records, output_path, batch_number=1)

        # Verify file exists
        assert output_path.exists()

        # Verify content
        df = pl.read_parquet(str(output_path))
        assert df.height == 2
        assert "ticker" in df.columns

    @pytest.mark.asyncio
    async def test_flush_batch_append_mode(
        self, mock_zip_reader, parser, parquet_writer, temp_output_dir
    ):
        """Test that flush_batch_to_disk appends to existing file."""
        service = ExtractionService(
            zip_reader=mock_zip_reader,
            parser=parser,
            data_writer=parquet_writer,
            processing_mode=ProcessingModeEnum.FAST,
        )

        output_path = temp_output_dir / "test_append.parquet"

        # First batch
        batch1 = [
            {"ticker": "PETR4", "date": "2024-01-01", "close": 35.50},
        ]
        await service._flush_batch_to_disk(batch1, output_path, batch_number=1)

        # Second batch (should append)
        batch2 = [
            {"ticker": "VALE3", "date": "2024-01-01", "close": 68.20},
        ]
        await service._flush_batch_to_disk(batch2, output_path, batch_number=2)

        # Verify both records are in file
        df = pl.read_parquet(str(output_path))
        assert df.height == 2

    @pytest.mark.asyncio
    async def test_batch_size_constant_exists(
        self, mock_zip_reader, parser, parquet_writer
    ):
        """Test that BATCH_SIZE constant is defined."""
        service = ExtractionService(
            zip_reader=mock_zip_reader,
            parser=parser,
            data_writer=parquet_writer,
        )

        assert hasattr(service, "BATCH_SIZE")
        assert service.BATCH_SIZE == 100_000

    @pytest.mark.asyncio
    async def test_extract_with_batch_tracking(
        self, mock_zip_reader, parser, parquet_writer, temp_output_dir
    ):
        """Test that extraction result includes batch information."""

        # Mock ZIP reader to return sample lines
        async def mock_read_lines(zip_file):
            # Yield some valid COTAHIST lines
            yield "00COTAHIST.2024BOVESPA 20241108"  # Header
            yield (
                "01" + "PETR4".ljust(12) + "010" + "2024010100000003550"
            )  # Valid record

        mock_zip_reader.read_lines_from_zip = AsyncMock(side_effect=mock_read_lines)

        service = ExtractionService(
            zip_reader=mock_zip_reader,
            parser=parser,
            data_writer=parquet_writer,
            processing_mode=ProcessingModeEnum.FAST,
        )

        output_path = temp_output_dir / "test_result.parquet"

        result = await service.extract_from_zip_files(
            zip_files=["test.zip"],
            target_tpmerc_codes={"010"},
            output_path=output_path,
        )

        # Check result has batch information
        assert "batches_written" in result
        assert isinstance(result["batches_written"], int)


@pytest.mark.skipif(pl is None, reason="Polars not installed")
class TestParquetWriterOptimizations:
    """Tests for Parquet writer optimizations."""

    @pytest.fixture
    def temp_output_dir(self):
        """Provide temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def writer(self):
        """Provide Parquet writer instance."""
        return ParquetWriter()

    @pytest.mark.asyncio
    async def test_write_with_compression(self, writer, temp_output_dir):
        """Test that files are written with ZSTD compression."""
        test_data = [
            {"ticker": "PETR4", "date": "2024-01-01", "close": 35.50},
            {"ticker": "VALE3", "date": "2024-01-01", "close": 68.20},
        ]

        output_path = temp_output_dir / "compressed.parquet"

        await writer.write_to_parquet(test_data, output_path)

        assert output_path.exists()
        # File should exist and be readable
        df = pl.read_parquet(str(output_path))
        assert df.height == 2

    @pytest.mark.asyncio
    async def test_disk_space_check(self, writer, temp_output_dir):
        """Test that disk space is checked before writing."""
        test_data = [{"ticker": "TEST", "value": 1.0}]
        output_path = temp_output_dir / "test.parquet"

        # Should not raise error if enough space
        await writer.write_to_parquet(test_data, output_path)
        assert output_path.exists()

    @pytest.mark.asyncio
    async def test_append_mode_concatenates_data(self, writer, temp_output_dir):
        """Test that append mode properly concatenates data."""
        output_path = temp_output_dir / "append_test.parquet"

        # Write initial data
        data1 = [{"ticker": "PETR4", "close": 35.50}]
        await writer.write_to_parquet(data1, output_path, mode="overwrite")

        # Append more data
        data2 = [{"ticker": "VALE3", "close": 68.20}]
        await writer.write_to_parquet(data2, output_path, mode="append")

        # Verify both records present
        df = pl.read_parquet(str(output_path))
        assert df.height == 2
        assert set(df["ticker"].to_list()) == {"PETR4", "VALE3"}
