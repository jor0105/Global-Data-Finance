import asyncio
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set

from ..application.interfaces import ICotahistParser, IDataWriter, IZipReader


class ProcessingMode(str, Enum):
    """Processing mode configuration."""

    FAST = "fast"
    SLOW = "slow"


class ExtractionService:
    """Service for extracting data from COTAHIST ZIP files asynchronously.

    This service controls resource consumption through processing modes:
    - FAST: High concurrency, more CPU/RAM usage
    - SLOW: Low concurrency, minimal CPU/RAM usage
    """

    def __init__(
        self,
        zip_reader: IZipReader,
        parser: ICotahistParser,
        data_writer: IDataWriter,
        processing_mode: ProcessingMode = ProcessingMode.FAST,
    ):
        """Initialize extraction service with dependencies.

        Args:
            zip_reader: Service for reading ZIP files
            parser: Parser for COTAHIST format
            data_writer: Writer for output data
            processing_mode: Resource consumption strategy
        """
        self.zip_reader = zip_reader
        self.parser = parser
        self.data_writer = data_writer
        self.processing_mode = processing_mode

        # Configure concurrency based on mode
        if processing_mode == ProcessingMode.FAST:
            self.max_concurrent_files = 10  # Process up to 10 files concurrently
        else:  # SLOW
            self.max_concurrent_files = 2  # Process only 2 files at a time

    async def extract_from_zip_files(
        self, zip_files: List[str], target_tpmerc_codes: Set[str], output_path: Path
    ) -> Dict[str, Any]:
        """Extract data from multiple ZIP files asynchronously.

        Args:
            zip_files: List of paths to ZIP files
            target_tpmerc_codes: Set of TPMERC codes to filter (e.g., {'010', '020'})
            output_path: Path where to save the extracted data

        Returns:
            Dictionary with extraction statistics
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_files)

        async def process_with_semaphore(zip_file: str):
            async with semaphore:
                return await self._process_single_zip(zip_file, target_tpmerc_codes)

        # Process all files with controlled concurrency
        results = await asyncio.gather(
            *[process_with_semaphore(zip_file) for zip_file in zip_files],
            return_exceptions=True,
        )

        # Consolidate all results
        all_records: List[Dict[str, Any]] = []
        success_count = 0
        error_count = 0
        errors = {}

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_count += 1
                errors[zip_files[i]] = str(result)
            elif isinstance(result, list):
                success_count += 1
                all_records.extend(result)

        # Write all data to Parquet
        if all_records:
            await self.data_writer.write_to_parquet(
                data=all_records, output_path=output_path
            )

        return {
            "total_files": len(zip_files),
            "success_count": success_count,
            "error_count": error_count,
            "total_records": len(all_records),
            "errors": errors,
            "output_file": str(output_path),
        }

    async def _process_single_zip(
        self, zip_file: str, target_tpmerc_codes: Set[str]
    ) -> List[Dict[str, Any]]:
        """Process a single ZIP file and extract matching records.

        Args:
            zip_file: Path to ZIP file
            target_tpmerc_codes: Set of TPMERC codes to filter

        Returns:
            List of parsed records
        """
        records = []

        # Stream lines from ZIP file
        async for line in await self.zip_reader.read_lines_from_zip(zip_file):
            # Parse line (returns None if not matching filter)
            parsed = self.parser.parse_line(line, target_tpmerc_codes)

            if parsed:
                records.append(parsed)

        return records
