# AGENTS.md

> Owner: Library Engineering
> Last reviewed: 2026-08-03
> Status: Confirmed
> Knowledge class: Agent policy

Project context and operating policy for agentic coding agents working in the
Global-Data-Finance repository.

## System Overview

Global-Data-Finance (`globaldatafinance`) is a Python distribution library for
extracting, normalizing, and persisting financial and economic data. The
implemented sources are Brazilian regulatory feeds from CVM and historical
market data from B3. It is consumed as a dependency, not run as a web service,
backend, frontend, database, queue, or deployment runtime.

The public boundary is intentionally narrow: the package root re-exports
`FundamentalStocksDataCVM`, `HistoricalQuotesB3`, and the public
`ExtractionResultB3` `TypedDict` from `src/globaldatafinance/__init__.py`.
Inputs include source selections, year ranges, COTAHIST files, configuration,
and caller-owned paths; outputs include typed results, source files, and
Parquet artifacts.

Durable priorities and invariants are:

- data integrity before throughput or convenience;
- public names, signatures, return shapes, exception behavior, and persisted
  schemas are compatibility-sensitive;
- inputs and downloaded content are validated before extraction or writes;
- path-safety checks run before directory creation or file writes;
- partial operations expose explicit success/error details;
- source-specific logic stays under `brazil/`, while generic utilities stay in
  `core/` or `macro_infra/`.

## Success Metrics

| Metric        | Target                                                                                                |
| ------------- | ----------------------------------------------------------------------------------------------------- |
| Coverage gate | At least 70% when the CI coverage command runs (`pytest.ini` and `pipeline.yml`)                      |
| Quality gate  | CI passes the uv lock check, security checks, pre-commit, mypy, pydocstyle, and coverage-backed tests |
| Compatibility | No unapproved changes to public API contracts or persisted output schemas                             |

## Pipeline Architecture

The documentation route starts at [`README.md`](README.md) and
[`docs/index.md`](docs/index.md). The runtime route starts at
`src/globaldatafinance/__init__.py`, delegates to public facades under
`application/`, and then to source implementations under `brazil/`.

The relevant source tree is:

```text
src/globaldatafinance/
├── __init__.py                 public re-exports
├── application/                public facades and formatters
├── brazil/                     CVM and B3 feature implementations
├── core/                       configuration, logging, safety, retries, resources
├── macro_infra/                generic HTTP and file helpers
└── macro_exceptions/           project exception base classes
```

The implemented flows are:

- **CVM:** `FundamentalStocksDataCVM` validates selections, years, and paths;
  `AsyncDownloadAdapterCVM` performs async downloads with retry and integrity
  handling; `ParquetExtractorAdapterCVM` extracts when requested; and
  `DownloadResultCVM` reports successful and failed downloads.
- **B3:** `HistoricalQuotesB3` validates assets, years, paths, output names,
  and mode; `ExtractHistoricalQuotesUseCaseB3` reads official COTAHIST ZIP/TXT
  files, parses the positional format, filters assets, and writes consolidated
  Parquet through the extraction service. `fast` and `slow` preserve distinct
  resource policies, and `ExtractionResultB3` remains the public mapping
  contract.

Facades expose the API, use cases wire components, adapters own network and
filesystem I/O, pure modules own validation and transformation, and
`*_formatter.py` modules own console presentation. Concrete adapters are instantiated and used directly, ensuring simple and readable code pathways.

When adding a source, create its feature modules under `brazil/<source>/`, add
the facade under `application/`, re-export new public symbols from
`__init__.py`, and default new persisted artifacts to Parquet unless an
accepted contract says otherwise.

For a first safe change:

1. Read [`docs/dev-guide/architecture.md`](docs/dev-guide/architecture.md)
   for ownership and module boundaries.
1. Open the owning facade and source modules: CVM starts at
   `application/cvm_docs/` and `brazil/cvm/`; B3 starts at
   `application/b3_docs/` and `brazil/b3_data/`.
1. Read [`docs/dev-guide/testing.md`](docs/dev-guide/testing.md), the matching
   tests, and [`docs/dev-guide/contributing.md`](docs/dev-guide/contributing.md)
   before changing behavior.
1. Use the relevant smoke or API-surface script when deterministic runtime
   evidence is needed.

Implemented code, manifests, tests, and accepted decisions describe the
current state. Proposals, unimplemented plans, and the empty `openspec/`
directory do not change runtime behavior.

## Configuration & Runtime

| Surface             | Location                                                           | Purpose                                                                        |
| ------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| Package and tooling | [`pyproject.toml`](pyproject.toml)                                 | Metadata, Hatchling build, dependency groups, and static quality configuration |
| Dependency lock     | [`uv.lock`](uv.lock)                                               | Reproducible uv environment and CI dependency input                            |
| Test configuration  | [`pytest.ini`](pytest.ini)                                         | Discovery, markers, and `fail_under = 70` when coverage is enabled             |
| Local hooks         | [`.pre-commit-config.yaml`](.pre-commit-config.yaml)               | File hygiene, lock, security, lint, tests, type, and docstring hooks           |
| Runtime settings    | `src/globaldatafinance/core/config.py`                             | Network timeout/retry/user-agent settings and debug flag                       |
| Logging settings    | `src/globaldatafinance/core/logging_config.py`                     | Level, file, structured, and detailed logging configuration                    |
| Package CI          | [`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml) | uv setup, lock, security, quality, type, docstring, and test gates             |

Confirmed environment names are:

- `DATAFINANCE_NETWORK_TIMEOUT`, `DATAFINANCE_NETWORK_MAX_RETRIES`,
  `DATAFINANCE_NETWORK_RETRY_BACKOFF`, `DATAFINANCE_NETWORK_USER_AGENT`, and
  `DATAFINANCE_DEBUG`;
- `DATAFIN_LOG_LEVEL`, `DATAFIN_LOG_FILE`, `DATAFIN_LOG_STRUCTURED`, and
  `DATAFIN_LOG_DETAILED_FORMAT`.

Use `uv` and the committed `uv.lock` for repository development. Do not create
or update Poetry, Pipenv, npm, Yarn, or other lockfiles during ordinary Python
library work. The tracked docs and publish workflows still use Poetry without
a tracked `poetry.lock`, while two security/deployment workflows reference
absent `npm`, `frontend`, and `backend` paths. These are unresolved workflow
conflicts, not evidence of a second runtime or release contract.

### Commands

| Action                                     | Command                                                                                                                    |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Sync development environment               | `uv sync`                                                                                                                  |
| Install hooks                              | `uv run pre-commit install`                                                                                                |
| Run full tests                             | `uv run pytest`                                                                                                            |
| Run unit tests                             | `uv run pytest -m unit`                                                                                                    |
| Run integration tests excluding slow cases | `uv run pytest -m "integration and not slow"`                                                                              |
| Run CI coverage gate                       | `uv run pytest -m "not integration and not slow" --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=70` |
| Run repository quality hooks               | `uv run pre-commit run --all-files --show-diff-on-failure`                                                                 |
| Run type checking                          | `uv run mypy src --ignore-missing-imports --pretty`                                                                        |
| Run security and docstring checks          | `uv run bandit -c pyproject.toml -r src -ll` and `uv run pydocstyle src --convention=google`                               |
| Check lockfile                             | `uv lock --check`                                                                                                          |
| Run CVM/B3 smoke checks                    | `uv run python scripts/smoke_cvm.py` / `uv run python scripts/smoke_b3.py`                                                 |
| Capture public API surface                 | `uv run python scripts/capture_api_surface.py`                                                                             |
| Build documentation                        | `uv run mkdocs build --strict`                                                                                             |

## Technical Stack

| Concern                | Current choice                                                                    |
| ---------------------- | --------------------------------------------------------------------------------- |
| Runtime and build      | Python `>=3.12,<4.0`, `src/` layout, Hatchling, `uv`                              |
| HTTP and concurrency   | `httpx[http2]`, `asyncio`, retries, and `psutil` resource monitoring              |
| Data processing        | `polars`, `pandas`, `pyarrow`, and Parquet                                        |
| Configuration and logs | `pydantic-settings` and the project logging configuration                         |
| Quality and security   | pytest, Ruff, mypy, pydocstyle, Bandit, pip-audit, detect-secrets, and pre-commit |
| Documentation          | MkDocs Material, configured for Portuguese (`pt`)                                 |

## Mandatory Rules

- Verify files before editing; plan before modifying; keep scope small,
  reviewable, and verifiable.
- `Chat = Portuguese`. New code, identifiers, comments, docstrings, and Git
  metadata use English. Keep user-facing MkDocs documentation aligned with
  the existing Portuguese corpus.
- Use `uv` and `uv run` for Python work. Do not mix dependency managers or
  regenerate another lockfile unless the task explicitly includes migration.
- Prefer repository-native entrypoints and official scripts. Run the relevant
  focused tests and then the official quality gate; report skipped, blocked, or
  failing validation with its impact.
- Treat implemented code, manifests, tests, and accepted decisions as current
  state. Treat proposals and unimplemented planning artifacts as planned state.
- Use the canonical doc route in `Related Documentation`; detailed contracts
  belong in canonical docs or owning modules, not duplicated in this file.
- Preserve the distribution-oriented package shape, the public facade under
  `application/`, and flat role-named source modules under `brazil/<source>/`.
- Keep source-specific behavior in its owning `brazil/<source>/` folder;
  `core/` and `macro_infra/` contain only genuinely generic behavior.
- Keep I/O in HTTP/filesystem/extraction/writer adapters, orchestration in
  clients/use cases, pure validation/transformation in logic modules, and
  console output in `*_formatter.py`. Never call `print(...)` from library
  code outside formatters; use the logging configuration instead.
- New sources need a source implementation, public facade, root re-export, and
  Parquet-by-default persistence unless an accepted contract says otherwise.
- Preserve public root exports, parameter names, defaults, return shapes,
  exception contracts, persisted schemas, and output naming unless the user
  explicitly approves a breaking change.
- Treat source input and Parquet output as data contracts. Validate integrity
  before extraction and preserve deterministic parser/writer behavior.
- Write tests for every behavioral change: happy and error paths for new
  behavior, and a regression test for every bug fix. Keep tests under `tests/`.
- Type-annotate public signatures and public-facing `client.py`/`core.py`
  surfaces; write Google-style docstrings; keep mypy and pydocstyle green.
- Never swallow exceptions silently. Re-raise, translate to a project
  exception with context, or log at WARNING or above with the original
  traceback. Do not raise raw `Exception`, `ValueError`, or `RuntimeError`
  from new library code; preserve the cause with `raise ... from exc`.
- Validate inputs at public and adapter boundaries and fail fast with a clear
  project exception. Use `async with` or `with` for acquired resources.
- Keep functions focused, names clear, imports sorted, and reusable values in
  configuration/constants or documented parameters. Do not leave irrelevant
  comments, dead/commented-out code, unused imports, unreachable branches, or
  stale compatibility paths.
- Run path-safety checks before `mkdir` or writes; preserve the shared blocklist
  for POSIX system directories, sensitive home directories, and documented
  Windows system paths.
- Preserve the B3 `COTAHIST_AYYYY.(ZIP|TXT)` filename contract, basename-only
  output names, and `fast`/`slow` processing semantics.
- For partial source failures, use the established result objects with explicit
  success and error details rather than inventing an exception-only flow.
- If code, docs, workflows, or tooling disagree about a manager, command,
  runtime, public contract, security boundary, or ownership, stop and report
  the conflict instead of choosing silently.

## Execution Policy

### Precedence

Rank: system constraints → repository/workspace policy and tooling → user
request. Act on the highest-ranking unambiguous, safe instruction without
asking again. If same-rank instructions conflict, prefer the more specific and
safer one.

### Hard Blocks

Never execute without the user naming the exact action:

- `git reset --hard`, `git reset --soft`, `git reset --mixed`, `git reset HEAD`,
  `git clean -fd`, forced checkouts, or any history rewrite.
- `git push --force`, `git push --force-with-lease`, `git rebase --root`,
  `git rebase -i --root`, `git filter-branch`, `git reflog expire`,
  `git update-ref --delete`, or any destructive remote/history operation.
- Remote piping: `curl | bash`, `wget | sh`, or any equivalent.
- Writes to `/etc`, `~/.ssh`, system packages, or paths outside the authorized
  repository/workspace scope.
- Anything that bypasses permissions, sandbox limits, authentication, or
  authorization controls.

### Secrets

Never seek, log, copy, or expand secrets. Treat `.env`, API keys, tokens,
cookies, auth sessions, certificates, and private keys as sensitive. If a
secret appears in output: stop, redact it, and report that sensitive data was
found.

### Repo Alignment

Follow canonical contracts, documentation, current code, accepted decisions,
and official scripts before inventing a workflow. Prefer existing patterns,
entrypoints, and abstractions. Do not silently change public contracts,
persisted formats, auth flows, runtime topology, or security boundaries. If
sources disagree, stop, report the ambiguity, and identify the conflict.

For this package, the aligned technical sources are `pyproject.toml`,
`uv.lock`, implemented `src/` code, tests, and
`.github/workflows/pipeline.yml`. The legacy workflow mismatch is documented
under `Configuration & Runtime` and must not be silently resolved by agents.

### Autonomy

Execute reversible repository/workspace changes without confirmation only when
the goal and success criteria are unambiguous, the change stays within the
authorized workspace, and version control can recover it. Stop and ask when
scope is ambiguous, side effects are destructive, external systems or
production are involved, secrets are involved, or same-rank instructions
conflict.

### Validation

Before concluding code or tooling changes, use the repository's official
validation entrypoint when applicable. Prefer repository-native commands and
scripts over custom one-off equivalents. If validation is skipped, unsupported,
or failing, report the reason and impact.

### Execution Safety

Before any destructive, publish, migration, deployment-like, or external-state
operation:

1. State exactly what will be affected.
1. Inspect and validate the exact target and scope.
1. Run a dry run when the command supports it.
1. Break complex operations into readable steps; do not hide behavior in opaque
   one-liners.

Before running local scripts that call the operating system, inspect the
command path. Stop and ask if the script is obfuscated, downloads executables,
touches secrets, or has unclear side effects.

### Failure Handling

If a security lock, permission denial, authentication boundary, or authorization
boundary blocks the task, stop. Do not work around it. Report the block, the
evidence, and the safest next step.

## Related Documentation

Read sources in this order: orientation, architecture and ownership, testing
and contribution, source contracts, operations/tooling, then implementation
details or planned work.

| Doc                                                                                                                                                                                                                                                         | Knowledge class        | Purpose                                                                               |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------- |
| [`README.md`](README.md) · [`docs/index.md`](docs/index.md)                                                                                                                                                                                                 | Orientation            | Mission, supported sources, installation, quickstart, and documentation map           |
| [`docs/user-guide/installation.md`](docs/user-guide/installation.md) · [`docs/user-guide/quickstart.md`](docs/user-guide/quickstart.md) · [`docs/user-guide/examples.md`](docs/user-guide/examples.md) · [`docs/user-guide/faq.md`](docs/user-guide/faq.md) | User guide             | Consumer setup, first usage, runnable examples, and troubleshooting                   |
| [`docs/user-guide/cvm-docs.md`](docs/user-guide/cvm-docs.md) · [`docs/user-guide/b3-docs.md`](docs/user-guide/b3-docs.md)                                                                                                                                   | User guide             | CVM and B3 inputs, outputs, modes, and examples                                       |
| [`docs/dev-guide/architecture.md`](docs/dev-guide/architecture.md) · [`docs/dev-guide/testing.md`](docs/dev-guide/testing.md) · [`docs/dev-guide/contributing.md`](docs/dev-guide/contributing.md)                                                          | Development            | Ownership, test strategy, quality workflow, and contribution rules                    |
| [`docs/dev-guide/api-reference.md`](docs/dev-guide/api-reference.md) · [`docs/reference/cvm-api.md`](docs/reference/cvm-api.md) · [`docs/reference/b3-api.md`](docs/reference/b3-api.md) · [`docs/reference/exceptions.md`](docs/reference/exceptions.md)   | Reference              | Public APIs, source contracts, and exception behavior                                 |
| [`docs/dev-guide/logging-system.md`](docs/dev-guide/logging-system.md) · [`docs/dev-guide/resource-monitoring.md`](docs/dev-guide/resource-monitoring.md) · [`docs/dev-guide/retry-strategy.md`](docs/dev-guide/retry-strategy.md)                          | Operations             | Logging, resource-aware concurrency, and retry policy                                 |
| [`pyproject.toml`](pyproject.toml) · [`uv.lock`](uv.lock) · [`pytest.ini`](pytest.ini) · [`.pre-commit-config.yaml`](.pre-commit-config.yaml)                                                                                                               | Repository facts       | Build, dependencies, tests, and local quality hooks                                   |
| [`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml) · [`mkdocs.yml`](mkdocs.yml)                                                                                                                                                             | Tooling                | Current package CI gates and documentation build/navigation                           |
| [`scripts/smoke_cvm.py`](scripts/smoke_cvm.py) · [`scripts/smoke_b3.py`](scripts/smoke_b3.py) · [`scripts/capture_api_surface.py`](scripts/capture_api_surface.py)                                                                                          | Operational checks     | Deterministic source-flow and public-API evidence                                     |
| [`.agents/README.md`](.agents/README.md) · [`openspec/`](openspec/)                                                                                                                                                                                         | Agent/planning tooling | Agent framework and planning boundary; neither overrides implemented runtime behavior |
