import os
import time

import pandas as pd
import requests
import wget
from Criando_pastas import *
from url_e_nomes import *


def Instalar_Fundamentos_Empresas_BR(
    diretorio_cvm, diretorio_b3, ano_inicial=2010, ano_final=2025, geral=False
):
    caminho_pasta_zip = os.path.join(diretorio_cvm, nome_pasta_zip)
    doc_cias_abertas = os.path.join(diretorio_b3, cias_abertas_doc)

    print(
        "Iniciando atualizações de dados fundamentalistas de companhias brasileiras..."
    )
    # CRIANDO DIRETÓRIOS E EXLCUINDO ARQUIVOS ANTIGOS#
    if geral:
        Criar_Pastas(diretorio_cvm, ano_inicial, ano_final, geral=True)
    else:
        Criar_Pastas(diretorio_cvm, ano_inicial, ano_final)
    print("Iniciando novas instalações...")
    # INICIANDO INSTALAÇÕES DE ARQUIVOS#
    anos_dfp = range(int(ano_inicial), int(ano_final))
    anos_itr = range(int(ano_inicial), int(ano_final) + 1)
    ano_cgvn = 2018 if int(ano_inicial) < 2018 else ano_inicial
    anos_cgvn = range(ano_cgvn, int(ano_final) + 1)
    listas_zip_cgvn = []
    listas_zip_dfp = []
    listas_zip_itr = []
    listas_zip_fre = []
    listas_zip_fca = []
    listas_zip_ipe = []
    listas_zip_vlmo = []
    # ZIPANDO ARQUIVOS#
    for ano in anos_cgvn:
        ano = str(ano)
        listas_zip_cgvn.append(nomes_cgvn + ano + ".zip")
    for ano in anos_itr:
        ano = str(ano)
        listas_zip_fca.append(nomes_fca + ano + ".zip")
    for ano in anos_itr:
        ano = str(ano)
        listas_zip_fre.append(nomes_fre + ano + ".zip")
    for ano in anos_dfp:
        ano = str(ano)
        listas_zip_dfp.append(nomes_dfp + ano + ".zip")
    for ano in anos_itr:
        ano = str(ano)
        listas_zip_itr.append(nomes_itr + ano + ".zip")
    for ano in anos_itr:
        ano = str(ano)
        listas_zip_ipe.append(nomes_ipe + ano + ".zip")
    for ano in anos_cgvn:
        ano = str(ano)
        listas_zip_vlmo.append(nomes_vlmo + ano + ".zip")
    # BAIXANDO DADOS CGVN#
    for arquivo in listas_zip_cgvn:
        try:
            wget.download(url_cgvn + arquivo, out=caminho_pasta_zip)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
    print("Dados de CGVN baixados...")
    time.sleep(0.5)
    # BAIXANDO DADOS FCA#
    for arquivo in listas_zip_fca:
        try:
            wget.download(url_fca + arquivo, out=caminho_pasta_zip)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
    print("Dados de FCA baixados...")
    time.sleep(0.5)
    # BAIXANDO DADOS IPE#
    for arquivo in listas_zip_ipe:
        try:
            wget.download(url_ipe + arquivo, out=caminho_pasta_zip)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
    print("Dados de IPE baixados...")
    time.sleep(0.5)
    # BAIXANDO DADOS VLMO#
    for arquivo in listas_zip_vlmo:
        try:
            wget.download(url_vlmo + arquivo, out=caminho_pasta_zip)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
    print("Dados de VLMO baixados...")
    time.sleep(0.5)
    # BAIXANDO DADOS FRE#
    for arquivo in listas_zip_fre:
        try:
            wget.download(url_fre + arquivo, out=caminho_pasta_zip)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
    print("Dados de FRE baixados...")
    time.sleep(0.5)
    # BAIXANDO DADOS DFP#
    for arquivo in listas_zip_dfp:
        try:
            wget.download(url_dfp + arquivo, out=caminho_pasta_zip)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
    print("Dados de DFPs baixados...")
    time.sleep(0.5)
    # BAIXANDO DADOS ITR#
    for arquivo in listas_zip_itr:
        try:
            if arquivo == "itr_cia_aberta_2010.zip":
                pass
            elif arquivo == "itr_cia_aberta_" + str(datetime.now().year) + ".zip":
                response = requests.head(url_itr + arquivo)
                if response.status_code == 200:
                    wget.download(url_itr + arquivo, out=caminho_pasta_zip)
            else:
                wget.download(url_itr + arquivo, out=caminho_pasta_zip)
        except Exception as e:
            print(f"Erro ao baixar {arquivo}: {e}")
    print("Dados de ITRs baixados...")
    # BAIXANDO ARQUIVO CIAS ABERTAS#
    time.sleep(0.5)
    if os.path.exists(doc_cias_abertas):
        os.remove(doc_cias_abertas)
        print("Arquivo 'cad_cia_aberta.parquet' removido com sucesso.")
    print("Atualizando arquivo CIAS ABERTAS contendo os nomes das empresas.")
    cias = pd.read_csv(url_cias_abertas, sep=";", decimal=",", encoding="ISO-8859-1")
    cias = cias[cias["SIT"] == "ATIVO"]
    cias = cias[
        [
            "CNPJ_CIA",
            "DENOM_SOCIAL",
            "DENOM_COMERC",
            "CD_CVM",
            "DT_INI_SIT",
            "SETOR_ATIV",
            "SIT_EMISSOR",
            "CONTROLE_ACIONARIO",
            "PAIS",
            "UF",
            "MUN",
            "EMAIL",
            "RESP",
            "EMAIL_RESP",
        ]
    ]
    cias.columns = colunas_cias_abertas
    cias["Nome Comercial"] = cias["Nome Comercial"].fillna(cias["Nome Social"])
    cias = cias
    cias.to_parquet(doc_cias_abertas)
    print("CIAS ABERTAS baixado com sucesso!")
    time.sleep(0.5)
    return ano_inicial, ano_final, anos_dfp, anos_cgvn, anos_itr


if __name__ == "__main__":
    df = Instalar_Fundamentos_Empresas_BR(diretorio_cvm, diretorio_b3, 2010)
