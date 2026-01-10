import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
from Baixando_dados import *
from Criando_pastas import *
from Extraindo_arquivos import *
from funcoes import *
from url_e_nomes import *


def concatenar_docs(
    diretorio,
    diretorio_b3,
    ano_inicial,
    ano_final,
    ano_cgvn=2018,
    ano_ipe=2024,
    novos=False,
):
    print("Concatenando todos os documentos iguais de anos separados em um só...")

    # ARRUMANDO ARQUIVOS E ORGANIZANDO TUDO EM UM ARQUIVO ÚNICO#
    caminho_pasta_anos = os.path.join(diretorio, nome_pasta_anos)
    caminho_docs_acoes_b3 = os.path.join(diretorio_b3, acoes_b3)
    docs_b3 = pd.read_parquet(caminho_docs_acoes_b3)
    docs_b3["cnpj"] = docs_b3["cnpj"].str.replace(r"\D", "", regex=True).str.zfill(14)
    mapa_cnpj = dict(zip(docs_b3["cnpj"], docs_b3["issuingCompany"]))
    mapa_cvm = dict(zip(docs_b3["codeCVM"], docs_b3["issuingCompany"]))
    mapa_nome = dict(zip(docs_b3["companyName"], docs_b3["issuingCompany"]))
    ano_final2 = ano_final + 1
    if novos:
        print("Concatenando novos arquivos...")
        caminho_pasta = os.path.join(diretorio, nome_pasta_atuais)
        ano_itr = ano_inicial
        ano_cgvn = ano_inicial
        ano_ipe = ano_inicial
    else:
        print("Concatenando arquivos antigos...")
        caminho_pasta = os.path.join(diretorio, nome_pasta_geral)
        ano_itr = 2011 if ano_inicial <= 2011 else ano_inicial

    # ARQUIVOS CGVN #
    data = pd.DataFrame()
    for ano in range(ano_cgvn, ano_final2):
        try:
            arquivo_parquet = (
                f"{caminho_pasta_anos}\\{nomes_arquivos_cgvn}{ano}.parquet"
            )
            arquivo = pd.read_parquet(arquivo_parquet)
            if not arquivo.empty:
                arquivo.drop(["Versao", "ID_Documento"], axis=1, inplace=True)
                arquivo["Data_Referencia"] = pd.to_datetime(
                    arquivo["Data_Referencia"], errors="coerce"
                )
                data = pd.concat([data, arquivo])
        except FileNotFoundError:
            pass
    if not data.empty:
        data["Código"] = 0
        data["CNPJ_Companhia"] = data["CNPJ_Companhia"].str.replace(
            r"\D", "", regex=True
        )
        data["Código"] = data["CNPJ_Companhia"].map(mapa_cnpj)
        mask_na = data["Código"].isna()
        data.loc[mask_na, "Código"] = data.loc[mask_na, "Nome_Empresarial"].map(
            mapa_nome
        )
        data = data.dropna(subset=["Código"])
        data.drop(["Nome_Empresarial", "CNPJ_Companhia"], axis=1, inplace=True)
        data.sort_values(by="Data_Referencia", ascending=False, inplace=True)
        data["Data_Referencia"] = data["Data_Referencia"].dt.strftime("%Y-%m-%d")
        data.to_parquet(
            f"{caminho_pasta}\\{nomes_arquivos_cgvn}{ano_inicial}-{ano_final}.parquet"
        )
        print("Arquivos CGVN foram organizados...")

    # ARQUIVOS IPE #
    if ano_ipe <= ano_final2:
        data = pd.DataFrame()
        for ano in range(ano_ipe, ano_final2):
            try:
                arquivo_parquet = (
                    f"{caminho_pasta_anos}\\{nomes_arquivos_ipe}{ano}.parquet"
                )
                arquivo = pd.read_parquet(arquivo_parquet)
                if not arquivo.empty:
                    arquivo.drop(
                        ["Versao", "Protocolo_Entrega", "Data_Referencia"],
                        axis=1,
                        inplace=True,
                    )
                    arquivo["Data_Entrega"] = pd.to_datetime(
                        arquivo["Data_Entrega"], errors="coerce"
                    )
                    data = pd.concat([data, arquivo])
            except Exception as e:
                print("Erro ao processar o arquivo IPE:", e)
        if not data.empty:
            data["Código"] = 0
            data["CNPJ_Companhia"] = data["CNPJ_Companhia"].str.replace(
                r"\D", "", regex=True
            )
            data["Código"] = data["Codigo_CVM"].map(mapa_cvm)
            mask_na = data["Código"].isna()
            data.loc[mask_na, "Código"] = data.loc[mask_na, "CNPJ_Companhia"].map(
                mapa_cnpj
            )
            data = data.dropna(subset=["Código"])
            data.drop(
                ["Nome_Companhia", "CNPJ_Companhia", "Codigo_CVM"], axis=1, inplace=True
            )
            data.sort_values(by="Data_Entrega", ascending=False, inplace=True)
            data["Data_Entrega"] = data["Data_Entrega"].dt.strftime("%Y-%m-%d")
            data.to_parquet(
                f"{caminho_pasta}\\{nomes_arquivos_ipe}{ano_inicial}-{ano_final}.parquet"
            )
            print("Arquivos IPE foram organizados...")
    else:
        print(
            "Arquivos IPE não foram organizados pois não existem dados até a data detalhada..."
        )

    # ARQUIVOS VLMO #
    data = pd.DataFrame()
    for ano in range(ano_cgvn, ano_final2):
        try:
            arquivo_parquet = (
                f"{caminho_pasta_anos}\\{nomes_arquivos_vlmo}{ano}.parquet"
            )
            arquivo = pd.read_parquet(arquivo_parquet)
            if not arquivo.empty:
                arquivo.drop(
                    ["Versao", "Preco_Unitario", "Volume"], axis=1, inplace=True
                )
                arquivo["Data_Movimentacao"] = pd.to_datetime(
                    arquivo["Data_Movimentacao"], errors="coerce"
                )
                data = pd.concat([data, arquivo])
        except FileNotFoundError:
            pass
    if not data.empty:
        data["CNPJ_Companhia"] = data["CNPJ_Companhia"].str.replace(
            r"\D", "", regex=True
        )
        data["Código"] = 0
        data["Código"] = data["CNPJ_Companhia"].map(mapa_cnpj)
        mask_na = data["Código"].isna()
        data.loc[mask_na, "Código"] = data.loc[mask_na, "Empresa"].map(mapa_nome)
        data = data.dropna(subset=["Código"])
        data.drop(["CNPJ_Companhia", "Data_Referencia"], axis=1, inplace=True)
        data.sort_values(by="Data_Movimentacao", ascending=False, inplace=True)
        data["Quantidade"] = data["Quantidade"].apply(
            lambda x: (
                f"{float(x):,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
                if pd.notnull(x)
                else ""
            )
        )
        data.to_parquet(
            f"{caminho_pasta}\\{nomes_arquivos_vlmo}{ano_inicial}-{ano_final}.parquet"
        )
        print("Arquivos VLMO foram organizados...")
    else:
        print(
            "Arquivos VLMO não foram organizados pois não existem dados até a data detalhada..."
        )

    # ARQUIVOS FCA #
    for nome in nomes_arquivos_fca:
        data = pd.DataFrame()
        for ano in range(ano_itr, ano_final2):
            try:
                arquivo_parquet = f"{caminho_pasta_anos}\\{nome}{ano}.parquet"
                arquivo = pd.read_parquet(arquivo_parquet)
                if not arquivo.empty:
                    arquivo["Data_Referencia"] = pd.to_datetime(
                        arquivo["Data_Referencia"], errors="coerce"
                    )
                    if nome == "fca_cia_aberta_geral_":
                        arquivo.drop(
                            [
                                "Data_Nome_Empresarial",
                                "Data_Categoria_Registro_CVM",
                                "Situacao_Registro_CVM",
                                "Data_Situacao_Registro_CVM",
                                "Data_Situacao_Emissor",
                                "Data_Especie_Controle_Acionario",
                                "Data_Alteracao_Exercicio_Social",
                            ],
                            axis=1,
                            inplace=True,
                        )
                    elif nome == "fca_cia_aberta_valor_mobiliario_":
                        arquivo.drop(
                            [
                                "Sigla_Classe_Acao_Preferencial",
                                "Classe_Acao_Preferencial",
                                "Sigla_Entidade_Administradora",
                                "Data_Fim_Negociacao",
                            ],
                            axis=1,
                            inplace=True,
                        )
                    elif nome == "fca_cia_aberta_canal_divulgacao_":
                        arquivo["Versao"] = pd.to_numeric(
                            arquivo["Versao"], errors="coerce"
                        )
                        arquivo = arquivo.sort_values(by="Versao", ascending=False)
                        arquivo = arquivo.drop_duplicates(
                            subset=["Canal_Divulgacao", "Data_Referencia"], keep="first"
                        )
                        arquivo.drop(["Versao", "Sigla_UF"], axis=1, inplace=True)
                    elif nome == "fca_cia_aberta_endereco_":
                        arquivo["Versao"] = pd.to_numeric(
                            arquivo["Versao"], errors="coerce"
                        )
                        arquivo = arquivo.sort_values(by="Versao", ascending=False)
                        arquivo = arquivo.drop_duplicates(
                            subset=["Tipo_Endereco", "Complemento"], keep="first"
                        )
                        arquivo.drop(
                            ["Versao", "Caixa_Postal", "DDI_Fax", "DDD_Fax", "Fax"],
                            axis=1,
                            inplace=True,
                        )
                    arquivo.drop("ID_Documento", axis=1, inplace=True)
                    data = pd.concat([data, arquivo])
            except FileNotFoundError:
                pass
        if not data.empty:
            data = organizar_geral3(data, reverter=True)
            data["Código"] = 0
            if nome in ["fca_cia_aberta_canal_divulgacao_", "fca_cia_aberta_endereco_"]:
                datas_unicas = data["Data_Referencia"].dropna().unique()
                datas_unicas = sorted(datas_unicas, reverse=True)
                if len(datas_unicas) >= 2:
                    data = data[data["Data_Referencia"] >= datas_unicas[1]]
            data["CNPJ_Companhia"] = data["CNPJ_Companhia"].str.replace(
                r"\D", "", regex=True
            )
            data["Código"] = data["CNPJ_Companhia"].map(mapa_cnpj)
            mask_na = data["Código"].isna()
            data.loc[mask_na, "Código"] = data.loc[mask_na, "Nome_Empresarial"].map(
                mapa_nome
            )
            data = data.dropna(subset=["Código"])
            data.drop(["CNPJ_Companhia"], axis=1, inplace=True)
            data.sort_values(by="Data_Referencia", ascending=False, inplace=True)
            data.to_parquet(f"{caminho_pasta}\\{nome}{ano_inicial}-{ano_final}.parquet")
    print("Arquivos FCA foram organizados...")

    # ARQUIVOS FRE #
    for nome in nomes_arquivos_fre:
        data = pd.DataFrame()
        for ano in range(ano_itr, ano_final2):
            try:
                arquivo_parquet = f"{caminho_pasta_anos}\\{nome}{ano}.parquet"
                arquivo = pd.read_parquet(arquivo_parquet)
                if not arquivo.empty:
                    if "Descricao_Outro_Cargo_Ocupado" in arquivo.columns:
                        arquivo["Descricao_Outro_Cargo_Ocupado"] = arquivo[
                            "Descricao_Outro_Cargo_Ocupado"
                        ].astype(str)
                    if nome == "fre_cia_aberta_membro_comite_":
                        arquivo["Percentual_Participacao_Reunioes"] = pd.to_numeric(
                            arquivo["Percentual_Participacao_Reunioes"], errors="coerce"
                        )
                        arquivo.drop(
                            ["Descricao_Outro_Cargo_Ocupado", "Data_Nascimento"],
                            axis=1,
                            inplace=True,
                        )
                    elif nome == "fre_cia_aberta_membro_comite_auditor_":
                        arquivo["Data_Nascimento"] = pd.to_datetime(
                            arquivo["Data_Nascimento"], errors="coerce"
                        )
                        arquivo.drop(
                            ["Descricao_Outro_Cargo_Ocupado"], axis=1, inplace=True
                        )
                    elif nome == "fre_cia_aberta_remuneracao_total_orgao_":
                        arquivo["Data_Fim_Exercicio_Social"] = pd.to_datetime(
                            arquivo["Data_Fim_Exercicio_Social"]
                        )
                        arquivo.drop("Data_Referencia", axis=1, inplace=True)
                        arquivo = arquivo[
                            pd.to_numeric(
                                arquivo["Numero_Membros_Remunerados"], errors="coerce"
                            )
                            > 0
                        ]
                        arquivo.sort_values(
                            by="Data_Fim_Exercicio_Social",
                            ascending=False,
                            inplace=True,
                        )
                        arquivo["Data_Fim_Exercicio_Social"] = arquivo[
                            "Data_Fim_Exercicio_Social"
                        ].dt.strftime("%Y-%m-%d")
                    elif nome == "fre_cia_aberta_titulo_exterior_":
                        arquivo["Data_Vencimento"] = pd.to_datetime(
                            arquivo["Data_Vencimento"], errors="coerce"
                        )
                        hoje = pd.to_datetime(datetime.today().date())
                        arquivo = arquivo[arquivo["Data_Vencimento"] >= hoje]
                        arquivo.drop("Data_Referencia", axis=1, inplace=True)
                        arquivo["Data_Vencimento"] = arquivo[
                            "Data_Vencimento"
                        ].dt.strftime("%Y-%m-%d")
                    elif nome == "fre_cia_aberta_capital_social_titulo_conversivel_":
                        arquivo.drop(["ID_Capital_Social"], axis=1, inplace=True)
                    elif nome == "fre_cia_aberta_participacao_sociedade_":
                        arquivo = arquivo[
                            [
                                "Data_Referencia",
                                "CNPJ_Companhia",
                                "Nome_Companhia",
                                "Razao_Social",
                                "CNPJ",
                                "Participacao_Emissor",
                            ]
                        ]
                        arquivo["CNPJ"] = arquivo["CNPJ"].astype(str)
                        arquivo["Participacao_Emissor"] = (
                            arquivo["Participacao_Emissor"]
                            .str.replace(",", ".")
                            .astype(float)
                            .apply(lambda x: "{:.2f}%".format(x))
                        )
                    elif nome == "fre_cia_aberta_auditor_":
                        arquivo.drop(["ID_Auditor"], axis=1, inplace=True)
                    elif nome == "fre_cia_aberta_capital_social_":
                        arquivo.drop(
                            ["ID_Capital_Social", "Prazo_Integralizacao"],
                            axis=1,
                            inplace=True,
                        )
                        arquivo["Quantidade_Acoes_Ordinarias"] = arquivo[
                            "Quantidade_Acoes_Ordinarias"
                        ].astype(float)
                        arquivo["Quantidade_Acoes_Preferenciais"] = arquivo[
                            "Quantidade_Acoes_Preferenciais"
                        ].astype(float)
                        arquivo["Quantidade_Total_Acoes"] = arquivo[
                            "Quantidade_Total_Acoes"
                        ].astype(float)
                        arquivo["Data_Referencia"] = pd.to_datetime(
                            arquivo["Data_Referencia"], errors="coerce"
                        )
                        arquivo["Data_Autorizacao_Aprovacao"] = pd.to_datetime(
                            arquivo["Data_Autorizacao_Aprovacao"], errors="coerce"
                        )
                        arquivo["Valor_Capital"] = arquivo["Valor_Capital"].astype(
                            float
                        )
                        arquivo["Quantidade_Total_Acoes"] = (
                            arquivo["Quantidade_Acoes_Ordinarias"]
                            + arquivo["Quantidade_Acoes_Preferenciais"]
                        )
                        mask2 = (
                            arquivo["Data_Referencia"]
                            < arquivo["Data_Autorizacao_Aprovacao"]
                        )
                        arquivo.loc[mask2, "Data_Referencia"] = arquivo.loc[
                            mask2, "Data_Autorizacao_Aprovacao"
                        ]
                    elif nome == "fre_cia_aberta_distribuicao_capital_":
                        arquivo = arquivo[
                            [
                                "CNPJ_Companhia",
                                "Data_Referencia",
                                "Nome_Companhia",
                                "Quantidade_Acionistas_PF",
                                "Quantidade_Acionistas_PJ",
                                "Quantidade_Acionistas_Investidores_Institucionais",
                                "Percentual_Acoes_Ordinarias_Circulacao",
                                "Percentual_Acoes_Preferenciais_Circulacao",
                                "Percentual_Total_Acoes_Circulacao",
                                "Data_Ultima_Assembleia",
                            ]
                        ]
                        arquivo["Total de Investidores"] = (
                            arquivo["Quantidade_Acionistas_PJ"]
                            + arquivo["Quantidade_Acionistas_PF"]
                            + arquivo[
                                "Quantidade_Acionistas_Investidores_Institucionais"
                            ]
                        )
                        arquivo["Percentual_Acoes_Ordinarias_Circulacao"] = (
                            arquivo["Percentual_Acoes_Ordinarias_Circulacao"]
                            .str.replace(",", ".")
                            .astype(float)
                            .apply(lambda x: "{:.2f}%".format(x))
                        )
                        arquivo["Percentual_Acoes_Preferenciais_Circulacao"] = (
                            arquivo["Percentual_Acoes_Preferenciais_Circulacao"]
                            .str.replace(",", ".")
                            .astype(float)
                            .apply(lambda x: "{:.2f}%".format(x))
                        )
                        arquivo["Percentual_Total_Acoes_Circulacao"] = (
                            arquivo["Percentual_Total_Acoes_Circulacao"]
                            .str.replace(",", ".")
                            .astype(float)
                            .apply(lambda x: "{:.2f}%".format(x))
                        )
                    elif nome == "fre_cia_aberta_posicao_acionaria_":
                        arquivo.fillna(np.nan, inplace=True)
                        for col in [
                            "Quantidade_Acao_Ordinaria_Circulacao",
                            "Quantidade_Acao_Preferencial_Circulacao",
                            "Quantidade_Total_Acoes_Circulacao",
                        ]:
                            arquivo[col] = (
                                arquivo[col]
                                .astype(str)
                                .str.replace(r"\.", "", regex=True)
                                .str.replace(",", ".", regex=False)
                                .astype(float)
                            )
                        arquivo = arquivo[
                            arquivo["Quantidade_Total_Acoes_Circulacao"] > 0
                        ]
                        arquivo["Percentual_Total_Acoes_Circulacao"] = arquivo[
                            "Percentual_Total_Acoes_Circulacao"
                        ].apply(
                            lambda x: (
                                (
                                    f"{float(x):,.1f}".replace(",", "v")
                                    .replace(".", ",")
                                    .replace("v", ".")
                                    + "%"
                                )
                                if pd.notnull(x) and float(x) < 100
                                else ""
                            )
                        )
                        arquivo = arquivo[
                            arquivo["Percentual_Total_Acoes_Circulacao"] != ""
                        ]
                        arquivo["Percentual_Acao_Ordinaria_Circulacao"] = arquivo[
                            "Percentual_Acao_Ordinaria_Circulacao"
                        ].apply(
                            lambda x: (
                                f"{float(x):,.1f}".replace(",", "v")
                                .replace(".", ",")
                                .replace("v", ".")
                                + "%"
                                if pd.notnull(x)
                                else ""
                            )
                        )
                        arquivo["Percentual_Acao_Preferencial_Circulacao"] = arquivo[
                            "Percentual_Acao_Preferencial_Circulacao"
                        ].apply(
                            lambda x: (
                                f"{float(x):,.1f}".replace(",", "v")
                                .replace(".", ",")
                                .replace("v", ".")
                                + "%"
                                if pd.notnull(x)
                                else ""
                            )
                        )
                        arquivo["Acionista"] = arquivo.apply(
                            lambda row: (
                                row["Acionista_Relacionado"]
                                if pd.notna(row["Acionista_Relacionado"])
                                and str(row["Acionista_Relacionado"]).strip() != ""
                                and row["Acionista"] in ["Outros", "Ações Tesouraria"]
                                else row["Acionista"]
                            ),
                            axis=1,
                        )
                        arquivo["CPF_CNPJ_Acionista"] = arquivo.apply(
                            lambda row: (
                                row["CPF_CNPJ_Acionista_Relacionado"]
                                if pd.isna(row["CPF_CNPJ_Acionista"])
                                and pd.notna(row["CPF_CNPJ_Acionista_Relacionado"])
                                and str(row["CPF_CNPJ_Acionista_Relacionado"]).strip()
                                != ""
                                else row["CPF_CNPJ_Acionista"]
                            ),
                            axis=1,
                        )
                        arquivo["Tipo_Pessoa_Acionista"] = arquivo.apply(
                            lambda row: (
                                row["Tipo_Pessoa_Acionista_Relacionado"]
                                if pd.isna(row["Tipo_Pessoa_Acionista"])
                                and pd.notna(row["Tipo_Pessoa_Acionista_Relacionado"])
                                and str(
                                    row["Tipo_Pessoa_Acionista_Relacionado"]
                                ).strip()
                                != ""
                                else row["Tipo_Pessoa_Acionista"]
                            ),
                            axis=1,
                        )
                        arquivo["Versao"] = pd.to_numeric(
                            arquivo["Versao"], errors="coerce"
                        )
                        arquivo = arquivo.sort_values(by="Versao", ascending=False)
                        arquivo.drop(
                            [
                                "ID_Acionista",
                                "ID_Documento",
                                "ID_Acionista_Relacionado",
                                "Sigla_UF",
                                "Versao",
                                "Acionista_Relacionado",
                                "Tipo_Pessoa_Acionista_Relacionado",
                                "CPF_CNPJ_Acionista_Relacionado",
                            ],
                            axis=1,
                            inplace=True,
                        )
                        arquivo.drop_duplicates(inplace=True)
                    elif nome == "fre_cia_aberta_capital_social_aumento_":
                        arquivo.drop(
                            ["ID_Capital_Social_Aumento"], axis=1, inplace=True
                        )
                    arquivo = organizar_geral3(arquivo)
                    data = pd.concat([data, arquivo])
            except FileNotFoundError:
                pass
        if nome in lista_atual:
            data = organizar_geral3(data, reverter=True)
        try:
            if not data.empty:
                data["Código"] = 0
                if nome in ["fre_cia_aberta_relacao_familiar_"]:
                    datas_unicas = data["Data_Referencia"].dropna().unique()
                    datas_unicas = sorted(datas_unicas, reverse=True)
                    if len(datas_unicas) >= 2:
                        data = data[data["Data_Referencia"] >= datas_unicas[1]]
                data["CNPJ_Companhia"] = data["CNPJ_Companhia"].str.replace(
                    r"\D", "", regex=True
                )
                data["Código"] = data["CNPJ_Companhia"].map(mapa_cnpj)
                mask_na = data["Código"].isna()
                data.loc[mask_na, "Código"] = data.loc[mask_na, "Nome_Companhia"].map(
                    mapa_nome
                )
                data = data.dropna(subset=["Código"])
                data.drop(["Nome_Companhia", "CNPJ_Companhia"], axis=1, inplace=True)
                data = arrumar_valor_numerico(data)
                data.to_parquet(
                    f"{caminho_pasta}\\{nome}{ano_inicial}-{ano_final}.parquet"
                )
        except Exception as e:
            print(f"Erro ao salvar: {nome} | Erro: {e}")
    print("Arquivos FRE foram organizados...")
