# Testing Strategy

Comprehensive guide detailing automated test organization, execution commands, and testing patterns implemented within Global-Data-Finance.

______________________________________________________________________

## Test Repository Hierarchy

The test directory structure cleanly mirrors the source tree. Subdirectories inside individual source test folders serve a strictly **organizational** purpose (grouping test scripts by functional topic to enhance code legibility) rather than architectural enforcement—all testing fixtures import symbols directly from the owning source modules.

```text
tests/
├── application/                       # Unit tests evaluating public application facades
│   ├── cvm_docs/
│   └── b3_docs/
│       └── result_formatters/
├── brazil/
│   ├── b3_data/
│   │   └── historical_quotes/         # Flat layout containing test_*.py scripts directly in folder
│   └── cvm/
│       └── fundamental_stocks_data/
│           ├── application/use_cases/ # Orchestration use case tests (client.py)
│           ├── domain/                # Value object and domain validator tests (core.py)
│           ├── infra/adapters/        # Concrete I/O adapter tests (http.py, extract.py)
│           ├── exceptions/            # Custom exception triggering suites (errors.py)
│           └── integration/           # Integration test suites marked with @pytest.mark.integration
├── core/
├── macro_infra/
└── macro_exceptions/
```

______________________________________________________________________

## Executing Tests

### Running the Entire Suite

```bash
uv run --locked --no-sync pytest
```

### Evaluating Code Coverage

Coverage configuration, including the `fail_under = 85` threshold, is owned by
`[tool.coverage.report]` in `pyproject.toml`. The `pytest.ini` file owns pytest
discovery, markers, and options.

```bash
uv run --locked --no-sync pytest --cov --cov-report=html
```

### Utilizing Pytest Markers

Registered markers in `pytest.ini` include: `unit`, `integration`, `slow`, and `asyncio` (enforced via `--strict-markers` to catch undeclared custom markers immediately).

```bash
# Execute only rapid isolated unit tests
uv run --locked --no-sync pytest -m unit

# Execute integration tests
uv run --locked --no-sync pytest -m integration

# Combine logical marker constraints
uv run --locked --no-sync pytest -m "integration and not slow"
```

______________________________________________________________________

## Authoring Tests

### Unit Test Pattern

```python
import pytest
from globaldatafinance.brazil.cvm.fundamental_stocks_data.core import (
    validate_docs_name,
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data.errors import (
    InvalidDocumentName,
)

@pytest.mark.unit
class TestValidateDocsName:
    def test_validate_valid_doc(self):
        """Verifies validation succeeds without exception on valid document code."""
        validate_docs_name("DFP")  # Should pass silently

    def test_validate_invalid_doc(self):
        """Verifies InvalidDocumentName is raised upon supplying unverified strings."""
        with pytest.raises(InvalidDocumentName):
            validate_docs_name("INVALID_CODE")
```

> Types and exceptions belong within the focused modules of their owning source feature: for CVM inside `brazil.cvm.fundamental_stocks_data.core` and `brazil.cvm.fundamental_stocks_data.errors`; for B3 logical separation is segmented topically—entities in `models.py`, value objects in `years.py`/`processing.py`, path security validators in `filesystem.py`, asset services in `assets.py`, and exceptions in `errors.py`.

### Mock and Dependency Substitution Strategies

To decouple unit verification from live network servers or real storage file system IO, test fixtures substitute external adapters using duck-typed stubs or `monkeypatch.setattr`:

```python
from globaldatafinance.brazil.cvm.fundamental_stocks_data.client import (
    DownloadDocumentsUseCaseCVM,
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data.core import (
    DownloadResultCVM,
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data.http import (
    DownloadTaskCVM,
)


class MockRepository:
    def download_docs(
        self,
        tasks: list[DownloadTaskCVM],
        *,
        automatic_extractor: bool | None = None,
    ) -> DownloadResultCVM:
        return DownloadResultCVM(
            successful_downloads=["DFP_2023", "ITR_2023"],
            failed_downloads={},
            elapsed_time=0.5,
        )


use_case = DownloadDocumentsUseCaseCVM(MockRepository())
result = use_case.execute(destination_path="/tmp/cvm")
assert result.success_count_downloads == 2
```

### Integration Testing Pattern

```python
import pytest
from globaldatafinance import FundamentalStocksDataCVM

@pytest.mark.integration
class TestFundamentalStocksDataIntegration:
    def test_get_available_docs(self):
        """Evaluates live instantiation and catalog mapping generation."""
        cvm = FundamentalStocksDataCVM()
        docs = cvm.get_available_docs()

        assert isinstance(docs, dict)
        assert len(docs) > 0
        assert "DFP" in docs
```

______________________________________________________________________

## Standard Test Fixtures

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_dir(tmp_path):
    """Provides an isolated temporary directory per test execution."""
    return tmp_path

@pytest.fixture
def sample_zip_file(tmp_path):
    """Creates an automated mockup ZIP archive file fixture."""
    zip_path = tmp_path / "test.zip"
    # Construct mockup ZIP structural headers...
    return zip_path
```

______________________________________________________________________

## Coverage Goals & Gates

Target: **>= 85% aggregated code coverage** (automatically enforced via
`fail_under = 85` in `[tool.coverage.report]` within `pyproject.toml`). This is
also the floor for newly introduced feature modules.

```bash
# Generate terminal missing line summary report
uv run --locked --no-sync pytest --cov --cov-report=term-missing

# Compile interactive HTML diagnostic coverage tree
uv run --locked --no-sync pytest --cov --cov-report=html
open htmlcov/index.html
```

______________________________________________________________________

## Continuous Integration (CI/CD)

Automated quality verification gates execute on GitHub Actions during:

- Commit pushes targeting `main` or `develop` branches
- Every Pull Request opened against project target branches
- Tagged release build packaging workflows

______________________________________________________________________

## Next Steps

- [Contributing Guide](contributing.md) - Workflow expectations for contributors
- [Architecture Guide](architecture.md) - Deep structural design concepts
