"""Orchestration layer for B3 historical_quotes extraction.

Consolidates use cases from prior `application/use_cases/`. Use case classes
are preserved here (rather than converted to bare functions) to keep the
existing test contract intact — tests call `<Class>.execute(...)` patterns and
are migrated only by import path per Phase 1 plan.
"""

import asyncio
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ....macro_exceptions import InvalidDestinationPathError
from .assets import AvailableAssetsServiceB3
from .cotahist_parser import CotahistParserB3
from .errors import InvalidOutputFilename
from .extraction_service import ExtractionServiceB3
from .filesystem import FileSystemServiceB3
from .models import DocsToExtractorB3
from .parquet_writer import ParquetWriterB3
from .processing import ExtractionConfigServiceB3, ProcessingModeEnumB3
from .years import YearValidationServiceB3
from .zip_reader import ZipFileReaderB3


class GetAvailableAssetsUseCaseB3:
    @staticmethod
    def execute() -> list[str]:
        """Get the list of available assets for historical quotes data."""
        return AvailableAssetsServiceB3.get_available_assets()


class GetAvailableYearsUseCaseB3:
    def get_current_year(self) -> int:
        """Get the current available year for historical quotes data."""
        return YearValidationServiceB3.get_current_year()

    def get_minimal_year(self) -> int:
        """Get the minimal available year for historical quotes data."""
        return YearValidationServiceB3.get_min_year()


class CreateRangeYearsUseCaseB3:
    """Use case for creating and validating a range of years."""

    @staticmethod
    def execute(initial_year: int, last_year: int) -> range:
        """Create and validate a range of years for data extraction."""
        year_range = YearValidationServiceB3.validate_and_create_year_range(
            initial_year, last_year
        )
        return year_range.to_range()


class CreateSetAssetsUseCaseB3:
    @staticmethod
    def execute(assets_list: list[str]) -> set[str]:
        """Create a set of available assets using AvailableAssetsServiceB3."""
        return AvailableAssetsServiceB3.validate_and_create_asset_set(
            assets_list
        )


class CreateSetToDownloadUseCaseB3:
    """Use case for finding ZIP files in a directory based on year range."""

    @staticmethod
    def execute(range_years: range, path: str) -> set[str]:
        """Find all document files in the given path for the year range."""
        if not isinstance(path, str):
            raise TypeError(
                f'path_of_docs must be a string, got {type(path).__name__}'
            )

        if not path or path.isspace():
            raise InvalidDestinationPathError(
                'path_of_docs cannot be empty or whitespace'
            )

        file_system = FileSystemServiceB3()
        validated_path = file_system.validate_directory_path(path)
        return file_system.find_files_by_years(validated_path, range_years)


class VerifyDestinationPathsUseCaseB3:
    @staticmethod
    def execute(destination_path: str) -> Path:
        return FileSystemServiceB3().prepare_destination_path(destination_path)


class ValidateExtractionConfigUseCaseB3:
    """Use case for validating extraction configuration."""

    @staticmethod
    def execute(processing_mode: str, output_filename: str) -> tuple[str, str]:
        """Validate processing mode and output filename."""
        valid_mode = ExtractionConfigServiceB3.validate_processing_mode(
            processing_mode
        )
        valid_filename = ExtractionConfigServiceB3.validate_output_filename(
            output_filename
        )
        return valid_mode, valid_filename


class CreateDocsToExtractUseCaseB3:
    """Use case for creating a DocsToExtractorB3 entity with validated parameters."""

    def __init__(
        self,
        path_of_docs: str,
        assets_list: list[str],
        initial_year: int,
        last_year: int,
        destination_path: str | None = None,
    ):
        if not isinstance(path_of_docs, str):
            raise TypeError(
                f'path_of_docs must be a string, got {type(path_of_docs).__name__}'
            )

        if destination_path is not None and not isinstance(
            destination_path, str
        ):
            raise TypeError(
                f'destination_path must be a string, got {type(destination_path).__name__}'
            )

        self.path_of_docs = path_of_docs
        self.assets_list = assets_list
        self.initial_year = initial_year
        self.last_year = last_year
        self.destination_path = (
            destination_path if destination_path else path_of_docs
        )

    def execute(self) -> DocsToExtractorB3:
        """Execute the use case to create a validated DocsToExtractorB3 entity."""
        set_assets = CreateSetAssetsUseCaseB3.execute(self.assets_list)

        range_years = CreateRangeYearsUseCaseB3.execute(
            self.initial_year, self.last_year
        )

        normalized_destination = VerifyDestinationPathsUseCaseB3().execute(
            self.destination_path
        )
        destination_path = (
            str(normalized_destination)
            if normalized_destination is not None
            else self.destination_path
        )
        documents_to_download = CreateSetToDownloadUseCaseB3.execute(
            range_years, self.path_of_docs
        )

        return DocsToExtractorB3(
            path_of_docs=self.path_of_docs,
            set_assets=set_assets,
            range_years=range_years,
            destination_path=destination_path,
            documents_to_download=documents_to_download,
        )


class ExtractHistoricalQuotesUseCaseB3:
    """Main orchestrator for extracting historical quotes from COTAHIST files.

    Holds reusable collaborators (zip_reader, parser, writer) across calls per
    D3 — this is the one use case kept as a class because it has real state.
    """

    def __init__(self):
        self.zip_reader = ZipFileReaderB3()
        self.parser = CotahistParserB3()
        self.data_writer = ParquetWriterB3()

    async def execute(
        self,
        docs_to_extract: DocsToExtractorB3,
        processing_mode: str = 'fast',
        output_filename: str = 'cotahist_extracted.parquet',
    ) -> dict[str, Any]:
        """Execute the extraction process."""
        # D4: factory removed — construct ExtractionServiceB3 directly. Invalid
        # processing_mode is already validated by
        # ValidateExtractionConfigUseCaseB3 in the facade, which raises
        # InvalidProcessingMode. The enum cast here is the final coercion.
        mode = ProcessingModeEnumB3(processing_mode.lower())
        extraction_service = ExtractionServiceB3(
            zip_reader=self.zip_reader,
            parser=self.parser,
            data_writer=self.data_writer,
            processing_mode=mode,
        )

        try:
            target_tpmerc_codes = (
                AvailableAssetsServiceB3.get_tpmerc_codes_for_assets(
                    docs_to_extract.set_assets
                )
            )

            zip_files: set[str] = docs_to_extract.documents_to_download

            if not zip_files:
                return {
                    'total_files': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'total_records': 0,
                    'errors': {},
                    'output_file': '',
                }

            output_path = (
                Path(docs_to_extract.destination_path) / output_filename
            )

            destination_resolved = Path(
                docs_to_extract.destination_path
            ).resolve()
            output_resolved = output_path.resolve()
            if not output_resolved.is_relative_to(destination_resolved):
                raise InvalidOutputFilename(
                    f'output path escapes destination: '
                    f'{output_resolved} not under {destination_resolved}'
                )

            result = await extraction_service.extract_from_zip_files(
                zip_files=zip_files,
                target_tpmerc_codes=target_tpmerc_codes,
                output_path=output_path,
            )
            return result
        finally:
            close_service = cast(Callable[[], Any], extraction_service.close)
            close_result = close_service()
            if inspect.isawaitable(close_result):
                await close_result

    def execute_sync(
        self,
        docs_to_extract: DocsToExtractorB3,
        processing_mode: str = 'fast',
        output_filename: str = 'cotahist_extracted.parquet',
    ) -> dict[str, Any]:
        """Synchronous wrapper for execute()."""
        return asyncio.run(
            self.execute(docs_to_extract, processing_mode, output_filename)
        )
