from typing import List, Optional

from .available_docs import UrlDocs
from .available_years import AvailableYears


class ListZipsToDownload:
    def __init__(self):
        self._url_docs = UrlDocs()
        self._available_years = AvailableYears()

    def get_list_zips_to_download(
        self,
        list_docs: Optional[List[str]] = None,
        initial_year: Optional[int] = None,
        last_year: Optional[int] = None,
    ) -> List[str]:
        range_years: range = self._available_years.return_range_years(
            initial_year, last_year
        )

        urls_docs: List[str] = self._url_docs.get_url_docs(list_docs)

        list_zips_to_download: List[str] = [
            url + str(year) + ".zip" for year in range_years for url in urls_docs
        ]

        return list_zips_to_download
