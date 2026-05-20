# Capability: B3 Historical Quotes

## Purpose
TBD - B3 positional COTAHIST historical quotes ZIP files extraction, parsing, filtering, and consolidation into a single Parquet dataset.

## Requirements

### Requirement: Public client class exposed via top-level package

The library SHALL expose a public class `HistoricalQuotesB3` re-exported from the top-level package (`from globaldatafinance import HistoricalQuotesB3`). The class SHALL be instantiable with no arguments and SHALL be the only sanctioned entrypoint for B3 historical quotes extraction.

#### Scenario: Import from top-level package

- **WHEN** a user runs `from globaldatafinance import HistoricalQuotesB3`
- **THEN** the import resolves successfully without requiring any submodule path

#### Scenario: Construction with no arguments

- **WHEN** a user runs `HistoricalQuotesB3()`
- **THEN** an instance is returned with all internal collaborators (extract orchestrator, validators, formatter) wired with defaults

#### Scenario: String representation

- **WHEN** a user runs `repr(HistoricalQuotesB3())`
- **THEN** the returned string is exactly `'HistoricalQuotesB3()'`

### Requirement: Extract COTAHIST ZIPs to consolidated Parquet

The client SHALL provide `extract(path_of_docs, assets_list, initial_year=None, last_year=None, destination_path=None, output_filename='cotahist_extracted', processing_mode='fast')` that reads B3 COTAHIST positional ZIP files from `path_of_docs`, parses them, filters by `assets_list`, and writes a single consolidated Parquet dataset to `destination_path`.

#### Scenario: Successful extraction returns enriched result dict

- **WHEN** a user calls `extract(path_of_docs, assets_list=['ações'], initial_year=2022, last_year=2023)` with a folder containing valid COTAHIST ZIPs
- **THEN** the method returns a dictionary with keys `success`, `message`, `total_files`, `success_count`, `error_count`, `total_records`, `output_file`, `assets`, `processing_mode`, `elapsed_time`

#### Scenario: destination_path=None defaults to path_of_docs

- **WHEN** the user omits `destination_path`
- **THEN** the Parquet output is written to `path_of_docs`

#### Scenario: Destination directory is created on demand

- **WHEN** `destination_path` does not exist but is writable
- **THEN** the method creates the directory and proceeds without raising

#### Scenario: Sensitive input directory is rejected before ZIP enumeration

- **WHEN** `path_of_docs` resolves inside `/etc`, `/root`, `/sys`, `/proc`, `/dev`, or `/boot`
- **THEN** the method raises `SecurityError` before enumerating ZIP files

#### Scenario: initial_year=None resolves to the minimal supported year

- **WHEN** the user omits `initial_year` (or passes `None`)
- **THEN** the method uses the minimal supported year `1986`

#### Scenario: last_year=None resolves to the current year

- **WHEN** the user omits `last_year` (or passes `None`)
- **THEN** the method uses the current calendar year as the upper bound

#### Scenario: Empty asset list raises EmptyAssetListError

- **WHEN** `assets_list` is empty or not a list
- **THEN** the method raises `EmptyAssetListError`

#### Scenario: Unknown asset class raises InvalidAssetsName

- **WHEN** `assets_list` contains a code that is not in `get_available_assets()`
- **THEN** the method raises `InvalidAssetsName`

#### Scenario: initial_year outside valid range raises InvalidFirstYear

- **WHEN** `initial_year` is below `1986` or above the current year
- **THEN** the method raises `InvalidFirstYear`

#### Scenario: last_year outside valid range raises InvalidLastYear

- **WHEN** `last_year` is below `initial_year` or above the current year
- **THEN** the method raises `InvalidLastYear`

#### Scenario: Partial parsing failures are reported, not raised

- **WHEN** one or more individual ZIPs fail to parse while at least one succeeds
- **THEN** the method returns the result dictionary with `error_count > 0` and entries under `errors`, without raising

### Requirement: Supported asset classes

The `extract` method SHALL accept `assets_list` values drawn from the supported asset classes: `'ações'`, `'etf'`, `'opções'`, `'termo'`, `'exercicio_opcoes'`, `'forward'`, `'leilao'`. The client SHALL expose `get_available_assets() -> List[str]` returning this list.

#### Scenario: Default asset list is non-empty and stable

- **WHEN** a user calls `get_available_assets()`
- **THEN** the returned list is non-empty and contains at least `'ações'` and `'etf'`

#### Scenario: Membership check supports input validation

- **WHEN** a user checks `'ações' in b3.get_available_assets()`
- **THEN** the expression evaluates to `True`

### Requirement: Processing modes for resource tradeoffs

The `extract` method SHALL accept `processing_mode='fast'` or `processing_mode='slow'`. Fast mode SHALL prioritize throughput at the cost of higher CPU/RAM; slow mode SHALL prioritize lower resource usage at the cost of throughput. Both modes SHALL produce the same Parquet output schema and record set for the same inputs.

#### Scenario: Fast mode is the default

- **WHEN** the user omits `processing_mode`
- **THEN** the method runs in `'fast'` mode

#### Scenario: Slow mode is accepted

- **WHEN** the user passes `processing_mode='slow'`
- **THEN** the method runs in `'slow'` mode and produces the same output schema as fast mode

#### Scenario: Invalid processing mode is rejected by validation

- **WHEN** the user passes a `processing_mode` not in `{'fast', 'slow'}`
- **THEN** the validation step raises `InvalidProcessingMode` before any ZIP is read

### Requirement: Output filename control

The `extract` method SHALL accept `output_filename: str = 'cotahist_extracted'`. The `.parquet` extension SHALL be appended automatically by the validation step; the user SHALL NOT be required to provide it.

#### Scenario: Default output filename

- **WHEN** the user omits `output_filename`
- **THEN** the output file is `cotahist_extracted.parquet`

#### Scenario: Custom filename without extension

- **WHEN** the user passes `output_filename='stocks_2020_2023'`
- **THEN** the output file is `stocks_2020_2023.parquet`

### Requirement: Discover available year range

The client SHALL provide `get_available_years() -> Dict[str, int]` returning a dictionary with keys `'minimal_year'` and `'current_year'`, mapping to the minimum supported COTAHIST year (`1986`) and the current calendar year respectively.

#### Scenario: Result contains both keys

- **WHEN** a user calls `get_available_years()`
- **THEN** the returned dictionary contains `'minimal_year'` and `'current_year'`, each mapped to an integer

#### Scenario: minimal_year is 1986

- **WHEN** a user calls `get_available_years()`
- **THEN** `result['minimal_year']` equals `1986`

#### Scenario: current_year matches the system year

- **WHEN** a user calls `get_available_years()`
- **THEN** `result['current_year']` equals the current calendar year on the host

### Requirement: Structured result with elapsed time and presentation decoupling

The `extract` method SHALL return a dictionary enriched with the metadata fields `assets`, `processing_mode`, and `elapsed_time`. Result enrichment SHALL be performed by a dedicated formatter module; console rendering SHALL be delegated to a separate formatter and SHALL NOT alter the returned dictionary.

#### Scenario: elapsed_time is populated

- **WHEN** `extract(...)` returns
- **THEN** `result['elapsed_time']` is a non-negative float measured from the start of extraction to its completion

#### Scenario: Result is identical regardless of console output

- **WHEN** the public `extract(...)` is called
- **THEN** the returned dictionary is identical regardless of whether console output is suppressed, and console rendering is performed by a dedicated formatter module
