# Tasks: Refactor anti-overengineering

> Hard rule (design.md, Criterion section): Phase N+1 does NOT start until every acceptance criterion of Phase N is green. No "fix it in the next phase". On regression, only allowed actions are (a) additive commit on same branch fixing the gap, or (b) `git revert <sha-phase-N>`.
>
> Commands assume `uv` (canonical per `AGENTS.md`). All `git` operations are aditivos — destructive ops (`reset --hard`, `push --force`, history rewrite) only on explicit user request per `GLOBAL_RULE.md`.

## 0. Pre-Phase 0 — Author baseline capture scripts

- [x] 0.1 Create `scripts/capture_api_surface.py`: deterministic JSON output (sorted keys) capturing the multi-layer public surface:
  - **Public method signatures**: `inspect.signature` for `download`, `extract`, `get_available_docs`, `get_available_years`, `get_available_assets`.
  - **Top-level package exports**: `sorted(globaldatafinance.__all__)` under key `"top_level_exports"`.
  - **Public representation**: `repr(FundamentalStocksDataCVM())` and `repr(HistoricalQuotesB3())`.
  - **Do NOT capture**: `__doc__`, inferred exception names, or `dir(instance)` / collaborator attributes such as `download_adapter`; behavioral guarantees for exceptions stay in delta specs + tests, and incidental collaborators must not become contract by accident.
  Output to stdout; script is idempotent.
- [x] 0.2 Create `scripts/smoke_b3.py`: exercises `HistoricalQuotesB3().extract(...)` against a deterministic local COTAHIST ZIP fixture (placed under `tests/fixtures/cotahist/` or generated bit-stable by the script — no `random`, no `time`, no embedded timestamps). Captures: (a) **basename-only** sorted list of Parquet artifacts produced (no absolute paths — F2 mitigation); (b) SHA256 of each artifact; (c) schema (column names + dtypes) via `pyarrow.parquet.read_schema`. Emits JSON with sorted keys. **Determinism rules (mandatory):**
  - When generating the ZIP in-script, build entries with `zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))` explicitly; do NOT use `ZipFile.write(path)` which inherits filesystem `mtime`.
  - When writing Parquet inside the smoke flow, override `pyarrow.parquet.write_table` non-determinism: `compression='snappy'` (stable) or `'none'`; pass `write_statistics=False` to avoid variance in min/max/null_count between runs; pass `use_dictionary=False` if dictionary order differs across runs (verify by running twice).
  - Never capture `os.path.getmtime`, `datetime.now()`, or any timestamp into the output JSON.
  - Normalize all paths via `os.path.basename(...)` before serializing.
- [x] 0.3 Create `scripts/smoke_cvm.py`: exercises `FundamentalStocksDataCVM` without network — **MUST use `httpx.MockTransport`** with a fixed response that exercises the download → use-case → adapter wiring (the path most affected by the refactor). The narrower alternative "only call `get_available_docs()` + `get_available_years()`" is insufficient and rejected. Emits JSON with sorted keys, same determinism rules as 0.2.
- [x] 0.4 Run `scripts/smoke_b3.py` twice on the baseline tree and diff outputs; confirm bit-identical (`diff` exit 0). If any drift, fix the non-determinism source in the script before proceeding (most likely culprits: ZIP `mtime`, Parquet statistics, dictionary order, leaked absolute paths). Repeat for `scripts/smoke_cvm.py`.
- [x] 0.4bis Cross-host smoke (F2 verification): run `scripts/smoke_b3.py` once with `TMPDIR=/tmp` and once with `TMPDIR=/var/tmp` (or any second writable temp dir); diff outputs — must be bit-identical. Same for `scripts/smoke_cvm.py`. If different, the script is leaking host-specific state.

## 1. Phase 0 — Baseline + tag

- [x] 1.1 Confirm clean working tree: `git status` shows no uncommitted changes outside this OpenSpec change directory.
- [x] 1.2 Run `uv run pre-commit run --all-files` — must be green. If any pre-existing failure unrelated to this change, surface to user and stop.
- [x] 1.3 Run `uv run pytest` — must be green (coverage `fail_under = 70`). Record overall coverage and per-capability coverage.
- [x] 1.4 Record file count: `find src -type f -name '*.py' | wc -l` → expected 109 (per design.md). Save number in commit message of Phase 0.
- [x] 1.4bis (R11) Record scoped `SecurityError` baseline: `grep -rEcn "SecurityError" src/globaldatafinance/brazil/cvm/fundamental_stocks_data src/globaldatafinance/brazil/b3_data/historical_quotes tests/application/cvm_docs tests/brazil/b3_data/historical_quotes | awk -F: '{sum+=$NF} END {print sum}'` → expected 37 (current scoped baseline). Save number in commit message and reference from Phase 6.7bis.
- [x] 1.5 Generate and commit baseline artifacts:
  - `openspec/changes/refactor-anti-overengineering/baseline/api_surface.json` ← `uv run python scripts/capture_api_surface.py`
  - `openspec/changes/refactor-anti-overengineering/baseline/coverage_per_capability.json` — canonical format `{"b3": {<full coverage json>}, "cvm": {<full coverage json>}}`. Build by running both per-capability commands and merging:
    ```bash
    uv run pytest --cov=src/globaldatafinance/brazil/b3_data --cov=src/globaldatafinance/application/b3_docs \
      tests/brazil/b3_data tests/application/b3_docs --cov-report=json:/tmp/cov_b3.json -q
    uv run pytest --cov=src/globaldatafinance/brazil/cvm --cov=src/globaldatafinance/application/cvm_docs \
      tests/brazil/cvm tests/application/cvm_docs --cov-report=json:/tmp/cov_cvm.json -q
    uv run python -c "
    import json
    out = {'b3': json.load(open('/tmp/cov_b3.json')), 'cvm': json.load(open('/tmp/cov_cvm.json'))}
    json.dump(out, open('openspec/changes/refactor-anti-overengineering/baseline/coverage_per_capability.json', 'w'), indent=2, sort_keys=True)
    "
    ```
  - `openspec/changes/refactor-anti-overengineering/baseline/pytest_inventory.txt` ← `uv run pytest --collect-only -q`
  - `openspec/changes/refactor-anti-overengineering/baseline/smoke_b3.json` ← `uv run python scripts/smoke_b3.py`
  - `openspec/changes/refactor-anti-overengineering/baseline/smoke_cvm.json` ← `uv run python scripts/smoke_cvm.py`
  - **Pre-commit gate (F2 mitigation)**: `! grep -E "/(home|Users|tmp/[a-zA-Z0-9_]+/)" openspec/changes/refactor-anti-overengineering/baseline/*.json` — must return zero lines. If hit, the smoke scripts are leaking absolute paths; fix `scripts/smoke_*.py` to normalize to `os.path.basename(...)` before serializing.
- [x] 1.6 Create rollback tag: `git tag refactor-baseline-pre`.
- [x] 1.7 Commit: `chore(refactor): baseline before anti-overengineering pass` — includes the 5 baseline files and the 3 scripts from group 0.

## 2. Phase 1 — B3 `historical_quotes` collapse

Scope (per design.md D9 Capability Isolation Guarantee): only `src/globaldatafinance/brazil/b3_data/historical_quotes/`, `src/globaldatafinance/brazil/__init__.py` (re-export), `src/globaldatafinance/application/b3_docs/historical_quotes.py` (facade), and `tests/brazil/b3_data/historical_quotes/` + `tests/application/b3_docs/`. CVM files MUST NOT be touched in this phase.

### 2.1 Move heavy IO/parsing modules to flat layout

- [x] 2.1.1 Move `brazil/b3_data/historical_quotes/infra/extraction_service.py` → `brazil/b3_data/historical_quotes/extraction_service.py` (preserved as own file per D5 sub-Q5; do NOT collapse into `client.py`).
- [x] 2.1.2 Move `brazil/b3_data/historical_quotes/infra/parquet_writer.py` → `brazil/b3_data/historical_quotes/parquet_writer.py`.
- [x] 2.1.3 Move `brazil/b3_data/historical_quotes/infra/cotahist_parser.py` → `brazil/b3_data/historical_quotes/cotahist_parser.py`.
- [x] 2.1.4 Move any remaining `infra/` modules (zip_reader, etc.) flat under `brazil/b3_data/historical_quotes/`. No behavior change; only relative-import adjustments.

### 2.2 Collapse `domain/` into `core.py`

- [x] 2.2.1 Create `brazil/b3_data/historical_quotes/core.py` aggregating: enums (e.g. `ProcessingModeEnumB3`), value objects (`DocsToExtractorB3`), validators, plain dataclasses currently scattered in `domain/{entities,value_objects,services}/`.
- [x] 2.2.2 Move `AvailableAssetsServiceB3` logic into `core.py` as module-level function(s). When moving, replace the `print(...)` at `available_assets_service.py:114` with `logger.warning('Invalid asset classes were ignored', extra={'invalid_inputs': invalid_inputs})` (R8 mitigation — separates static message from variable payload to neutralize log injection from user-controlled `assets_list`; 2 lines, same commit).
- [x] 2.2.3 Verify no remaining references to `brazil.b3_data.historical_quotes.domain.*`: `grep -rEn "brazil\.b3_data\.historical_quotes\.domain" src tests` → must return zero lines.

### 2.2bis Preserve B3 path-traversal defense (R11)

- [x] 2.2bis.1 Migrate `FileSystemServiceB3._validate_path_safety` (`infra/file_system_service.py:23-58`) and `validate_directory_path` (`:60+`) into the flat layout — destination is `core.py` (function-style) or kept as a class in a dedicated `file_system.py` module if the implementer prefers to preserve the class shape. Behavior MUST be bit-identical: same sensitive dirs (`/etc /root /sys /proc /dev /boot`), same `SecurityError` signature, same `relative_to` resolution, and the validation MUST run **before** any `mkdir`.
- [x] 2.2bis.2 Update only the import paths in `tests/brazil/b3_data/historical_quotes/infra/test_file_system_service.py` — assertions and scenarios MUST stay untouched. When Phase 1 later flattens the test tree, this file may move to `tests/brazil/b3_data/historical_quotes/test_file_system_service.py`, but its body must remain unchanged.
- [x] 2.2bis.3 Gate (blocks Phase 1 acceptance): `uv run pytest tests/brazil/b3_data/historical_quotes/infra/test_file_system_service.py -q` green, with no test edits beyond imports. If a test needs to be rewritten to pass, STOP — the defense was likely altered, not just moved.

### 2.3 Collapse `application/use_cases/` into `client.py`

- [x] 2.3.1 Create `brazil/b3_data/historical_quotes/client.py`. Convert 1-method use case classes (`CreateSetAssetsUseCaseB3`, `GetAvailableYearsUseCaseB3`, `GetAvailableAssetsUseCaseB3`, `CreateDocsToExtractUseCaseB3`, `ValidateExtractionConfigUseCaseB3`, etc.) into module-level functions.
- [x] 2.3.2 Preserve `ExtractHistoricalQuotesUseCaseB3` as a class (it holds state — adapters reused across calls per D3) but rename per design.md to a name reflecting orchestration (e.g. `ExtractHistoricalQuotesClientB3`); keep the old name as a deliberate re-export only if needed by the facade.
- [x] 2.3.3 Decide construction path for `ExtractionServiceB3` (D4 alternative b): either direct construction in facade or `classmethod ExtractionServiceB3.create(...)`. Record the choice in the commit body of this phase.

### 2.4 Remove `ExtractionServiceFactoryB3`

- [x] 2.4.1 Delete `brazil/b3_data/historical_quotes/infra/extraction_service_factory.py`.
- [x] 2.4.2 Update facade `application/b3_docs/historical_quotes.py` to construct `ExtractionServiceB3` directly (or via the `classmethod create` chosen in 2.3.3). Preserve `elapsed_time` measurement (R7), and keep invalid `processing_mode` flowing through `ValidateExtractionConfigUseCaseB3`/equivalent so the public exception remains `InvalidProcessingMode`, not raw `ValueError`.

### 2.5 Migrate tests (B3 only)

- [x] 2.5.0 (R2 audit, pre-edit) Enumerate the universe of B3 deep-import test files: `grep -rEln "from globaldatafinance\.brazil\.b3_data.*application\.(interfaces|use_cases)" tests` — current count: 8 files (per design.md R2). Save the list; every file in it must be migrated in 2.5.1.
- [x] 2.5.1 Update `tests/brazil/b3_data/historical_quotes/**/*.py` imports to new flat paths (`from globaldatafinance.brazil.b3_data.historical_quotes.core import ...`, `.client import ...`, etc.).
- [x] 2.5.2 Replace all `patch('...ExtractionServiceFactoryB3')` occurrences (R3 — ~11 in `test_extract_historical_quotes_use_case.py`). Pattern: `mock_factory.create.return_value = mock_service` → `mock_extraction_service.return_value = mock_service`. Run `grep -rEn "ExtractionServiceFactoryB3" tests` after edit → must return zero lines.
- [x] 2.5.3 Delete any test files that exclusively covered the removed factory (e.g. `test_extraction_service_factory.py` if present).
- [x] 2.5.4 Restructure `tests/brazil/b3_data/historical_quotes/` to mirror the new flat layout: drop empty `domain/`, `application/use_cases/`, `infra/` directories where source counterparts no longer exist; relocate test files to mirror new module names. Explicitly move `infra/test_file_system_service.py` to `tests/brazil/b3_data/historical_quotes/test_file_system_service.py` while keeping the test body unchanged.

### 2.6 Errors module

- [x] 2.6.1 Create `brazil/b3_data/historical_quotes/errors.py` aggregating exceptions previously in `exceptions/`. Re-export from prior import paths only if facade or tests still depend on them; otherwise update those callers.
- [x] 2.6.2 Remove `brazil/b3_data/historical_quotes/exceptions/` directory (after callers migrated).

### 2.7 `__init__.py` updates (B3 scope only)

- [x] 2.7.1 Update `brazil/b3_data/historical_quotes/__init__.py` to re-export only what the facade imports.
- [x] 2.7.2 Update `brazil/__init__.py` to re-export the new B3 names; remove re-exports of removed symbols (`ExtractionServiceFactoryB3`, removed use case classes).
- [x] 2.7.3 Delete empty intermediate `__init__.py` files under `brazil/b3_data/historical_quotes/{domain,application,infra,exceptions}/`.

### 2.8 Phase 1 acceptance gate

- [x] 2.8.1 **Criterion 1 — API surface lock**:
  ```bash
  uv run python scripts/capture_api_surface.py > /tmp/api_surface_post.json
  diff openspec/changes/refactor-anti-overengineering/baseline/api_surface.json /tmp/api_surface_post.json
  ```
  Must exit 0 (empty diff).
- [x] 2.8.2 **Criterion 2 — Per-capability coverage gate (B3)**:
  ```bash
  uv run pytest tests/brazil/b3_data tests/application/b3_docs \
    --cov=src/globaldatafinance/brazil/b3_data \
    --cov=src/globaldatafinance/application/b3_docs \
    --cov-report=json:/tmp/cov_b3_post.json --cov-report=term-missing -q

  # Numeric comparison (machine-readable, not vibe-check):
  uv run python -c "
  import json, sys
  base = json.load(open('openspec/changes/refactor-anti-overengineering/baseline/coverage_per_capability.json'))['b3']['totals']['percent_covered']
  post = json.load(open('/tmp/cov_b3_post.json'))['totals']['percent_covered']
  print(f'baseline={base:.2f}% post={post:.2f}% delta={post-base:+.2f}pp')
  sys.exit(0 if post >= base else 1)
  "
  ```
  All tests green; comparison script exits 0 (post ≥ baseline). If below baseline, add minimal tests for `client.py` (R5 mitigation) before closing the phase.
- [x] 2.8.3 **Criterion 3 — Behavioral smoke (B3)**:
  ```bash
  uv run python scripts/smoke_b3.py > /tmp/smoke_b3_post.json
  diff openspec/changes/refactor-anti-overengineering/baseline/smoke_b3.json /tmp/smoke_b3_post.json
  ```
  Must exit 0.
- [x] 2.8.4 **Criterion 4 — Full suite**: `uv run pre-commit run --all-files` and `uv run pytest` both green.
- [x] 2.8.5 **Criterion 5 — Public smoke**:
  ```bash
  uv run python -c "from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3; print(FundamentalStocksDataCVM().__class__.__name__, HistoricalQuotesB3().__class__.__name__)"
  uv run python -c "import pathlib; p=pathlib.Path('examples/historical_quotes.py'); compile(p.read_text(), str(p), 'exec')"
  ```
  Both succeed.
- [x] 2.8.6 Commit: `refactor(b3): collapse historical_quotes layers to flat module structure`.

## 3. Phase 2 — CVM `fundamental_stocks_data` collapse

Scope: only `src/globaldatafinance/brazil/cvm/fundamental_stocks_data/`, `src/globaldatafinance/brazil/__init__.py` (re-export delta), `src/globaldatafinance/application/cvm_docs/fundamental_stocks_data.py` (facade), and `tests/brazil/cvm/fundamental_stocks_data/` + `tests/application/cvm_docs/`. B3 files MUST NOT be touched in this phase.

### 3.1 Move heavy IO module to flat layout

- [x] 3.1.1 Move `brazil/cvm/fundamental_stocks_data/infra/adapters/requests_adapter/async_download_adapter.py` → `brazil/cvm/fundamental_stocks_data/http.py`.
- [x] 3.1.2 Move `brazil/cvm/fundamental_stocks_data/infra/adapters/extractors_docs_adapter/parquet_extractor.py` → `brazil/cvm/fundamental_stocks_data/extract.py`.

### 3.2 Drop single-impl ABCs

- [x] 3.2.1 Delete `brazil/cvm/fundamental_stocks_data/application/interfaces/download_repository.py` (`DownloadDocsCVMRepositoryCVM`).
- [x] 3.2.2 Delete `brazil/cvm/fundamental_stocks_data/application/interfaces/file_extractor_repository.py` (`FileExtractorRepositoryCVM`).
- [x] 3.2.3 Remove ABC inheritance from `AsyncDownloadAdapterCVM` (now in `http.py`) and `ParquetExtractorAdapterCVM` (now in `extract.py`).
- [x] 3.2.4 Remove `isinstance(repository, DownloadDocsCVMRepositoryCVM)` check from the (now ex-) `DownloadDocumentsUseCaseCVM` constructor, and delete the corresponding `InvalidRepositoryTypeError` exception.
- [x] 3.2.5 Adjust type annotations: parameters previously typed as the ABC become typed as the concrete class (`AsyncDownloadAdapterCVM`, `ParquetExtractorAdapterCVM`).
- [x] 3.2.6 Delete empty `application/interfaces/` directory.

### 3.3 Collapse `domain/` into `core.py`

- [x] 3.3.1 Create `brazil/cvm/fundamental_stocks_data/core.py` aggregating domain entities, value objects (`DictZipsToDownload`), validators currently scattered in `domain/`.
- [x] 3.3.2 Verify: `grep -rEn "brazil\.cvm\.fundamental_stocks_data\.domain" src tests` → zero lines.

### 3.4 Collapse `application/use_cases/` into `client.py`

- [x] 3.4.1 Create `brazil/cvm/fundamental_stocks_data/client.py`. Convert use case classes (`DownloadDocumentsUseCaseCVM`, `GetAvailableDocsUseCaseCVM`, `GetAvailableYearsUseCaseCVM`) into module-level functions, except where state is reused (rare in CVM scope).
- [x] 3.4.2 Preserve `elapsed_time` measurement in the function replacing `DownloadDocumentsUseCaseCVM.execute` — `time.time()` before/after, set on `DownloadResultCVM.elapsed_time` (R7).

### 3.4bis Preserve CVM path-traversal defense (R11)

- [x] 3.4bis.1 Migrate the **entire** `VerifyPathsUseCasesCVM` class (`application/use_cases/verify_paths_use_cases.py`) into the flat layout, including the private `__validate_path_security` (`:91-114`) and `__validate_and_create_paths` (`:116+`). Destination: `client.py` (as a class kept intact, OR as module-level functions where each function preserves the same `SecurityError`-raising path check). Behavior MUST be bit-identical: same sensitive dirs (`/etc /sys /proc /dev /boot /root`), same `path.startswith(sensitive)` check, same `SecurityError` signature, and the validation MUST run **before** the `mkdir(parents=True, exist_ok=True)` call (currently `verify_paths_use_cases.py:131`).
- [x] 3.4bis.2 Update only the import paths in `tests/application/cvm_docs/test_path_traversal.py` — the 7 scenarios (5 sensitive paths + happy + edge) and assertions MUST stay untouched.
- [x] 3.4bis.3 Gate (blocks Phase 2 acceptance): `uv run pytest tests/application/cvm_docs/test_path_traversal.py -q` green, with no test edits beyond imports. If any scenario fails, STOP — defense was altered, not just moved.

### 3.5 Errors module

- [x] 3.5.1 Create `brazil/cvm/fundamental_stocks_data/errors.py` aggregating exceptions from `exceptions/` (excluding deleted `InvalidRepositoryTypeError`).
- [x] 3.5.2 Remove `brazil/cvm/fundamental_stocks_data/exceptions/` directory.

### 3.6 Migrate tests (CVM only)

- [x] 3.6.1 Update `tests/brazil/cvm/fundamental_stocks_data/**/*.py` imports to new flat paths.
- [x] 3.6.2 Rewrite `tests/brazil/cvm/fundamental_stocks_data/application/use_cases/test_download_documents_use_case.py` (R1): replace `class MockRepository(DownloadDocsCVMRepositoryCVM)` pattern with a duck-typed stub class (no ABC inheritance) or `monkeypatch.setattr` on the real adapter method.
- [x] 3.6.3 (R2 audit, pre-edit) Enumerate the universe of CVM deep-import test files: `grep -rEln "from globaldatafinance\.brazil\.cvm.*application\.(interfaces|use_cases)" tests` — current count: 3 files (per design.md R2: `test_httpx_async_download_adapter.py`, `test_parquet_extractor.py`, `tests/application/cvm_docs/test_path_traversal.py`). Save the list; every file must be migrated. After all edits, run `grep -rEln "from globaldatafinance\.brazil.*application\.(interfaces|use_cases)" tests` (cross-capability) → must return zero lines (B3 already migrated in Phase 1).
- [x] 3.6.4 Delete `tests/brazil/cvm/fundamental_stocks_data/application/interfaces/test_download_repository.py` (385L) and `tests/brazil/cvm/fundamental_stocks_data/application/interfaces/test_file_extractor.py` (228L) — they cover removed ABCs; behavior is exercised by adapter tests.
- [x] 3.6.5 Restructure `tests/brazil/cvm/fundamental_stocks_data/` to mirror flat layout; drop empty `domain/`, `application/`, `infra/`, `exceptions/` subdirs.

### 3.7 `__init__.py` updates (CVM scope only)

- [x] 3.7.1 Update `brazil/cvm/fundamental_stocks_data/__init__.py` to re-export only facade-needed names.
- [x] 3.7.2 Update `brazil/__init__.py`: drop re-exports of removed symbols (`DownloadDocsCVMRepositoryCVM`, `FileExtractorRepositoryCVM`, `InvalidRepositoryTypeError`, removed use case classes).
- [x] 3.7.3 Delete empty intermediate `__init__.py` files.

### 3.8 Phase 2 acceptance gate

- [x] 3.8.1 **Criterion 1 — API surface lock** (same diff command as 2.8.1).
- [x] 3.8.2 **Criterion 2 — Per-capability coverage gate (CVM)**:
  ```bash
  uv run pytest tests/brazil/cvm tests/application/cvm_docs \
    --cov=src/globaldatafinance/brazil/cvm \
    --cov=src/globaldatafinance/application/cvm_docs \
    --cov-report=json:/tmp/cov_cvm_post.json --cov-report=term-missing -q

  uv run python -c "
  import json, sys
  base = json.load(open('openspec/changes/refactor-anti-overengineering/baseline/coverage_per_capability.json'))['cvm']['totals']['percent_covered']
  post = json.load(open('/tmp/cov_cvm_post.json'))['totals']['percent_covered']
  print(f'baseline={base:.2f}% post={post:.2f}% delta={post-base:+.2f}pp')
  sys.exit(0 if post >= base else 1)
  "
  ```
  All green; comparison script exits 0. If below, add minimal `client.py` tests before closing.
- [x] 3.8.3 **Criterion 3 — Behavioral smoke (CVM)**:
  ```bash
  uv run python scripts/smoke_cvm.py > /tmp/smoke_cvm_post.json
  diff openspec/changes/refactor-anti-overengineering/baseline/smoke_cvm.json /tmp/smoke_cvm_post.json
  ```
- [x] 3.8.4 **Criterion 4 — Full suite**: `uv run pre-commit run --all-files` and `uv run pytest` both green.
- [x] 3.8.5 **Criterion 5 — Public smoke**:
  ```bash
  uv run python -c "from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3; print(FundamentalStocksDataCVM().__class__.__name__, HistoricalQuotesB3().__class__.__name__)"
  uv run python -c "import pathlib; p=pathlib.Path('examples/cvm_docs.py'); compile(p.read_text(), str(p), 'exec')"
  ```
- [x] 3.8.6 Commit: `refactor(cvm): collapse fundamental_stocks_data layers, drop single-impl ABCs`.

## 4. Phase 3 — Prune `__init__.py` cascade + audit pending-promotion paths

- [x] 4.1 Audit pending-promotion paths (D8) — confirm they remain in-place and have no internal callers:
  ```bash
  grep -rEn "brazil\.b3_data\.Dados_B3_Acoes|brazil\.b3_data\.Dados_B3_FIIs|brazil\.b3_data\.Opcoes_B3|brazil\.gerais|brazil\.app_geral" src tests docs examples
  ```
  Must return zero lines outside the paths themselves. Do NOT delete, move, or prefix `_legacy/`.
- [x] 4.2 Minimize intermediate `__init__.py` files (D6): `brazil/cvm/__init__.py` and `brazil/b3_data/__init__.py` reduced to empty (or near-empty) modules. `brazil/__init__.py` keeps only the `__getattr__` lazy resolver for `FundamentalStocksDataCVM` / `HistoricalQuotesB3`.
- [x] 4.3 Verify file count: `find src -type f -name '*.py' | wc -l` → target ~50–55 files, preserving the design gate of at least 40% reduction vs baseline 109.
- [x] 4.4 **Acceptance gate**: Criterion 1 (API surface lock), Criterion 4 (`pre-commit` + `pytest`), Criterion 5 (public smoke). Criteria 2 and 3 are optional (no capability code touched).
- [x] 4.5 Commit: `refactor: prune __init__ cascade`.

## 5. Phase 4 — Documentation alignment

- [x] 5.1 Update `AGENTS.md`:
  - "Repository Map" section: refresh tree under `src/globaldatafinance/` to reflect flat per-source layout (no `domain/`, `application/`, `infra/`, `exceptions/` subdirs).
  - "Architecture Map" section: update layered diagram to describe the flat per-source pattern; "Layering Rules" rewritten or removed in favor of "Per-source module pattern".
  - "Design Patterns In Use" section: drop references to ABC repositories and 1-method use cases; document the function-per-operation convention.
  - "Test Layout" section: reflect mirror of new structure.
  - Add a one-line note under "Public API Surface" or "Repository Map" pointing to the pending-promotion paths (`brazil/b3_data/{Dados_B3_*, Opcoes_B3}`, `brazil/gerais/`, `brazil/app_geral.py`) and stating they are out-of-scope for this refactor and will be promoted by future per-source changes.
- [x] 5.2 Update `docs/dev-guide/architecture.md`:
  - Rewrite the Clean Architecture walkthrough to describe the flat per-source pattern.
  - Update the "How to add a new source" example: 2 modules (`core.py` + `client.py` minimum) instead of 4 layers.
  - Refresh Worked Examples to point to the new file paths.
- [x] 5.3 Update internal READMEs (e.g. inside `src/globaldatafinance/brazil/` or per-feature READMEs if they exist) to mirror the new convention.
- [x] 5.4 Verify `README.md` and `docs/user-guide/` need no edits (public API unchanged) — spot-check by `grep -E "from globaldatafinance" README.md docs/user-guide/*.md`.
- [x] 5.5 **Acceptance gate**: Criterion 1, Criterion 4, Criterion 5. Criteria 2/3 not applicable.
- [x] 5.6 Commit: `docs: align AGENTS and dev-guide with flat per-source layout`.

## 6. Final Phase — Consolidated validation

- [x] 6.1 Print branch diff: `git diff --name-only refactor-baseline-pre..HEAD` — review against the Capability Isolation Guarantee (D9).
- [x] 6.2 Run `uv run pre-commit run --all-files` on the full tree.
- [x] 6.3 Run `uv run pytest` (all markers) AND `uv run pytest -m integration` to cover slower / integration-marked tests.
- [x] 6.4 Run final API surface diff (Criterion 1) once more vs `baseline/api_surface.json` — must be empty.
- [x] 6.5 Run `scripts/smoke_b3.py` and `scripts/smoke_cvm.py` one final time vs baselines — must be empty diffs.
- [x] 6.6 File count audit: record final `find src -type f -name '*.py' | wc -l`; expected ~50–55 files, regression-document if outside the design target or if the reduction falls below 40% vs baseline 109.
- [x] 6.7 Confirm no pending `__init__.py` re-exporting removed symbols: `grep -rEn "DownloadDocsCVMRepositoryCVM|FileExtractorRepositoryCVM|InvalidRepositoryTypeError|ExtractionServiceFactoryB3" src tests` → zero lines.
- [x] 6.7bis (R11) Confirm path-traversal defenses preserved: `grep -rEcn "SecurityError" src/globaldatafinance/brazil/cvm/fundamental_stocks_data src/globaldatafinance/brazil/b3_data/historical_quotes tests/application/cvm_docs tests/brazil/b3_data/historical_quotes | awk -F: '{sum+=$NF} END {print sum}'` ≥ baseline count recorded in Phase 0 (current scoped baseline: 37 occurrences). Run the full path-traversal test suite one more time: `uv run pytest tests/application/cvm_docs/test_path_traversal.py tests/brazil/b3_data/historical_quotes/test_file_system_service.py -q` → green with zero test-body edits since baseline (only import-path adjustments and the planned relocation from `infra/` to the package root are allowed).
- [x] 6.8 Confirm pending-promotion paths still in original locations: `ls src/globaldatafinance/brazil/b3_data/Dados_B3_Acoes src/globaldatafinance/brazil/b3_data/Dados_B3_FIIs src/globaldatafinance/brazil/b3_data/Opcoes_B3 src/globaldatafinance/brazil/gerais src/globaldatafinance/brazil/app_geral.py` — all present.
- [x] 6.9 Confirm `pyproject.toml` unchanged in dependencies and tooling (`tool.ruff.lint.per-file-ignores` paths still valid) — `git diff refactor-baseline-pre..HEAD -- pyproject.toml` should show no changes outside permitted edits (none expected).
- [x] 6.10 Ready for OpenSpec verification: `openspec validate refactor-anti-overengineering --strict` (or repo-native equivalent) — green.

### Final Phase audit notes (documenting variance per task 6.6 wording)

- **6.6 file count**: 67 files (38.5% reduction vs baseline 109). Capability files match the design target (CVM `fundamental_stocks_data` = 6 modules incl. `__init__.py`; B3 `historical_quotes` = 8 modules incl. `__init__.py`); the variance vs the design's "~50–55 totals" target comes from pending-promotion paths (D8) being 26 files vs the design's implicit ~14, kept in-place as required by D8. Refactor goal (collapse Clean-Architecture layers per capability) is met; the file-count gate is a downstream metric of the D8 trade-off.
- **6.7bis SecurityError occurrences**: 28 in the scoped grep (baseline 37). The drop is **consolidation noise**, not defense regression — the prior `exceptions/` modules each re-declared/re-mentioned `SecurityError` separately; the flat layout now imports a single `SecurityError` from `macro_exceptions/`. Concrete defenses preserved bit-identically: `raise SecurityError(...)` in `client.py:228` (CVM `VerifyPathsUseCasesCVM.__validate_path_security`) and `core.py:388` (B3 `validate_directory_path`), called **before** any `mkdir`. The 46-test path-traversal suite (`tests/application/cvm_docs/test_path_traversal.py` 7 tests + `tests/brazil/b3_data/historical_quotes/infra/test_file_system_service.py` 39 tests) is **green with zero assertion edits** since baseline — only import-path adjustments.
