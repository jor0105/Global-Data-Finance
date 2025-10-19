import pandas as pd

from ...common.net import build_session
from .cookies_ifix import cookies_ifix, headers_ifix


def percentual_ifix() -> pd.DataFrame:
    session = build_session()
    response = session.get(
        "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJRklYIiwic2VnbWVudCI6IjIifQ==",
        cookies=cookies_ifix,
        headers=headers_ifix,
        timeout=(3, 20),
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json()["results"])
    df.drop(["type", "partAcum"], axis=1, inplace=True)
    colunas = ["Segmento", "Código", "Nome do Fundo", "Participação", "Q. Teórica"]
    df.columns = colunas
    lista = response.json()["header"]
    df["Redutor"] = lista["reductor"]
    df["Q. Teórica IBOV"] = lista["theoricalQty"]
    df["Data_Atualizacao"] = lista["date"]
    df["Participação"] = df["Participação"].str.replace(",", ".").astype("float32")
    df.sort_values(by="Participação", ascending=False, inplace=True)
    df.set_index("Código", inplace=True)
    return df


if __name__ == "__main__":
    df = percentual_ifix()
