import re
from datetime import datetime

import numpy as np
import pandas as pd
import requests

from ...docs.imports import data
from ..Tabela_Ops_Abertas.cookies_opcoes2 import cookies_op2, headers_op2

_PAT_EXCLUIR = re.compile(r"\b(?:EG|ED|EX|EJ|EDJ|ATZ)\b")


def dados_opcoes_br2() -> pd.DataFrame:
    data_formatada = datetime.strftime(data, "%Y%m%d")
    referer_url = f"https://www.b3.com.br/json/{data_formatada}/Posicoes/Empresa/SI_C_OPCPOSABEMP.json"
    response = requests.get(
        referer_url, cookies=cookies_op2, headers=headers_op2, timeout=(3, 20)
    )
    response.raise_for_status()
    body = response.json()
    empresa = body.get("Empresa", {})
    parts = []
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        items = empresa.get(ch)
        if items:
            parts.append(pd.DataFrame(items))
    if not parts:
        return pd.DataFrame(
            columns=[
                "Código",
                "Nome da Empresa",
                "Tipo",
                "Opção",
                "Preço Exercício",
                "Data Vencimento",
                "Posições Cobertas",
                "Posições Descobertas",
                "Posições Travadas",
                "Posições Totais",
                "Titulares",
                "Lançadores",
                "Tipo Ação",
            ]
        )
    df = pd.concat(parts, ignore_index=True)
    df["dtVen"] = pd.to_datetime(df["dtVen"], format="%Y%m%d")
    colunas = [
        "Opção",
        "Preço Exercício",
        "Nome da Empresa",
        "Posições Cobertas",
        "Posições Descobertas",
        "Titulares",
        "Posições Travadas",
        "Posições Totais",
        "Lançadores",
        "Data Vencimento",
        "tMerc",
        "Código",
        "Tipo Ação",
    ]
    df.columns = colunas
    df["Opção"] = df["Opção"].astype(str)
    df["Tipo"] = np.where(
        df["Opção"].str[4].isin(list("MNOPQRSTUVWXYZ")), "Put", "Call"
    )
    df = df[
        [
            "Código",
            "Nome da Empresa",
            "Tipo",
            "Opção",
            "Preço Exercício",
            "Data Vencimento",
            "Posições Cobertas",
            "Posições Descobertas",
            "Posições Travadas",
            "Posições Totais",
            "Titulares",
            "Lançadores",
            "tMerc",
            "Tipo Ação",
        ]
    ]
    df["Preço Exercício"] = pd.to_numeric(df["Preço Exercício"], errors="coerce")
    df["Spread Travas, Cobertas e Descobertas"] = (
        df["Posições Travadas"] + df["Posições Cobertas"] - df["Posições Descobertas"]
    )
    df["Diferença entre vendedores e compradores"] = df["Titulares"] - df["Lançadores"]
    df = df.drop(columns=["tMerc"])
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
    df = dados_opcoes_br2()
