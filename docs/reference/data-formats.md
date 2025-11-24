# Formatos de Dados

Documentação dos formatos de dados utilizados pelo Global-Data-Finance.

---

## Arquivos CVM

### Formato ZIP

Arquivos baixados da CVM são fornecidos em formato ZIP:

```
dfp_cia_aberta_2023.zip
├── dfp_cia_aberta_2023.csv
├── dfp_cia_aberta_BPA_con_2023.csv
├── dfp_cia_aberta_BPP_con_2023.csv
├── dfp_cia_aberta_DRE_con_2023.csv
└── ...
```

### Conversão para Parquet

Com `automatic_extractor=True`, arquivos são convertidos para Parquet:

```
dfp_cia_aberta_2023/
├── dfp_cia_aberta_2023.parquet
├── dfp_cia_aberta_BPA_con_2023.parquet
└── ...
```

**Vantagens do Parquet**:

- ✅ Compressão eficiente (~70% menor)
- ✅ Leitura muito mais rápida
- ✅ Suporte a schemas tipados
- ✅ Compatível com Pandas, Polars, Spark

---

## Arquivos COTAHIST

### Formato Original

Arquivos COTAHIST são TXT com largura fixa:

```
COTAHIST_A2023.ZIP
└── COTAHIST_A2023.TXT (layout de largura fixa)
```

### Formato Parquet Gerado

Global-Data-Finance converte para Parquet com schema estruturado:

**Colunas principais**:

| Coluna                | Tipo      | Descrição           |
| --------------------- | --------- | ------------------- |
| `data`                | `date`    | Data da cotação     |
| `codigo_negociacao`   | `string`  | Ticker (ex: PETR4)  |
| `nome_empresa`        | `string`  | Nome da empresa     |
| `preco_abertura`      | `float64` | Preço de abertura   |
| `preco_maximo`        | `float64` | Preço máximo        |
| `preco_minimo`        | `float64` | Preço mínimo        |
| `preco_fechamento`    | `float64` | Preço de fechamento |
| `volume_negociado`    | `float64` | Volume financeiro   |
| `quantidade_negocios` | `int64`   | Número de negócios  |
| `tipo_mercado`        | `int32`   | Código do mercado   |

---

## Leitura de Dados

### Com Pandas

```python
import pandas as pd

# Ler Parquet
df = pd.read_parquet("cotahist_extracted.parquet")

# Filtrar
petr4 = df[df['codigo_negociacao'] == 'PETR4']

# Análise
print(df.describe())
```

### Com Polars (Recomendado)

```python
import polars as pl

# Ler Parquet (lazy)
df = pl.scan_parquet("cotahist_extracted.parquet")

# Filtrar e coletar
petr4 = df.filter(pl.col('codigo_negociacao') == 'PETR4').collect()

# Muito mais rápido para grandes volumes
```

---

## Estruturas de Resultado

### DownloadResultCVM

```python
@dataclass
class DownloadResultCVM:
    success_count_downloads: int
    error_count_downloads: int
    successful_downloads: Dict[str, List[int]]
    failed_downloads: Dict[str, str]

    def has_errors(self) -> bool:
        return self.error_count_downloads > 0
```

### Resultado de Extração B3

```python
{
    'success': bool,
    'message': str,
    'total_files': int,
    'success_count': int,
    'error_count': int,
    'total_records': int,
    'output_file': str,
    'errors': List[str]
}
```

---

## Tamanhos de Arquivo

### CVM (por ano)

| Documento | ZIP     | Parquet | Compressão |
| --------- | ------- | ------- | ---------- |
| DFP       | ~50 MB  | ~15 MB  | 70%        |
| ITR       | ~200 MB | ~60 MB  | 70%        |
| FRE       | ~100 MB | ~30 MB  | 70%        |

### B3 (por ano)

| Classe | Registros | Parquet |
| ------ | --------- | ------- |
| Ações  | ~250k     | ~100 MB |
| ETF    | ~50k      | ~20 MB  |
| Opções | ~500k     | ~200 MB |

---

Veja também:

- [API CVM](cvm-api.md)
- [API B3](b3-api.md)
- [Exemplos](../user-guide/examples.md)
