from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

from ...common.net import build_session
from .cookies_acoes import cookies, headers
from .urls import URLS_DADOSB3


def _fetch_json(session: requests.Session, url: str) -> dict:
    resp = session.get(url, cookies=cookies, headers=headers, timeout=(3, 20))
    resp.raise_for_status()
    return resp.json()


def dados_acoes_b3() -> pd.DataFrame:
    """Baixa as páginas de empresas da B3 em paralelo com pooling e retries."""
    session = build_session()
    dfs = []
    # Paraleliza downloads; 8 workers geralmente é um bom equilíbrio rede/CPU
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_json, session, url): url for url in URLS_DADOSB3}
        for fut in as_completed(futures):
            data = fut.result()
            df = pd.DataFrame(data.get("results", []))
            if not df.empty:
                dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    acao = pd.concat(dfs, ignore_index=True)
    # Inicializa colunas esperadas
    for col in (
        "Quantidade de ações ON",
        "Quantidade de ações PN",
        "Quantidade de ações Totais",
    ):
        if col not in acao.columns:
            acao[col] = 0
    # Remove colunas não usadas
    drop_cols = ["typeBDR", "status", "segment", "segmentEng", "type", "market"]
    acao = acao.drop(
        columns=[c for c in drop_cols if c in acao.columns], errors="ignore"
    )
    return acao


if __name__ == "__main__":
    df = dados_acoes_b3()
