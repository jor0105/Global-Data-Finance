import logging
import os

import pandas as pd
import requests
import time

from globaldatafinance.brazil.b3_data.Dados_B3_Acoes.Funcao_Dados_B3.cookies_acoes import (
    cookies,
    headers,
)
from globaldatafinance.brazil.b3_data.Dados_B3_Acoes.Funcao_Dados_B3.urls import (
    URLS_DADOSB3,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def tratar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza o tratamento dos dados do DataFrame resultante.

    1. Remove a coluna 'typeBDR'.
    2. Converte 'codeCVM', 'cnpj', 'marketIndicator', 'type' para Int64.
    3. Converte 'dateListing' para objeto data.
    """
    if df.empty:
        return df

    # 0. Remoção da coluna segmentEng (solicitado pelo usuário)
    if 'segmentEng' in df.columns:
        df = df.drop(columns=['segmentEng'])

    # 1. Remoção de linhas de BDR e coluna typeBDR
    if 'typeBDR' in df.columns:
        # Excluir linhas que tenham qualquer conteúdo em typeBDR (são BDRs)
        # Mantém apenas onde é NaN/Nulo ou string vazia
        df = df[df['typeBDR'].isna() | (df['typeBDR'] == '')]
        df = df.drop(columns=['typeBDR'])

    # 2. Mudando dados das colunas para int64 (Nullable Int64)
    cols_to_int = ['codeCVM', 'cnpj', 'marketIndicator', 'type']
    for col in cols_to_int:
        if col in df.columns:
            # errors='coerce' transforma valores inválidos em NaN
            # .astype('Int64') permite inteiros com NaN
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    # 3. Mudando a coluna dateListing para date
    if 'dateListing' in df.columns:
        df['dateListing'] = pd.to_datetime(
            df['dateListing'], errors='coerce', format='%d/%m/%Y'
        ).dt.date

    return df


def dados_acoes_b3():
    lista_dfs = []

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # Segundos

    for i, url in enumerate(URLS_DADOSB3, 1):
        logger.info(f"Processando página {i}/{len(URLS_DADOSB3)}...")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url,
                    cookies=cookies,
                    headers=headers,
                )

                if response.status_code != 200:
                    logger.warning(
                        f"Tentativa {attempt}/{MAX_RETRIES} falhou na página {i}: "
                        f"Status {response.status_code}"
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
                    continue

                data = response.json()
                if 'results' in data:
                    df_atual = pd.DataFrame(data['results'])
                    lista_dfs.append(df_atual)
                    logger.info(f"Página {i} processada com sucesso.")
                    logger.debug(f"{len(df_atual)} registros encontrados.")
                    break # Sucesso, sai do loop de tentativas
                else:
                    logger.warning(f"Página {i}: Campo 'results' não encontrado.")
                    break # Resposta válida mas sem dados, não tenta de novo

            except requests.exceptions.JSONDecodeError:
                logger.error(
                    f"Tentativa {attempt}/{MAX_RETRIES} falhou na página {i}: "
                    "Resposta não é um JSON válido."
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Tentativa {attempt}/{MAX_RETRIES} falhou na página {i}: {str(e)}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

        # Delay entre páginas diferentes (opcional, mantendo o original)
        time.sleep(2)

    if not lista_dfs:
        logger.warning("Nenhum dado encontrado.")
        return pd.DataFrame()

    df_final = pd.concat(lista_dfs, ignore_index=True)
    df_final = tratar_dados(df_final)

    # Validação e Salva em Parquet
    if not df_final.empty:
        output_path = "/home/jordan/Downloads/Databases/Documentos_B3/Ações_B3.parquet"
        output_dir = os.path.dirname(output_path)

        try:
            os.makedirs(output_dir, exist_ok=True)
            df_final.to_parquet(output_path, index=False)
            logger.info(f"Arquivo salvo com sucesso em: {output_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar o arquivo: {str(e)}")
    else:
        logger.warning("DataFrame vazio após tratamento. Nenhum arquivo foi gerado.")

    return df_final


if __name__ == "__main__":
    dados_acoes_b3()
