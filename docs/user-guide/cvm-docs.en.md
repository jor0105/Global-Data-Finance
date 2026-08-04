# CVM Regulatory Documents

Comprehensive documentation guide for utilizing the `FundamentalStocksDataCVM` class to download corporate fundamental financial filings from CVM (Securities and Exchange Commission of Brazil).

---

## Overview

The `FundamentalStocksDataCVM` class exposes a clean, highly extensible interface designed to retrieve official filings directly from regulatory servers, including annual financial statements, quarterly disclosures, corporate governance forms, and reference reports of Brazilian public companies.

### Highlights

- ✅ Automated processing across diverse document types and categories
- ✅ Flexible temporal parameter boundaries
- ✅ Native automated conversion into columnar Apache Parquet files (optional)
- ✅ Concurrent asynchronous down-streaming (3–5x faster than linear requests)
- ✅ Resilient connection exception handling and automated retry policies
- ✅ Transparent structured tracking and status console output

---

## Available Document Types

CVM publishes official disclosures under the following classifications:

| Document Code | Complete Portuguese Title           | Description                              | Available Since |
| ------------- | ----------------------------------- | ---------------------------------------- | --------------- |
| **DFP**       | Demonstração Financeira Padronizada | Standardized Annual Financial Statements | 2010            |
| **ITR**       | Informação Trimestral               | Quarterly Interim Financial Reports      | 2011            |
| **FRE**       | Formulário de Referência            | Complete Reference Form Disclosures     | 2010            |
| **FCA**       | Formulário Cadastral                | Corporate Cadastral Registration Forms   | 2010            |
| **CGVN**      | Código de Governança                | Corporate Governance Practices Reports   | 2018            |
| **VLMO**      | Valores Mobiliários                 | Securities Trading and Holding Declarations | 2018            |
| **IPE**       | Informações Periódicas e Eventuais  | Periodic and Eventual Filings (Material Facts) | 2010            |

!!! info "Historical Data Depth"
    The major structural financial forms (`DFP`, `FRE`, `FCA`, `IPE`) span from fiscal year 2010 onward, while `ITR` disclosures start in 2011 and `CGVN`/`VLMO` commence in 2018.

---

## Basic Usage

### Library Import

```python
from globaldatafinance import FundamentalStocksDataCVM
```

### Instantiate Public Client

```python
cvm = FundamentalStocksDataCVM()
```

### Minimal Download Script

```python
# Download DFP archives covering the past 3 fiscal years
cvm.download(
    destination_path="/home/user/cvm_data",
    list_docs=["DFP"],
    initial_year=2021,
    last_year=2023
)
```

---

## Core Public Methods

### `download()`

Downloads regulatory CVM archives directly into a designated filesystem destination.

#### Method Signature

```python
def download(
    self,
    destination_path: str,
    list_docs: Optional[List[str]] = None,
    initial_year: Optional[int] = None,
    last_year: Optional[int] = None,
    automatic_extractor: bool = False,
) -> None
```

#### Parameters

| Parameter             | Type        | Mandatory | Description                                                   |
| --------------------- | ----------- | --------- | ------------------------------------------------------------- |
| `destination_path`    | `str`       | ✅ Yes    | Target filesystem directory where downloaded bundles are saved |
| `list_docs`           | `List[str]` | ❌ No     | Specific document codes to fetch. Defaults to all codes when `None` |
| `initial_year`        | `int`       | ❌ No     | Starting historical fiscal year (inclusive). Defaults to minimal supported year |
| `last_year`           | `int`       | ❌ No     | Ending fiscal year (inclusive). Defaults to current operating year |
| `automatic_extractor` | `bool`      | ❌ No     | When set to `True`, automatically unpacks and normalizes ZIP bundles into Parquet datasets |

#### Usage Examples

**Example 1: Basic DFP Download**

```python
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2020,
    last_year=2023
)
```

**Example 2: Downloading Multiple Document Types**

```python
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR", "FRE"],
    initial_year=2022
)
```

**Example 3: Download with Automated Parquet Extraction**

```python
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2022,
    automatic_extractor=True  # Automatically normalizes ZIP records directly into Apache Parquet
)
```

**Example 4: Full Spectrum Download**

```python
# Omitting list_docs retrieves every supported document category in parallel
cvm.download(
    destination_path="/data/cvm_complete",
    initial_year=2023
)
```

---

### `get_available_docs()`

Retrieves a mapped catalog containing all supported regulatory document types along with descriptive definitions.

#### Method Signature

```python
def get_available_docs(self) -> Dict[str, str]
```

#### Return Value

A dictionary mapping acronym document codes to their full professional titles.

#### Example Execution

```python
cvm = FundamentalStocksDataCVM()
docs = cvm.get_available_docs()

for code, description in docs.items():
    print(f"{code}: {description}")
```

**Console Output**:

```
DFP: Demonstração Financeira Padronizada
ITR: Informação Trimestral
FRE: Formulário de Referência
FCA: Formulário Cadastral
CGVN: Código de Governança
VLMO: Valores Mobiliários
IPE: Informações Periódicas e Eventuais
```

---

### `get_available_years()`

Returns descriptive information detailing permissible temporal intervals across supported filings.

#### Method Signature

```python
def get_available_years(self) -> Dict[str, int]
```

#### Return Value

A structural dictionary describing historical floor boundaries:

| Dictionary Key                   | Description                              |
| -------------------------------- | ---------------------------------------- |
| `"General Document Years"`       | Minimum historical starting year for general filings (2010) |
| `"ITR Document Years"`           | Minimum historical year for ITR quarterly disclosures (2011) |
| `"CGVN and VMLO Document Years"` | Minimum historical year for governance disclosures (2018) |
| `"Current Year"`                 | Real-time operational system year        |

#### Example Execution

```python
cvm = FundamentalStocksDataCVM()
years = cvm.get_available_years()

print(f"General disclosures available since: {years['General Document Years']}")
print(f"Interim statements (ITR) available since: {years['ITR Document Years']}")
print(f"Active operating system year: {years['Current Year']}")
```

---

## Advanced Implementations

### Incremental Data Synchronizer

Execute selective historical synchronization to avoid re-downloading existing archives:

```python
import os
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
base_path = "/data/cvm"

# Inspect existing local storage directory
existing_years = set()
if os.path.exists(base_path):
    for filename in os.listdir(base_path):
        if "DFP" in filename:
            # Extract fiscal year from the standard filename naming contract
            year = int(filename.split("_")[-1].replace(".zip", ""))
            existing_years.add(year)

# Identify missing target fiscal years
current_year = 2023
all_years = set(range(2020, current_year + 1))
missing_years = all_years - existing_years

if missing_years:
    min_year = min(missing_years)
    max_year = max(missing_years)

    cvm.download(
        destination_path=base_path,
        list_docs=["DFP"],
        initial_year=min_year,
        last_year=max_year
    )
else:
    print("✓ Local database is fully synchronized")
```

### Pre-execution Input Validation

Programmatically filter out invalid requests before transmitting network instructions:

```python
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()

# Validate document parameter compliance
requested_docs = ["DFP", "ITR", "FRE"]
available_docs = cvm.get_available_docs()

valid_docs = [doc for doc in requested_docs if doc in available_docs]
invalid_docs = [doc for doc in requested_docs if doc not in available_docs]

if invalid_docs:
    print(f"⚠️  Discarding unsupported document strings: {invalid_docs}")
    print(f"✓ Authorized processing items: {valid_docs}")

# Validate temporal input limits
years_info = cvm.get_available_years()
requested_year = 2015

if requested_year < years_info['General Document Years']:
    print(f"⚠️  Requested fiscal period {requested_year} is prior to floor {years_info['General Document Years']}")
else:
    # Trigger safe downstream extraction
    cvm.download(
        destination_path="/data/cvm",
        list_docs=valid_docs,
        initial_year=requested_year
    )
```

---

## Error Handling & Exceptions

### Custom Exception Hierarchy

The CVM module enforces fail-fast error behavior by raising specialized exception types:

| Exception Class               | Trigger Condition                       | Recommended Handling Pattern               |
| ----------------------------- | --------------------------------------- | ------------------------------------------ |
| `InvalidDocumentName`          | Provided document string is unrecognized| Validate inputs via `get_available_docs()`  |
| `InvalidFirstYear`            | Requested initial year below historical floor | Inspect boundaries with `get_available_years()`|
| `InvalidLastYear`             | End year is prior to start year or invalid | Validate parameters prior to invocation    |
| `NetworkError`                | Network connection or TLS handshake failure | Implement application-level fallback alarms|
| `TimeoutError`                | Remote regulatory server request timeout| Re-execute during off-peak processing hours|
| `InvalidDestinationPathError` | Target filesystem path fails safety check| Confirm folder write and creation access   |

---

## Directory & File Layout

### Download Repository Hierarchy

Persisted ZIP archives are systematically grouped within individual category folders:

```
destination_path/
    DFP/
        2020/
            dfp_cia_aberta_2020.zip
        2021/
            dfp_cia_aberta_2021.zip
        2022/
            dfp_cia_aberta_2022.zip
        2023/
            dfp_cia_aberta_2023.zip
    ITR/
        2020/
            itr_cia_aberta_2020.zip
        2021/
            itr_cia_aberta_2021.zip
        2022/
            itr_cia_aberta_2022.zip
        2023/
            itr_cia_aberta_2023.zip
    FRE/
        2020/
            fre_cia_aberta_2020.zip
        2021/
            fre_cia_aberta_2021.zip
        2022/
            fre_cia_aberta_2022.zip
        2023/
            fre_cia_aberta_2023.zip
    FCA/
        2020/
            fca_cia_aberta_2020.zip
        2021/
            fca_cia_aberta_2021.zip
        2022/
            fca_cia_aberta_2022.zip
        2023/
            fca_cia_aberta_2023.zip
    etc...
```

### Internal ZIP Structure

Each downloaded archive encloses separate structured tables covering distinct accounting dimensions:

```
dfp_cia_aberta_2023.zip
├── dfp_cia_aberta_2023.csv # General company metadata
├── dfp_cia_aberta_BPA_con_2023.csv # Consolidated Balance Sheet - Active Assets
├── dfp_cia_aberta_BPP_con_2023.csv # Consolidated Balance Sheet - Liabilities & Equity
├── dfp_cia_aberta_DRE_con_2023.csv # Income Statement (Profit & Loss)
├── dfp_cia_aberta_DFC_MD_con_2023.csv # Statement of Cash Flows (Direct Method)
├── dfp_cia_aberta_DFC_MI_con_2023.csv # Statement of Cash Flows (Indirect Method)
├── dfp_cia_aberta_DVA_con_2023.csv # Value Added Statement
└── ...
```

### Automated Parquet Extraction Output

When initializing requests with `automatic_extractor=True`, all enclosed files are unpacked and transformed into high-performance Parquet format:

```
destination_path/
├── DFP/
    2023/
    │ ├── dfp_cia_aberta_2023.parquet
    │ ├── dfp_cia_aberta_BPA_con_2023.parquet
    │ ├── dfp_cia_aberta_BPP_con_2023.parquet
    │ └── ...
└── ...
```

---

## Best Practices

### 1. Partition Long Temporal Intervals

```python
# ❌ Avoid sweeping multidecade synchronous downloads
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],
    initial_year=2010,  # 25+ years requested at once!
    last_year=2023
)

# ✅ Execute segmented, highly predictable batch slices
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],
    initial_year=2020,  # Controlled 3–4 year slices
    last_year=2023
)
```

### 2. Verify Available Filesystem Space

```python
import shutil

# Measure accessible filesystem capacity
stats = shutil.disk_usage("/data")
free_gb = stats.free / (1024**3)

if free_gb < 10:
    print(f"⚠️  Insufficient workspace capacity detected: {free_gb:.2f} GB")
else:
    cvm.download(destination_path="/data", ...)
```

### 3. Rely on Parquet for Quantitative Processing

```python
# Whenever downstream statistical workloads are intended, enforce automatic Parquet extraction
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2022,
    automatic_extractor=True  # Massively accelerates dataframe loading
)
```

---

## Performance & Optimization

### Asynchronous Concurrency

The CVM implementation utilizes `AsyncDownloadAdapterCVM` by default, delivering significant throughput improvements:

- ⚡ **3–5x Faster** than linear synchronous sequential script executions
- 🔄 **Automated Fault Recovery** utilizing exponential retry backoff loops
- 📊 **Real-time Diagnostic Logs** detailing active concurrent thread transfers
- 🧵 **Multi-threaded Worker Execution** (defaulting to 8 concurrent worker queues)

### Benchmark Comparisons

Estimated duration required to fetch 1 complete annual DFP archive bundle:

| Ingestion Method        | Execution Duration | Relative Throughput |
| ----------------------- | ------------------ | ------------------- |
| Sequential standard HTTP| ~60s               | 1x (Baseline)       |
| AsyncDownloadAdapterCVM | ~15s               | **4x Faster**       |

---

## Next Steps

- 📈 **[B3 Quotes](b3-docs.md)** - Explore historical market exchange extraction
- 💻 **[Practical Examples](examples.md)** - Review comprehensive production code workflows
- 🔧 **[API Reference](../reference/cvm-api.md)** - Inspect technical signatures and contracts
- ❓ **[FAQ](faq.md)** - Answers to common setup and troubleshooting questions

---

!!! tip "Performance Best Practice"
    For analytical pipeline integrations, consistently specify `automatic_extractor=True`. Columnar Parquet data structures bypass repetitive textual CSV decoding overhead during dataframe initialization.
