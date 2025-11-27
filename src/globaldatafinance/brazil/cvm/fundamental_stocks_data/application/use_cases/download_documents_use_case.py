from typing import Dict, List, Optional, Tuple

from ......core import get_logger
from ...domain import DownloadResultCVM
from ...exceptions import InvalidRepositoryTypeError, MissingDownloadUrlError
from ..interfaces import DownloadDocsCVMRepositoryCVM
from .generate_range_years_use_cases import GenerateRangeYearsUseCasesCVM
from .generate_urls_use_case import GenerateUrlsUseCaseCVM
from .verify_paths_use_cases import VerifyPathsUseCasesCVM

logger = get_logger(__name__)


class DownloadDocumentsUseCaseCVM:
    """Orchestrator use case for downloading CVM documents."""

    def __init__(self, repository: DownloadDocsCVMRepositoryCVM) -> None:
        """Initialize the orchestrator with a repository.

        Args:
            repository: Implementation of DownloadDocsCVMRepositoryCVM.
        """
        if not isinstance(repository, DownloadDocsCVMRepositoryCVM):
            raise InvalidRepositoryTypeError(
                actual_type=type(repository).__name__,
            )

        self.__repository = repository
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
        """Execute the download operation.

        Args:
            destination_path: Directory path where files will be saved.
            list_docs: List of document type codes (e.g., ["DFP", "ITR"]).
            initial_year: Starting year for downloads (inclusive).
            last_year: Ending year for downloads (inclusive).

        Returns:
            DownloadResultCVM containing successful downloads and encountered errors.
        """
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

        import time

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
        """Prepare download tasks from the input dictionaries."""
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
