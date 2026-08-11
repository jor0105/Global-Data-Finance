# Architecture

Comprehensive documentation detailing the structural architecture of Global-Data-Finance, foundational design patterns, and internal module organization.

______________________________________________________________________

## Overview

Global-Data-Finance is a Python distribution library published via PyPI whose public API boundary is deliberately narrow — exposing at the package root level the core classes `FundamentalStocksDataCVM` and `HistoricalQuotesB3`, alongside the typed dictionary contract `ExtractionResultB3`. Internamente, each supported data source is implemented within its own dedicated directory utilizing a **flat layout of role-named modules**.

This architectural paradigm prioritizes:

- ✅ **Readability**: concise module files with explicit operational roles (CVM: `core.py`, `client.py`, `http.py`, `extract.py`, `errors.py`; B3: role-named modules — `client.py`, `assets.py`, `models.py`, `years.py`, `processing.py`, `filesystem.py`, `errors.py`, supplemented by domain subpackages)
- ✅ **Maintainability**: a clean, concise structure pragmatically aligned with module capabilities and functional boundaries
- ✅ **Extensibility**: integrating a new regulatory source = adding a sibling source folder implementing the identical flat role set
- ✅ **Testability**: straightforward dependency injection and duck typing to isolate and test components cleanly without ceremony

______________________________________________________________________

## Repository Structure

```text
globaldatafinance/
├── src/globaldatafinance/
│   ├── __init__.py                  # public top-level re-exports
│   ├── application/                 # PUBLIC FACADE LAYER (top-level)
│   │   ├── b3_docs/
│   │   │   ├── historical_quotes.py            # HistoricalQuotesB3
│   │   │   ├── extraction_result_formatter.py
│   │   │   └── result_formatters/
│   │   └── cvm_docs/
│   │       ├── fundamental_stocks_data.py      # FundamentalStocksDataCVM
│   │       └── download_result_formatter.py
│   ├── brazil/                      # SOURCE FEATURE IMPLEMENTATIONS
│   │   ├── b3_data/
│   │   │   └── historical_quotes/   # role-named modules + domain subpackages
│   │   │       ├── client.py                  # ExtractHistoricalQuotesUseCaseB3 + orchestration routines
│   │   │       ├── assets.py                  # AvailableAssetsServiceB3 (validation + TPMERC mapping)
│   │   │       ├── models.py                  # DocsToExtractorB3 (dataclass)
│   │   │       ├── years.py                   # YearRangeB3 (value object + boundary validators)
│   │   │       ├── processing.py              # ProcessingModeEnumB3, _ProcessingModeConfig
│   │   │       ├── filesystem.py              # FileSystemServiceB3.validate_directory_path
│   │   │       ├── errors.py                  # source-specific exception definitions
│   │   │       ├── zip_reader.py              # COTAHIST ZIP discovery and decompression
│   │   │       ├── cotahist_parser.py         # fixed-width positional parser (isolated domain module)
│   │   │       ├── parquet_writer/            # subpackage: Parquet compiler and writer
│   │   │       └── extraction_service/        # subpackage: thread-pool streaming orchestration
│   │   └── cvm/
│   │       └── fundamental_stocks_data/   # flat module layout (5 core modules + 2 helpers)
│   │           ├── core.py                    # AvailableDocsCVM, AvailableYearsCVM, DictZipsToDownloadCVM, DownloadResultCVM
│   │           ├── client.py                  # DownloadDocumentsUseCaseCVM, GenerateUrlsUseCaseCVM, VerifyPathsUseCasesCVM
│   │           ├── http.py                    # AsyncDownloadAdapterCVM (async httpx + retry + integrity check)
│   │           ├── extract.py                 # ParquetExtractorAdapterCVM
│   │           ├── download_validation.py     # validate_downloaded_file, validate_parquet_files, find_parquet_files
│   │           ├── download_extraction.py     # extract_downloaded_file (orchestrates extraction + validation)
│   │           └── errors.py                  # source-specific exception definitions
│   ├── core/                        # cross-cutting infrastructure utilities
│   ├── macro_infra/                 # shared generic HTTP and filesystem adapters
│   └── macro_exceptions/            # root project exception hierarchy
├── tests/                           # pytest suites mirroring src structure
├── docs/                            # MkDocs documentation corpus
└── pyproject.toml
```

______________________________________________________________________

## Source Module Patterns

Every folder under `brazil/<country>/<source>/` implements the identical set of **system roles**. The role-to-file mapping is unified in CVM (one designated file per role) and decomposed granularly in B3 (where pure data constructs and domain validation routines are broken into topical modules to prevent an oversized `core.py`). Introducing a new data source can adopt either pattern — the guiding principle is long-term code legibility.

| Architectural Role           | CVM                                                | B3                                                                                     |
| ---------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Pure data constructs         | `core.py`                                          | `models.py` + `years.py` + `processing.py`                                             |
| Validation / domain services | `core.py` (`AvailableDocsCVM.validate_*`)          | `assets.py` (`AvailableAssetsServiceB3`) + `filesystem.py` (`validate_directory_path`) |
| Orchestration / use cases    | `client.py`                                        | `client.py`                                                                            |
| HTTP network adaptation      | `http.py` (`AsyncDownloadAdapterCVM`)              | (N/A — COTAHIST ingestion operates on localized ZIP/TXT files via `zip_reader.py`)     |
| Extraction / Parquet writer  | `extract.py` (`ParquetExtractorAdapterCVM`)        | `parquet_writer/` (subpackage)                                                         |
| Format schema parser         | —                                                  | `cotahist_parser.py`                                                                   |
| Validation helpers           | `download_validation.py`, `download_extraction.py` | Embedded inside `filesystem.py` / `client.py`                                          |
| Exception definitions        | `errors.py`                                        | `errors.py`                                                                            |

Auxiliary utility classes or helper functions remain internal to their module unless explicitly consumed across boundaries — the true unit of extensibility in the codebase is the *source implementation*, not abstract object hierarchies.

> **Why B3 avoids a consolidated `core.py`.** The operational domain of B3 resides across topical modules (`assets.py`, `models.py`, `years.py`, `processing.py`, `filesystem.py`) rather than a single `core.py` because each topic possesses substantial critical mass (~100–300 lines of logic) and serves divergent internal callers. Consolidating them would sacrifice 5 clean, focused files in favor of an unwieldy monolith.

______________________________________________________________________

## Observable Architectural Layers

The repository is organized around **two well-delineated operational layers**:

### 1. Public Facade Layer (`application/`)

**Responsibility**: Maintains the semantic versioning contract exposed to external library consumers.

```python
# src/globaldatafinance/application/cvm_docs/fundamental_stocks_data.py
from ...brazil.cvm.fundamental_stocks_data import (
    AsyncDownloadAdapterCVM,
    DownloadDocumentsUseCaseCVM,
    DownloadResultCVM,
    ParquetExtractorAdapterCVM,
    # ...
)

class FundamentalStocksDataCVM:
    def __init__(self):
        self.download_adapter = AsyncDownloadAdapterCVM(...)
        self.__download_use_case = DownloadDocumentsUseCaseCVM(self.download_adapter)

    def download(self, destination_path, list_docs=None, initial_year=None, last_year=None):
        result = self.__download_use_case.execute(
            destination_path=destination_path,
            list_docs=list_docs,
            initial_year=initial_year,
            last_year=last_year,
        )
        self.__result_formatter.print_result(result)
        return result
```

The public facade imports **directly** from the source flat modules without traversing obscure re-exports in intermediate `brazil/__init__.py` bridges.

### 2. Source Implementation Layer (`brazil/<country>/<source>/`)

Each financial feed is self-contained across ~5–8 functional modules. CVM implementation example:

```python
# src/globaldatafinance/brazil/cvm/fundamental_stocks_data/core.py
class AvailableDocsCVM:
    DOCS_MAPPING = {
        'DFP': 'Demonstração Financeira Padronizada',
        'ITR': 'Informação Trimestral',
        # ...
    }

    def validate_docs_name(self, doc_name: str) -> None:
        if doc_name not in self.DOCS_MAPPING:
            raise InvalidDocumentName(f'Invalid document: {doc_name}')
```

```python
# src/globaldatafinance/brazil/cvm/fundamental_stocks_data/client.py
class DownloadDocumentsUseCaseCVM:
    def __init__(self, repository: AsyncDownloadAdapterCVM) -> None:
        self.__repository: AsyncDownloadAdapterCVM = repository
        # ...

    def execute(self, destination_path, list_docs=None, initial_year=None, last_year=None) -> DownloadResultCVM:
        start_time = time.time()
        # ... orchestration tasks ...
        result = self.__repository.download_docs(tasks)
        result.elapsed_time = time.time() - start_time
        return result
```

```python
# src/globaldatafinance/brazil/cvm/fundamental_stocks_data/http.py
class AsyncDownloadAdapterCVM:
    def download_docs(self, tasks) -> DownloadResultCVM:
        # Concrete implementation utilizing async httpx pools, retry policies, and MD5 integrity verification
        ...
```

The orchestration use case interacts with `AsyncDownloadAdapterCVM` via its observable method signature, allowing unit test suites to substitute lightweight duck-typed stubs without unnecessary mock framework overhead (see "Testing Patterns" below).

______________________________________________________________________

## Foundational Design Patterns

### Functions (or Lightweight Classes) per Operation in `client.py`

Most operations are modeled as clean module-level functions or concise classes focused strictly on their specialized operational responsibility, invoked directly by the application facade. Classes are utilized primarily when **reusable execution state exists**: for instance, `ExtractHistoricalQuotesUseCaseB3` preserves references to `zip_reader + parser + writer + processing_mode` across invocations and therefore remains structured as a class.

```python
# Pure operational helper in client.py
def generate_range_years(initial_year: int | None, last_year: int | None) -> list[int]:
    ...

# Stateful orchestration use case
class ExtractHistoricalQuotesUseCaseB3:
    def __init__(self, zip_reader, parser, writer, processing_mode):
        ...
    def execute(self, paths_of_docs, docs_to_extract):
        ...
```

### Direct and Concrete Adapters

Adapters governing network and filesystem I/O—such as `AsyncDownloadAdapterCVM` and `ParquetExtractorAdapterCVM`—are imported and instantiated directly within core runtime paths, ensuring maximum traceability and simplified navigation across the codebase.

### Explicit Result Objects

Operations capable of partial runtime failures return structured result dataclasses containing explicit success metrics and failure details, rather than executing disruptive `raise` exceptions upon encountering partial interruptions.

```python
@dataclass
class DownloadResultCVM:
    success_count_downloads: int
    error_count_downloads: int
    successful_downloads: list[str]
    failed_downloads: dict[str, str]
    elapsed_time: float

    def has_errors(self) -> bool:
        return self.error_count_downloads > 0
```

### Immutable Value Objects

Immutable domain constructs in `core.py` encapsulate data validation and initialization bounds (`DictZipsToDownloadCVM`, `DocsToExtractorB3`, etc.).

### Separation of Console Presentation

All CLI presentation output and console diagnostic reporting reside exclusively inside `*_formatter.py` modules within `application/`. Core business logic in `client.py` and domain modules remains completely free of direct formatting calls or interactive I/O.

### Preserved Path-Traversal Defense Contracts

`VerifyPathsUseCasesCVM` (CVM, inside `client.py`) and helper `FileSystemServiceB3` (B3, inside `filesystem.py`) evaluate directory structures and explicitly raise a `SecurityError` prior to any filesystem `mkdir` or file write, proactively blocking unauthorized execution inside restricted POSIX paths such as `/etc /sys /proc /dev /boot /root`. These defense boundaries form an invariant observable contract for `FundamentalStocksDataCVM.download(destination_path=...)` and `HistoricalQuotesB3.extract(path_of_docs=...)`—they must remain bit-identical across any future refactoring initiatives.

______________________________________________________________________

## Runtime Data Flows

### CVM Document Download Pipeline

```mermaid
graph TD
    A[FundamentalStocksDataCVM] -->|1. invoke download| B[DownloadDocumentsUseCaseCVM]
    B -->|2. validate input boundaries| C[AvailableDocsCVM / AvailableYearsCVM in core.py]
    B -->|3. compile URL targets| D[GenerateUrlsUseCaseCVM in client.py]
    B -->|4. path safety evaluation| E[VerifyPathsUseCasesCVM<br/>raise SecurityError on /etc, /sys, ...]
    B -->|5. trigger async worker pool| F[AsyncDownloadAdapterCVM in http.py]
    F -->|6. HTTP down-streaming| G[Remote CVM Servers]
    F -->|7. integrity check & write| H[Local Filesystem Storage]
    F -->|8. return operational statistics| B
    B -->|9. return DownloadResultCVM| A
    A -->|10. render console tracking| I[DownloadResultFormatter]
```

### B3 Historical Quote Extraction Pipeline

```mermaid
graph TD
    A[HistoricalQuotesB3] -->|1. invoke extract| B[ExtractHistoricalQuotesUseCaseB3]
    B -->|2. validate asset arguments| C[Domain validators in assets.py / years.py]
    B -->|3. evaluate target directory| D[validate_directory_path<br/>raise SecurityError on /etc, /sys, ...]
    B -->|4. discover archive targets| E[zip_reader.py]
    E -->|5. stream ZIP ascii entries| F[cotahist_parser.py]
    F -->|6. emit intermediate dataframes| G[extraction_service/]
    G -->|7. manage threadpool & memory flush| H[parquet_writer/]
    H -->|8. persist consolidated Parquet| I[Local Filesystem Storage]
    B -->|9. return ExtractionResultB3| A
    A -->|10. render execution outcome| J[ExtractionResultFormatter]
```

______________________________________________________________________

## Adding a New Data Source

To integrate a novel regulatory or exchange feed (e.g., US SEC filings), establish a new sibling directory implementing role-named operational modules. For compact data feeds, the streamlined 5-module CVM pattern provides an ideal baseline; for complex feeds, mirror the granular composition of B3 to segment topical logic before `core.py` exceeds manageable complexity thresholds.

```text
src/globaldatafinance/usa/sec/fundamental_data/
├── core.py        # entities, value objects, domain validators (consolidate if ≤ ~300 lines)
├── client.py      # orchestration routines / use cases
├── http.py        # concrete asynchronous HTTP download adapter
├── extract.py     # concrete extraction adapter (when applicable)
└── errors.py      # source-specific exception hierarchy
```

Subsequent integration steps:

1. **Internal Namespace**: Add an `__init__.py` file inside the source folder (or leave blank if no internal re-export aggregation is required).

2. **Public Application Facade**: Create `src/globaldatafinance/application/sec_docs/fundamental_data.py` containing a public facade class `FundamentalDataSEC` importing directly from your flat source modules:

   ```python
   from ...usa.sec.fundamental_data import (
       DownloadAdapterSEC,
       DownloadDocumentsUseCaseSEC,
       # ...
   )
   ```

3. **Package Boundary Export**: Re-export the new symbol inside `src/globaldatafinance/__init__.py` and `src/globaldatafinance/application/__init__.py`. Treat this as a **semver-sensitive feature expansion**.

4. **Test Suite Mirroring**: Establish `tests/usa/sec/fundamental_data/` grouped cleanly by functional topic. Test fixtures must import symbols directly from flat source modules.

5. **Documentation Alignment**: Register the new architecture map within `AGENTS.md` and this architecture guide, and author reference manuals inside `docs/reference/`.

______________________________________________________________________

## Testing Patterns

The repository test tree precisely mirrors source implementations:

```text
tests/
├── brazil/
│   ├── cvm/fundamental_stocks_data/
│   │   ├── application/use_cases/    # topical test grouping (organizational, not architectural)
│   │   ├── domain/                   # tests covering value objects and validators (core.py)
│   │   ├── infra/adapters/           # unit tests for concrete I/O adapters (http.py, extract.py)
│   │   ├── exceptions/               # test suites verifying custom exception triggers (errors.py)
│   │   └── integration/              # integration test markers
│   └── b3_data/historical_quotes/    # flat test layout: 21 test_*.py scripts within folder
└── application/
    ├── cvm_docs/   # unit tests covering public facades
    └── b3_docs/
        └── result_formatters/
```

Subdirectories inside the CVM testing hierarchy are strictly **organizational** (grouping files by topic to maximize scannability) rather than strict architectural assertions—test routines import directly from source modules via `from globaldatafinance.brazil.cvm.fundamental_stocks_data.client import ...`.

### Mock and Stub Strategies

To verify orchestrators and adapters cleanly in isolated environments without triggering real network or IO calls, tests employ simple dependency substitution:

- **Duck-typed Stubs**: Lightweight test classes implementing exclusively the target methods invoked by the orchestrator.
- **`monkeypatch.setattr`**: Patches targeted instance methods or attributes on concrete adapters during runtime execution.
- **`httpx.MockTransport`**: Supplies deterministic HTTP payload responses and simulated status codes for network adapter suites without requiring live server bindings.

Duck-typed stub example:

```python
class MockRepository:
    def download_docs(self, tasks):
        return DownloadResultCVM(
            success_count_downloads=2,
            error_count_downloads=0,
            successful_downloads=['DFP_2023', 'ITR_2023'],
            failed_downloads={},
        )

use_case = DownloadDocumentsUseCaseCVM(MockRepository())
result = use_case.execute(destination_path='/tmp/cvm')
assert result.success_count_downloads == 2
```

Test coverage gates are enforced per functional capability: `tests/brazil/<source>/` combined with `tests/application/<facade>/` thoroughly validates each data source as an autonomous subsystem.

______________________________________________________________________

## Next Steps

- 📖 **[API Reference](api-reference.md)** — Comprehensive surface signatures and interface descriptions
- 🤝 **[Contributing Guide](contributing.md)** — Rules and quality workflow for contributors
- 🧪 **[Testing Strategy](testing.md)** — Instructions on writing and running automated suites
- 🔧 **[Advanced Usage](advanced-usage.md)** — Deep performance tuning and customized execution profiles
