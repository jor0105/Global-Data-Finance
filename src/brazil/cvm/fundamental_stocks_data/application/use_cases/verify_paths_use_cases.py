import logging
import os
from typing import Dict, Set

from src.brazil.cvm.fundamental_stocks_data.exceptions import EmptyDocumentListError
from src.macro_exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)

logger = logging.getLogger(__name__)


class VerifyPathsUseCases:
    def __init__(
        self,
        destination_path: str,
        new_set_docs: Set[str],
        range_years: range,
    ):
        verify_destination_path = self.__validate_and_create_paths(destination_path)
        self.destination_path = verify_destination_path
        self.new_set_docs = new_set_docs
        self.range_years = range_years

        if not new_set_docs:
            raise EmptyDocumentListError()

        logger.debug(
            f"VerifyPathsUseCases created: "
            f"path={self.destination_path}, "
            f"docs={self.new_set_docs}"
        )

    def execute(self) -> None:
        """Create and verify directory structure for documents and years.

        Returns:
            Dictionary with structure: {doc: {year: path}}
        """
        # Create subdirectories for each document type
        self.docs_paths: Dict[str, Dict[int, str]] = {}
        for doc in self.new_set_docs:
            doc_path = os.path.join(self.destination_path, doc)
            validated_doc_path = self.__validate_and_create_paths(doc_path)

            # Create subdirectories for each year within document path
            self.docs_paths[doc] = {}
            for year in self.range_years:
                year_path = os.path.join(validated_doc_path, str(year))
                validated_year_path = self.__validate_and_create_paths(year_path)
                self.docs_paths[doc][year] = validated_year_path

        logger.info(
            f"Directory structure created successfully. "
            f"Documents: {len(self.docs_paths)}, "
            f"Years per document: {len(self.range_years)}"
        )

        print("Folders for installation checked/created. Starting installations...")

    @staticmethod
    def __validate_and_create_paths(path: str) -> str:
        # path -> destination_path

        if not isinstance(path, str):
            raise TypeError(
                f"Destination path must be a string, got {type(path).__name__}"
            )

        if not path or path.isspace():
            raise InvalidDestinationPathError("path cannot be empty or whitespace")

        normalized_path = os.path.abspath(os.path.expanduser(path))

        if os.path.exists(normalized_path):
            if not os.path.isdir(normalized_path):
                raise PathIsNotDirectoryError(normalized_path)

            if not os.access(normalized_path, os.W_OK):
                raise PathPermissionError(normalized_path)

            logger.debug(f"Destination directory already exists: {normalized_path}")
        else:
            try:
                os.makedirs(normalized_path, exist_ok=True)
                logger.info(f"Created destination directory: {normalized_path}")
            except PermissionError as e:
                raise PathPermissionError(normalized_path) from e
            except OSError as e:
                raise OSError(
                    f"Failed to create directory {normalized_path}: {e}"
                ) from e

        logger.debug(
            f"Princiapl destination path validated and ready: {normalized_path}"
        )
        return normalized_path
