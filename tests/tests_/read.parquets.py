import polars as pl

arquivo = pl.read_parquet(
    "/home/jordan/Downloads/Databases/dados_bolsa_br/COTAHIST/cotahist_acoes_2024.parquet"
)
