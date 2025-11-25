from typing import Set

from ...infra import FileSystemServiceB3


class CreateSetToDownloadUseCaseB3:
    """Use case for finding ZIP files in a directory based on year range."""

    @staticmethod
    def execute(range_years: range, path: str) -> Set[str]:
        """Find all document files in the given path for the specified year range.

        Args:
            range_years: Range of years to search for
            path: Directory path containing the ZIP files

        Returns:
            Set of file paths matching the year criteria
        """
        file_system = FileSystemServiceB3()
        validated_path = file_system.validate_directory_path(path)
        return file_system.find_files_by_years(validated_path, range_years)
