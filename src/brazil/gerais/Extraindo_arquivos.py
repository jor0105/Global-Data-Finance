import os
from zipfile import ZipFile

import pandas as pd
from funcoes import *
from url_e_nomes import *


def extrair_arquivos_cvm(diretorio, anos_dfp, anos_cgvn, anos_itr):
    print("Começando extração dos documentos zipados...")
    caminho_pasta_zip = os.path.join(diretorio, nome_pasta_zip)
    caminho_pasta_anos = os.path.join(diretorio, nome_pasta_anos)
    # EXTRAINDO ARQUIVOS E TRANSFORMANDO EM PARQUET#
    for arquivo in os.listdir(caminho_pasta_zip):
        caminho_arquivo = os.path.join(caminho_pasta_zip, arquivo)
        ZipFile(caminho_arquivo, "r").extractall(caminho_pasta_zip)

    # EXTRAINDO ARQUIVOS CGVN #
    extracao_docs(caminho_pasta_zip, caminho_pasta_anos, nomes_arquivos_cgvn, anos_cgvn)

    # EXTRAINDO ARQUIVOS VLMO #
    extracao_docs(caminho_pasta_zip, caminho_pasta_anos, nomes_arquivos_vlmo, anos_cgvn)

    # EXTRAINDO ARQUIVOS IPE #
    extracao_docs(caminho_pasta_zip, caminho_pasta_anos, nomes_arquivos_ipe, anos_itr)

    # EXTRAINDO ARQUIVOS FCA #
    extracao_docs(
        caminho_pasta_zip,
        caminho_pasta_anos,
        nomes_arquivos_fca,
        anos_itr,
        diversos=True,
    )

    # EXTRAINDO ARQUIVOS FRE #
    extracao_docs(
        caminho_pasta_zip,
        caminho_pasta_anos,
        nomes_arquivos_fre,
        anos_itr,
        diversos=True,
    )

    # EXTRAINDO ARQUIVOS DFP #
    for ano in anos_dfp:
        for nome in nomes_arquivos:
            arquivo_dfp = f"{caminho_pasta_zip}\\{nomes_dfp}{nome}{ano}.csv"
            arquivo1 = pd.read_csv(
                arquivo_dfp, sep=";", decimal=",", encoding="ISO-8859-1"
            )
            arquivo1.to_parquet(f"{caminho_pasta_anos}\\{nomes_dfp}{nome}{ano}.parquet")

    # EXTRAINDO ARQUIVOS ITR #
    for ano in anos_itr:
        for nome in nomes_arquivos:
            arquivo_itr = f"{caminho_pasta_zip}\\{nomes_itr}{nome}{ano}.csv"
            if os.path.exists(arquivo_itr):
                arquivo2 = pd.read_csv(
                    arquivo_itr, sep=";", decimal=",", encoding="ISO-8859-1"
                )
                arquivo2.to_parquet(
                    f"{caminho_pasta_anos}\\{nomes_itr}{nome}{ano}.parquet"
                )

    # EXCLUINDO ARQUIVOS ZIP #
    for item in os.listdir(caminho_pasta_zip):
        caminho_item = os.path.join(caminho_pasta_zip, item)
        os.remove(caminho_item)

    print("Extração em Parquet e exclusão de ZIPs concluída.")


if __name__ == "__main__":
    from Baixando_dados import Instalar_Fundamentos_Empresas_BR

    ano_inicial, ano_final, anos_dfp, anos_cgvn, anos_itr = (
        Instalar_Fundamentos_Empresas_BR(diretorio_cvm, diretorio_b3, 2010, geral=True)
    )
    extrair_arquivos_cvm(diretorio_cvm, anos_dfp, anos_cgvn, anos_itr)
    # arquivo1 = r'D:\Downloads\Dados_Fundamentalistas\CVM Empresas BR\vlmo_cia_aberta_con_2024.parquet'
    # df = pd.read_parquet(arquivo1)
