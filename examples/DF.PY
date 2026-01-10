import polars as pl

caminho = f'/home/jordan/Downloads/Databases/dados_bolsa_br/Docs_Cvm/ITR/2025/itr_cia_aberta_composicao_capital_2025.parquet'

df = pl.read_parquet(caminho)
