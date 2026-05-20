# AGENTS.md

Project context for agentic coding agents working on the **Global-Data-Finance** codebase.

## Documentation Boundary

- `AGENTS.md` is the global project map: product purpose, architecture, layering rules, runtime model, and codebase navigation.
- `.agents/rules/*.md` is the canonical source for execution policy, safety protocol, validation discipline, and working rules.
- `.agents/README.md` documents the local agent framework itself.
- `docs/dev-guide/architecture.md` is the canonical long-form architecture reference; this file is the high-level map.

## System Snapshot

- `globaldatafinance` is a Python 3.12+ library (PyPI package) for extracting, normalizing, and persisting global financial and economic data.
- The library is distribution-shaped (`src/` layout, `hatchling` build, published via PyPI) — it is consumed as a dependency, not a running service.
- Current production data sources are Brazilian regulatory (CVM) and exchange (B3) feeds; the architecture is intentionally extensible to other markets.
- Core runtime traits are async/parallel I/O (`httpx[http2]`, `asyncio`), columnar processing (`polars`, `pandas`, `pyarrow`), and Parquet as the canonical output format.
- The codebase uses a **flat per-source module pattern**: each data source lives in `brazil/<country>/<source>/` with a small set of role-named modules (`core.py`, `client.py`, `http.py`/`extract.py`, `errors.py`, plus heavy parsing/IO files preserved as their own modules). The public facade lives in `application/`.

## Product Direction

- The product vision is a high-performance, clean-architecture toolkit that abstracts the messy reality of regulatory and market data behind small, predictable Python entrypoints.
- When tradeoffs appear, optimize for: throughput on bulk downloads, integrity of extracted data, clarity of the public API, and ease of adding new sources/adapters.
- Target users are Python developers, data scientists, quantitative analysts, and fintech teams who need reliable financial datasets without reinventing parsers and ETL.
- Near-term bias favors: more sources beyond Brazil, richer result/observability metadata, faster bulk extraction, and idiomatic typing throughout the public surface.

## Success Metrics

| Metric                              | Target                                |
| ----------------------------------- | ------------------------------------- |
| Test coverage (`pytest --cov`)      | `fail_under = 70` enforced by config  |
| Lint / format / typecheck           | 100% green (`ruff`, `mypy`, `bandit`) |
| Public API stability                | No silent contract changes            |
| Bulk download / extraction speedup  | Materially faster than naive baseline |

## Core Product Surfaces

- **CVM regulatory downloads** (`FundamentalStocksDataCVM`): bulk download of DFP, ITR, FRE, FCA, CGVN, VLMO, IPE with async concurrency, retries, integrity checks, and optional automatic extraction to Parquet.
- **B3 historical quotes** (`HistoricalQuotesB3`): parses legacy positional `COTAHIST` ZIP files into a consolidated Parquet dataset; supports asset filtering (ações, ETFs, BDRs, opções, termo, futuros) and `fast` / `slow` processing modes.
- **Result objects and formatters**: structured success/error reporting (`DownloadResultCVM`, extraction results) plus dedicated formatters that decouple console UX from business logic.
- **Cross-cutting infrastructure**: shared HTTP adapter, file extractor, resource monitor, retry strategy, progress reporting, and logging configuration in `core/` and `macro_infra/`.

## Repository Map

```text
repo root
├── src/globaldatafinance/    library source (Clean Architecture layers)
├── tests/                    pytest suites mirroring src/ structure
├── docs/                     MkDocs site (user-guide, dev-guide, reference)
├── examples/                 runnable usage snippets
├── pyproject.toml            project metadata, deps, ruff/mypy/bandit config
├── pytest.ini                pytest + coverage configuration
├── mkdocs.yml                documentation site config
├── .pre-commit-config.yaml   pre-commit hooks
├── uv.lock                   uv-managed dependency lockfile
├── .agents/                  local agent framework, rules, workflows
└── .github/                  CI workflows, issue templates, prompts
```

## Architecture Map

The package has two parallel axes:

1. A **public facade** in `application/` that users import.
2. **Feature implementations** in `brazil/<country>/<source>/`, each laid out as a **flat set of role-named modules** (no per-source `domain` / `application` / `infra` / `exceptions` subdirectories).

```text
src/globaldatafinance/
├── __init__.py                    re-exports the public API
├── application/                   PUBLIC FACADE — top-level entrypoints
│   ├── cvm_docs/
│   │   ├── fundamental_stocks_data.py     FundamentalStocksDataCVM
│   │   └── download_result_formatter.py
│   └── b3_docs/
│       ├── historical_quotes.py           HistoricalQuotesB3
│       ├── extraction_result_formatter.py
│       └── result_formatters/
├── brazil/                        FEATURE IMPLEMENTATIONS (Brazil sources)
│   ├── cvm/
│   │   └── fundamental_stocks_data/        ~5 flat modules
│   │       ├── core.py            entities, value objects, validators
│   │       ├── client.py          use-case-shaped functions + orchestrator
│   │       ├── http.py            AsyncDownloadAdapterCVM (HTTP I/O)
│   │       ├── extract.py         ParquetExtractorAdapterCVM (file extraction)
│   │       └── errors.py          feature-specific exceptions
│   └── b3_data/
│       ├── historical_quotes/     ~7–8 flat modules
│       │   ├── core.py            enums, value objects, validators, file-system safety
│       │   ├── client.py          use-case-shaped functions + ExtractHistoricalQuotesUseCaseB3 (stateful)
│       │   ├── cotahist_parser.py positional COTAHIST parser (preserved as own module)
│       │   ├── parquet_writer.py  Parquet writer (preserved as own module)
│       │   ├── extraction_service.py  streaming/threadpool orchestration (preserved as own module)
│       │   ├── zip_reader.py      ZIP reader
│       │   └── errors.py
│       ├── Dados_B3_Acoes/        pending-promotion B3 datasets (D8 — in-place; no internal callers)
│       ├── Dados_B3_FIIs/
│       └── Opcoes_B3/
├── core/                          cross-cutting utilities
│   ├── config.py                  pydantic-settings configuration
│   ├── logging_config.py          structured logging setup
│   └── utils/
│       ├── resource_monitor.py    CPU/RAM-aware concurrency
│       ├── retry_strategy.py      exponential backoff policy
│       └── progress.py            progress reporting
├── macro_infra/                   shared generic infrastructure
│   ├── requests_adapter.py        generic HTTP client wrapper
│   ├── extractor_file.py          generic ZIP / file extractor
│   └── read_files.py              file reading helpers
└── macro_exceptions/              project-wide exception base classes
```

### Test Layout

```text
tests/
├── core/                          mirrors src/.../core/
│   └── utils/
├── macro_infra/
├── macro_exceptions/
├── application/                   covers the public facade
│   ├── cvm_docs/
│   └── b3_docs/
│       └── result_formatters/
└── brazil/                        per-feature test trees
    ├── cvm/fundamental_stocks_data/   tests grouped by topic (domain types, use cases, adapters, integration)
    └── b3_data/historical_quotes/     tests grouped by topic (parser, writer, extraction, integration, type validation)
```

Test files import from the flat source paths (e.g. `from globaldatafinance.brazil.cvm.fundamental_stocks_data.client import DownloadDocumentsUseCaseCVM`). The test subdirectories under each feature are organizational, not architectural — they mirror logical groupings, not the (now removed) Clean Architecture layers.

Test files use `test_*.py`; the pytest config (`pytest.ini`) registers the markers `unit`, `integration`, `slow`, `asyncio` and enforces `--strict-markers`, `--strict-config`, and `--maxfail=1`.

### Documentation Layout

```text
docs/
├── index.md
├── user-guide/                    installation, quickstart, CVM/B3 usage, FAQ
├── dev-guide/                     architecture, testing, contributing, advanced usage
├── reference/                     per-module API reference (cvm-api, b3-api, exceptions)
└── assets/                        static assets for MkDocs Material
```

`mkdocs.yml` configures the documentation site; `mkdocs-material` is the theme.

## Per-source module pattern

Each `brazil/<country>/<source>/` directory uses a flat layout with role-named modules:

- `core.py` — pure data types (entities, value objects, enums), validators, and any path/file-safety helpers. No HTTP, no I/O side-effects beyond filesystem checks.
- `client.py` — use-case-shaped functions (or stateful orchestrator classes where adapters are reused across calls). Wires `core.py` types and `http.py` / `extract.py` adapters.
- `http.py` — concrete HTTP/download adapter for the source (e.g. `AsyncDownloadAdapterCVM`). Used directly; no ABC indirection.
- `extract.py` — concrete file/extraction adapter (e.g. `ParquetExtractorAdapterCVM`). Used directly; no ABC indirection.
- `errors.py` — feature-specific exception classes (subclasses of `macro_exceptions` bases).
- Heavy parsing/IO modules (e.g. B3 `cotahist_parser.py`, `parquet_writer.py`, `extraction_service.py`) stay as their own modules when their size or focus justifies it.

Cross-cutting rules:

- The public facade lives in `application/<facade>/<source>.py` and imports directly from the flat source modules (e.g. `from ...brazil.cvm.fundamental_stocks_data import DownloadDocumentsUseCaseCVM`).
- `core/` and `macro_infra/` are shared utilities consumable from any module, but they must stay generic — feature-specific logic does not belong here.
- `macro_exceptions/` holds project-wide exception base classes; feature-specific exceptions live inside the feature's `errors.py`.
- Intermediate `__init__.py` files (`brazil/__init__.py`, `brazil/<country>/__init__.py`, `brazil/<country_data>/__init__.py`) are intentionally near-empty. Re-exports live in two canonical places: the top-level `globaldatafinance/__init__.py` and each source's `__init__.py`.

When adding a new data source, create a new folder under the appropriate country/market namespace with the flat module set above (`core.py` + `client.py` minimum), and expose the public class via a new module under `src/globaldatafinance/application/`.

## Public API Surface

The public surface is intentionally narrow. Everything users import lives under the top-level package:

```python
from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3
```

These two classes are re-exported in `src/globaldatafinance/__init__.py`. Any new public entrypoint must be re-exported there to be part of the API contract. Treat additions as semver-relevant changes.

**Pending-promotion paths.** `brazil/b3_data/{Dados_B3_Acoes, Dados_B3_FIIs, Opcoes_B3}`, `brazil/gerais/`, and `brazil/app_geral.py` are kept in-place but are explicitly **out of scope** for the flat per-source pattern. They have no internal callers and will be promoted (per source) in future OpenSpec changes that bring each one onto the `core.py` / `client.py` convention.

## Design Patterns In Use

- **Function-per-operation in `client.py`**: most operations are module-level functions or classes with a single public method, called directly from the facade — no `execute(...)`-only wrappers and no single-impl ABCs. Classes are reserved for genuine stateful orchestration (e.g. `ExtractHistoricalQuotesUseCaseB3` caches its adapters across calls).
- **Concrete adapters, no ABC indirection**: HTTP and extraction adapters (`AsyncDownloadAdapterCVM`, `ParquetExtractorAdapterCVM`, etc.) are imported and constructed directly. The pre-refactor `DownloadDocsCVMRepositoryCVM` / `FileExtractorRepositoryCVM` interfaces and `ExtractionServiceFactoryB3` were removed when they had a single implementation.
- **Result objects**: operations return typed result dataclasses (e.g. `DownloadResultCVM`) with explicit success / failure breakdowns instead of raising for partial failures.
- **Value Objects**: immutable types (e.g. `DictZipsToDownloadCVM`, `DocsToExtractorB3`) encapsulate validation and construction; they live in `core.py`.
- **Formatter separation**: presentation/console output lives in dedicated `*_formatter.py` modules under `application/` so the `client.py` layer stays I/O-free.
- **Path-traversal defense as contract**: `VerifyPathsUseCasesCVM` (CVM `client.py`) and the `validate_directory_path` helper (B3 `core.py`) raise `SecurityError` before any `mkdir`, blocking writes to `/etc /sys /proc /dev /boot /root`. Behavior must stay bit-identical when these helpers move.

See `docs/dev-guide/architecture.md` for worked examples of each pattern.

## Runtime And I/O Model

- HTTP I/O is async via `httpx[http2]` with custom retry/backoff (`core/utils/retry_strategy.py`).
- Concurrency is adaptive: `core/utils/resource_monitor.py` reads CPU/RAM (`psutil`) to keep download fan-out within machine capacity.
- File integrity is validated after each download (ZIP / hash checks) before extraction is attempted.
- B3 historical quotes have two processing modes: `fast` (in-memory, faster, higher RAM) and `slow` (streamed, lower RAM).
- The canonical persisted format is **Parquet** (`pyarrow` writers, `polars`/`pandas` readers). New sources should default to Parquet output.
- Logging is configured by `core/logging_config.py` and is the only sanctioned observability channel inside the library — do not `print(...)` from non-formatter code.

## Configuration Surfaces

- `pyproject.toml` is the single source of truth for dependencies, build, and tooling config. Project pins **Python 3.12+** (also classified for 3.13 / 3.14).
- `core/config.py` uses `pydantic-settings` for runtime configuration where applicable.
- Tooling config (all inside `pyproject.toml` unless noted):
  - `ruff`: `line-length = 79`, single quotes, Blue-style formatting.
  - `mypy`: `python_version = "3.12"`, `warn_return_any`, `ignore_missing_imports`.
  - `bandit`: excludes `.venv`; tests skip `B101`/`B108`.
  - `pydocstyle`: Google convention, only on non-test files.
  - `pytest.ini`: testpaths `tests`, coverage `fail_under = 70`, strict markers/config.
  - `.pre-commit-config.yaml`: orchestrates lint/format/typecheck/security hooks.

## Validation Workflow

Before declaring code changes done, run the repo-native validation entrypoints:

```bash
# Format + lint + static checks (pre-commit runs ruff, mypy, bandit, pydocstyle, etc.)
uv run pre-commit run --all-files

# Tests (coverage enforced at fail_under = 70)
uv run pytest

# Optional: filter by marker
uv run pytest -m unit
uv run pytest -m "integration and not slow"
```

`uv` is the canonical environment/dependency manager (`uv.lock` is committed). Poetry usage in docs is historical; prefer `uv` for local workflows unless instructed otherwise.

## Related Documentation

- `README.md`: user-facing introduction, install, quickstart, API summary.
- `docs/user-guide/`: installation, quickstart, per-source usage, FAQ.
- `docs/dev-guide/architecture.md`: full Clean Architecture walkthrough with examples.
- `docs/dev-guide/testing.md`: how to write and run tests, fixtures, markers.
- `docs/dev-guide/contributing.md`: contribution workflow and standards.
- `docs/dev-guide/{resource-monitoring,retry-strategy,logging-system}.md`: cross-cutting infrastructure references.
- `docs/reference/{cvm-api,b3-api,exceptions}.md`: per-module API reference.
- `.agents/rules/*.md`: canonical execution, safety, and validation rules.
- `.agents/README.md`: local agent ownership, prompts, manifests, workflows.
