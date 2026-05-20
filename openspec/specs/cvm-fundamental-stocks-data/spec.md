# Capability: CVM Fundamental Stocks Data

## Purpose
TBD - Bulk download of CVM regulatory documents (DFP, ITR, etc.) with adaptive concurrency, integrity checks, and automatic extraction to Parquet format.

## Requirements

### Requirement: Public client class exposed via top-level package

The library SHALL expose a public class `FundamentalStocksDataCVM` re-exported from the top-level package (`from globaldatafinance import FundamentalStocksDataCVM`). The class SHALL be instantiable with no arguments and SHALL be the only sanctioned entrypoint for CVM regulatory document operations.

#### Scenario: Import from top-level package

- **WHEN** a user runs `from globaldatafinance import FundamentalStocksDataCVM`
- **THEN** the import resolves successfully without requiring any submodule path

#### Scenario: Construction with no arguments

- **WHEN** a user runs `FundamentalStocksDataCVM()`
- **THEN** an instance is returned with all internal collaborators (download adapter, extractor, use cases, formatter) wired with defaults

#### Scenario: String representation

- **WHEN** a user runs `repr(FundamentalStocksDataCVM())`
- **THEN** the returned string is exactly `'FundamentalStocksDataCVM()'`

### Requirement: Bulk download of CVM regulatory documents

The client SHALL provide a `download(destination_path, list_docs=None, initial_year=None, last_year=None, automatic_extractor=False)` method that downloads CVM regulatory ZIP documents (DFP, ITR, FRE, FCA, CGVN, VLMO, IPE) to a local directory and returns a `DownloadResultCVM` object aggregating per-file successes and failures.

#### Scenario: Download succeeds for valid inputs

- **WHEN** a user calls `download(destination_path, list_docs=['DFP'], initial_year=2020, last_year=2023)` with a valid writable path and the CVM endpoints reachable
- **THEN** the requested ZIPs are persisted under `destination_path` and a `DownloadResultCVM` is returned with `success_count_downloads`, `error_count_downloads`, `successful_downloads`, `failed_downloads`, and `elapsed_time` populated

#### Scenario: Destination directory is created on demand

- **WHEN** `destination_path` does not exist but is writable
- **THEN** the method creates the directory and proceeds without raising

#### Scenario: Sensitive destination path is rejected before directory creation

- **WHEN** `destination_path` resolves inside `/etc`, `/sys`, `/proc`, `/dev`, `/boot`, or `/root`
- **THEN** the method raises `SecurityError` before creating directories or writing files

#### Scenario: list_docs=None selects all available document types

- **WHEN** the user omits `list_docs` (or passes `None`)
- **THEN** the method downloads all document types returned by `get_available_docs()`

#### Scenario: initial_year=None resolves to the minimum supported year

- **WHEN** the user omits `initial_year` (or passes `None`)
- **THEN** the method uses the minimum year applicable to each document type as returned by `get_available_years()`

#### Scenario: last_year=None resolves to the current year

- **WHEN** the user omits `last_year` (or passes `None`)
- **THEN** the method uses the current calendar year as the upper bound

#### Scenario: Invalid document name raises InvalidDocName

- **WHEN** `list_docs` contains a code that is not in `get_available_docs()`
- **THEN** the method raises `InvalidDocName`

#### Scenario: initial_year outside the valid range raises InvalidFirstYear

- **WHEN** `initial_year` is below the minimum supported year for the requested document types or above the current year
- **THEN** the method raises `InvalidFirstYear`

#### Scenario: last_year outside the valid range raises InvalidLastYear

- **WHEN** `last_year` is below `initial_year` or above the current year
- **THEN** the method raises `InvalidLastYear`

#### Scenario: Non-boolean automatic_extractor raises TypeError

- **WHEN** `automatic_extractor` is provided with a non-boolean value
- **THEN** the method raises `TypeError` with a message naming the offending type

#### Scenario: Partial failures are reported, not raised

- **WHEN** one or more individual file downloads fail (e.g. transient HTTP errors after retries) while at least one succeeds
- **THEN** the method returns a `DownloadResultCVM` with `error_count_downloads > 0` and the corresponding entries in `failed_downloads`, without raising

### Requirement: Optional Parquet extraction during download

The `download` method SHALL accept `automatic_extractor: bool = False`. When `True`, downloaded ZIP files SHALL be extracted to Parquet format using the bundled file extractor. When `False`, only the original ZIP files SHALL be persisted.

#### Scenario: automatic_extractor=True triggers Parquet extraction

- **WHEN** `automatic_extractor=True` is passed and downloads succeed
- **THEN** the corresponding Parquet artifacts are produced alongside or in place of the downloaded ZIPs, according to the extractor's policy

#### Scenario: automatic_extractor=False keeps ZIPs untouched

- **WHEN** `automatic_extractor=False` (or omitted) is passed
- **THEN** the downloaded ZIP files remain in `destination_path` without extraction

### Requirement: Discover available document types

The client SHALL provide `get_available_docs() -> Dict[str, str]` returning a mapping from document type code (e.g. `'DFP'`, `'ITR'`, `'FCA'`, `'FRE'`, `'CGVN'`, `'VLMO'`, `'IPE'`) to its human-readable description.

#### Scenario: Mapping is non-empty and includes known codes

- **WHEN** a user calls `get_available_docs()`
- **THEN** the returned dictionary is non-empty and contains at least the entries for `'DFP'` and `'ITR'`

#### Scenario: Result is suitable for membership checks

- **WHEN** a user checks `'DFP' in cvm.get_available_docs()`
- **THEN** the expression evaluates to `True`

### Requirement: Discover available year ranges

The client SHALL provide `get_available_years() -> Dict[str, int]` returning the minimum years available per document family plus the current calendar year, keyed by `'General Document Years'`, `'ITR Document Years'`, `'CGVN and VMLO Document Years'`, and `'Current Year'`.

#### Scenario: Result contains all expected keys

- **WHEN** a user calls `get_available_years()`
- **THEN** the returned dictionary contains all four keys above, each mapped to an integer year

#### Scenario: Current Year matches the system year

- **WHEN** a user calls `get_available_years()`
- **THEN** `result['Current Year']` equals the current calendar year on the host

### Requirement: Structured result object for download operations

The `download` method SHALL return a `DownloadResultCVM` object that records per-file outcomes via `add_success_downloads()` / `add_error_downloads()` and exposes at minimum: `success_count_downloads`, `error_count_downloads`, `successful_downloads`, `failed_downloads`, `elapsed_time`. Result construction SHALL NOT depend on console formatting; presentation SHALL be delegated to a dedicated formatter.

#### Scenario: elapsed_time is populated

- **WHEN** `download(...)` returns
- **THEN** `result.elapsed_time` is a non-negative float measured from the start of the download to its completion

#### Scenario: Formatter is decoupled from result construction

- **WHEN** the public `download(...)` is called
- **THEN** the returned `DownloadResultCVM` is identical regardless of whether console output is suppressed, and console rendering is performed by a dedicated formatter module
