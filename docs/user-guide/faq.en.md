# Frequently Asked Questions (FAQ)

Answers and solutions addressing common inquiries regarding installation, configuration, and architectural usage of Global-Data-Finance.

______________________________________________________________________

## Installation & Setup

### How do I install Global-Data-Finance?

Execute the simple pip command below inside your terminal:

```bash
pip install globaldatafinance
```

Consult our comprehensive [Installation Guide](installation.md) for deeper instructions involving virtual environments and alternate package managers like `uv`.

### Which Python version is required?

Global-Data-Finance strictly requires **Python 3.12 or newer**. Python runtime environments prior to version 3.12 lack the required async syntax and standard library typing features and are officially unsupported.

### Is installing within a virtual environment recommended?

Yes, absolutely! Isolating dependencies via `venv` or `conda` is deeply recommended to avoid cross-package collisions:

```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
pip install globaldatafinance
```

______________________________________________________________________

## General Library Operations

### Where does the library store downloaded files?

Downloaded bundles and extracted Parquet datasets are consistently written into whatever folder path is supplied to the `destination_path` method argument:

```python
cvm.download(destination_path="/home/user/financial_data")
# Files persisted directly inside: /home/user/financial_data/
```

### How can I dynamically inspect which documents and asset classes are supported?

Invoke the introspectable public `get_available_*` discovery methods attached to each public facade:

```python
# For CVM Corporate Filings
cvm = FundamentalStocksDataCVM()
docs = cvm.get_available_docs()
years = cvm.get_available_years()

# For B3 Market Quotes
b3 = HistoricalQuotesB3()
assets = b3.get_available_assets()
years = b3.get_available_years()
```

______________________________________________________________________

## CVM Regulatory Documents

### What financial disclosure categories can be downloaded from CVM?

- **DFP**: Standardized Annual Financial Statements (Demonstrações Financeiras Padronizadas)
- **ITR**: Quarterly Interim Financial Statements (Informações Trimestrais)
- **FRE**: Reference Form Disclosures (Formulário de Referência)
- **FCA**: Corporate Cadastral Registration Forms (Formulário Cadastral)
- **CGVN**: Corporate Governance Reports (Código de Governança)
- **VLMO**: Securities Trading & Holding Declarations (Valores Mobiliários)
- **IPE**: Periodic and Eventual Filings (Informações Periódicas e Eventuais)

See [CVM Documents](cvm-docs.md) for full parameter references.

### How do I restrict downloads to a single document type?

Pass a one-element list containing your target document code into `list_docs`:

```python
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],  # Restricts download strictly to DFP archives
    initial_year=2022
)
```

### What does the `automatic_extractor` parameter do?

When specifying `automatic_extractor=True`, downloaded ZIP bundles are automatically decompressed, evaluated, and converted into columnar Apache Parquet files natively optimized for high-speed dataframe analytics:

```python
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],
    automatic_extractor=True  # Converts raw accounting CSV ledgers straight into .parquet files
)
```

### How does the library handle connection dropouts or interrupted HTTP transfers?

The underlying network layer features automated asynchronous retries coupled with custom exponential back-off strategies. For mission-critical production pipelines, consider pairing library retries with application-level orchestration traps (review our [Retry Strategy Architecture](../dev-guide/retry-strategy.md)).

______________________________________________________________________

## B3 Historical Market Quotes

### Where can I obtain official COTAHIST historical quote archives?

Download raw historical bundles directly from B3's official data portal:
🔗 [https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)

### What is the distinction between `fast` and `slow` processing modes?

| Processing Profile | Performance | CPU Usage | RAM Consumption | Recommended Use                        |
| ------------------ | ----------- | --------- | --------------- | -------------------------------------- |
| **fast**           | High        | Intensive | ~2GB            | Standard multi-core machines (Default) |
| **slow**           | Moderate    | Minimal   | ~500MB          | Constrained RAM or background workers  |

```python
# Execute using Fast mode (Recommended Default)
result = b3.extract(..., processing_mode="fast")

# Execute using Slow mode
result = b3.extract(..., processing_mode="slow")
```

### How do I filter extractions strictly for spot market stocks?

Supply `"ações"` inside the required `assets_list` argument:

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],  # Isolates equity instruments from options, futures, or ETFs
    initial_year=2023
)
```

### Can I extract multiple asset classifications simultaneously?

Yes! Include multiple asset keywords within the passed list array:

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf", "opções"],
    initial_year=2023
)
```

### How can I customize the filename of the produced Parquet artifact?

Provide your preferred base filename string (excluding the `.parquet` extension) via `output_filename`:

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    output_filename="equities_2023"  # Generates an artifact titled: equities_2023.parquet
)
```

______________________________________________________________________

## Performance & System Optimization

### How are CVM file downloads accelerated?

Global-Data-Finance automatically processes CVM downloads using `AsyncDownloadAdapterCVM`, leveraging asynchronous parallel HTTP streaming that executes 3–5x faster than conventional blocking scripts.

### How can I maximize B3 market quote extraction throughput?

Maintain the default `"fast"` processing profile:

```python
result = b3.extract(..., processing_mode="fast")
```

### Can I spawn parallel worker processes across separate historical years?

Yes! You can orchestrate multi-threaded or multi-process concurrent extractions utilizing Python's native `concurrent.futures` or `multiprocessing` toolsets:

```python
from concurrent.futures import ProcessPoolExecutor
from globaldatafinance import HistoricalQuotesB3

def process_fiscal_year(year):
    b3 = HistoricalQuotesB3()
    return b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=year,
        last_year=year,
        output_filename=f"stocks_year_{year}"
    )

# Run concurrent extraction jobs spanning multiple CPU cores
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_fiscal_year, range(2020, 2024)))
```

______________________________________________________________________

## Data Analytics & Downstream Ingestion

### What libraries should I use to analyze generated Parquet datasets?

Use either Pandas or Polars:

```python
# Utilizing traditional Pandas
import pandas as pd
df = pd.read_parquet("cotahist_extracted.parquet")

# Utilizing optimized Polars (Recommended)
import polars as pl
df = pl.read_parquet("cotahist_extracted.parquet")
```

### Which dataframe engine is recommended: Pandas or Polars?

- **Pandas**: Traditional industry standard with broad legacy support, well suited for small to moderate tabular structures.
- **Polars**: High-performance Rust-based query engine featuring minimal RAM consumption and extreme speed; ideally suited for massive multi-year tick ledgers.

For analyzing extensive quantitative financial times series, we deeply recommend **Polars**.

### How do I isolate trading activity for a specific ticker symbol?

```python
import polars as pl

df = pl.read_parquet("cotahist_extracted.parquet")

# Isolate PETR4 stock executions
petr4 = df.filter(pl.col('ticker') == 'PETR4')

# Or equivalently in Pandas
import pandas as pd
df = pd.read_parquet("cotahist_extracted.parquet")
petr4 = df[df['ticker'] == 'PETR4']
```

______________________________________________________________________

## Troubleshooting & Common Exceptions

### "No module named 'globaldatafinance'"

**Cause**: The library has not been installed into your active Python interpreter or your virtual environment remains inactive.
**Solution**: Activate your environment and reinstall:

```bash
pip install globaldatafinance
```

### "Python version not supported"

**Cause**: The script is executing under a Python runtime older than 3.12.
**Solution**: Upgrade your machine interpreter to Python 3.12+.

### "InvalidDocumentName"

**Cause**: An unconfirmed document acronym string was supplied to `list_docs`.
**Solution**: Confirm valid document strings via programmatic catalog inspection:

```python
docs = cvm.get_available_docs()
print(list(docs.keys()))
```

### "EmptyDirectoryError"

**Cause**: The provided target input directory is empty or lacks valid COTAHIST source files.
**Solution**: Ensure files matching the naming contract `COTAHIST_AYYYY.(ZIP|TXT)` reside inside the target folder.

### "NetworkError" or "TimeoutError"

**Cause**: Remote regulatory web server connection dropouts or rate limitations.
**Solution**:

1. Verify active internet access and DNS resolution.
2. Re-attempt execution during non-peak server hours.
3. Review our [Retry Strategy Architectural Guide](../dev-guide/retry-strategy.md).

______________________________________________________________________

## Production Deployment & Pipeline Integration

### Is Global-Data-Finance ready for production usage?

Yes! The library is extensively verified under comprehensive CI quality gates. Production deployment guidelines:

- Maintain diagnostic logging setups
- Wrap invocations within robust application-level exception handlers
- Monitor local storage capacity and system RAM parameters

### How do I automate unattended periodic data syncing?

Schedule automated script executions using operating system schedulers such as `cron` on POSIX servers:

```bash
# Crontab configuration executing harvesting script daily at 02:00 AM
0 2 * * * /path/to/venv/bin/python /path/to/harvester.py
```

### How can I integrate extraction steps into Apache Airflow or modern data pipelines?

Global-Data-Finance integrates cleanly into orchestration engines such as:

- **Apache Airflow**: Build Python Operators inside DAG definitions
- **Prefect**: Implement processing routines inside tasks and flows
- **Dagster**: Package extractions as software-defined ops or assets
- **Luigi**: Wire methods directly inside operational pipeline steps

Minimal Airflow Task snippet:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from globaldatafinance import FundamentalStocksDataCVM

def sync_cvm_filings():
    cvm = FundamentalStocksDataCVM()
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2023,
        automatic_extractor=True
    )

with DAG('cvm_sync_dag', ...) as dag:
    task = PythonOperator(
        task_id='download_regulatory_filings',
        python_callable=sync_cvm_filings
    )
```

______________________________________________________________________

## Contributing & Community

### How can I contribute feature expansions to the repository?

Consult our developer [Contribution Guide](../dev-guide/contributing.md) for architectural expectations and validation practices.

### Where should I report bugs or unexpected runtime behavior?

Submit a detailed bug report issue directly to our repository tracker:
🔗 [https://github.com/jordanestralioto/Global-Data-Finance/issues](https://github.com/jordanestralioto/Global-Data-Finance/issues)

### How can I propose architectural enhancements?

Open a discussion thread or feature request issue tagged as `enhancement` on GitHub.

______________________________________________________________________

## Licensing & Terms

### Under what license is Global-Data-Finance released?

Apache License, Version 2.0.

### Am I authorized to deploy this library within commercial or enterprise applications?

Yes! The Apache 2.0 license freely grants commercial distribution, modification, and integration usage.

### Are there external copyright restrictions attached to downloaded financial datasets?

Regulatory filings and market transaction records are public data provided officially by CVM and B3. Always review official terms of use broadcast by each financial body:

- **CVM**: [http://www.cvm.gov.br/](http://www.cvm.gov.br/)
- **B3**: [https://www.b3.com.br/](https://www.b3.com.br/)

______________________________________________________________________

## Support & Assistance

### Where can I seek developer support?

1. **Documentation**: Review our canonical [Documentation Corpus](../index.md)
2. **Issue Tracker**: [Submit a GitHub Issue](https://github.com/jordanestralioto/Global-Data-Finance/issues)
3. **Direct Contact**: estraliotojordan@gmail.com

### How should security vulnerabilities be reported?

For sensitive architectural or security bug reporting, transmit details privately via email to: estraliotojordan@gmail.com

______________________________________________________________________

!!! tip "Didn't find your answer?"
Open an inquiry discussion on our GitHub repository or consult the [Technical API Reference](../reference/cvm-api.md).
