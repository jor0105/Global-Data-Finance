import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

from ...common.net import build_session
from .cookies_vol import cookies_vol_acoes, headers_vol_acoes
from .urls import (
    url1_vol_acoes,
    url2_vol_acoes,
    url3_vol_acoes,
    url4_vol_acoes,
    url5_vol_acoes,
    url6_vol_acoes,
    url7_vol_acoes,
    url8_vol_acoes,
)

URLS_VOL = [
    url1_vol_acoes,
    url2_vol_acoes,
    url3_vol_acoes,
    url4_vol_acoes,
    url5_vol_acoes,
    url6_vol_acoes,
    url7_vol_acoes,
    url8_vol_acoes,
]

_PAT_EXCLUIR = re.compile(r"\b(?:EG|ED|EX|EJ|EDJ|ATZ)\b")


def _fetch_vol(session: requests.Session, url: str) -> pd.DataFrame:
    resp = session.get(
        url, cookies=cookies_vol_acoes, headers=headers_vol_acoes, timeout=(3, 20)
    )
    resp.raise_for_status()
    df = pd.DataFrame(resp.json().get("results", []))
    if "tradingName" in df.columns:
        df = df.drop("tradingName", axis=1)
    return df


def dados_vol_acoes_b3() -> pd.DataFrame:
    session = build_session()
    dfs: list[pd.DataFrame] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_vol, session, url): url for url in URLS_VOL}
        for fut in as_completed(futures):
            df = fut.result()
            if not df.empty:
                dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    vol_df = pd.concat(dfs, ignore_index=True)
    colunas = [
        "Código",
        "Tipo Ação",
        "Std_1_Mes",
        "Vol_1_Mes_Anualizada",
        "Std_3_Mes",
        "Vol_3_Mes_Anualizada",
        "Std_6_Mes",
        "Vol_6_Mes_Anualizada",
        "Std_12_Mes",
        "Vol_12_Mes_Anualizada",
    ]
    vol_df.columns = colunas
    vol_df["Tipo Ação"] = (
        vol_df["Tipo Ação"]
        .str.replace(_PAT_EXCLUIR, "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return vol_df


if __name__ == "__main__":
    df = dados_vol_acoes_b3()
