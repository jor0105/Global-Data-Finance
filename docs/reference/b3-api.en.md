# B3 API - Technical Specification

Detailed technical specification covering the B3 historical quote extraction API.

______________________________________________________________________

## HistoricalQuotesB3

### Primary Class Definition

```python
class HistoricalQuotesB3:
    """High-level facade for B3 market quote extraction and normalization."""
```

### Public Methods

#### `extract()`

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

**Description**: Parses COTAHIST archives, filters target asset transactions, and compiles a unified Parquet file.

**Parameters**:

| Parameter          | Type            | Required | Default                | Description                      |
| ------------------ | --------------- | -------- | ---------------------- | -------------------------------- |
| `path_of_docs`     | `str`           | Yes      | -                      | Source folder with COTAHIST ZIPs |
| `assets_list`      | `List[str]`     | Yes      | -                      | Targeted asset categories        |
| `initial_year`     | `Optional[int]` | No       | `1986`                 | Initial historical fiscal year   |
| `last_year`        | `Optional[int]` | No       | Active System Year     | Ending historical fiscal year    |
| `destination_path` | `Optional[str]` | No       | Matches `path_of_docs` | Output artifact destination      |
| `output_filename`  | `str`           | No       | `"cotahist_extracted"` | Target Parquet base filename     |
| `processing_mode`  | `str`           | No       | `"fast"`               | Execution mode: "fast"/"slow"    |

**Return Contract (`ExtractionResultB3`)**: Diagnostic mapping dictionary featuring:

- `success` (`bool`): Success status confirmation for overall execution
- `message` (`str`): Human-readable conclusion status note
- `total_files` (`int`): Total count of candidate archives inspected
- `success_count` (`int`): Count of cleanly extracted archive bundles
- `error_count` (`int`): Count of corrupted or incompatible files skipped
- `total_records` (`int`): Aggregate count of financial transactions consolidated
- `output_file` (`str`): Absolute filesystem path of produced Parquet file
- `errors` (`List[str]`): Detailed stack traces or parser validation errors

**Raised Exceptions**:

- `EmptyAssetListError`: Empty array supplied for `assets_list` parameter
- `InvalidAssetsName`: Supplied instrument keyword unsupported by filter rules
- `InvalidFirstYear`: Initial year parameter set below 1986 historical floor
- `InvalidLastYear`: Ending year preceded initial year or surpassed active year limits
- `EmptyDirectoryError`: Target source directory lacked valid COTAHIST input archives
- `ExtractionError`: Corruption or positional alignment errors encountered during parsing

**Execution Example**:

```python
b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf"],
    initial_year=2022,
    last_year=2023,
    processing_mode="fast"
)
print(f"✓ Consolidated {result['total_records']:,} trading records")
```

#### `get_available_assets()`

```python
def get_available_assets(self) -> List[str]
```

**Description**: Returns an exhaustive whitelist of permissible asset filter strings.

**Return Structure**: List of instrument string identifiers.

**Execution Example**:

```python
assets = b3.get_available_assets()
# Returns: ['ações', 'etf', 'opções', ...]
```

#### `get_available_years()`

```python
def get_available_years(self) -> Dict[str, int]
```

**Description**: Queries bounding boundaries representing permissible historical time horizons.

**Return Structure**: Dictionary featuring:

- `"minimal_year"`: Floor starting year (1986)
- `"current_year"`: Real-time operational system year

**Execution Example**:

```python
years = b3.get_available_years()
# Returns: {'minimal_year': 1986, 'current_year': active_year}
```

______________________________________________________________________

## Asset Classification Codes

| Code Identifier  | Description          | Included Market Segments                 |
| ---------------- | -------------------- | ---------------------------------------- |
| ações            | Equities / Stocks    | 010 (spot cash market), 012 (fractional) |
| etf              | ETFs                 | Exchange Traded Fund structures          |
| opções           | Options              | 070 (calls), 080 (puts)                  |
| termo            | Forward Term Markets | Forward clearing agreements              |
| exercicio_opcoes | Option Exercises     | Exercised contract transactions          |
| forward          | Forward Contracts    | Over-the-counter and forward agreements  |
| leilao           | Auction Market       | Extraordinary clearing auction registers |

______________________________________________________________________

## Computational Execution Modes

| Processing Mode | Speed Profile | CPU Load  | RAM Demand | Recommended Operating Profile          |
| --------------- | ------------- | --------- | ---------- | -------------------------------------- |
| fast            | Maximum       | Intensive | ~2GB       | Default profile for standard workflows |
| slow            | Moderate      | Low       | ~500MB     | Constrained RAM server environments    |

______________________________________________________________________

## Related Documentation

- [B3 User Guide](../user-guide/b3-docs.md)
- [Exception Hierarchy](exceptions.md)
