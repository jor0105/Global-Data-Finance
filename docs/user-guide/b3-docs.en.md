# B3 Historical Quotes

Complete user documentation guide for employing the `HistoricalQuotesB3` API to parse and process official historical market exchange COTAHIST archives from B3 (Brazilian Stock Exchange).

______________________________________________________________________

## Overview

The `HistoricalQuotesB3` class provides a high-performance engine capable of ingesting official COTAHIST bundle archives from B3, extracting precise historical transactions across diverse market asset classes, and compiling them directly into columnar Apache Parquet storage.

### Highlights

- ✅ Targeted extraction spanning multiple exchange asset classes
- ✅ Dual processing engines (in-memory `fast` and incremental `slow` mode)
- ✅ Automatic structural type normalization into Apache Parquet
- ✅ Deep historical compatibility dating back to fiscal year **1986**
- ✅ Granular asset filtering syntax to exclude unnecessary instrument types
- ✅ Comprehensive execution tracking and diagnostic console outputs

______________________________________________________________________

## Supported Asset Categories

B3 archives historical financial transactions under the following standard categories:

| Parameter Keyword    | Professional Classification  | Included Sub-Market Classifications           |
| -------------------- | ---------------------------- | --------------------------------------------- |
| **ações**            | Stocks & Equities            | Spot market (010) and fractional market (012) |
| **etf**              | Exchange Traded Funds (ETFs) | Exchange Traded Fund instruments              |
| **opções**           | Options Contracts            | Option Calls (070) and Option Puts (080)      |
| **termo**            | Forward Term Contracts       | Term financial agreements                     |
| **exercicio_opcoes** | Option Exercises             | Option execution transaction registers        |
| **forward**          | Forward Contracts            | Over-the-counter and forward agreements       |
| **leilao**           | Auction Market Records       | Extraordinary auction clearing executions     |

!!! info "Historical Depth"
B3 COTAHIST historical quote archives cover market transaction activity continuously from **1986** through the present day.

______________________________________________________________________

## Basic Usage

### Library Import

```python
from globaldatafinance import HistoricalQuotesB3
```

### Instantiate Public Client

```python
b3 = HistoricalQuotesB3()
```

### Simple Extraction Example

```python
# Extract historical stock quotes from current year archives
result = b3.extract(
    path_of_docs="/home/user/cotahist_zips",
    assets_list=["ações"],
    initial_year=2023
)

print(f"✓ Successfully processed and consolidated {result['total_records']:,} transaction records")
```

______________________________________________________________________

## Core Public Methods

### `extract()`

Parses COTAHIST archives (ZIP bundles or plain positional TXT files) and exports filtered records into a unified Parquet file.

#### Method Signature

```python
def extract(
    self,
    path_of_docs: str,
    assets_list: List[str],
    initial_year: Optional[int] = None,
    last_year: Optional[int] = None,
    destination_path: Optional[str] = None,
    output_filename: str = "cotahist_extracted",
    processing_mode: str = "fast",
) -> Dict[str, Any]
```

#### Parameters

| Parameter          | Type        | Mandatory | Description                                                        |
| ------------------ | ----------- | --------- | ------------------------------------------------------------------ |
| `path_of_docs`     | `str`       | ✅ Yes    | Filesystem path pointing to raw COTAHIST archives                  |
| `assets_list`      | `List[str]` | ✅ Yes    | Selected asset filtering category strings                          |
| `initial_year`     | `int`       | ❌ No     | Starting historical year (default: 1986)                           |
| `last_year`        | `int`       | ❌ No     | Ending historical year (default: current system year)              |
| `destination_path` | `str`       | ❌ No     | Destination output directory (default: matches `path_of_docs`)     |
| `output_filename`  | `str`       | ❌ No     | Base filename of the target Parquet artifact (omit file extension) |
| `processing_mode`  | `str`       | ❌ No     | Execution concurrency profile: `"fast"` or `"slow"`                |

#### Return Contract

A typed diagnostic mapping dictionary (`ExtractionResultB3`) containing the following entries:

| Dictionary Key  | Type        | Description                                         |
| --------------- | ----------- | --------------------------------------------------- |
| `success`       | `bool`      | `True` if extraction pipeline completed cleanly     |
| `message`       | `str`       | Human-readable summary of the execution outcome     |
| `total_files`   | `int`       | Total count of COTAHIST archives evaluated          |
| `success_count` | `int`       | Number of archives successfully parsed and merged   |
| `error_count`   | `int`       | Number of archives encountering format exceptions   |
| `total_records` | `int`       | Cumulative count of consolidated Parquet records    |
| `output_file`   | `str`       | Absolute filesystem path of the produced `.parquet` |
| `errors`        | `List[str]` | Detailed stack traces or validation failure notes   |

#### Usage Examples

**Example 1: Core Stock Extraction**

```python
b3 = HistoricalQuotesB3()

result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2022,
    last_year=2023
)

if result['success']:
    print(f"✓ Generated Parquet file: {result['output_file']}")
    print(f"✓ Total consolidated rows: {result['total_records']:,}")
```

**Example 2: Multi-Asset Ingestion**

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf", "opções"],
    initial_year=2020,
    last_year=2023,
    output_filename="multi_assets_2020_2023"
)
```

**Example 3: Low-Footprint Background Execution**

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2023,
    processing_mode="slow"  # Minimizes active system memory footprint
)
```

**Example 4: Custom Export Routing**

```python
result = b3.extract(
    path_of_docs="/data/cotahist_zips",
    destination_path="/data/processed_quotes",
    assets_list=["ações", "etf"],
    initial_year=2023,
    output_filename="stocks_etf_2023"
)
# Resulting artifact persisted at: /data/processed_quotes/stocks_etf_2023.parquet
```

______________________________________________________________________

### `get_available_assets()`

Returns an exhaustive list of valid asset string identifiers supported by the extraction filters.

#### Method Signature

```python
def get_available_assets(self) -> List[str]
```

#### Return Value

A list containing permissible asset filtering strings.

#### Example Execution

```python
b3 = HistoricalQuotesB3()
assets = b3.get_available_assets()

print("Supported asset categories:")
for asset in assets:
    print(f"  • {asset}")
```

**Console Output**:

```
Supported asset categories:
  • ações
  • etf
  • opções
  • termo
  • exercicio_opcoes
  • forward
  • leilao
```

______________________________________________________________________

### `get_available_years()`

Returns dictionary containing extreme boundaries of supported historical time horizons.

#### Method Signature

```python
def get_available_years(self) -> Dict[str, int]
```

#### Return Value

A dictionary detailing:

| Key              | Description                           |
| ---------------- | ------------------------------------- |
| `"minimal_year"` | Earliest supported fiscal year (1986) |
| `"current_year"` | Real-time system operational year     |

#### Example Execution

```python
b3 = HistoricalQuotesB3()
years = b3.get_available_years()

print(f"B3 market archives available from {years['minimal_year']} through {years['current_year']}")
```

______________________________________________________________________

## Processing Execution Modes

The extraction pipeline provides distinct computational operational modes:

### Fast Mode (Default) ⚡

- **Performance Profile**: Maximum analytical speed
- **CPU Utilization**: Multi-core concurrent vectorization
- **RAM Allocation**: Higher in-memory footprint
- **Recommended Use**: Dedicated data processing servers and moderate-to-large analytical jobs

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    processing_mode="fast"  # Default configuration
)
```

### Slow Mode 🐢

- **Performance Profile**: Moderated incremental throughput
- **CPU Utilization**: Low single-core processing
- **RAM Allocation**: Low stream memory consumption
- **Recommended Use**: Memory-constrained environments, shared hardware, or background cron processing

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    processing_mode="slow"
)
```

### Performance Benchmark Comparison

| Processing Profile | Measured Throughput | CPU Impact | Peak RAM  | Guidance                   |
| ------------------ | ------------------- | ---------- | --------- | -------------------------- |
| **fast**           | ~12,317 rows/s      | High       | ~4,260 MB | ✅ Recommended Default     |
| **slow**           | ~8,557 rows/s       | Low        | ~1,571 MB | Memory-Constrained Servers |

______________________________________________________________________

## Advanced Recipes & Implementations

### Full-Spectrum Asset Extraction

```python
from globaldatafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()

# Dynamically fetch all supported instrument classifications
all_assets = b3.get_available_assets()

# Extract every asset class simultaneously
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=all_assets,
    initial_year=2023,
    output_filename="complete_market_2023"
)

print(f"✓ Extracted {result['total_records']:,} rows spanning {len(all_assets)} asset classes")
```

### Year-by-Year Partitioned Ingestion

```python
from globaldatafinance import HistoricalQuotesB3
import os

b3 = HistoricalQuotesB3()
base_path = "/data/cotahist"
output_path = "/data/extracted_quotes"

# Process historical epochs individually to yield segregated Parquet files per year
for year in range(2020, 2024):
    output_file = f"equities_{year}"

    result = b3.extract(
        path_of_docs=base_path,
        destination_path=output_path,
        assets_list=["ações"],
        initial_year=year,
        last_year=year,
        output_filename=output_file
    )

    if result['success']:
        print(f"✓ {year}: {result['total_records']:,} transaction rows extracted")
    else:
        print(f"✗ {year}: Extraction exception detected")
```

### Pre-Execution Integrity & Path Verification

```python
from globaldatafinance import HistoricalQuotesB3
import os

b3 = HistoricalQuotesB3()
path_docs = "/data/cotahist"

# 1. Confirm source repository accessibility
if not os.path.exists(path_docs):
    print(f"✗ Target repository inaccessible: {path_docs}")
    exit(1)

# 2. Confirm COTAHIST naming contract presence
zip_files = [f for f in os.listdir(path_docs) if f.startswith("COTAHIST") and (f.endswith(".ZIP") or f.endswith(".TXT"))]

if not zip_files:
    print(f"✗ Zero compliant COTAHIST archives found within {path_docs}")
    exit(1)

print(f"✓ Discovered {len(zip_files)} COTAHIST candidate archives")

# 3. Validate requested asset list
requested_assets = ["ações", "etf"]
available_assets = b3.get_available_assets()

invalid_assets = [a for a in requested_assets if a not in available_assets]
if invalid_assets:
    print(f"✗ Discarding unverified asset strings: {invalid_assets}")
    exit(1)

# 4. Trigger extraction pipeline
result = b3.extract(
    path_of_docs=path_docs,
    assets_list=requested_assets,
    initial_year=2023
)
```

______________________________________________________________________

## Error Handling & Exceptions

### Custom Exception Hierarchy

| Exception Class       | Trigger Condition                         | Recommended Handling Pattern                   |
| --------------------- | ----------------------------------------- | ---------------------------------------------- |
| `EmptyAssetListError` | Provided `assets_list` parameter is empty | Supply at least one recognized asset string    |
| `InvalidAssetsName`   | An asset string falls outside whitelist   | Query valid terms via `get_available_assets()` |
| `InvalidFirstYear`    | `initial_year` parameter below 1986 floor | Specify temporal lower bounds >= 1986          |
| `InvalidLastYear`     | End year prior to start year              | Confirm monotonic temporal ordering            |
| `EmptyDirectoryError` | Source folder lacks COTAHIST files        | Inspect folder contents prior to invocation    |
| `ExtractionError`     | Corruption detected in positional layout  | Verify ZIP MD5 hash integrity                  |

______________________________________________________________________

## Official COTAHIST File Formats

### File Naming Contract

B3 adheres to a strict historical naming convention:

```
COTAHIST_AYYYY.(ZIP|TXT)
```

Where `YYYY` denotes a four-digit fiscal year (e.g., `COTAHIST_A2023.ZIP`).

### Official Data Source

Official COTAHIST market bundles can be downloaded directly from B3:

🔗 **[https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)**

### Internal Archive Structure

Within each historical ZIP bundle sits a fixed-width positional ASCII text file:

```
COTAHIST_A2023.ZIP
└── COTAHIST_A2023.TXT  (Fixed-width positional historical transaction ledger)
```

______________________________________________________________________

## Extracted Parquet Schema

### Consolidated Column Architecture

The resulting consolidated Parquet file surfaces the following structured schema:

| Column Name            | Data Type | Description                                    |
| ---------------------- | --------- | ---------------------------------------------- |
| `data_pregao`          | `date`    | Trading session calendar date                  |
| `codigo_bdi`           | `string`  | BDI market execution classification code       |
| `ticker`               | `string`  | Instrument symbol / ticker (e.g., PETR4)       |
| `tipo_mercado`         | `string`  | Market clearing segment code                   |
| `nome_resumido`        | `string`  | Corporate issuer short name                    |
| `especificacao_papel`  | `string`  | Security equity specification (e.g., ON, PN)   |
| `preco_abertura`       | `decimal` | Session open trading price                     |
| `preco_maximo`         | `decimal` | Session intraday maximum price                 |
| `preco_minimo`         | `decimal` | Session intraday minimum price                 |
| `preco_medio`          | `decimal` | Volume-weighted intraday average price         |
| `preco_fechamento`     | `decimal` | Session closing execution price                |
| `melhor_oferta_compra` | `decimal` | Highest bid quotation at session close         |
| `melhor_oferta_venda`  | `decimal` | Lowest ask quotation at session close          |
| `numero_negocios`      | `int`     | Cumulative quantity of trade executions        |
| `quantidade_total`     | `int`     | Cumulative quantity of traded contracts/shares |
| `volume_total`         | `decimal` | Total monetary session trading turnover        |
| `data_vencimento`      | `date`    | Contract expiration maturity date              |
| `fator_cotacao`        | `int`     | Price quotation lot scaling factor             |
| `codigo_isin`          | `string`  | International Securities Identification Number |
| `numero_distribuicao`  | `int`     | Corporate action distribution sequence number  |

### Reading with Pandas

```python
import pandas as pd

df = pd.read_parquet("/data/processed_quotes/cotahist_extracted.parquet")

print(df.head())
print(f"\nDataframe shape: {df.shape}")
print(f"Time series interval: {df['data_pregao'].min()} to {df['data_pregao'].max()}")
```

### Reading with Polars (High Performance)

```python
import polars as pl

df = pl.read_parquet("/data/processed_quotes/cotahist_extracted.parquet")

print(df.head())
print(f"\nDataframe shape: {df.shape}")
print(f"In-memory estimation: {df.estimated_size('mb'):.2f} MB")
```

______________________________________________________________________

## Best Practices

### 1. Harness Fast Mode for Extensive Datasets

```python
# ✅ Highly recommended for processing extensive historical ranges
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=1986,  # Complete historical depth
    processing_mode="fast"
)
```

### 2. Segment Exports by Asset Class

```python
# ✅ Best practice: maintain dedicated Parquet files per asset category
for asset in ["ações", "etf", "opções"]:
    result = b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=[asset],
        initial_year=2023,
        output_filename=f"{asset}_2023"
    )

# ❌ Avoid bundling disparate instrument structures into a single monolithic output file
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf", "opções", "termo", "forward"],
    initial_year=1986,
    output_filename="monolith"
)
```

### 3. Monitor Free Filesystem Capacity

```python
import shutil

stats = shutil.disk_usage("/data")
free_gb = stats.free / (1024**3)

if free_gb < 5:
    print(f"⚠️  Low storage detected: {free_gb:.2f} GB available")
    # Toggle processing_mode="slow" or process narrowed annual chunks
else:
    pass
```

______________________________________________________________________

## Next Steps

- 📄 **[CVM Documents](cvm-docs.md)** - Guide to downloading CVM regulatory financial statements
- 💻 **[Practical Examples](examples.md)** - Explore actionable quantitative analytics workflows
- 🔧 **[API Reference](../reference/b3-api.md)** - Review comprehensive structural API definitions
- ❓ **[FAQ](faq.md)** - Answers to common installation and architectural inquiries

______________________________________________________________________

!!! tip "Analytical Best Practice"
Once historical quotes are compiled into Parquet files, consume them via `polars`. Its lazy evaluation engine and predicate pushdown capabilities significantly outperform pandas when processing multi-year tick ledgers.
