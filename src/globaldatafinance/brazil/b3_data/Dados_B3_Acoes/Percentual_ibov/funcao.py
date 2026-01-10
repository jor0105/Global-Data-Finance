import pandas as pd

from ...common.net import build_session
from .cookies_percentual_ibov import cookies_percentual_ibov, headers_percentual_ibov


def percentual_ibov() -> pd.DataFrame:
    session = build_session()
    response = session.get(
        "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQlNEIiwic2VnbWVudCI6IjEifQ==",
        cookies=cookies_percentual_ibov,
        headers=headers_percentual_ibov,
        timeout=(3, 20),
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json()["results"])
    df = df.drop(columns=["partAcum", "type"])
    colunas = ["Segmento", "Código", "Nome Empresa", "Participação", "Q. Teórica"]
    df.columns = colunas
    lista = response.json()["header"]
    df["Redutor"] = lista["reductor"]
    df["Q. Teórica IBOV"] = lista["theoricalQty"]
    df["Data_Atualizacao"] = lista["date"]
    df["Participação"] = df["Participação"].str.replace(",", ".").astype("float32")
    df.sort_values(by="Participação", ascending=False, inplace=True)
    return df


if __name__ == "__main__":
    df = percentual_ibov()
