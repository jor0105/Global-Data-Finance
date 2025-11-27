import os
from pathlib import Path
from typing import Dict, Set

from ......core import get_logger
from ......macro_exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
    SecurityError,
)
from ...domain import AvailableYearsCVM
from ...exceptions import EmptyDocumentListError

logger = get_logger(__name__)


class VerifyPathsUseCasesCVM:
    def __init__(
        self,
        destination_path: str,
        new_set_docs: Set[str],
        range_years: range,
    ):
        self.destination_path = destination_path
        self.new_set_docs = new_set_docs
        self.range_years = range_years
        self.__available_years = AvailableYearsCVM()

        if not new_set_docs:
            raise EmptyDocumentListError()

        logger.debug(
            f'VerifyPathsUseCasesCVM created: '
            f'path={self.destination_path}, '
            f'docs={self.new_set_docs}'
        )

    def execute(self) -> Dict[str, Dict[int, str]]:
        """Create and verify directory structure for documents and years.

        Returns:
            Dictionary with structure: {doc: {year: path}}
        """
        docs_paths: Dict[str, Dict[int, str]] = {}
        for doc in self.new_set_docs:
            doc_path = str(Path(self.destination_path) / doc)
            validated_doc_path = self.__validate_and_create_paths(doc_path)

            docs_paths[doc] = {}
            for year in self.range_years:
                is_valid = self.__is_valid_year_for_doc(doc, year)
                if not is_valid:
                    logger.debug(
                        f'Skipping folder for doc={doc}, year={year} (invalid year for this document)'
                    )
                    continue
                year_path = str(Path(validated_doc_path) / str(year))
                validated_year_path = self.__validate_and_create_paths(
                    year_path
                )
                docs_paths[doc][year] = validated_year_path

        logger.info(
            f'Directory structure created successfully. '
            f'Documents: {len(docs_paths)}, '
            f'Years per document: {[len(years) for years in docs_paths.values()]}'
        )

        print(
            'Installation folders checked/created. Starting installations...'
        )

        return docs_paths

    def __is_valid_year_for_doc(self, doc: str, year: int) -> bool:
        doc_upper = doc.upper()
        min_itr = self.__available_years.get_minimal_itr_year()
        min_cgvn_vlmo = self.__available_years.get_minimal_cgvn_vlmo_year()
        min_general = self.__available_years.get_minimal_general_year()

        if doc_upper == 'ITR':
            return year >= min_itr

        if doc_upper in {'VLMO', 'CGVN'}:
            return year >= min_cgvn_vlmo

        return year >= min_general

    @staticmethod
    def __validate_path_security(path: Path) -> None:
        """Validate path security to prevent path traversal attacks.

        This prevents path traversal attacks where malicious paths like
        '/etc/malicious' or '../../../sensitive' could write to sensitive
        system directories.

        Args:
            path: Normalized path to validate

        Raises:
            SecurityError: If path traversal to sensitive directories is detected
        """
        sensitive_paths = ['/etc', '/sys', '/proc', '/dev', '/boot', '/root']

        path_str = str(path)
        for sensitive in sensitive_paths:
            if path_str.startswith(sensitive):
                raise SecurityError(
                    'Attempted write to sensitive system directory',
                    path=path_str,
                )

        logger.debug('Path security validation passed.')

    @staticmethod
    def __validate_and_create_paths(path: str) -> str:
        if not isinstance(path, str):
            raise TypeError(
                f'Destination path must be a string, got {type(path).__name__}'
            )

        if not path or path.isspace():
            raise InvalidDestinationPathError(
                'path cannot be empty or whitespace'
            )

        normalized_path = Path(path).expanduser().resolve()

        # SECURITY: Validate against path traversal BEFORE creating directories
        VerifyPathsUseCasesCVM.__validate_path_security(normalized_path)

        if normalized_path.exists():
            if not normalized_path.is_dir():
                raise PathIsNotDirectoryError(str(normalized_path))

            if not os.access(str(normalized_path), os.W_OK):
                raise PathPermissionError(str(normalized_path))

            logger.debug(
                f'Destination directory already exists: {normalized_path}'
            )
        else:
            try:
                normalized_path.mkdir(parents=True, exist_ok=True)
                logger.info(
                    f'Created destination directory: {normalized_path}'
                )
            except PermissionError as e:
                raise PathPermissionError(str(normalized_path)) from e
            except OSError as e:
                raise OSError(
                    f'Failed to create directory {normalized_path}: {e}'
                ) from e

        logger.debug(
            f'Destination path validated and ready: {normalized_path}'
        )
        return str(normalized_path)
