import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from ...domain import AvailableAssets, DocsToExtractor
from ...infra import (
    CotahistParser,
    ExtractionService,
    FileSystemService,
    ParquetWriter,
    ProcessingMode,
    ZipFileReader,
)


class ExtractHistoricalQuotesUseCase:
    """Main use case for extracting historical quotes from COTAHIST files.

    This orchestrates the entire flow:
    1. Validation of inputs
    2. Reading ZIP files
    3. Parsing COTAHIST format
    4. Filtering by asset classes
    5. Saving to Parquet
    """

    def __init__(
        self,
        file_system_service: Optional[FileSystemService] = None,
        zip_reader: Optional[ZipFileReader] = None,
        parser: Optional[CotahistParser] = None,
        data_writer: Optional[ParquetWriter] = None,
    ):
        """Initialize use case with dependencies (allows dependency injection).

        Args:
            file_system_service: Service for file system operations
            zip_reader: Service for reading ZIP files
            parser: Parser for COTAHIST format
            data_writer: Writer for output data
        """
        self.file_system_service = file_system_service or FileSystemService()
        self.zip_reader = zip_reader or ZipFileReader()
        self.parser = parser or CotahistParser()
        self.data_writer = data_writer or ParquetWriter()

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
            Dictionary with extraction results and statistics
        """
        # Convert processing mode string to enum
        mode = (
            ProcessingMode.FAST
            if processing_mode.lower() == "fast"
            else ProcessingMode.SLOW
        )

        # Create extraction service with configured mode
        extraction_service = ExtractionService(
            zip_reader=self.zip_reader,  # type: ignore
            parser=self.parser,  # type: ignore
            data_writer=self.data_writer,  # type: ignore
            processing_mode=mode,
        )

        # Map user-friendly asset classes to TPMERC codes
        target_tpmerc_codes = AvailableAssets.get_target_tmerc_codes(
            docs_to_extract.set_assets
        )

        # Convert set of document paths to list
        zip_files = list(docs_to_extract.set_documents_to_download)

        if not zip_files:
            return {
                "success": False,
                "message": "No ZIP files found for the specified years",
                "total_files": 0,
                "success_count": 0,
                "error_count": 0,
                "total_records": 0,
            }

        # Define output path
        output_path = Path(docs_to_extract.destination_path) / output_filename

        # Execute extraction
        result = await extraction_service.extract_from_zip_files(
            zip_files=zip_files,
            target_tpmerc_codes=target_tpmerc_codes,
            output_path=output_path,
        )

        result["success"] = result["error_count"] == 0
        result["message"] = self._generate_message(result)

        return result

    def _generate_message(self, result: Dict[str, Any]) -> str:
        """Generate a user-friendly message from extraction results."""
        if result["error_count"] == 0:
            return (
                f"Successfully extracted {result['total_records']} records "
                f"from {result['success_count']} files. "
                f"Saved to: {result['output_file']}"
            )
        else:
            return (
                f"Extraction completed with errors. "
                f"Processed {result['success_count']}/{result['total_files']} files. "
                f"Extracted {result['total_records']} records. "
                f"Errors: {result['error_count']}"
            )

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
