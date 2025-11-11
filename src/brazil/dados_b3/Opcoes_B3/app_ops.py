import os

import numpy as np
import pandas as pd

from ..common.io_utils import write_parquet
from ..Dados_B3_Acoes.Vol_Ativos.funcao_vol import dados_vol_acoes_b3
from ..docs.imports import cotacoes_doc_conc, data_hoje, lista_feriados
from ..docs.local_para_baixar import vol_ativos_b3
from .Calc_Ops.funcao import opcoes_calculo
from .Tabela_Ops_Abertas.funcao2 import dados_opcoes_br2
from .Tabela_Todas_Ops.funcao1 import dados_opcoes_br


def dados_opcoes_b3(taxa_selic_atual):
    df_opcoes_b3 = dados_opcoes_br()
    df_opcoes_b3_2 = dados_opcoes_br2()
    for df in (df_opcoes_b3, df_opcoes_b3_2):
        df["Opção"] = df["Opção"].astype(str).str.strip()
        df["Tipo Ação"] = df["Tipo Ação"].astype(str).str.strip()
    # Juntando dados das duas tabelas #
    colunas = [
        "Posições Cobertas",
        "Posições Descobertas",
        "Posições Travadas",
        "Posições Totais",
        "Titulares",
        "Lançadores",
        "Spread Travas, Cobertas e Descobertas",
        "Diferença entre vendedores e compradores",
    ]
    df_opcoes_b3 = df_opcoes_b3.merge(
        df_opcoes_b3_2[["Opção", "Tipo Ação"] + colunas],
        on=["Opção", "Tipo Ação"],
        how="left",
    )
    df_opcoes_b3["Ação"] = df_opcoes_b3["Opção"].str[:4]
    df_opcoes_b3["Data Vencimento"] = pd.to_datetime(df_opcoes_b3["Data Vencimento"])
    df_opcoes_b3.drop("Nome da Empresa", axis=1, inplace=True)
    if df_opcoes_b3["Última Negociação"].iloc[0].date() != data_hoje:
        print(
            f"Atenção! Dados de opções desatualizado. Data: {df_opcoes_b3['Última Negociação'].iloc[0].date()}"
        )
    df_opcoes_b3 = df_opcoes_b3.drop("Última Negociação", axis=1)
    # Fazendo coluna de Dias Úteis #
    vencimentos_np = df_opcoes_b3["Data Vencimento"].values.astype("datetime64[D]")
    feriados_np = np.array(lista_feriados, dtype="datetime64[D]")
    hoje_np = np.datetime64(data_hoje, "D")
    dias = np.busday_count(hoje_np, vencimentos_np, holidays=feriados_np)
    dias = np.where(dias > 1, dias - 1, dias)
    df_opcoes_b3["Dias Úteis"] = dias
    # Fazendo coluna de Vol_Hist do Ativo #
    df_dados_vol_acoes_b3 = dados_vol_acoes_b3()
    write_parquet(df_dados_vol_acoes_b3, vol_ativos_b3)
    print("Download Volatilidade de Ativos B3.")

    def ultimo_fechamento_por_codigo(codigo):
        try:
            nome_arquivo = f"{codigo}_B_0_Diário.parquet"
            caminho = os.path.join(cotacoes_doc_conc, nome_arquivo)
            tabela = pd.read_parquet(caminho)
            return tabela["Fechamento"].iat[-1]
        except Exception:
            print(f"Ativo {codigo} não encontrado.")

    df_dados_vol_acoes_b3["Preço Ação"] = [
        ultimo_fechamento_por_codigo(c) for c in df_dados_vol_acoes_b3["Código"]
    ]
    df_dados_vol_acoes_b3["Código4"] = df_dados_vol_acoes_b3["Código"].str[:4]
    df_opcoes_b3["Tipo Ação"] = (
        df_opcoes_b3["Tipo Ação"].str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df_merge = df_opcoes_b3.merge(
        df_dados_vol_acoes_b3[
            [
                "Código4",
                "Tipo Ação",
                "Vol_1_Mes_Anualizada",
                "Vol_3_Mes_Anualizada",
                "Vol_6_Mes_Anualizada",
                "Vol_12_Mes_Anualizada",
                "Preço Ação",
            ]
        ],
        left_on=["Ação", "Tipo Ação"],
        right_on=["Código4", "Tipo Ação"],
        how="left",
    )
    condicoes = [
        df_merge["Dias Úteis"] < 30,
        (df_merge["Dias Úteis"] >= 30) & (df_merge["Dias Úteis"] < 75),
        (df_merge["Dias Úteis"] >= 75) & (df_merge["Dias Úteis"] < 135),
        df_merge["Dias Úteis"] >= 135,
    ]
    escolhas = [
        df_merge["Vol_1_Mes_Anualizada"],
        df_merge["Vol_3_Mes_Anualizada"],
        df_merge["Vol_6_Mes_Anualizada"],
        df_merge["Vol_12_Mes_Anualizada"],
    ]
    df_merge["Vol_Historica"] = np.select(condicoes, escolhas, default=0)
    colunas_final = list(df_opcoes_b3.columns) + ["Vol_Historica", "Preço Ação"]
    df_opcoes_b3 = df_merge[colunas_final].copy()
    df_opcoes_b3["Vol_Historica"] = (
        df_opcoes_b3["Vol_Historica"].astype(str).str.replace(",", ".").astype(float)
    )
    df_opcoes_b3["Preço Ação"] = (
        df_opcoes_b3["Preço Ação"].astype(str).str.replace(",", ".").astype(float)
    )
    df_opcoes_b3["Preço Exercício"] = (
        df_opcoes_b3["Preço Exercício"].astype(str).str.replace(",", ".").astype(float)
    )
    df_opcoes_b3["Dias Úteis"] = df_opcoes_b3["Dias Úteis"].astype(int)
    df_opcoes_b3 = df_opcoes_b3.fillna(0)
    df_opcoes_b3["Preço Ideal"] = 0
    df_opcoes_b3["Preço Ideal"] = df_opcoes_b3.apply(
        lambda row: opcoes_calculo(
            row["Preço Ação"],
            row["Preço Exercício"],
            row["Dias Úteis"],
            taxa_selic_atual,
            row["Vol_Historica"],
            row["Tipo"],
        ),
        axis=1,
    )
    reorganizar_colunas = [
        "Tipo",
        "Opção",
        "Tipo Opção",
        "Data Vencimento",
        "Dias Úteis",
        "Preço Exercício",
        "Preço Ideal",
        "Vol_Historica",
        "Posições Cobertas",
        "Posições Travadas",
        "Posições Totais",
        "Titulares",
        "Lançadores",
        "Spread Travas, Cobertas e Descobertas",
        "Diferença entre vendedores e compradores",
        "Preço Ação",
        "Código",
        "Tipo Ação",
    ]
    df_opcoes_b3 = df_opcoes_b3[reorganizar_colunas]
    mapeamento = {
        "ON NM": 3,
        "DRN": 34,
        "PN N2": 4,
        "ON": 3,
        "DR3": 33,
        "UNT NM": 11,
        "PN N1": 4,
        "UNT N2": 11,
        "PNA N1": 5,
        "PNB N1": 6,
        "ON N1": 3,
        "ON N2": 3,
        "PNB N2": 6,
        "CI": 11,
        "DR2": 32,
        "UNT N1": 11,
        "UNT": 11,
        "PNB": 6,
        "DR1": 31,
    }
    df_opcoes_b3["Código"] = df_opcoes_b3["Código"].astype(str)
    df_opcoes_b3["Código"] = df_opcoes_b3["Código"] + df_opcoes_b3["Tipo Ação"].map(
        mapeamento
    ).fillna(0).astype(int).astype(str)
    # PEGANDO VALOR IDEAL DO PREÇO DA OPÇÃO E VALORES DO MT5#
    # lista_opcoes = df_opcoes_b3[df_opcoes_b3['Posições Totais'].notna()]['Opção'].unique().tolist()
    # df_opcoes_MT5 = atualizar_preco_mt5(lista_opcoes)

    return df_opcoes_b3
