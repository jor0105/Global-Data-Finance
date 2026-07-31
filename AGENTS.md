# AGENTS.md

> Owner: Library Engineering
> Last reviewed: 2026-07-31
> Status: Canonical
> Knowledge class: Agent policy

Project context for agentic coding agents working on the Global-Data-Finance codebase.

## System Overview

Global-Data-Finance (`globaldatafinance`) is a Python 3.12+ library published
on PyPI for extracting, normalizing, and persisting global financial and
economic data. It is distribution-shaped (`src/` layout, `hatchling` build,
consumed as a dependency) — not a running service. Current production data
sources are Brazilian regulatory feeds (CVM) and exchange feeds (B3); the
architecture is intentionally extensible to other markets.

The library exposes two main entrypoints — `FundamentalStocksDataCVM` (bulk
download of DFP, ITR, FRE, FCA, CGVN, VLMO, IPE with async concurrency,
retries, integrity checks, and optional Parquet extraction) and
`HistoricalQuotesB3` (positional COTAHIST ZIP parsing into consolidated
Parquet with asset filtering and `fast`/`slow` processing modes) — plus a
public `ExtractionResultB3` TypedDict contract for typed result access.

**Design priorities** (in order): data integrity → public API stability →
bulk throughput → ease of adding new sources.

**Target users**: Python developers, data scientists, quantitative analysts,
and fintech teams who need reliable financial datasets without reinventing
parsers and ETL.

## Success Metrics

| Metric                             | Target                                |
| ---------------------------------- | ------------------------------------- |
| Test coverage (`pytest --cov`)     | `fail_under = 70` enforced by config  |
| Lint / format / typecheck          | 100% green (`ruff`, `mypy`, `bandit`) |
| Public API stability               | No silent contract changes            |
| Bulk download / extraction speedup | Materially faster than naive baseline |

## Architecture

The package has two parallel axes: a **public facade** in `application/`
that users import, and **feature implementations** in `brazil/<source>/`,
each laid out as a flat set of role-named modules. Cross-cutting utilities
live in `core/` and `macro_infra/`. Heavy I/O/parsers stay as separate
modules within each feature.

Architecture patterns, code ownership, and layering contracts are owned by
[`docs/dev-guide/architecture.md`](docs/dev-guide/architecture.md). This
file does not restate them — see "Related Documentation" below for the full
doc set.

### Source Tree

```text
src/globaldatafinance/
├── __init__.py                    re-exports the public API
├── application/                   PUBLIC FACADE — top-level entrypoints
│   ├── cvm_docs/
│   │   ├── fundamental_stocks_data.py     FundamentalStocksDataCVM
│   │   └── download_result_formatter.py
│   └── b3_docs/
│       ├── historical_quotes.py           HistoricalQuotesB3
│       ├── types.py                       ExtractionResultB3 (public TypedDict)
│       ├── extraction_result_formatter.py
│       └── result_formatters/
├── brazil/                        FEATURE IMPLEMENTATIONS (Brazil sources)
│   ├── cvm/
│   │   └── fundamental_stocks_data/
│   │       ├── core.py            entities, value objects, validators
│   │       ├── client.py          use-case orchestrator
│   │       ├── http.py            AsyncDownloadAdapterCVM (HTTP I/O)
│   │       ├── extract.py         ParquetExtractorAdapterCVM
│   │       ├── download_validation.py
│   │       ├── download_extraction.py
│   │       └── errors.py
│   └── b3_data/
│       └── historical_quotes/
│           ├── models.py          value objects (DocsToExtractorB3)
│           ├── filesystem.py      path validation, COTAHIST matching
│           ├── assets.py          asset name validation
│           ├── processing.py      processing mode enum, filename sanitization
│           ├── years.py           year range limits and validation
│           ├── client.py          ExtractHistoricalQuotesUseCaseB3 (stateful)
│           ├── cotahist_parser.py positional COTAHIST parser
│           ├── parquet_writer/    Parquet writer subpackage
│           ├── extraction_service/ streaming/threadpool orchestration
│           ├── zip_reader.py
│           └── errors.py
├── core/                          cross-cutting utilities
│   ├── config.py                  pydantic-settings configuration
│   ├── logging_config.py          structured logging setup
│   └── utils/
│       ├── resource_monitor.py    CPU/RAM-aware concurrency
│       ├── retry_strategy.py      exponential backoff policy
│       ├── progress.py            progress reporting
│       ├── path_safety.py         path traversal defense helpers
│       └── files.py               file utility helpers
├── macro_infra/                   shared generic infrastructure
│   ├── requests_adapter.py        generic HTTP client wrapper
│   ├── extractor_file.py          generic ZIP / file extractor
│   └── read_files.py              file reading helpers
└── macro_exceptions/              project-wide exception base classes
```

### Public API Surface

The public surface is intentionally narrow:

```python
from globaldatafinance import (
    FundamentalStocksDataCVM,
    HistoricalQuotesB3,
    ExtractionResultB3,
)
```

These three symbols are re-exported in `src/globaldatafinance/__init__.py`.
Any new public entrypoint must be re-exported there to be part of the API
contract. Treat additions as semver-relevant changes.

### Design Patterns

- **Flat per-source modules**: each `brazil/<source>/` uses role-named
  modules (`core.py` for types/validators, `client.py` for use-case
  orchestration, `http.py`/`extract.py` for adapters, `errors.py` for
  exceptions). No nested `domain/infra/exceptions` subdirectories.
- **Concrete adapters, no ABC indirection**: HTTP and extraction adapters
  are imported and constructed directly — no single-impl ABCs.
- **Result objects over exceptions for partial failures**: operations return
  typed result dataclasses or TypedDicts (e.g. `DownloadResultCVM`,
  `ExtractionResultB3`) with explicit success/failure breakdowns.
- **Formatter separation**: console output lives in `*_formatter.py`
  modules under `application/`; `client.py` stays I/O-free.
- **Path-traversal defense as contract**: path validation helpers raise
  `SecurityError`/`PathPermissionError` before any `mkdir`, blocking
  writes to `/etc /sys /proc /dev /boot /root`.

### Runtime & I/O Model

- HTTP I/O is async via `httpx[http2]` with custom retry/backoff.
- Concurrency is adaptive: `resource_monitor.py` reads CPU/RAM (`psutil`)
  to keep download fan-out within machine capacity.
- File integrity is validated after each download before extraction.
- B3 has two processing modes: `fast` (in-memory) and `slow` (streamed).
- Canonical persisted format is **Parquet**. New sources default to Parquet.
- Logging via `core/logging_config.py` only — never `print(...)` from
  non-formatter code.

### Adding a New Source

Create a new folder under `brazil/<source>/` with the flat module set
(`core.py` + `client.py` minimum). Expose the public class via a new module
under `application/`. Re-export in `__init__.py`.

## Configuration & Runtime

| Surface | Location | Purpose |
| ------- | -------- | ------- |
| `pyproject.toml` | repo root | Dependencies, build, ruff/mypy/bandit config (single source of truth) |
| `PydanticSettings` | `core/config.py` | Runtime configuration where applicable |
| `pytest.ini` | repo root | Test config and coverage enforcement |
| `.pre-commit-config.yaml` | repo root | Lint/format/typecheck/security hooks |
| `.env` | repo root | Optional local environment overrides |
| `uv.lock` | repo root | Pinned dependency lockfile |

### Commands

| Action | Command |
| ------ | ------- |
| Validation (lint + typecheck + tests) | `uv run pre-commit run --all-files` |
| Tests (coverage enforced) | `uv run pytest` |
| Tests (unit only) | `uv run pytest -m unit` |
| Tests (integration, skip slow) | `uv run pytest -m "integration and not slow"` |
| Smoke CVM | `uv run python scripts/smoke_cvm.py` |
| Smoke B3 | `uv run python scripts/smoke_b3.py` |

`uv` is the canonical environment/dependency manager. Poetry usage in docs
is historical; prefer `uv` for local workflows unless instructed otherwise.

## Technical Stack

- Python `3.12+` (classified for 3.13 / 3.14)
- `httpx[http2]` for async HTTP I/O
- `asyncio` for concurrency orchestration
- `polars`, `pandas`, `pyarrow` for columnar processing and Parquet I/O
- `psutil` for adaptive CPU/RAM-aware concurrency
- `pydantic-settings` for runtime configuration
- `hatchling` as build backend (PyPI distribution)
- `ruff` for linting and formatting (Blue style, 79 chars, single quotes)
- `mypy` for type checking
- `bandit` for security scanning
- `pydocstyle` for docstring convention (Google style)
- `pytest` for testing (with `pytest-cov`, `pytest-asyncio`, `pytest-benchmark`)
- `pre-commit` for git hook enforcement
- `uv` for dependency management and execution
- `MkDocs` + `mkdocs-material` for documentation site

## Mandatory Rules

### Project-Specific

- Do not write irrelevant comments in the code.
- Verify files before editing; do not assume structure or behavior.
- `Code/Git = English` and `Chat = Portuguese`.
- Plan before modifying and keep scope small and verifiable.
- Prefer `uv run` for Python commands.
- Treat source data and persisted Parquet outputs as canonical; new sources
  should default to Parquet.
- Do not `print(...)` from non-formatter code; use `core/logging_config.py`.
- Keep feature-specific logic in `brazil/<source>/`; `core/` and
  `macro_infra/` hold only generic shared utilities.
- Treat current runtime code and accepted decisions as current state. Active
  OpenSpec changes are planned state until implementation and verification.
- Start architecture questions at `docs/dev-guide/architecture.md`, then open
  only the owning doc, reference, or guide needed for the task.
- Do not move system details into this file; use links for canonical docs.

### Engineering Standards

These apply regardless of language or stack. Agents must follow them
without exception:

- **Never swallow exceptions silently.** Every `except` block must either
  re-raise, translate to a domain exception with context, or log at WARNING
  or above with the original traceback. Bare `except: pass` is forbidden.
- **Use the project's exception hierarchy.** Feature exceptions inherit
  from `macro_exceptions/`. Do not raise raw `Exception`, `ValueError`, or
  `RuntimeError` from library code — wrap in a domain exception that
  carries the original cause (`raise DomainError(...) from e`).
- **Type-annotate all public signatures.** Every function, method, and
  class attribute in the public API and in `client.py`/`core.py` modules
  must have complete type annotations. Internal helpers should be annotated
  when non-obvious. `mypy` must pass.
- **Write tests for every behavioral change.** New features need at least
  one happy-path and one error-path test. Bug fixes must include a
  regression test that fails without the fix and passes with it. Tests
  mirror `src/` structure under `tests/`.
- **Preserve backward compatibility by default.** Do not change return
  types, parameter names, default values, or exception types of public
  API methods without explicit user approval. If a breaking change is
  unavoidable, document it and treat it as semver-major.
- **Keep functions focused and small.** A function should do one thing. If
  a function needs a comment block explaining "step 1, step 2, step 3",
  extract each step. Prefer pure functions where state is not needed.
- **Name things for clarity, not brevity.** Variable, function, and class
  names must be self-documenting. Avoid abbreviations except
  domain-standard ones (`CVM`, `B3`, `DFP`, `ITR`, etc.). Use
  `snake_case` for modules, functions, variables; `PascalCase` for
  classes and type aliases.
- **Write Google-style docstrings for public APIs.** Every public class and
  function must have a docstring. Follow the Google convention enforced by
  `pydocstyle`. Include `Args`, `Returns`, `Raises` sections when
  non-trivial.
- **No dead code, no commented-out code.** If code is not needed, delete
  it. Version control is the archive. Unused imports, unreachable branches,
  and TODO-without-issue are code smells to fix immediately.
- **Separate I/O from logic.** Pure computation lives in `core.py` or
  domain modules. I/O (HTTP, file system, database) lives in adapter
  modules (`http.py`, `extract.py`, `filesystem.py`). The `client.py`
  module wires them together but does not contain I/O itself.
- **Handle resources explicitly.** Use `async with` / `with` for anything
  that acquires and releases a resource (HTTP clients, file handles,
  temporary directories). Never leave resources to garbage collection.
- **Do not hardcode values.** Magic numbers, paths, URLs, and thresholds
  belong in configuration (`core/config.py`), constants modules, or
  function parameters with documented defaults — not inline in logic.
- **Fail fast and loud.** Validate inputs at the boundary (public API
  methods, adapter entry points). Raise immediately with a clear message
  rather than propagating invalid state through multiple layers.
- **Imports must be sorted and grouped.** `ruff` with `isort` rules
  handles this automatically. First-party imports use
  `known-first-party = ["globaldatafinance"]`.

## Execution Policy

### Precedence

Rank: system constraints → repo/workspace policy and tooling → user request.
Act on the highest-ranking unambiguous, safe instruction without asking again.
If same-rank instructions conflict: prefer the more specific and safer one.

### Hard Blocks

Never execute without the user naming the exact action:

- `git reset --hard`, `git reset --soft`, `git reset --mixed`,
  `git reset HEAD`, `git clean -fd`, forced checkouts, or any history
  rewrite.
- `git push --force`, `git push --force-with-lease`, `git rebase --root`,
  `git rebase -i --root`, `git filter-branch`, `git reflog expire`,
  `git update-ref --delete` or any destructive remote/history operation.
- Remote piping: `curl | bash`, `wget | sh`, or any equivalent.
- Writes to `/etc`, `~/.ssh`, system packages, or paths outside the
  workspace.
- Anything that bypasses permissions, sandbox limits, or auth controls.

### Secrets

Never seek, log, copy, or expand secrets. Treat `.env`, API keys, tokens,
cookies, auth sessions, and private keys as sensitive. If a secret appears
in output: stop, redact, report that sensitive data was found.

### Repo Alignment

Follow the repository's canonical contracts, docs, and official scripts
before inventing a new workflow. Prefer existing project patterns,
entrypoints, and abstractions over ad hoc alternatives. Do not silently
change public contracts, persisted formats, auth flows, runtime topology,
or security boundaries. If code, docs, and tooling disagree: stop, report
the ambiguity, and identify the conflicting sources.

### Autonomy

Execute reversible workspace changes without confirmation only when all
hold:

- Goal and success criteria are unambiguous.
- Change is contained inside the workspace.
- Change is fully recoverable via version control.

Stop and ask when: ambiguous scope, destructive side effects, external
systems, production impact, secrets involved, or conflict between
same-rank instructions.

### Validation

Before concluding code or tooling changes, use the repository's official
validation entrypoint when applicable. Prefer repo-native commands and
scripts over custom one-off equivalents. If validation is skipped,
unsupported, or failing, report that explicitly with the reason and
impact.

### Execution Safety

Before any destructive, publish, migration, or deployment-like operation:

1. State exactly what will be affected.
2. Run a dry run when the command supports it.
3. Break complex operations into readable steps — never opaque one-liners.

Before running local scripts that call the OS: inspect the command path.
Stop and ask if the script is obfuscated, downloads executables, touches
secrets, or has unclear side effects.

### Failure Handling

If a security lock, permission denial, or auth boundary blocks the task:
stop. Do not work around it. Report the block, the evidence, and the
safest next step.

## Related Documentation

Ordered by progressive disclosure.

| Doc | Knowledge class | Purpose |
| --- | --------------- | ------- |
| `README.md` | Orientation | Public entry point: mission, install, quickstart, API summary |
| [`docs/index.md`](docs/index.md) | Orientation | Documentation portal and routes |
| [`docs/user-guide/installation.md`](docs/user-guide/installation.md) | User guide | Install and setup |
| [`docs/user-guide/quickstart.md`](docs/user-guide/quickstart.md) | User guide | First usage walkthrough |
| [`docs/user-guide/cvm-docs.md`](docs/user-guide/cvm-docs.md) | User guide | CVM source usage |
| [`docs/user-guide/b3-docs.md`](docs/user-guide/b3-docs.md) | User guide | B3 source usage |
| [`docs/user-guide/examples.md`](docs/user-guide/examples.md) | User guide | Runnable usage examples |
| [`docs/user-guide/faq.md`](docs/user-guide/faq.md) | User guide | Frequently asked questions |
| [`docs/dev-guide/architecture.md`](docs/dev-guide/architecture.md) | Architecture | Full architecture walkthrough: layers, patterns, ownership |
| [`docs/dev-guide/testing.md`](docs/dev-guide/testing.md) | Testing | How to write and run tests, fixtures, markers |
| [`docs/dev-guide/contributing.md`](docs/dev-guide/contributing.md) | Governance | Contribution workflow and standards |
| [`docs/dev-guide/resource-monitoring.md`](docs/dev-guide/resource-monitoring.md) | Reference | CPU/RAM-aware concurrency documentation |
| [`docs/dev-guide/retry-strategy.md`](docs/dev-guide/retry-strategy.md) | Reference | Exponential backoff policy documentation |
| [`docs/dev-guide/logging-system.md`](docs/dev-guide/logging-system.md) | Reference | Structured logging configuration |
| [`docs/dev-guide/advanced-usage.md`](docs/dev-guide/advanced-usage.md) | Reference | Advanced usage patterns and API surface |
| [`docs/dev-guide/api-reference.md`](docs/dev-guide/api-reference.md) | Reference | Developer API reference |
| [`docs/reference/cvm-api.md`](docs/reference/cvm-api.md) | Reference | CVM module API reference |
| [`docs/reference/b3-api.md`](docs/reference/b3-api.md) | Reference | B3 module API reference |
| [`docs/reference/exceptions.md`](docs/reference/exceptions.md) | Reference | Exception hierarchy reference |
| `.agents/README.md` | Tooling | Agent framework: ownership, prompts, manifests, mirror policy |
| `openspec/` | Planned | OpenSpec change lifecycle (changes/ and specs/) |
