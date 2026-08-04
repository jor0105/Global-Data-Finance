# Advanced Usage

Advanced computational techniques, customization strategies, and optimization patterns for Global-Data-Finance.

---

## Core Utilities

### Logging System

Enable professional centralized logging for pipeline tracing and diagnostics:

```python
from globaldatafinance.core import setup_logging, get_logger, log_execution_time

# Configure system-wide logging
setup_logging(level="INFO", log_file="app.log")

# Retrieve module-specific logger instance
logger = get_logger(__name__)

# Emit structured contextual logging events
logger.info(
    "Download workflow initiated",
    extra={"doc_type": "DFP", "year": 2023}
)

# Measure execution performance via timing context manager
with log_execution_time(logger, "CVM Filing Ingestion", total=5):
    cvm.download(...)
```

[View comprehensive logging documentation →](logging-system.md)

### Global Configuration Tuning

Customize underlying network timeout and retry behavior via environment variables:

```bash
# Expand socket timeout threshold for high-latency connections
export DATAFINANCE_NETWORK_TIMEOUT=900

# Increase maximum connection retry attempts
export DATAFINANCE_NETWORK_MAX_RETRIES=10

# Configure an aggressive exponential retry back-off factor
export DATAFINANCE_NETWORK_RETRY_BACKOFF=3.0
```

```python
from globaldatafinance.core.config import settings

# Verify active runtime network configurations
print(f"Active network timeout: {settings.network.timeout}s")
print(f"Max configured retries: {settings.network.max_retries}")
```

### Resource Monitoring Engine

Autonomously evaluate system telemetry to dynamically constrain concurrency patterns:

```python
from globaldatafinance.core.utils.resource_monitor import (
    ResourceMonitor,
    ResourceState,
    ResourceLimits
)

# Initialize monitor telemetry instance
monitor = ResourceMonitor()

# Evaluate immediate system capacity state
state = monitor.check_resources()
if state == ResourceState.CRITICAL:
    print("Warning: System resources entering critical saturation!")

# Calculate dynamically throttled worker thread limits
safe_workers = monitor.get_safe_worker_count(max_workers=16)
print(f"Allocated {safe_workers} safe concurrent worker threads")

# Pause execution until system resources return below saturation thresholds
monitor.wait_for_resources(timeout_seconds=120)
```

[View resource monitoring documentation →](resource-monitoring.md)

### Custom Retry Strategies

Implement tailored retry loop policies when constructing defensive pipeline wrappers:

```python
from globaldatafinance.core.utils.retry_strategy import RetryStrategy
import time

strategy = RetryStrategy(
    initial_backoff=1.0,
    max_backoff=30.0,
    multiplier=2.0
)

max_retries = 5
for attempt in range(max_retries):
    try:
        result = risky_operation()
        break
    except Exception as exc:
        if not strategy.is_retryable(exc):
            raise

        if attempt < max_retries - 1:
            backoff = strategy.calculate_backoff(attempt)
            print(f"Retry attempt {attempt + 1} scheduled in {backoff}s...")
            time.sleep(backoff)
```

[View retry strategy documentation →](retry-strategy.md)

---

## Custom Adapter Substitution & Duck Typing

The HTTP network adapter (`AsyncDownloadAdapterCVM`) and extractor adapter (`ParquetExtractorAdapterCVM`) operate as concrete classes enforcing clean, observable method signatures. The core orchestrator (`DownloadDocumentsUseCaseCVM`) accepts any dependency injection object exposing the expected target method (`download_docs(tasks)`), leveraging idiomatic duck typing. To supersede standard adapter behavior, inject a custom class matching the target signature.

### Replacing the HTTP Download Adapter

```python
from globaldatafinance.brazil.cvm.fundamental_stocks_data.client import (
    DownloadDocumentsUseCaseCVM,
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data.core import (
    DownloadResultCVM,
)


class MyCustomAdapter:
    """Alternative download adapter utilizing duck-typed interface matching."""

    def download_docs(self, tasks) -> DownloadResultCVM:
        # tasks represents the structured sequence emitted by GenerateUrlsUseCaseCVM:
        # a collection of (doc_name, url, destination_path) tuples.
        # Implement your customized transport infrastructure (wget, aiohttp, gsutil, etc.)
        # and return the identical expected result tracking object.
        return DownloadResultCVM(
            success_count_downloads=0,
            error_count_downloads=0,
            successful_downloads=[],
            failed_downloads={},
            elapsed_time=0.0,
        )


adapter = MyCustomAdapter()
use_case = DownloadDocumentsUseCaseCVM(repository=adapter)
result = use_case.execute(
    destination_path="./cvm_custom_data",
    list_docs=["DFP"],
    initial_year=2023,
    last_year=2023,
)
```

> The library architecture values clarity and extensible composition: orchestrators interact with operational adapters purely through public method signatures (duck typing), enabling custom implementations to be injected seamlessly without burdensome abstract base class inheritance. Review `docs/dev-guide/architecture.md` for complete architectural details.

---

## Advanced Logging Customization

### Configuring Dedicated Logging Handlers

```python
import logging
from globaldatafinance.core import get_logger

# Register custom module logger
logger = get_logger("my_custom_pipeline")

# Attach file output handler with explicit debugging threshold
file_handler = logging.FileHandler("globaldatafinance_debug.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Emit diagnostic record
logger.info("Custom pipeline execution starting...")
```

---

## Parallel Multi-Process Execution

### Spawning Concurrent Multi-Year Extractions

```python
from concurrent.futures import ProcessPoolExecutor
from globaldatafinance import HistoricalQuotesB3

def extract_year(year):
    b3 = HistoricalQuotesB3()
    return b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=year,
        last_year=year,
        output_filename=f"stocks_{year}"
    )

years = range(2020, 2024)
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(extract_year, years))

for year, result in zip(years, results):
    print(f"Fiscal Year {year}: Normalized {result['total_records']:,} trading records")
```

---

## Pipeline Orchestration Integration

### Apache Airflow

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from globaldatafinance import FundamentalStocksDataCVM

def download_cvm_task():
    cvm = FundamentalStocksDataCVM()
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2023
    )

with DAG(
    'cvm_daily_sync_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily'
) as dag:

    download_step = PythonOperator(
        task_id='download_cvm_records',
        python_callable=download_cvm_task
    )
```

### Prefect Workflows

```python
from prefect import flow, task
from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3

@task
def download_cvm():
    cvm = FundamentalStocksDataCVM()
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2023
    )

@task
def extract_b3():
    b3 = HistoricalQuotesB3()
    return b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=2023
    )

@flow
def financial_data_pipeline():
    download_cvm()
    result = extract_b3()
    return result

if __name__ == "__main__":
    financial_data_pipeline()
```

---

## Memory Optimization Patterns

### Targeted Column Projection & Lazy Scanning with Polars

```python
import polars as pl

# Project exclusively required columns during disk decompression
df = pl.read_parquet(
    "cotahist.parquet",
    columns=["data_pregao", "ticker", "preco_fechamento"]
)

# Leverage lazy computation graphs to evaluate predicates prior to in-memory collection
df = pl.scan_parquet("cotahist.parquet") \
    .filter(pl.col("ticker") == "PETR4") \
    .collect()
```

### Iterative Chunked Ingestion with Pandas

```python
import pandas as pd

# Iterate massive Parquet archives across sequential memory chunks
for chunk in pd.read_parquet(
    "cotahist.parquet",
    chunksize=100000
):
    # Process slice directly without saturating system RAM
    process_chunk(chunk)
```

---

## Monitoring & Visual Tracking

### Interactive Progress Visualizations with Tqdm

```python
from tqdm import tqdm
from globaldatafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()

years = range(2020, 2024)
for year in tqdm(years, desc="Normalizing historical annual epochs"):
    result = b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=year,
        last_year=year
    )
```

---

## Next Steps

- [Architecture Guide](architecture.md) - Deep structural design concepts
- [Practical Examples](../user-guide/examples.md) - End-to-end operational code examples
