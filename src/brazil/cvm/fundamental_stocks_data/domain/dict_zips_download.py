from typing import Dict, List, Optional, Set, Tuple

from .available_docs import UrlDocs
from .available_years import AvailableYears


class DictZipsToDownload:
    def __init__(self):
        self._url_docs = UrlDocs()
        self._available_years = AvailableYears()

    def get_dict_zips_to_download(
        self,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> Tuple[Dict[str, List[str]], Set[str]]:
        range_years: range = self._available_years.return_range_years(
            initial_year, last_year
        )

        dict_urls_docs, set_docs = self._url_docs.get_url_docs(list_docs)

        dict_zips_to_download: Dict[str, List[str]] = {
            doc: [url + str(year) + ".zip" for year in range_years]
            for doc, url in dict_urls_docs.items()
        }

        return dict_zips_to_download, set_docs
