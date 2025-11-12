import asyncio
from pathlib import Path
from typing import Any, Dict

from ...domain import AvailableAssetsService, DocsToExtractor
from ...infra import CotahistParser, ParquetWriter, ZipFileReader


class ExtractHistoricalQuotesUseCase:
    """Main use case for extracting historical quotes from COTAHIST files.

    This orchestrates the entire extraction flow by:
    1. Creating the appropriate extraction service (fast/slow mode)
    2. Mapping user-friendly asset names to internal TPMERC codes
    3. Delegating extraction to the service layer
    4. Returning raw results (without presentation logic)

    Note: Message generation and success determination are handled
    by the presentation layer (HistoricalQuotesResultFormatter).
    This follows Single Responsibility Principle.
    """

    def __init__(self):
        self.zip_reader = ZipFileReader()
        self.parser = CotahistParser()
        self.data_writer = ParquetWriter()

    async def execute(
        self,
        docs_to_extract: DocsToExtractor,
        processing_mode: str = "fast",
        output_filename: str = "cotahist_extracted.parquet",
    ) -> Dict[str, Any]:
        """Execute the extraction process.

        Args:
            docs_to_extract: Entity containing validated extraction parameters
            processing_mode: 'fast' or 'slow' for resource management
            output_filename: Name of the output Parquet file

        Returns:
            Dictionary with raw extraction results (without success/message fields)
        """
        from ...infra.extraction_service_factory import ExtractionServiceFactory

        # Create extraction service based on processing mode
        extraction_service = ExtractionServiceFactory.create(
            zip_reader=self.zip_reader,
            parser=self.parser,
            data_writer=self.data_writer,
            processing_mode=processing_mode,
        )

        # Map user-friendly asset classes to TPMERC codes
        target_tpmerc_codes = AvailableAssetsService.get_tpmerc_codes_for_assets(
            docs_to_extract.set_assets
        )

        # Convert set of document paths to list
        zip_files = list(docs_to_extract.set_documents_to_download)

        # Handle edge case: no ZIP files found
        if not zip_files:
            return {
                "total_files": 0,
                "success_count": 0,
                "error_count": 0,
                "total_records": 0,
                "errors": {},
                "output_file": "",
            }

        # Define output path
        output_path = Path(docs_to_extract.destination_path) / output_filename

        # Execute extraction and return raw results
        result = await extraction_service.extract_from_zip_files(
            zip_files=zip_files,
            target_tpmerc_codes=target_tpmerc_codes,
            output_path=output_path,
        )

        return result

    def execute_sync(
        self,
        docs_to_extract: DocsToExtractor,
        processing_mode: str = "fast",
        output_filename: str = "cotahist_extracted.parquet",
    ) -> Dict[str, Any]:
        """Synchronous wrapper for execute() method.

        This is a convenience method for users who don't want to deal with asyncio.

        Args:
            docs_to_extract: Entity containing validated extraction parameters
            processing_mode: 'fast' or 'slow' for resource management
            output_filename: Name of the output Parquet file

        Returns:
            Dictionary with extraction results and statistics
        """
        return asyncio.run(
            self.execute(docs_to_extract, processing_mode, output_filename)
        )
