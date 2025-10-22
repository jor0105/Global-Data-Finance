import re
from datetime import datetime

import numpy as np
import pandas as pd
import requests

from ...docs.imports import data  # mantém a lógica existente de filtragem por data
from ..Tabela_Todas_Ops.cookies_opcoes1 import cookies_op1, headers_op1

_PAT_EXCLUIR = re.compile(r"\b(?:EG|ED|EX|EJ|EDJ|ATZ)\b")


def dados_opcoes_br() -> pd.DataFrame:
    data_formatada = datetime.strftime(data, "%Y%m%d")
    referer_url = f"https://www.b3.com.br/json/{data_formatada}/Series/Empresa/SI_C_OPCSEREMP.json"
    response = requests.get(
        referer_url, cookies=cookies_op1, headers=headers_op1, timeout=(3, 20)
    )
    response.raise_for_status()
    body = response.json()
    empresa = body.get("Empresa", {})
    parts = []
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        items = empresa.get(ch)
        if items:
            parts.append(pd.DataFrame(items))
    if empresa.get("3"):
        parts.append(pd.DataFrame(empresa["3"]))
    if not parts:
        return pd.DataFrame(
            columns=[
                "Opção",
                "Preço Exercício",
                "Tipo Ação",
                "Nome da Empresa",
                "Tipo Opção",
                "Data Vencimento",
                "Última Negociação",
                "Tipo",
                "Código",
            ]
        )
    df = pd.concat(parts, ignore_index=True)
    df["dtVen"] = pd.to_datetime(df["dtVen"], format="%Y%m%d")
    df = df.drop(columns=["nmEmp", "tMerc"], errors="ignore")
    colunas = [
        "Opção",
        "Preço Exercício",
        "Tipo Ação",
        "Nome da Empresa",
        "Tipo Opção",
        "Data Vencimento",
        "Última Negociação",
    ]
    df.columns = colunas
    df["Última Negociação"] = pd.to_datetime(
        df["Última Negociação"], format="%Y%m%d", errors="coerce"
    )
    df["Tipo"] = np.where(df["Opção"].str[4].isin(list("ABCDEFGHIJKL")), "Call", "Put")
    df["Código"] = df["Opção"].str[:4]
    df = df[df["Data Vencimento"] >= data]
    df["Tipo Ação"] = (
        df["Tipo Ação"]
        .astype(str)
        .str.replace(_PAT_EXCLUIR, "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return df


if __name__ == "__main__":
    df = dados_opcoes_br()
