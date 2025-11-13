import os
from pathlib import Path
from typing import Dict, Set

from src.brazil.cvm.fundamental_stocks_data.domain import AvailableYears
from src.brazil.cvm.fundamental_stocks_data.exceptions import EmptyDocumentListError
from src.core import get_logger
from src.macro_exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)

logger = get_logger(__name__)


class VerifyPathsUseCases:
    def __init__(
        self,
        destination_path: str,
        new_set_docs: Set[str],
        range_years: range,
    ):
        self.destination_path = destination_path
        self.new_set_docs = new_set_docs
        self.range_years = range_years
        self.__available_years = AvailableYears()

        if not new_set_docs:
            raise EmptyDocumentListError()

        logger.debug(
            f"VerifyPathsUseCases created: "
            f"path={self.destination_path}, "
            f"docs={self.new_set_docs}"
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
                        f"Skipping folder for doc={doc}, year={year} (invalid year for this document)"
                    )
                    continue
                year_path = str(Path(validated_doc_path) / str(year))
                validated_year_path = self.__validate_and_create_paths(year_path)
                docs_paths[doc][year] = validated_year_path

        logger.info(
            f"Directory structure created successfully. "
            f"Documents: {len(docs_paths)}, "
            f"Years per document: {[len(years) for years in docs_paths.values()]}"
        )

        print("Installation folders checked/created. Starting installations...")

        return docs_paths

    def __is_valid_year_for_doc(self, doc: str, year: int) -> bool:
        doc_upper = doc.upper()
        min_itr = self.__available_years.get_minimal_itr_year()
        min_cgvn_vlmo = self.__available_years.get_minimal_cgvn_vlmo_year()
        min_general = self.__available_years.get_minimal_general_year()

        if doc_upper == "ITR":
            return year >= min_itr

        if doc_upper in {"VLMO", "CGVN"}:
            return year >= min_cgvn_vlmo

        return year >= min_general

    @staticmethod
    def __validate_and_create_paths(path: str) -> str:
        if not isinstance(path, str):
            raise TypeError(
                f"Destination path must be a string, got {type(path).__name__}"
            )

        if not path or path.isspace():
            raise InvalidDestinationPathError("path cannot be empty or whitespace")

        normalized_path = Path(path).expanduser().resolve()

        if normalized_path.exists():
            if not normalized_path.is_dir():
                raise PathIsNotDirectoryError(str(normalized_path))

            if not os.access(str(normalized_path), os.W_OK):
                raise PathPermissionError(str(normalized_path))

            logger.debug(f"Destination directory already exists: {normalized_path}")
        else:
            try:
                normalized_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created destination directory: {normalized_path}")
            except PermissionError as e:
                raise PathPermissionError(str(normalized_path)) from e
            except OSError as e:
                raise OSError(
                    f"Failed to create directory {normalized_path}: {e}"
                ) from e

        logger.debug(f"Destination path validated and ready: {normalized_path}")
        return str(normalized_path)
