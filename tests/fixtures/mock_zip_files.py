"""Mock ZIP file utilities for testing."""

from pathlib import Path
from typing import Union
from zipfile import ZipFile

from .sample_cotahist_data import SampleCotahistData


class MockZipFiles:
    """Utilities for creating mock COTAHIST ZIP files for testing."""

    @staticmethod
    def create_zip_with_content(
        zip_path: Union[str, Path],
        txt_filename: str,
        content: str,
    ) -> Path:
        """Create a ZIP file with specified content.

        Args:
            zip_path: Path where to create the ZIP file
            txt_filename: Name of the text file inside the ZIP
            content: Content to write in the text file

        Returns:
            Path to the created ZIP file
        """
        zip_path = Path(zip_path)
        with ZipFile(zip_path, "w") as zf:
            zf.writestr(txt_filename, content)
        return zip_path

    @staticmethod
    def create_cotahist_zip(
        directory: Path,
        year: int,
        content: str | None = None,
    ) -> Path:
        """Create a mock COTAHIST ZIP file following B3 naming convention.

        Args:
            directory: Directory where to create the ZIP
            year: Year for the COTAHIST file
            content: Optional content; if None, uses full sample data

        Returns:
            Path to the created ZIP file
        """
        if content is None:
            content = SampleCotahistData.get_full_sample_file()

        zip_filename = f"COTAHIST_A{year}.ZIP"
        txt_filename = f"COTAHIST_A{year}.TXT"
        zip_path = directory / zip_filename

        return MockZipFiles.create_zip_with_content(
            zip_path=zip_path,
            txt_filename=txt_filename,
            content=content,
        )

    @staticmethod
    def create_minimal_cotahist_zip(
        directory: Path,
        year: int,
    ) -> Path:
        """Create a minimal COTAHIST ZIP file with just one record.

        Args:
            directory: Directory where to create the ZIP
            year: Year for the COTAHIST file

        Returns:
            Path to the created ZIP file
        """
        content = SampleCotahistData.get_minimal_sample_file()
        return MockZipFiles.create_cotahist_zip(directory, year, content)

    @staticmethod
    def create_empty_cotahist_zip(
        directory: Path,
        year: int,
    ) -> Path:
        """Create an empty COTAHIST ZIP file (only header and trailer).

        Args:
            directory: Directory where to create the ZIP
            year: Year for the COTAHIST file

        Returns:
            Path to the created ZIP file
        """
        content = "\n".join(
            [
                SampleCotahistData.get_header(),
                SampleCotahistData.get_trailer(0),
            ]
        )
        return MockZipFiles.create_cotahist_zip(directory, year, content)

    @staticmethod
    def create_multiple_cotahist_zips(
        directory: Path,
        start_year: int,
        end_year: int,
    ) -> list[Path]:
        """Create multiple COTAHIST ZIP files for a year range.

        Args:
            directory: Directory where to create the ZIPs
            start_year: First year (inclusive)
            end_year: Last year (inclusive)

        Returns:
            List of paths to created ZIP files
        """
        zip_paths = []
        for year in range(start_year, end_year + 1):
            zip_path = MockZipFiles.create_cotahist_zip(directory, year)
            zip_paths.append(zip_path)
        return zip_paths
