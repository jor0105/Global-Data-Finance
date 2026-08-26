# AGENTS.md

> Owner: Library Engineering
> Last reviewed: 2026-08-25
> Status: Confirmed
> Knowledge class: Agent policy

Project context and operating policy for agentic coding agents working in the
Global-Data-Finance repository.

## System Overview

Global-Data-Finance (`globaldatafinance`) is a Python distribution library for
extracting, normalizing, and persisting financial and economic data. The
implemented sources are Brazilian regulatory feeds from CVM and historical
market data from B3. Python applications consume it as a dependency; it is not
run as a service, database, queue, or deployment runtime.

The public boundary is intentionally narrow: the package root re-exports
`FundamentalStocksDataCVM`, `HistoricalQuotesB3`, and the public
`ExtractionResultB3` `TypedDict` from
`src/globaldatafinance/__init__.py`. Inputs include source selections, year
ranges, COTAHIST files, configuration, and caller-owned paths. Outputs include
typed result objects, downloaded source files, and Parquet artifacts.

Data integrity takes priority over throughput or convenience. Public names,
signatures, defaults, return shapes, exception behavior, and persisted schemas
are compatibility-sensitive. Inputs and downloaded content must be validated
before extraction or writes, path-safety checks must run before directory
creation or file writes, and partial operations must expose explicit success
and error details. Source-specific behavior belongs in the owning CVM or B3
feature directory; genuinely generic behavior belongs in `core/` or
`macro_infra/`.

## Success Metrics

| Metric        | Target                                                                                                                                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Coverage gate | At least 85% for the coverage-enabled quality tests, configured by `tool.coverage.report.fail_under` in `pyproject.toml` and exercised by [`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml) |
| Quality gate  | CI passes the uv lock check, security checks, pre-commit checks, mypy, and coverage-backed tests                                                                                                             |

## Pipeline Architecture

The human documentation route starts at [`README.md`](README.md) and
[`docs/index.md`](docs/index.md). The runtime route starts at
`src/globaldatafinance/__init__.py`, delegates to the public facades in
`src/globaldatafinance/application/cvm_docs/` and
`src/globaldatafinance/application/b3_docs/`, and then delegates to the source
implementations in
`src/globaldatafinance/brazil/cvm/fundamental_stocks_data/` and
`src/globaldatafinance/brazil/b3_data/historical_quotes/`.

The cross-cutting owners are `src/globaldatafinance/core/` for configuration,
logging, path safety, retries, progress, and resource monitoring;
`src/globaldatafinance/macro_infra/` for generic HTTP and file adapters; and
`src/globaldatafinance/macro_exceptions/` for project exception bases. Tests
mirror the public and source boundaries under `tests/application/`,
`tests/brazil/`, `tests/core/`, `tests/macro_infra/`, and
`tests/macro_exceptions/`.

The implemented flows are:

- **CVM:** `FundamentalStocksDataCVM` validates document selections, year
  ranges, and paths through the use cases in
  `brazil/cvm/fundamental_stocks_data/`. `AsyncDownloadAdapterCVM` performs
  asynchronous HTTP downloads with retry and integrity handling;
  `ParquetExtractorAdapterCVM` extracts when requested; and
  `DownloadResultCVM` reports successful and failed downloads.
- **B3:** `HistoricalQuotesB3` validates assets, years, paths, output names,
  and processing mode. `ExtractHistoricalQuotesUseCaseB3` reads official
  `COTAHIST_A{YYYY}.ZIP` or `.TXT` files, parses their positional format,
  filters assets, and writes consolidated Parquet through
  `extraction_service/` and `parquet_writer/`. `fast` and `slow` retain
  distinct resource policies, and `ExtractionResultB3` remains the public
  mapping contract.

Facades expose the API, clients and use cases orchestrate work, adapters own
network and filesystem I/O, focused modules own validation and transformation,
and `*_formatter.py` modules own console presentation. Concrete adapters are
instantiated and used directly, keeping the execution path easy to trace.

For a first safe change, follow this route:

1. Read [`docs/dev-guide/architecture.md`](docs/dev-guide/architecture.md) for
   ownership and module boundaries.
2. Open the owning facades and source modules: CVM starts at
   `application/cvm_docs/fundamental_stocks_data.py` and
   `brazil/cvm/fundamental_stocks_data/`; B3 starts at
   `application/b3_docs/historical_quotes.py` and
   `brazil/b3_data/historical_quotes/`.
3. Read [`docs/dev-guide/testing.md`](docs/dev-guide/testing.md), the matching
   tests under `tests/`, and
   [`docs/dev-guide/contributing.md`](docs/dev-guide/contributing.md) before
   changing behavior.
4. For deterministic usage checks, use the real onboarding examples
   [`examples/01_quickstart_cvm.py`](examples/01_quickstart_cvm.py),
   [`examples/02_quickstart_b3.py`](examples/02_quickstart_b3.py), and
   [`examples/03_advanced_options_b3.py`](examples/03_advanced_options_b3.py).
   For installation and public-import expectations, read
   [`docs/user-guide/installation.md`](docs/user-guide/installation.md) and
   the facade tests under `tests/application/`.

Implemented code, manifests, tests, accepted decisions, and current
documentation describe the current state. `openspec/` is an existing planning
area with no implemented specifications at this review; proposals and
unimplemented plans do not change runtime behavior or override the sources
above.

## Configuration & Runtime

| Surface                                  | Location                                                                                                                                                                                                     | Purpose                                                                                                                                                                                         |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Package metadata and build               | [`pyproject.toml`](pyproject.toml)                                                                                                                                                                           | Project metadata, Python range, Hatchling build, dependency groups, coverage, Ruff, mypy, and import-linter configuration                                                                       |
| Dependency manager and lockfile          | [`uv.lock`](uv.lock)                                                                                                                                                                                         | Reproducible uv dependency resolution used by local development and CI                                                                                                                          |
| Pytest configuration                     | [`pytest.ini`](pytest.ini)                                                                                                                                                                                   | Test discovery, markers, strict pytest options, and test-path defaults; coverage ownership is in `pyproject.toml`                                                                               |
| Local quality hooks                      | [`.pre-commit-config.yaml`](.pre-commit-config.yaml)                                                                                                                                                         | Staged integrity, read-only uv lock validation, secrets and supply-chain scans, Ruff, Markdown/YAML/action checks, import graph checks, pre-push type/test/audit gates, and manual harness sync |
| MkDocs configuration                     | [`mkdocs.yml`](mkdocs.yml)                                                                                                                                                                                   | MkDocs Material site configuration; Portuguese is the default language and the English `*.en.md` build is enabled through the i18n plugin                                                       |
| Runtime settings                         | `src/globaldatafinance/core/config.py`                                                                                                                                                                       | Network timeout, retry count, retry backoff, user-agent, and global debug settings                                                                                                              |
| Logging settings                         | `src/globaldatafinance/core/logging_config.py`                                                                                                                                                               | Log level, optional file, structured output flag, and detailed-format settings                                                                                                                  |
| Main CI quality gate                     | [`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml)                                                                                                                                           | uv lock, security, pre-commit, type, and coverage-backed test gates on Python 3.12, 3.13, and 3.14                                                                                              |
| Security and invariant workflows         | [`.github/workflows/pr-security-gate.yml`](.github/workflows/pr-security-gate.yml)                                                                                                                           | Ruff security, pip-audit, detect-secrets, mypy, and public API export checks                                                                                                                    |
| Documentation and distribution workflows | [`.github/workflows/docs.yml`](.github/workflows/docs.yml), [`.github/workflows/publish.yml`](.github/workflows/publish.yml), [`.github/workflows/deploy-staging.yml`](.github/workflows/deploy-staging.yml) | MkDocs strict build/deploy, package build/publish, and staging distribution smoke validation                                                                                                    |

### Commands

| Action                                     | Command                                                                                                               |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Sync the development environment           | `uv sync --locked --all-extras --dev`                                                                                 |
| Install all local hook stages              | `uv run --locked --no-sync pre-commit install --install-hooks`                                                        |
| Run the full test suite                    | `uv run --locked --no-sync pytest`                                                                                    |
| Run unit tests                             | `uv run --locked --no-sync pytest -m unit`                                                                            |
| Run integration tests excluding slow cases | `uv run --locked --no-sync pytest -m "integration and not slow"`                                                      |
| Run the CI coverage gate                   | `uv run --locked --no-sync pytest -m "not integration and not slow" --cov --cov-report=xml --cov-report=term-missing` |
| Run all repository quality hooks           | `uv run --locked --no-sync pre-commit run --all-files --show-diff-on-failure`                                         |
| Type-check the source gate                 | `uv run --locked --no-sync mypy src --pretty`                                                                         |
| Run full Ruff lint on source               | `uv run --locked --no-sync ruff check src`                                                                            |
| Run the explicit Ruff security gate        | `uv run --locked --no-sync ruff check --select S src`                                                                 |
| Audit dependency vulnerabilities           | `uv run --locked --no-sync pip-audit`                                                                                 |
| Check the committed lockfile               | `uv lock --check`                                                                                                     |
| Build the distribution                     | `uv build`                                                                                                            |
| Build documentation strictly               | `uv run --locked --no-sync mkdocs build --strict`                                                                     |

Coverage configuration, including `fail_under = 85`, belongs to
`[tool.coverage.report]` in `pyproject.toml`; do not add coverage settings to
`pytest.ini` or duplicate the threshold with a command-line flag. The CI
quality job also runs this supplementary type surface:
`uv run --locked --no-sync mypy src tests examples scripts --disable-error-code no-untyped-def --pretty`. Targeted tests may be selected with
`uv run --locked --no-sync pytest tests/...`, the import-cycle script is run with
`uv run --locked --no-sync python scripts/check-import-cycles.py`, and the onboarding
examples are run with `uv run --locked --no-sync python examples/<example>.py` when their external
or local-data prerequisites are available. These are additional checks, not
substitutes for the source gate or the official aggregate quality command.

The public environment variable names confirmed by the configuration modules
are `DATAFINANCE_NETWORK_TIMEOUT`, `DATAFINANCE_NETWORK_MAX_RETRIES`,
`DATAFINANCE_NETWORK_RETRY_BACKOFF`, `DATAFINANCE_NETWORK_USER_AGENT`, and
`DATAFINANCE_DEBUG`; logging uses `DATAFIN_LOG_LEVEL`, `DATAFIN_LOG_FILE`,
`DATAFIN_LOG_STRUCTURED`, and `DATAFIN_LOG_DETAILED_FORMAT`. Never copy values
from `.env` files, credentials, or other secret-bearing environment sources.

## Technical Stack

- Python `>=3.12,<4.0`, `src/` layout, Hatchling build system, and `uv` with
  the committed `uv.lock`.
- `httpx[http2]` and `asyncio` for HTTP/concurrency, with retries and
  `psutil`-based resource monitoring.
- `polars`, `pandas`, `pyarrow`, and Parquet for data processing and persisted
  output; `pydantic-settings` for configuration.
- `pytest`, `pytest-cov`, and `pytest-asyncio` for tests; Ruff for formatting,
  lint, security `S`, and Google-style docstring `D` rules; mypy for type
  checking.
- pre-commit with detect-secrets, gitleaks, zizmor, import-linter, the local
  import-cycle checker, pip-audit, and repository hygiene hooks; mdformat,
  yamllint, actionlint, and codespell for non-Python quality checks.
- MkDocs Material with `mkdocs-static-i18n` for Portuguese canonical pages and
  English `*.en.md` pages; `uv build` and Hatchling for distribution artifacts.

## Mandatory Rules

- Do not write irrelevant comments in code.

- Verify files before editing; do not assume structure or behavior.

- Plan before modifying and keep scope small, reviewable, and verifiable.

- Write well-factored code with clear single responsibility per function,
  class, or module; do not create monolithic functions that handle multiple
  concerns.

- Never leave duplicated logic; extract common functionality into shared
  functions or modules.

- Never introduce circular imports or mutual module dependencies.

- Deliver only what is necessary to satisfy the request end-to-end; do not
  bundle unrequested changes or mix structural refactors with bug fixes.

- Always act as a skeptic: verify hypotheses empirically instead of accepting
  them, whether they came from the user or from you. Never flatter the user or
  engage in sycophantic agreement.

- Do not leave dead code, unused compatibility paths, duplicated ownership,
  stale documentation, unused imports, unreachable branches, or commented-out
  code after a completed clean cutover unless compatibility is an explicit
  project requirement.

- Do not write code files whose sole purpose is to re-export other files or
  modules without added value.

- `__init__.py` files must never contain code or implementation logic; they
  must only contain explicit exports.

- Never edit generated mirrors or generated files directly; change the source
  and re-run its generation or sync command.

- Chat is Portuguese (or adapted to the user's preferred language).
  Product documentation is maintained bilingually in both Portuguese (PT-BR)
  and English. Code, comments, Git commits/branches/PRs, and planning
  artifacts are English. Commit messages use Conventional Commits.

- Follow the repository's established naming, formatting, ownership, and
  module boundaries. Keep detailed contracts in the canonical owner documents
  rather than duplicating them here.

- Keep this file focused on durable policy, the system map, and navigation. Put
  detailed contracts in their canonical owner documents and link to them here.

- Use `uv` to manage dependencies and `uv run` as the standard command runner
  for Python work. Use the committed `uv.lock`; do not create or update Poetry,
  Pipenv, npm, Yarn, or other lockfiles unless the task explicitly includes a
  migration.

- Prefer repository-native entrypoints and official scripts. Before concluding
  a change, run the relevant focused checks and the official aggregate gate;
  report skipped, blocked, or failing validation with its impact.

- Preserve Python 3.12+ support, the Hatchling distribution shape, and the
  existing library abstractions. Do not introduce a web framework or a
  competing framework/parallel architectural path.

- Preserve the public facade under `application/`, the current CVM modules in
  `brazil/cvm/fundamental_stocks_data/`, and the current B3 modules in
  `brazil/b3_data/historical_quotes/`. Keep generic concerns in `core/` or
  `macro_infra/` only when they are genuinely shared.

- Keep I/O in HTTP, filesystem, extraction, and writer adapters; orchestration
  in clients/use cases; pure validation and transformation in focused logic
  modules; and console output in `*_formatter.py`. Do not call `print(...)`
  from library code outside formatters; use the logging configuration instead.

- When adding a source, provide its source implementation, public facade, root
  export, tests, and canonical documentation. Default new persisted artifacts
  to Parquet unless an accepted contract says otherwise.

- Update tests, contracts, and canonical documentation together whenever
  behavior or a public boundary changes. Tests belong under `tests/` and must
  prove happy paths, error paths, edge cases, and regressions rather than merely
  nominal line coverage.

- Preserve public root exports, parameter names, defaults, return shapes,
  exception contracts, persisted schemas, and output naming unless the user
  explicitly approves a breaking change.

- Treat source input and Parquet output as data contracts. Validate integrity
  before extraction and preserve deterministic parser and writer behavior.

- Validate inputs at public and adapter boundaries and fail fast with a clear
  project exception. Use `async with` or `with` for acquired resources.

- Never swallow exceptions silently. Re-raise, translate to a project
  exception with context, or log at WARNING or above with the original
  traceback. Do not raise raw `Exception`, `ValueError`, or `RuntimeError`
  from new library code; preserve the cause with `raise ... from exc`.

- Type-annotate public signatures and public-facing `client.py`/`core.py`
  surfaces; write Google-style docstrings and keep mypy and Ruff's `D` rules
  green.

- Keep functions focused, names clear, imports sorted, and reusable values in
  configuration/constants or documented parameters. Do not leave unused
  imports or unreachable branches.

- Run path-safety checks before `mkdir` or writes. Preserve the shared
  blocklist for POSIX system directories, sensitive user-secret directories,
  and documented Windows system paths.

- Preserve the B3 `COTAHIST_AYYYY.(ZIP|TXT)` filename contract, basename-only
  output names, and distinct `fast`/`slow` processing semantics.

- For partial source failures, use the established result objects with explicit
  success and error details rather than inventing an exception-only flow.

- Treat implemented code, manifests, tests, accepted decisions, and current
  documentation as current state. Treat proposals, plans, and unimplemented
  specifications in `openspec/` as planned state; they do not govern runtime.

- Start architecture, operations, testing, and governance questions at the
  owning sources listed under `Related Documentation`; open only the material
  needed for the task.

- Do not silently change public contracts, persisted formats, authentication
  flows, security boundaries, runtime topology, or deployment behavior.

- If code, docs, workflows, or tooling disagree about a manager, command,
  runtime, public contract, security boundary, or ownership, stop and report
  the conflict instead of choosing silently.

## Execution Policy

### Precedence

Rank: system constraints → repository/workspace policy and tooling → user
request. Act on the highest-ranking unambiguous, safe instruction without asking
again. If same-rank instructions conflict, prefer the more specific and safer
one.

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
cookies, auth sessions, certificates, and private keys as sensitive. If a secret
appears in output: stop, redact it, and report that sensitive data was found.

### Repo Alignment

Follow the repository's canonical contracts, documentation, current code,
accepted decisions, and official scripts before inventing a new workflow. Prefer
existing project patterns, entrypoints, and abstractions over ad hoc
alternatives. Do not silently change public contracts, persisted formats, auth
flows, runtime topology, or security boundaries. If code, docs, and tooling
disagree: stop, report the ambiguity, and identify the conflicting sources.

For this package, the aligned technical sources are `pyproject.toml`,
`uv.lock`, implemented `src/` code, tests, current documentation, and the
workflows under `.github/workflows/`. Planning material in `openspec/` does not
override implemented runtime behavior.

### Autonomy

Execute reversible repository/workspace changes without confirmation only when
the goal and success criteria are unambiguous, the change stays within the
authorized repository/workspace scope, and version control can recover it.
Stop and ask when scope is ambiguous, side effects are destructive, external
systems or production are involved, secrets are involved, or same-rank
instructions conflict.

### Validation

Before concluding code or tooling changes, use the repository's official
validation entrypoint when applicable. Prefer repository-native commands and
official scripts over custom one-off equivalents. If validation is skipped,
unsupported, or failing, report that explicitly with the reason and impact.

### Execution Safety

Before any destructive, publish, migration, deployment-like, or external-state
operation:

1. State exactly what will be affected.
2. Inspect and validate the exact target and scope.
3. Run a dry run when the command supports it.
4. Break complex operations into readable steps; do not hide behavior in opaque
   one-liners.

Before running local scripts that call the operating system, inspect the command
path. Stop and ask if the script is obfuscated, downloads executables, touches
secrets, or has unclear side effects.

### Failure Handling

If a security lock, permission denial, authentication boundary, or authorization
boundary blocks the task, stop. Do not work around it. Report the block, the
evidence, and the safest next step.

## Related Documentation

Read sources in this progressive-disclosure order: orientation and onboarding;
architecture and contribution; tests; contracts and API reference;
operations and retry; manifests, lockfile, hooks, and CI; runnable examples;
then planned OpenSpec material when the task explicitly concerns planning.

| Doc                                                                                                                                                                                                                                                                                                                                                                                     | Knowledge class                 | Purpose                                                                                                                                    |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [`README.md`](README.md) · [`docs/index.md`](docs/index.md)                                                                                                                                                                                                                                                                                                                             | Orientation                     | Mission, supported sources, installation route, quickstart, and documentation map                                                          |
| [`docs/user-guide/installation.md`](docs/user-guide/installation.md) · [`docs/user-guide/quickstart.md`](docs/user-guide/quickstart.md) · [`docs/user-guide/cvm-docs.md`](docs/user-guide/cvm-docs.md) · [`docs/user-guide/b3-docs.md`](docs/user-guide/b3-docs.md) · [`docs/user-guide/examples.md`](docs/user-guide/examples.md) · [`docs/user-guide/faq.md`](docs/user-guide/faq.md) | User guide                      | Consumer setup, source inputs and outputs, first usage, runnable examples, and troubleshooting                                             |
| [`docs/dev-guide/architecture.md`](docs/dev-guide/architecture.md) · [`docs/dev-guide/contributing.md`](docs/dev-guide/contributing.md)                                                                                                                                                                                                                                                 | Development                     | Ownership, module boundaries, contribution workflow, and change conventions                                                                |
| [`docs/dev-guide/testing.md`](docs/dev-guide/testing.md) · `tests/`                                                                                                                                                                                                                                                                                                                     | Tests                           | Test organization, markers, fixtures, regression strategy, and executable behavior checks                                                  |
| [`docs/dev-guide/api-reference.md`](docs/dev-guide/api-reference.md) · [`docs/reference/cvm-api.md`](docs/reference/cvm-api.md) · [`docs/reference/b3-api.md`](docs/reference/b3-api.md) · [`docs/reference/exceptions.md`](docs/reference/exceptions.md)                                                                                                                               | Reference                       | Public APIs, source contracts, return shapes, and exception behavior                                                                       |
| [`docs/dev-guide/logging-system.md`](docs/dev-guide/logging-system.md) · [`docs/dev-guide/resource-monitoring.md`](docs/dev-guide/resource-monitoring.md) · [`docs/dev-guide/retry-strategy.md`](docs/dev-guide/retry-strategy.md)                                                                                                                                                      | Operations                      | Logging, resource-aware concurrency, and retry policy                                                                                      |
| [`pyproject.toml`](pyproject.toml) · [`uv.lock`](uv.lock) · [`pytest.ini`](pytest.ini) · [`.pre-commit-config.yaml`](.pre-commit-config.yaml) · [`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml) · [`mkdocs.yml`](mkdocs.yml)                                                                                                                                         | Tooling                         | Build metadata, dependency lock, pytest behavior, local hooks, CI gates, and documentation navigation                                      |
| [`examples/README.md`](examples/README.md) · [`examples/01_quickstart_cvm.py`](examples/01_quickstart_cvm.py) · [`examples/02_quickstart_b3.py`](examples/02_quickstart_b3.py) · [`examples/03_advanced_options_b3.py`](examples/03_advanced_options_b3.py)                                                                                                                             | Examples and operational checks | Runnable onboarding and source-specific usage checks; CVM examples may use the network and B3 examples require local COTAHIST inputs       |
| [`openspec/`](openspec/)                                                                                                                                                                                                                                                                                                                                                                | Planned                         | Existing planning area currently without implemented specifications; it must not govern runtime unless an accepted change makes it current |

The Portuguese pages are the default MkDocs corpus. English `*.en.md` pages are
translation counterparts, and changes to a page with a counterpart must keep
content and navigation aligned. `openspec/` is planned material, not a runtime
or policy authority. No generated, mirrored, exploratory, or archived source is
canonical unless an accepted repository decision explicitly says so.
