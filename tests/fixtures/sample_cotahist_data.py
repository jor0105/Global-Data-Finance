"""Sample COTAHIST data for testing.

This module provides realistic COTAHIST line data following the official
B3 layout specification for testing purposes.
"""


class SampleCotahistData:
    """Sample COTAHIST data generator for testing."""

    @staticmethod
    def get_header() -> str:
        """Get COTAHIST header line (type 00)."""
        return "00COTAHIST.2023BOVESPA " + " " * 214

    @staticmethod
    def get_trailer(total_records: int = 2) -> str:
        """Get COTAHIST trailer line (type 99).

        Args:
            total_records: Number of records (excluding header/trailer)
        """
        records_str = str(total_records).zfill(11)
        return f"99COTAHIST{records_str}" + " " * 222

    @staticmethod
    def get_stock_line(
        ticker: str = "PETR4",
        date_str: str = "20231201",
        close_price: int = 3525,  # 35.25 in V99 format
        tpmerc: str = "010",  # Vista (cash market)
    ) -> str:
        """Generate a stock quote line (type 01).

        Args:
            ticker: Stock ticker (up to 12 chars)
            date_str: Date in YYYYMMDD format
            close_price: Closing price in (11)V99 format (e.g., 3525 = 35.25)
            tpmerc: Market type code (010=Vista, 020=Fracionário)

        Returns:
            245-byte COTAHIST line
        """
        # Build line according to COTAHIST layout
        line = (
            "01"  # Record type (pos 1-2)
            + date_str  # Trading date (pos 3-10)
            + "02"  # BDI code (pos 11-12)
            + ticker.ljust(12)  # Ticker (pos 13-24)
            + tpmerc  # Market type (pos 25-27)
            + "PETROBRAS".ljust(12)  # Short name (pos 28-39)
            + "PN        "  # Specification (pos 40-49)
            + " " * 3  # Prazo merc (pos 50-52)
            + "BRL"  # Currency (pos 53-55)
            + " "  # Reserved (pos 56)
            + str(close_price).zfill(13)  # Open price (pos 57-69)
            + str(close_price + 100).zfill(13)  # Max price (pos 70-82)
            + str(close_price - 100).zfill(13)  # Min price (pos 83-95)
            + str(close_price).zfill(13)  # Avg price (pos 96-108)
            + str(close_price).zfill(13)  # Close price (pos 109-121)
            + str(close_price).zfill(13)  # Best buy (pos 122-134)
            + str(close_price).zfill(13)  # Best sell (pos 135-147)
            + "00100"  # Total trades (pos 148-152)
            + "000000000001000000"  # Total quantity (pos 153-170)
            + "000000000035250000"  # Total volume (pos 171-188)
            + "000000000035250000"  # Preexe (pos 189-201)
            + " " * 1  # Reserved (pos 202)
            + "00000000"  # Expiration date (pos 203-210)
            + "0000001"  # Fatcot (pos 211-217)
            + "000000000003525"  # Preexe (pos 218-230)
            + "BRPETRACNPR6"  # ISIN (pos 231-242)
            + "010"  # Distribution number (pos 243-245)
        )
        return line

    @staticmethod
    def get_etf_line(
        ticker: str = "BOVA11",
        date_str: str = "20231201",
        close_price: int = 12050,  # 120.50 in V99 format
    ) -> str:
        """Generate an ETF quote line.

        Args:
            ticker: ETF ticker
            date_str: Date in YYYYMMDD format
            close_price: Closing price in (11)V99 format

        Returns:
            245-byte COTAHIST line
        """
        return SampleCotahistData.get_stock_line(
            ticker=ticker,
            date_str=date_str,
            close_price=close_price,
            tpmerc="010",  # ETFs also use vista market
        )

    @staticmethod
    def get_option_line(
        ticker: str = "PETRM240",
        date_str: str = "20231201",
        close_price: int = 150,  # 1.50 in V99 format
    ) -> str:
        """Generate an options quote line.

        Args:
            ticker: Option ticker
            date_str: Date in YYYYMMDD format
            close_price: Closing price in (11)V99 format

        Returns:
            245-byte COTAHIST line
        """
        return SampleCotahistData.get_stock_line(
            ticker=ticker,
            date_str=date_str,
            close_price=close_price,
            tpmerc="070",  # Options market
        )

    @staticmethod
    def get_full_sample_file() -> str:
        """Get a complete COTAHIST file content with multiple records.

        Returns:
            Multi-line string with header, data records, and trailer
        """
        lines = [
            SampleCotahistData.get_header(),
            SampleCotahistData.get_stock_line("PETR4", "20231201", 3525),
            SampleCotahistData.get_stock_line("VALE3", "20231201", 6280),
            SampleCotahistData.get_etf_line("BOVA11", "20231201", 12050),
            SampleCotahistData.get_option_line("PETRM240", "20231201", 150),
            SampleCotahistData.get_trailer(4),
        ]
        return "\n".join(lines)

    @staticmethod
    def get_minimal_sample_file() -> str:
        """Get a minimal COTAHIST file with just one record.

        Returns:
            Multi-line string with header, one data record, and trailer
        """
        lines = [
            SampleCotahistData.get_header(),
            SampleCotahistData.get_stock_line("PETR4", "20231201", 3525),
            SampleCotahistData.get_trailer(1),
        ]
        return "\n".join(lines)
