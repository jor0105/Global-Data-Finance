# API Reference

Complete high-level architectural documentation reference covering the public surface of Global-Data-Finance.

______________________________________________________________________

## Module `globaldatafinance` (Public Root Exports)

The primary entrypoint classes and contracts are exposed directly at the top-level package boundary:

### `FundamentalStocksDataCVM`

Public interface facade responsible for managing regulatory CVM financial filing downloads and Parquet extractions.

#### Methods

**`__init__()`**

```python
def __init__(self) -> None
```

Initializes the CVM client facade configuring standard async down-streaming adapters and underlying use case pipelines.

**`download()`**

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

Downloads regulatory CVM archives directly into a local filesystem directory.

**Parameters**:

- `destination_path` (`str`): Target destination storage directory.
- `list_docs` (`List[str]`, optional): Selected document type codes (e.g., `["DFP", "ITR"]`). Defaults to all supported document categories when omitted.
- `initial_year` (`int`, optional): Starting historical fiscal year (inclusive).
- `last_year` (`int`, optional): Ending fiscal year (inclusive). Defaults to the active system year.
- `automatic_extractor` (`bool`): When set to `True`, deconstructs downloaded ZIP ledgers into columnar Apache Parquet files.

**`get_available_docs()`**

```python
def get_available_docs(self) -> Dict[str, str]
```

Returns an introspectable dictionary mapping permissible document acronym codes to their descriptive Portuguese legal classifications.

**`get_available_years()`**

```python
def get_available_years(self) -> Dict[str, int]
```

Returns a structural dictionary summarizing permissible temporal starting floors and current operating system year limits across distinct document categories.

______________________________________________________________________

### `HistoricalQuotesB3`

Public interface facade governing historical market exchange quote extraction from official B3 COTAHIST repositories.

#### Methods

**`__init__()`**

```python
def __init__(self) -> None
```

Initializes the B3 extraction facade and registers underlying asset classification mappers and extraction service pipelines.

**`extract()`**

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

Parses COTAHIST ZIP or TXT archives, extracts transaction registers corresponding to selected asset classifications, and compiles them directly into a consolidated Apache Parquet output file.

**Parameters**:

- `path_of_docs` (`str`): Source directory enclosing target raw COTAHIST archives (`COTAHIST_AYYYY.ZIP` or `.TXT`).
- `assets_list` (`List[str]`): Required asset category filtering tags (e.g., `["ações", "etf"]`).
- `initial_year` (`int`, optional): Historical beginning fiscal year (lower bound floor: 1986).
- `last_year` (`int`, optional): Ending fiscal year (defaults to current system operational year).
- `destination_path` (`str`, optional): Custom directory destination for the generated Parquet artifact (defaults to `path_of_docs` when omitted).
- `output_filename` (`str`): Base output filename for the created Parquet file (omit `.parquet` file extension).
- `processing_mode` (`str`): Computational execution mode: `"fast"` (multi-threaded in-memory processing) or `"slow"` (minimal RAM incremental stream processing).

**Returns**:

- `ExtractionResultB3` (`Dict[str, Any]`): A diagnostic mapping containing runtime confirmation metrics including `success`, `total_records`, `output_file`, `success_count`, and stack trace `errors`.

**`get_available_assets()`**

```python
def get_available_assets(self) -> List[str]
```

Returns a comprehensive list of permissible asset category string parameters supported by extraction filtering rules.

**`get_available_years()`**

```python
def get_available_years(self) -> Dict[str, int]
```

Returns dictionary defining available lower temporal boundaries (`minimal_year`: 1986) and upper bound operational limits (`current_year`).

______________________________________________________________________

## Related References

For specialized technical contracts and deep internal structural references, consult:

- [CVM API Specification](../reference/cvm-api.md) - Deep architectural breakdown of CVM processing pipelines
- [B3 API Specification](../reference/b3-api.md) - Detailed technical documentation for B3 extraction contracts
- [Exception Hierarchy](../reference/exceptions.md) - Diagnostic reference covering project exception classes
