import locale
import time

import numpy as np
import pandas as pd

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")


def organizar_geral(df, valor=""):
    if valor.lower() == "dre":
        df.loc[df["CD_CONTA"] == "3.99.02.01", "DS_CONTA"] = "ON Diluído"
        df.loc[df["CD_CONTA"] == "3.99.02.02", "DS_CONTA"] = "PN Diluído"
        repetidos = df["CD_CONTA"] == df["CD_CONTA"].shift(-1)
        df.loc[repetidos.shift(1, fill_value=False), "DS_CONTA"] = "Acumulado"
        df = df[
            ~df.apply(
                lambda row: row.astype(str).str.contains("Acumulado", case=False)
            ).any(axis=1)
        ]
    if valor.lower() == "dra":
        repetidos = df["CD_CONTA"] == df["CD_CONTA"].shift(1)
        df.loc[repetidos.shift(1, fill_value=False), "DS_CONTA"] = "Acumulado"
        df = df[
            ~df.apply(
                lambda row: row.astype(str).str.contains("Acumulado", case=False)
            ).any(axis=1)
        ]
    df["CD_CONTA"] = pd.to_numeric(df["CD_CONTA"], errors="coerce").fillna(0)
    mask_zero = df["CD_CONTA"] == 0
    filled = df["CD_CONTA"].replace(0, np.nan).ffill()
    df["CD_CONTA"] = np.where(
        mask_zero & filled.notna(), filled + 0.0001, df["CD_CONTA"]
    )
    mask = df["ESCALA_MOEDA"] == "UNIDADE"
    df.loc[mask, "VL_CONTA"] = df.loc[mask, "VL_CONTA"] / 1000
    valores_unicos = set(df["ESCALA_MOEDA"].dropna().unique())
    valores_validos = {"UNIDADE", "MIL"}
    if not valores_unicos.issubset(valores_validos):
        valores_invalidos = valores_unicos - valores_validos
        print(f"Há valores diferentes de 'UNIDADE' e 'MIL': {valores_invalidos}")
    df.drop(columns=["ESCALA_MOEDA"], inplace=True)
    df["VL_CONTA"] = round(df["VL_CONTA"], 2)
    df["CD_CONTA"] = round(df["CD_CONTA"], 4)
    df = df.set_index(["CD_CONTA", "ST_CONTA_FIXA", "DS_CONTA"])
    df.index.names = ["Número", "Conta Fixa", "Valor contábil"]
    return df


def organizar_geral2(df):
    df = df[df["ORDEM_EXERC"] == "ÚLTIMO"]
    df["DT_REFER"] = pd.to_datetime(df["DT_REFER"], errors="coerce")
    df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")
    df["CD_CVM"] = pd.to_numeric(df["CD_CVM"], errors="coerce")
    df.drop(["VERSAO", "GRUPO_DFP", "ORDEM_EXERC", "MOEDA"], axis=1, inplace=True)
    return df


def organizar_geral3(df, reverter=False):
    if reverter:
        if "Data_Referencia" in df.columns:
            df["Data_Referencia"] = pd.to_datetime(
                df["Data_Referencia"], errors="coerce"
            )
            df.sort_values(by="Data_Referencia", ascending=False, inplace=True)
            lista_unicos = df["Data_Referencia"].unique().tolist()
            if len(lista_unicos) > 0:
                ultima_data = (
                    lista_unicos[4] if len(lista_unicos) >= 4 else lista_unicos[-1]
                )
                df = df[df["Data_Referencia"] >= ultima_data]
    else:
        try:
            try:
                df.drop(["Versao", "ID_Documento"], axis=1, inplace=True)
            except:
                pass
            if "Data_Referencia" in df.columns:
                df.sort_values(by="Data_Referencia", inplace=True)
        except:
            pass
    return df


def extracao_docs(local_docs, local_baixar, nomes_arquivos, anos, diversos=False):
    if not diversos:
        for ano in anos:
            try:
                arquivo = f"{local_docs}\\{nomes_arquivos}{ano}.csv"
                arquivo1 = pd.read_csv(
                    arquivo, sep=";", decimal=",", encoding="ISO-8859-1"
                )
                arquivo1.to_parquet(f"{local_baixar}\\{nomes_arquivos}{ano}.parquet")
            except FileNotFoundError:
                pass
            except pd.errors.ParserError as e:
                print(f"Erro ao processar o arquivo {arquivo}: {str(e)}")
            time.sleep(0.5)
    else:
        for ano in anos:
            for nome in nomes_arquivos:
                try:
                    arquivo = f"{local_docs}\\{nome}{ano}.csv"
                    arquivo1 = pd.read_csv(
                        arquivo, sep=";", decimal=",", encoding="ISO-8859-1"
                    )
                    arquivo1.to_parquet(f"{local_baixar}\\{nome}{ano}.parquet")
                except FileNotFoundError:
                    pass
                except pd.errors.ParserError as e:
                    print(f"Erro ao processar o arquivo {arquivo}: {str(e)}")
                time.sleep(0.5)


def arrumar_valor_numerico(df):
    colunas = [
        "Quantidade_Acoes_Ordinarias",
        "Quantidade_Acoes_Preferenciais",
        "Quantidade_Total_Acoes",
        "Quantidade_Acionistas_PF",
        "Quantidade_Acionistas_PJ",
        "Quantidade_Acionistas_Investidores_Institucionais",
        "Total_de_Investidores",
        "Quantidade_Acao_Ordinaria_Circulacao",
        "Quantidade_Acao_Preferencial_Circulacao",
        "Quantidade_Total_Acoes_Circulacao",
        "Quantidade",
    ]
    if any(col in df.columns for col in colunas):
        for coluna in colunas:
            try:
                df[coluna] = df[coluna].apply(
                    lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else ""
                )
            except:
                pass
    return df
