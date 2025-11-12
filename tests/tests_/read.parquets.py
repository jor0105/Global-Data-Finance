import polars as pl

arquivo = pl.read_parquet(
    "/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/Extracted/stocks_etf_2022_2024.parquet"
)
