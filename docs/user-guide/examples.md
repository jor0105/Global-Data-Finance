# Exemplos Práticos

Esta página apresenta exemplos completos e práticos de uso do Global-Data-Finance em cenários reais.

---

## Exemplo 1: Download Completo de DFP

Baixar demonstrações financeiras padronizadas de empresas brasileiras.

```python
from datafinance import FundamentalStocksDataCVM

# Criar cliente
cvm = FundamentalStocksDataCVM()

# Download de DFP com extração automática
cvm.download(
    destination_path="/home/usuario/dados_financeiros/dfp",
    list_docs=["DFP"],
    initial_year=2020,
    last_year=2023,
    automatic_extractor=True  # Converte para Parquet
)

print("✓ Download e extração concluídos!")
```

---

## Exemplo 2: Extração de Ações e ETFs

Extrair cotações históricas de ações e ETFs com alto desempenho.

```python
from datafinance import HistoricalQuotesB3
import time

# Criar cliente
b3 = HistoricalQuotesB3()

# Medir tempo de execução
start_time = time.time()

# Extrair dados
result = b3.extract(
    path_of_docs="/home/usuario/cotahist",
    assets_list=["ações", "etf"],
    initial_year=2021,
    last_year=2023,
    destination_path="/home/usuario/cotacoes",
    output_filename="acoes_etf_2021_2023",
    processing_mode="fast"
)

elapsed = time.time() - start_time

# Exibir resultados
if result['success']:
    print(f"✓ Extração concluída em {elapsed:.2f}s")
    print(f"  Registros: {result['total_records']:,}")
    print(f"  Throughput: {result['total_records']/elapsed:,.0f} registros/s")
    print(f"  Arquivo: {result['output_file']}")
```

---

## Exemplo 3: Pipeline Completo

Pipeline completo de download CVM e extração B3.

```python
from datafinance import FundamentalStocksDataCVM, HistoricalQuotesB3
import os


# Diretórios
base_dir = "/home/usuario/dados_financeiros"
cvm_dir = os.path.join(base_dir, "cvm")
cotahist_dir = os.path.join(base_dir, "cotahist")
output_dir = os.path.join(base_dir, "processado")

# === ETAPA 1: Download CVM ===
print("=" * 60)
print("ETAPA 1: Download de Documentos CVM")
print("=" * 60)

cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path=cvm_dir,
    list_docs=["DFP", "ITR"],
    initial_year=2022,
    last_year=2023,
    automatic_extractor=True
)

# === ETAPA 2: Extração B3 ===
print("\n" + "=" * 60)
print("ETAPA 2: Extração de Cotações B3")
print("=" * 60)

b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs=cotahist_dir,
    assets_list=["ações", "etf"],
    initial_year=2022,
    last_year=2023,
    destination_path=output_dir,
    output_filename="cotacoes_2022_2023"
)

# === RESUMO ===
print("\n" + "=" * 60)
print("RESUMO FINAL")
print("=" * 60)
print(f"✓ Pipeline concluído!")
print(f"✓ Dados CVM salvos em: {cvm_dir}")
print(f"✓ Cotações B3 salvas em: {result['output_file']}")
```

---

## Exemplo 4: Análise com Pandas

Analisar dados extraídos usando Pandas.

```python
import pandas as pd
from datafinance import HistoricalQuotesB3

# 1. Extrair dados
b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2023,
    output_filename="acoes_2023"
)

# 2. Carregar Parquet
df = pd.read_parquet(result['output_file'])

# 3. Análises básicas
print("=" * 60)
print("ANÁLISE DE DADOS")
print("=" * 60)

print(f"\nTotal de registros: {len(df):,}")
print(f"Período: {df['data'].min()} a {df['data'].max()}")
print(f"Ativos únicos: {df['codigo_negociacao'].nunique()}")

# Top 10 ativos por volume
top_volume = df.groupby('codigo_negociacao')['volume_negociado'].sum().nlargest(10)
print("\nTop 10 ativos por volume:")
for ticker, volume in top_volume.items():
    print(f"  {ticker}: R$ {volume/1e9:.2f}B")

# Estatísticas de preço
print(f"\nEstatísticas de preço de fechamento:")
print(df['preco_fechamento'].describe())
```

---

## Exemplo 5: Processamento com Polars

Usar Polars para processamento de alto desempenho.

```python
import polars as pl
from datafinance import HistoricalQuotesB3

# Extrair dados
b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2020,
    last_year=2023
)

# Carregar com Polars (muito mais rápido que Pandas)
df = pl.read_parquet(result['output_file'])

# Análises com Polars
print(f"Shape: {df.shape}")
print(f"Memória: {df.estimated_size('mb'):.2f} MB")

# Filtrar apenas PETR4
petr4 = df.filter(pl.col('codigo_negociacao') == 'PETR4')

# Calcular retornos diários
petr4 = petr4.with_columns([
    ((pl.col('preco_fechamento') / pl.col('preco_fechamento').shift(1)) - 1)
    .alias('retorno_diario')
])

# Estatísticas
print(f"\nPETR4 - Estatísticas:")
print(f"  Retorno médio diário: {petr4['retorno_diario'].mean():.4%}")
print(f"  Volatilidade: {petr4['retorno_diario'].std():.4%}")
print(f"  Preço mínimo: R$ {petr4['preco_minimo'].min():.2f}")
print(f"  Preço máximo: R$ {petr4['preco_maximo'].max():.2f}")
```

---

## Exemplo 6: Automação com Script

Script completo para automação de downloads.

```python
#!/usr/bin/env python3
"""
Script de automação para download e processamento de dados financeiros.
"""

import argparse
import sys
from pathlib import Path
from datafinance import FundamentalStocksDataCVM, HistoricalQuotesB3

def main():
    parser = argparse.ArgumentParser(description="Download dados financeiros")
    parser.add_argument("--tipo", choices=["cvm", "b3", "ambos"], required=True)
    parser.add_argument("--destino", type=str, required=True)
    parser.add_argument("--ano-inicial", type=int, default=2022)
    parser.add_argument("--ano-final", type=int, default=2023)
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    # Criar diretório de destino
    dest_path = Path(args.destino)
    dest_path.mkdir(parents=True, exist_ok=True)

    try:
        if args.tipo in ["cvm", "ambos"]:
            print("Baixando documentos CVM...")
            cvm = FundamentalStocksDataCVM()
            cvm.download(
                destination_path=str(dest_path / "cvm"),
                list_docs=["DFP", "ITR"],
                initial_year=args.ano_inicial,
                last_year=args.ano_final,
                automatic_extractor=True
            )

        if args.tipo in ["b3", "ambos"]:
            print("Extraindo cotações B3...")
            b3 = HistoricalQuotesB3()
            result = b3.extract(
                path_of_docs=str(dest_path / "cotahist"),
                assets_list=["ações", "etf"],
                initial_year=args.ano_inicial,
                last_year=args.ano_final,
                destination_path=str(dest_path / "cotacoes")
            )

            if result['success']:
                print(f"✓ Extraídos {result['total_records']:,} registros")

        print("✓ Processamento concluído!")
        return 0

    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Uso**:

```bash
# Download apenas CVM
python script.py --tipo cvm --destino /data --ano-inicial 2022

# Download apenas B3
python script.py --tipo b3 --destino /data --ano-inicial 2020 --ano-final 2023

# Download de ambos
python script.py --tipo ambos --destino /data --verbose
```

---

## Exemplo 7: Integração com Jupyter Notebook

Usar Global-Data-Finance em notebooks Jupyter para análise interativa.

```python
# Célula 1: Imports e configuração
from datafinance import HistoricalQuotesB3
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("darkgrid")
%matplotlib inline

# Célula 2: Extrair dados
b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2023
)

# Célula 3: Carregar e filtrar
df = pl.read_parquet(result['output_file'])
petr4 = df.filter(pl.col('codigo_negociacao') == 'PETR4').to_pandas()

# Célula 4: Visualizar
plt.figure(figsize=(14, 6))
plt.plot(petr4['data'], petr4['preco_fechamento'])
plt.title('PETR4 - Preço de Fechamento (2023)', fontsize=16)
plt.xlabel('Data')
plt.ylabel('Preço (R$)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Célula 5: Análise de volume
plt.figure(figsize=(14, 6))
plt.bar(petr4['data'], petr4['volume_negociado'] / 1e6, alpha=0.7)
plt.title('PETR4 - Volume Negociado (2023)', fontsize=16)
plt.xlabel('Data')
plt.ylabel('Volume (Milhões R$)')
plt.tight_layout()
plt.show()
```

---

## Próximos Passos

- 📄 **[Documentos CVM](cvm-docs.md)** - Guia detalhado da API CVM
- 📈 **[Cotações B3](b3-docs.md)** - Guia detalhado da API B3
- ❓ **[FAQ](faq.md)** - Perguntas frequentes
- 🔧 **[Uso Avançado](../dev-guide/advanced-usage.md)** - Técnicas avançadas
