import pandas as pd

# (posição_inicial - 1, posição_final)
col_specs = [
    (0, 2),  # TIPREG: Tipo de Registro
    (2, 10),  # DATPREG: Data do Pregão
    (10, 12),  # CODBDI: Código BDI
    (12, 24),  # CODNEG: Ticker (Código de Negociação)
    (24, 27),  # TPMERC: Tipo de Mercado
    (27, 39),  # NOMRES: Nome Resumido da Empresa
    (39, 49),  # ESPECI: Especificação do Papel
    (56, 69),  # PREABE: Preço de Abertura
    (69, 82),  # PREMAX: Preço Máximo
    (82, 95),  # PREMIN: Preço Mínimo
    (108, 121),  # PREULT: Preço de Fechamento (Último)
    (152, 170),  # QUATOT: Quantidade Total de Títulos Negociados
    (170, 188),  # VOLTOT: Volume Total de Títulos Negociados
]

# Nomes correspondentes para as colunas
col_names = [
    "TIPREG",
    "DATPREG",
    "CODBDI",
    "CODNEG",
    "TPMERC",
    "NOMRES",
    "ESPECI",
    "PREABE",
    "PREMAX",
    "PREMIN",
    "PREULT",
    "QUATOT",
    "VOLTOT",
]


# Caminho para o seu arquivo descompactado
# (Exemplo usa o arquivo de 2024 que analisamos)
filepath = "/home/jordan/Downloads/COTAHIST_A2024.TXT"

# --- ETAPA 2: LEITURA DO ARQUIVO ---
# Lemos o arquivo de largura fixa (fwf)
# É crucial ler tudo como string (dtype=str) para evitar erros
# de conversão automática, especialmente nos códigos.
try:
    df_raw = pd.read_fwf(
        filepath,
        colspecs=col_specs,
        names=col_names,
        header=None,
        dtype=str,  # Importante: ler tudo como texto primeiro
    )
except FileNotFoundError:
    print(f"Erro: Arquivo '{filepath}' não encontrado.")
    # Adicione aqui o tratamento de erro apropriado
    exit()


# --- ETAPA 3: FILTRAGEM PARA AÇÕES ---

# 1. Manter apenas registros de dados (Tipo '01')
#    Isso remove o Header (Tipo '00') e o Trailer (Tipo '99')
df_data = df_raw[df_raw["TIPREG"] == "01"].copy()

# 2. Filtrar pelo Tipo de Mercado (TPMERC)
#    De acordo com o layout (página 9), '010' é 'CASH' (Mercado à Vista)[cite: 92].
#    Isso remove Opções ('070', '080'), Termo ('030'), etc.
df_vista = df_data[df_data["TPMERC"] == "010"]

# 3. Filtrar pelo Código BDI (CODBDI)
#    Este é o filtro final. De acordo com o layout (página 6):
#    - '02' é 'ROUND LOT' (Lote Padrão).
#    - '96' é 'FACTIONARY' (Mercado Fracionário).
#    - Outros códigos ('12', '14', etc.) são FIIs, BDRs, Debêntures.
#
#    Para obter "apenas ações" no sentido estrito, usamos '02'.
df_stocks = df_vista[df_vista["CODBDI"] == "02"].copy()


# --- ETAPA 4: LIMPEZA E CONVERSÃO DOS DADOS ---

# 1. Converter colunas de PREÇO e VOLUME
#    O layout indica que todos os preços são (11)V99 ou (16)V99.
#    Isso significa que são inteiros e devem ser divididos por 100.
price_cols = ["PREABE", "PREMAX", "PREMIN", "PREULT", "VOLTOT"]
for col in price_cols:
    df_stocks[col] = pd.to_numeric(df_stocks[col]) / 100.0

# 2. Converter QUATOT (Quantidade) para numérico
df_stocks["QUATOT"] = pd.to_numeric(df_stocks["QUATOT"])

# 3. Converter a Data do Pregão para o formato datetime
df_stocks["DATPREG"] = pd.to_datetime(df_stocks["DATPREG"], format="%Y%m%d")

# 4. Limpar espaços em branco dos tickers e nomes
df_stocks["CODNEG"] = df_stocks["CODNEG"].str.strip()
df_stocks["NOMRES"] = df_stocks["NOMRES"].str.strip()
df_stocks["ESPECI"] = df_stocks["ESPECI"].str.strip()

# --- RESULTADO ---
print("DataFrame final de Ações (Lote Padrão):")
print(df_stocks.head())

print("\nInformações do DataFrame:")
df_stocks.info()

# Salvar em um formato eficiente (opcional)
# df_stocks.to_parquet('acoes_2024.parquet', index=False)
# df_stocks.to_csv('acoes_2024.csv', index=False)
