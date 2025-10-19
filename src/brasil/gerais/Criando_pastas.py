import os
import time

from url_e_nomes import *


def Criar_Pastas(diretorio, ano_inicial, ano_final, geral=False):
    caminho_pasta_anos = os.path.join(diretorio, nome_pasta_anos)
    caminho_pasta_geral = os.path.join(diretorio, nome_pasta_geral)
    caminho_pasta_atuais = os.path.join(diretorio, nome_pasta_atuais)
    caminho_pasta_zip = os.path.join(diretorio, nome_pasta_zip)

    # CRIANDO PASTA DE DOCUMENTOS PARQUET #
    if os.path.isdir(caminho_pasta_anos):
        for item in os.listdir(caminho_pasta_anos):
            caminho_item = os.path.join(caminho_pasta_anos, item)
            ano_arquivo = item.split("_")[-1].split(".")[0]
            for i in range(int(ano_inicial), int(ano_final) + 1):
                if str(i) == ano_arquivo:
                    os.remove(caminho_item)
        print(
            f"Documentos antigos únicos do ano {ano_inicial} até {ano_final} foram excluídos com sucesso."
        )
    else:
        print(f"A pasta {nome_pasta_anos} não foi encontrada. Criando...")
        time.sleep(1)
        os.makedirs(caminho_pasta_anos)
        print(f"Pasta {nome_pasta_anos} criada com sucesso.")
    time.sleep(0.5)

    # CRIANDO PASTA DE DOCUMENTOS ANTIGOS #
    if os.path.isdir(caminho_pasta_geral):
        if geral:
            for item in os.listdir(caminho_pasta_geral):
                caminho_item = os.path.join(caminho_pasta_geral, item)
                os.remove(caminho_item)
            print(
                f"Documentos fundamentalistas antigos gerais do ano 2010 até {ano_final} foram excluídos com sucesso."
            )
    else:
        print(f"A pasta {nome_pasta_geral} não foi encontrada. Criando...")
        time.sleep(1)
        os.makedirs(caminho_pasta_geral)
        print(f"Pasta {nome_pasta_geral} criada com sucesso.")
    time.sleep(0.5)

    # CRIANDO PASTA DE DOCUMENTOS ATUAIS #
    if os.path.isdir(caminho_pasta_atuais):
        for item in os.listdir(caminho_pasta_atuais):
            caminho_item = os.path.join(caminho_pasta_atuais, item)
            os.remove(caminho_item)
        print(
            f"Documentos fundamentalistas do ano {ano_inicial} até {ano_final} foram excluídos com sucesso."
        )
    else:
        print(f"A pasta {nome_pasta_atuais} não foi encontrada. Criando...")
        time.sleep(1)
        os.makedirs(caminho_pasta_atuais)
        print(f"Pasta {nome_pasta_atuais} criada com sucesso.")
    time.sleep(0.5)

    # CRIANDO PASTA DE DOCUMENTOS DE ZIPS #
    if os.path.isdir(caminho_pasta_zip):
        for item in os.listdir(caminho_pasta_zip):
            caminho_item = os.path.join(caminho_pasta_zip, item)
            os.remove(caminho_item)
        print("Documentos da pasta de zips foram excluídos.")
    else:
        print(f"A pasta {nome_pasta_zip} não foi encontrada. Criando...")
        time.sleep(1)
        os.makedirs(caminho_pasta_zip)
        print(f"Pasta {nome_pasta_zip} criada com sucesso.")
    time.sleep(0.5)
