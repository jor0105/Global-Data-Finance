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
- The codebase follows Clean Architecture with strict layering: `domain` → `application` → `infra`, plus a public `application/` facade.

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

The package follows Clean Architecture with two parallel axes:

1. A **public facade** in `application/` that users import.
2. **Feature implementations** in `brazil/` (per source/market), each split into the canonical `domain` / `application` / `infra` / `exceptions` layers.

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
│   │   └── fundamental_stocks_data/
│   │       ├── domain/            entities, value objects, validators
│   │       ├── application/       use cases + repository interfaces
│   │       │   ├── interfaces/
│   │       │   └── use_cases/
│   │       ├── infra/             adapters (HTTP, extractors)
│   │       │   └── adapters/
│   │       │       ├── requests_adapter/
│   │       │       └── extractors_docs_adapter/
│   │       └── exceptions/
│   └── b3_data/
│       ├── historical_quotes/     same 4-layer split as CVM
│       │   ├── domain/{entities,services,value_objects}/
│       │   ├── application/use_cases/
│       │   ├── infra/
│       │   └── exceptions/
│       ├── Dados_B3_Acoes/        legacy/ancillary B3 datasets
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
└── brazil/                        mirrors each feature's 4 layers
    ├── cvm/fundamental_stocks_data/{domain,application,infra,integration,exceptions}/
    └── b3_data/historical_quotes/{domain,application,infra,integration}/
        └── domain/{entities,services,value_objects,exceptions}/
```

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

## Layering Rules

Layer dependencies flow inward only — outer layers depend on inner abstractions, never the reverse:

- `domain/` has **no dependencies** on `application/` or `infra/`. Pure entities, value objects, validators, and business rules. Imports from `core/` or `macro_exceptions/` only when strictly needed.
- `application/` (inside a feature) defines **use cases** and **repository interfaces** (`ABC` classes). It depends on `domain/`, never on `infra/`.
- `infra/` provides **concrete adapters** that implement the repository interfaces from `application/`. Holds the HTTP client, file extractor, and any other external-system glue.
- `application/` at the **package root** is the **public facade**: it wires concrete adapters into use cases and exposes the user-facing classes (`FundamentalStocksDataCVM`, `HistoricalQuotesB3`).
- `core/` and `macro_infra/` are shared utilities consumable from any layer, but they must stay generic — feature-specific logic does not belong here.
- `macro_exceptions/` holds project-wide exception base classes; feature-specific exceptions live inside the feature's `exceptions/` folder.

When adding a new data source, replicate the 4-layer split (`domain` / `application` / `infra` / `exceptions`) inside a new feature folder under the appropriate country/market namespace, and expose the public class via a new module under `src/globaldatafinance/application/`.

## Public API Surface

The public surface is intentionally narrow. Everything users import lives under the top-level package:

```python
from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3
```

These two classes are re-exported in `src/globaldatafinance/__init__.py`. Any new public entrypoint must be re-exported there to be part of the API contract. Treat additions as semver-relevant changes.

## Design Patterns In Use

- **Repository pattern**: `application/interfaces/*` declares `ABC` repositories (e.g. `DownloadDocsCVMRepository`); `infra/adapters/*` provides concrete implementations (e.g. `AsyncDownloadAdapterCVM`).
- **Use Case pattern**: each business operation is a class with a single `execute(...)` method (e.g. `DownloadDocumentsUseCaseCVM`, `ExtractHistoricalQuotesUseCaseB3`).
- **Result objects**: operations return typed result dataclasses (e.g. `DownloadResultCVM`) with explicit success / failure breakdowns instead of raising for partial failures.
- **Value Objects**: immutable domain types (e.g. `DictZipsToDownload`, `DocsToExtractorB3`) encapsulate validation and construction.
- **Formatter separation**: presentation/console output lives in dedicated `*_formatter.py` modules so the use-case layer stays I/O-free.

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
