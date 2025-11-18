from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

from ..common.net import build_session  # type: ignore
from .cookies_capital_social import cookies, headers
from .urls import url_cap_social_list


def _fetch_capital_social(session: requests.Session, url: str) -> pd.DataFrame:
    resp = session.get(url, cookies=cookies, headers=headers, timeout=(3, 20))
    resp.raise_for_status()
    data = resp.json().get("results", [])
    return pd.DataFrame(data)


def dados_capital_social_br() -> pd.DataFrame:
    session = build_session()
    dfs: list[pd.DataFrame] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {
            ex.submit(_fetch_capital_social, session, url): url
            for url in url_cap_social_list
        }
        for fut in as_completed(futures):
            df = fut.result()
            if not df.empty:
                dfs.append(df)
    acao = pd.concat(dfs, ignore_index=True)
    acao.columns = [
        "Empresa",
        "Código",
        "Nome da Companhia",
        "Mercado",
        "Tipo Capital",
        "Valor",
        "Data Aprovação",
        "ON",
        "PN",
        "Total",
    ]
    return acao


if __name__ == "__main__":
    df = dados_capital_social_br()
