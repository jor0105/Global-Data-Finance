"""Orchestration layer for CVM fundamental_stocks_data.

Consolidates the prior `application/use_cases/` modules into one file.
Simple use cases stay as thin wrapper classes (test contract). The
download orchestrator and the path-traversal verifier remain full classes:
the first holds state across calls (D3), the second preserves the R11
security boundary bit-identically.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ....core import get_logger
from ....core.utils import assert_path_not_sensitive
from ....macro_exceptions import (
    InvalidDestinationPathError,
    PathIsNotDirectoryError,
    PathPermissionError,
)
from .core import (
    AvailableDocsCVM,
    AvailableYearsCVM,
    DictZipsToDownloadCVM,
    DownloadResultCVM,
)
from .errors import EmptyDocumentListError, MissingDownloadUrlError
from .http import AsyncDownloadAdapterCVM

logger = get_logger(__name__)


class GetAvailableDocsUseCaseCVM:
    """Use case for retrieving available CVM document types."""

    def __init__(self) -> None:
        self.__available_docs = AvailableDocsCVM()
        logger.debug('GetAvailableDocsUseCaseCVM initialized')

    def execute(self) -> Dict[str, str]:
        """Retrieve available document types."""
        logger.info('Retrieving available document types')
        try:
            docs = self.__available_docs.get_available_docs()
            logger.debug(f'Retrieved {len(docs)} document types')
            return docs
        except Exception as e:
            logger.error(f'Failed to retrieve available documents: {e}')
            raise


class GetAvailableYearsUseCaseCVM:
    """Use case for retrieving available years for CVM documents."""

    def __init__(self) -> None:
        self.__available_years = AvailableYearsCVM()
        logger.debug('GetAvailableYearsUseCaseCVM initialized')

    def execute(self) -> Dict[str, int]:
        """Retrieve available years information."""
        logger.info('Retrieving available years information')
        try:
            years_info = {
                'General Document Years': self.__available_years.get_minimal_general_year(),
                'ITR Document Years': self.__available_years.get_minimal_itr_year(),
                'CGVN and VMLO Document Years': self.__available_years.get_minimal_cgvn_vlmo_year(),
                'Current Year': self.__available_years.get_current_year(),
            }
            logger.debug(f'Retrieved years information: {years_info}')
            return years_info
        except Exception as e:
            logger.error(f'Failed to retrieve available years: {e}')
            raise


class GenerateRangeYearsUseCasesCVM:
    """Use case for generating an inclusive year range."""

    def __init__(self) -> None:
        self.__range_years = AvailableYearsCVM()
        logger.debug('GenerateRangeYearsUseCasesCVM initialized')

    def execute(
        self,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> range:
        logger.debug(
            f'Generating Range Years, years={initial_year}-{last_year}'
        )
        try:
            range_years = self.__range_years.return_range_years(
                initial_year=initial_year,
                last_year=last_year,
            )
            logger.info(f'Generated range of years: {list(range_years)}')
            return range_years
        except Exception as e:
            logger.error(f'Failed to generate range of years: {e}')
            raise


class GenerateUrlsUseCaseCVM:
    """Use case for generating download URLs."""

    def __init__(self) -> None:
        self.__dict_generator = DictZipsToDownloadCVM()
        logger.debug('GenerateUrlsUseCaseCVM initialized')

    def execute(
        self,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> Tuple[Dict[str, List[str]], Set[str]]:
        """Generate download URLs for specified documents and years."""
        logger.debug(
            f'Generating URLs for docs={list_docs}, years={initial_year}-{last_year}'
        )
        try:
            dict_zips, new_set_docs = (
                self.__dict_generator.get_dict_zips_to_download(
                    list_docs=list_docs,
                    initial_year=initial_year,
                    last_year=last_year,
                )
            )
            total_urls = sum(len(urls) for urls in dict_zips.values())
            logger.info(
                f'Generated {total_urls} URLs from {len(dict_zips)} document types'
            )
            return dict_zips, new_set_docs
        except Exception as e:
            logger.error(f'Failed to generate URLs: {e}')
            raise


class VerifyPathsUseCasesCVM:
    """Verify and create destination directory structure for CVM downloads.

    Path-traversal defense (R11) delegates to the shared
    :func:`globaldatafinance.core.utils.assert_path_not_sensitive` helper
    so the CVM and B3 facades enforce the same blocklist with the same
    path-aware semantics. The check runs **before** any ``mkdir``.
    """

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
        """Create and verify directory structure for documents and years."""
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

        assert_path_not_sensitive(normalized_path, raw_input=path)

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


class DownloadDocumentsUseCaseCVM:
    """Orchestrator use case for downloading CVM documents.

    Kept as a stateful class (D3) — caches the download repository and
    the sub-use-case helpers across calls. Tests inspect the private
    mangled attributes (`_DownloadDocumentsUseCaseCVM__repository` etc.),
    so the constructor must keep the same name-mangling layout.

    `isinstance(repository, ABC)` check from the pre-refactor version is
    intentionally removed (task 3.2.4) — Python duck-typing is enough,
    and the single-impl ABC offered no real safety.
    """

    def __init__(self, repository: AsyncDownloadAdapterCVM) -> None:
        """Initialize the orchestrator with a repository-shaped collaborator."""
        self.__repository: AsyncDownloadAdapterCVM = repository
        self.__url_generator = GenerateUrlsUseCaseCVM()
        self.__range_years_generator = GenerateRangeYearsUseCasesCVM()

        logger.debug(
            f'DownloadDocumentsUseCaseCVM initialized with '
            f'repository={repository.__class__.__name__}'
        )

    def execute(
        self,
        destination_path: str,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> DownloadResultCVM:
        """Execute the download operation."""
        logger.info(
            f'Starting download orchestration: '
            f'path={destination_path}, '
            f'docs={list_docs}, '
            f'years={initial_year}-{last_year}'
        )

        range_years = self.__range_years_generator.execute(
            initial_year=initial_year,
            last_year=last_year,
        )

        dict_urls_zips, new_set_docs = self.__url_generator.execute(
            list_docs=list_docs,
            initial_year=initial_year,
            last_year=last_year,
        )

        verify_paths = VerifyPathsUseCasesCVM(
            destination_path=destination_path,
            new_set_docs=new_set_docs,
            range_years=range_years,
        )
        docs_paths = verify_paths.execute()

        start_time = time.time()

        try:
            tasks = self.__prepare_download_tasks(dict_urls_zips, docs_paths)
            result = self.__repository.download_docs(tasks)

            end_time = time.time()
            result.elapsed_time = end_time - start_time

            logger.info(
                f'Download completed in {result.elapsed_time:.2f}s: '
                f'✓ {result.success_count_downloads} successful, '
                f'✗ {result.error_count_downloads} errors'
            )

            if result.successful_downloads:
                logger.debug(
                    f'Successfully downloaded: {", ".join(result.successful_downloads)}'
                )

            if result.failed_downloads:
                failed_info = '; '.join(
                    [
                        f'{doc}: {error}'
                        for doc, error in result.failed_downloads.items()
                    ]
                )
                logger.warning(f'Failed downloads: {failed_info}')

            return result

        except Exception as e:
            logger.error(f'Download execution failed: {e}', exc_info=True)
            raise

    def __prepare_download_tasks(
        self,
        dict_zip_to_download: Dict[str, List[str]],
        docs_paths: Dict[str, Dict[int, str]],
    ) -> List[Tuple[str, str, str, str]]:
        """Prepare download tasks from URL and path dictionaries."""
        tasks = []
        for doc_name, years_dict in docs_paths.items():
            if doc_name not in dict_zip_to_download:
                raise MissingDownloadUrlError(doc_name)

            url_list = dict_zip_to_download[doc_name]

            for year_int, destination_path in years_dict.items():
                year_str = str(year_int)
                matching_url = None
                for url in url_list:
                    if year_str in url:
                        matching_url = url
                        break

                if matching_url:
                    tasks.append(
                        (matching_url, doc_name, year_str, destination_path)
                    )
                else:
                    logger.warning(
                        f'No URL found for {doc_name}_{year_str} in dict_zip_to_download'
                    )

        return tasks
