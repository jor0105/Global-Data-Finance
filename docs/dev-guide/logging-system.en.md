# Logging System

Complete technical reference covering the advanced centralized logging infrastructure implemented across Global-Data-Finance.

---

## Overview

Global-Data-Finance incorporates a professional centralized logging subsystem designed specifically for high-throughput library distribution:

- ✅ **Lazy Initialization**: Logging remains silently disabled by default (respecting standard Python library citizenship practices)
- ✅ **Multi-Target Handlers**: Configurable simultaneous routing to console outputs and rotating filesystem files
- ✅ **Granular Level Filtering**: Full support for standard severity thresholds (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- ✅ **Performance Benchmarking**: Integrated timing context managers designed to capture operation latencies automatically
- ✅ **Structured Metadata Binding**: Context-aware log emission supporting structured parameter propagation
- ✅ **Environment Override Compatibility**: Real-time runtime overrides via confirmed OS environment variables

---

## Architecture

### Primary Subsystem Components

```text
src/core/logging_config.py
├── setup_logging()           # Subsystem configuration entrypoint
├── get_logger()              # Module logger registry retrieval
├── log_execution_time()      # Latency tracking performance context manager
├── log_with_context()        # Structured key-value event logger
├── LoggingSettings           # Pydantic configuration container
├── StructuredFormatter       # Custom formatting layout engine
└── ContextFilter             # Metadata enrichment logging filter
```

---

## Basic Usage

### 1. Enable Library Logging

In accordance with Python best practices for dependency distributions, logging is **disabled by default**. To activate event reporting:

```python
from globaldatafinance.core import setup_logging

# Activate logging across the library hierarchy at severity INFO
setup_logging(level="INFO")
```

### 2. Retrieve a Module Logger Instance

```python
from globaldatafinance.core import get_logger

logger = get_logger(__name__)
logger.info("Processing job started")
logger.debug("Detailed debug tracing")
logger.warning("Potential configuration warning")
logger.error("Exception encountered during operational step")
```

### 3. Structured Context Logging

```python
logger.info(
    "Dataset normalization completed",
    extra={
        "filename": "dfp_cia_aberta_2023.csv",
        "records": 1000,
        "elapsed_ms": 250
    }
)
```

**Console Output**:

```text
2025-11-25 17:30:00 | INFO     | my_pipeline_module | Dataset normalization completed | filename=dfp_cia_aberta_2023.csv | records=1000 | elapsed_ms=250
```

---

## Configuration

### Severity Level Thresholds

| Severity Level | Operational Scope                       | Typical Example Event                              |
| -------------- | --------------------------------------- | -------------------------------------------------- |
| **DEBUG**      | Deep diagnostic execution traces         | Variable parameter inspections, worker loop steps  |
| **INFO**       | Standard operational lifecycle metrics  | "Download initiated", "Parquet file persisted"     |
| **WARNING**    | Recoverable anomalies or degradations    | "Target archive exists, skipping", "Timeout retry" |
| **ERROR**      | Non-fatal operation exceptions          | "Failed downloading individual DFP table slice"    |
| **CRITICAL**   | Severe failures impacting overall runtime | "Storage exhaustion detected", "Out of memory"   |

### Programmatic Configuration

```python
from globaldatafinance.core import setup_logging

# Standard activation
setup_logging(level="INFO")

# Route logging outputs directly to a filesystem log destination
setup_logging(
    level="DEBUG",
    log_file="/var/log/datafinance/execution.log"
)

# Enable detailed formatting (includes precise line numbers and symbol signatures)
setup_logging(
    level="DEBUG",
    use_detailed_format=True
)
```

### Environment Variable Configuration

Confirmed environment configuration parameter names:

```bash
# Define threshold level
export DATAFIN_LOG_LEVEL=DEBUG

# Direct logging output to file destination
export DATAFIN_LOG_FILE=/var/log/datafin.log

# Enable detailed structural reporting
export DATAFIN_LOG_DETAILED_FORMAT=true

# Toggle structured formatting
export DATAFIN_LOG_STRUCTURED=true
```

```python
from globaldatafinance.core import setup_logging

# Ingest settings directly from environment declarations
setup_logging()
```

---

## Advanced Capabilities

### Performance Timing & Latency Profiling

Leverage the automated `log_execution_time()` context manager to track operational durations:

```python
from globaldatafinance.core import log_execution_time, get_logger

logger = get_logger(__name__)

with log_execution_time(logger, "Parse COTAHIST ZIP archive", filename="COTAHIST_A2023.ZIP"):
    parse_file("COTAHIST_A2023.ZIP")
```

**Console Output**:

```text
Starting: Parse COTAHIST ZIP archive | operation=Parse COTAHIST ZIP archive | filename=COTAHIST_A2023.ZIP
Completed: Parse COTAHIST ZIP archive | operation=Parse COTAHIST ZIP archive | elapsed_seconds=2.45 | filename=COTAHIST_A2023.ZIP
```

Upon encountering runtime failures:

```text
Failed: Parse COTAHIST ZIP archive | operation=Parse COTAHIST ZIP archive | elapsed_seconds=1.23 | error=File not found | filename=COTAHIST_A2023.ZIP
```

### Contextual Event Reporting

```python
from globaldatafinance.core import log_with_context, get_logger

logger = get_logger(__name__)

log_with_context(
    logger,
    "info",
    "Parallel download batch completed",
    url="https://example.com/bundle.zip",
    size_mb=125.5,
    duration_seconds=45
)
```

### Confirming Active Configuration State

```python
from globaldatafinance.core import is_logging_configured, setup_logging

if not is_logging_configured():
    setup_logging(level="INFO")
```

### Accessing Active Settings Metrics

```python
from globaldatafinance.core import get_logging_settings

settings = get_logging_settings()
print(f"Active threshold level: {settings.level}")
print(f"Registered file sink: {settings.log_file}")
print(f"Detailed syntax enabled: {settings.detailed_format}")
```

---

## Practical Examples

### Example 1: Standard Application Logging Integration

```python
from globaldatafinance import FundamentalStocksDataCVM
from globaldatafinance.core import setup_logging, get_logger

# Activate operational logging
setup_logging(level="INFO", log_file="pipeline.log")

logger = get_logger(__name__)
logger.info("Application execution commenced")

# Execute library operations
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2023
)

logger.info("Application execution finished successfully")
```

### Example 2: Diagnostic Debugging Configuration

```python
from globaldatafinance import HistoricalQuotesB3
from globaldatafinance.core import setup_logging

# Enable DEBUG intensity alongside detailed function line signatures
setup_logging(
    level="DEBUG",
    log_file="/tmp/datafinance_debug.log",
    use_detailed_format=True
)

b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2023
)
```

### Example 3: Dedicated Module Logger Patterns

```python
# my_processing_pipeline.py
from globaldatafinance import FundamentalStocksDataCVM
from globaldatafinance.core import (
    setup_logging,
    get_logger,
    log_execution_time
)

setup_logging(level="INFO")
logger = get_logger(__name__)

def process_financial_filings():
    logger.info("Starting filing processing workflow")

    with log_execution_time(logger, "CVM Document Extraction"):
        cvm = FundamentalStocksDataCVM()
        cvm.download(
            destination_path="/data/cvm",
            list_docs=["DFP"],
            initial_year=2023
        )

    logger.info("Workflow execution completed cleanly")

if __name__ == "__main__":
    process_financial_filings()
```

---

## Log Layout specifications

### Default Syntax

```text
2025-11-25 17:30:00 | INFO     | module.name | Log text content
```

### Detailed Syntax

Appends exact module line numbering and caller function terminology:

```text
2025-11-25 17:30:00 | INFO     | module.name:123 | caller_function_name | Log text content
```

### Context-Enriched Syntax

```text
2025-11-25 17:30:00 | INFO     | module.name | Message | key1=value1 | key2=value2
```

---

## Best Practices

### 1. Consistently Register Module Hierarchies via `get_logger(__name__)`

```python
# ✅ Correct - preserve clean namespace nesting
logger = get_logger(__name__)

# ❌ Discouraged - using isolated literal identifier names
logger = get_logger("my_logger")
```

### 2. Match Severity Levels Accurately to Impact

```python
# ✅ Correct usage
logger.debug("Inspected iteration state variable: %s", value)
logger.info("Extraction loop commenced")
logger.warning("Archive verification checksum bypassed")
logger.error("Failed decompressing archive file", exc_info=True)

# ❌ Discouraged usage
logger.info("Loop index variable: %s", value)  # Should utilize DEBUG
logger.error("Completed extraction step")      # Should utilize INFO
```

### 3. Rely on Structured Metadata Dictionaries

```python
# ✅ Correct - explicit structured field assignment
logger.info(
    "Dataframe normalized",
    extra={"filename": "cotahist.parquet", "size_mb": 10.5}
)

# ❌ Discouraged - mixing unparseable values within string interpolation
logger.info(f"File cotahist.parquet processed with size: 10.5 MB")
```

### 4. Harness Context Managers for Latency Profiling

```python
# ✅ Correct - automated exception tracking and duration timing
with log_execution_time(logger, "Download Workflow"):
    download_files()

# ❌ Discouraged - manual timer bookkeeping
start = time.time()
download_files()
logger.info(f"Execution took {time.time() - start} seconds")
```

---

## Troubleshooting

### Log outputs are not displayed in the console

```python
# Confirm explicit initialization was performed
from globaldatafinance.core import setup_logging
setup_logging(level="INFO")
```

### Duplicate log statements emitting simultaneously

```python
# Ensure setup_logging() is not instantiated within internal functional loops;
# Re-invoking setup_logging() dynamically reconfigures existing root handlers cleanly.
setup_logging(level="DEBUG")
```

### Filesystem log generation fails with permissions exceptions

```python
# Ensure appropriate directory read/write capability exists for target destinations
setup_logging(level="INFO", log_file="/var/log/app.log")

# On unprivileged user workstations, direct sinks toward /tmp or user profile folders
setup_logging(level="INFO", log_file="/tmp/app.log")
```

---

## Related Documentation

- [Global Configuration](advanced-usage.md#global-configuration-tuning) - Settings & environment variables
- [Advanced Usage](advanced-usage.md) - Deep optimization patterns and integration recipes
