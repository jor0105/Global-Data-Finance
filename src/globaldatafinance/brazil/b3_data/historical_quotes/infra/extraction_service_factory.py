from ..domain import ProcessingModeEnumB3
from .cotahist_parser import CotahistParserB3
from .extraction_service import ExtractionServiceB3
from .parquet_writer import ParquetWriterB3
from .zip_reader import ZipFileReaderB3


class ExtractionServiceFactoryB3:
    """Factory for creating ExtractionServiceB3 instances.

    Follows Factory Pattern to encapsulate the creation logic and
    configuration of ExtractionServiceB3 based on processing mode.
    """

    @staticmethod
    def create(
        zip_reader: ZipFileReaderB3,
        parser: CotahistParserB3,
        data_writer: ParquetWriterB3,
        processing_mode: str = "fast",
    ) -> ExtractionServiceB3:
        """Create an ExtractionServiceB3 with the specified configuration.

        Args:
            zip_reader: ZIP file reader implementation
            parser: COTAHIST parser implementation
            data_writer: Parquet data writer implementation
            processing_mode: Processing strategy - "fast" or "slow"

        Returns:
            Configured ExtractionServiceB3 instance

        Raises:
            ValueError: If processing_mode is invalid
        """
        try:
            mode = ProcessingModeEnumB3(processing_mode.lower())
        except ValueError:
            valid_modes = [m.value for m in ProcessingModeEnumB3]
            raise ValueError(
                f"Invalid processing_mode '{processing_mode}'. "
                f"Must be one of: {valid_modes}"
            )

        return ExtractionServiceB3(
            zip_reader=zip_reader,
            parser=parser,
            data_writer=data_writer,
            processing_mode=mode,
        )
