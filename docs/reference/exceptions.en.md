# Exception Reference

Complete structural catalog of custom error boundaries and exception types defined in Global-Data-Finance.

______________________________________________________________________

## Root Infrastructure Exceptions (`macro_exceptions`)

### `NetworkError`

```python
class NetworkError(Exception):
    """Network connection failure encountered during download operations."""
```

**Trigger Condition**: HTTP connection disruptions, socket timeouts, or TLS handshakes failures.

**Recommended Handling**:

```python
try:
    cvm.download(...)
except NetworkError as exc:
    print(f"Network transport interruption: {exc}")
    # Assess internet routing and implement retry back-off
```

### `TimeoutError`

```python
class TimeoutError(Exception):
    """Request timeout exceeded during socket read operations."""
```

**Trigger Condition**: Remote regulatory endpoints fail to respond within configured threshold boundaries.

### `ExtractionError`

```python
class ExtractionError(Exception):
    """Failure encountered during ZIP decompression or tabular translation."""
```

**Trigger Condition**: Archive corrupted headers or unexpected positional CSV/TXT formatting mismatches.

### `EmptyDirectoryError`

```python
class EmptyDirectoryError(Exception):
    """Target directory is empty or lacks compliant source files."""
```

**Trigger Condition**: Target source folders do not enclose necessary input files matching naming contracts.

### `InvalidDestinationPathError`

```python
class InvalidDestinationPathError(ValueError):
    """Target filesystem path destination is invalid or inaccessible."""
```

**Trigger Condition**: Target export directory access denied or restricted by OS authorization permissions.

### `DiskFullError`

```python
class DiskFullError(OSError):
    """Storage volume capacity exhaustion encountered."""
```

**Trigger Condition**: Available hard storage capacity depleted before file write completion.

### `SecurityError`

```python
class SecurityError(Exception):
    """Path safety check failed or restricted filesystem traversal detected."""
```

**Trigger Condition**: Attempted writing or directory creation aimed directly at system-level restricted POSIX routes (`/etc`, `/sys`, `/boot`, `/root`, etc.).

______________________________________________________________________

## CVM Domain Exceptions

### `InvalidDocumentName`

```python
class InvalidDocumentName(Exception):
    """Supplied document type acronym is unrecognized."""
```

**Trigger Condition**: Document parameter keyword falls outside supported CVM filing catalog.

**Recommended Handling**:

```python
try:
    cvm.download(list_docs=["UNSUPPORTED_CODE"])
except InvalidDocumentName:
    docs = cvm.get_available_docs()
    print(f"Supported document keywords: {list(docs.keys())}")
```

### `InvalidFirstYear`

```python
class InvalidFirstYear(Exception):
    """Supplied starting fiscal year falls outside valid boundaries."""
```

**Trigger Condition**: Requested initial year falls below historic floor (e.g., prior to 2010) or exceeds active system year.

### `InvalidLastYear`

```python
class InvalidLastYear(Exception):
    """Supplied ending fiscal year is invalid."""
```

**Trigger Condition**: Ending year precedes initial starting year or exceeds current operating year.

### `EmptyDocumentListError`

```python
class EmptyDocumentListError(Exception):
    """Document filter list parameter was supplied empty."""
```

**Trigger Condition**: An empty array (`[]`) was passed into `list_docs`.

______________________________________________________________________

## B3 Domain Exceptions

### `InvalidAssetsName`

```python
class InvalidAssetsName(Exception):
    """Supplied asset filter keyword is unrecognized."""
```

**Trigger Condition**: Asset parameter falls outside whitelist classifications supported by extraction rules.

**Recommended Handling**:

```python
try:
    b3.extract(assets_list=["unsupported_asset"])
except InvalidAssetsName:
    assets = b3.get_available_assets()
    print(f"Supported asset filters: {assets}")
```

### `EmptyAssetListError`

```python
class EmptyAssetListError(Exception):
    """Required assets filter list parameter was supplied empty."""
```

**Trigger Condition**: An empty array (`[]`) was supplied into mandatory `assets_list` argument.

______________________________________________________________________

## Exception Class Hierarchy

```text
Exception
├── NetworkError
├── TimeoutError
├── ExtractionError
│   └── CorruptedZipError
├── SecurityError
├── InvalidDocumentName
├── InvalidFirstYear
├── InvalidLastYear
├── InvalidAssetsName
├── EmptyAssetListError
├── EmptyDocumentListError
└── EmptyDirectoryError

ValueError
└── InvalidDestinationPathError

OSError
└── DiskFullError
```

______________________________________________________________________

## Comprehensive Exception Handling Pattern

```python
from globaldatafinance import FundamentalStocksDataCVM
from globaldatafinance.brazil.cvm.fundamental_stocks_data.errors import (
    InvalidDocumentName,
    InvalidFirstYear,
    InvalidLastYear,
)
from globaldatafinance.macro_exceptions import (
    NetworkError,
    TimeoutError,
    DiskFullError,
)

cvm = FundamentalStocksDataCVM()

try:
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2022
    )
except InvalidDocumentName as exc:
    print(f"Parameter validation fault: {exc}")
except InvalidFirstYear as exc:
    print(f"Temporal parameter boundary violation: {exc}")
except NetworkError as exc:
    print(f"Network connection failure: {exc}")
except TimeoutError as exc:
    print(f"Remote server request timeout: {exc}")
except DiskFullError as exc:
    print(f"Filesystem capacity exhaustion: {exc}")
except Exception as exc:
    print(f"Unexpected operational exception: {exc}")
```

> Source-specific exception definitions reside inside `errors.py` modules within their owning domain features (e.g., `brazil.cvm.fundamental_stocks_data.errors`, `brazil.b3_data.historical_quotes.errors`).

______________________________________________________________________

## Related Documentation

- [CVM API Reference](cvm-api.md)
- [B3 API Reference](b3-api.md)
- [Frequently Asked Questions](../user-guide/faq.md)
