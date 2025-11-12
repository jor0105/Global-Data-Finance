from ..domain import ProcessingModeEnum
from .cotahist_parser import CotahistParser
from .extraction_service import ExtractionService
from .parquet_writer import ParquetWriter
from .zip_reader import ZipFileReader


class ExtractionServiceFactory:
    """Factory for creating ExtractionService instances.

    Follows Factory Pattern to encapsulate the creation logic and
    configuration of ExtractionService based on processing mode.
    """

    @staticmethod
    def create(
        zip_reader: ZipFileReader,
        parser: CotahistParser,
        data_writer: ParquetWriter,
        processing_mode: str = "fast",
    ) -> ExtractionService:
        """Create an ExtractionService with the specified configuration.

        Args:
            zip_reader: ZIP file reader implementation
            parser: COTAHIST parser implementation
            data_writer: Parquet data writer implementation
            processing_mode: Processing strategy - "fast" or "slow"

        Returns:
            Configured ExtractionService instance

        Raises:
            ValueError: If processing_mode is invalid
        """
        # Convert string to enum
        try:
            mode = ProcessingModeEnum(processing_mode.lower())
        except ValueError:
            valid_modes = [m.value for m in ProcessingModeEnum]
            raise ValueError(
                f"Invalid processing_mode '{processing_mode}'. "
                f"Must be one of: {valid_modes}"
            )

        return ExtractionService(
            zip_reader=zip_reader,
            parser=parser,
            data_writer=data_writer,
            processing_mode=mode,
        )
