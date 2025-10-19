from dataclasses import dataclass
from typing import List, Set

from src.brasil.dados_cvm.dados_fundamentalistas.domain.urls_docs import UrlDocs


@dataclass
class ListToDownload:
    list_zips_to_download: List = []
    anos_dfp = range(int(ano_inicial), int(ano_final))
    __url_docs: UrlDocs = UrlDocs()

    def update_list_to_download(
        self, list_name_docs: List, initial_year: int = 2010, last_year: int = 2025
    ) -> None:
        set_years: Set[int] = set(range(int(initial_year), int(last_year)))

        for ano in set_years:
            ano = str(ano)
            listas_zip_cgvn.append(nomes_cgvn + ano + ".zip")
