from typing import Dict, List, Optional, Set, Tuple

from src.brazil.cvm.fundamental_stocks_data.domain import DictZipsToDownload
from src.core import get_logger

logger = get_logger(__name__)


class GenerateUrlsUseCase:
    """Use case for generating download URLs."""

    def __init__(self) -> None:
        self.__dict_generator = DictZipsToDownload()
        logger.debug("GenerateUrlsUseCase initialized")

    def execute(
        self,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> Tuple[Dict[str, List[str]], Set[str]]:
        """Generate download URLs for specified documents and years.

        Args:
            list_docs: List of document type codes (e.g., ["DFP", "ITR"]).
            initial_year: Starting year for downloads (inclusive).
            last_year: Ending year for downloads (inclusive).

        Returns:
            A tuple containing a dictionary mapping document types to lists of download URLs and a set of document types.
        """
        logger.debug(
            f"Generating URLs for docs={list_docs}, "
            f"years={initial_year}-{last_year}"
        )

        try:
            dict_zips, new_set_docs = self.__dict_generator.get_dict_zips_to_download(
                list_docs=list_docs,
                initial_year=initial_year,
                last_year=last_year,
            )

            total_urls = sum(len(urls) for urls in dict_zips.values())
            logger.info(
                f"Generated {total_urls} URLs from " f"{len(dict_zips)} document types"
            )

            return dict_zips, new_set_docs

        except Exception as e:
            logger.error(f"Failed to generate URLs: {e}")
            raise
