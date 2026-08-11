# Contributing Guide

Complete instructions and developer expectations for contributing code and feature enhancements to Global-Data-Finance.

______________________________________________________________________

## Configuring Your Development Environment

### 1. Fork and Clone

```bash
# Create a fork on GitHub, then execute:
git clone https://github.com/jordanestralioto/Global-Data-Finance.git
cd Global-Data-Finance
```

### 2. Install Dependencies

`uv` serves as the canonical project dependency manager (with the verified `uv.lock` committed directly to repository tracking). Development strictly requires **Python 3.12+**.

```bash
# Synchronize environment dependencies (automatically provisions a .venv directory)
uv sync

# Execute commands within the isolated virtual workspace:
uv run pytest
uv run mypy src
```

### 3. Install Pre-commit Quality Hooks

```bash
uv run pre-commit install --install-hooks
```

______________________________________________________________________

## Code Style & Standards

### Style Guidelines

- Strictly obey **PEP 8** formatting rules
- Declare comprehensive **type hints** across all public and private signatures
- Format module docstrings adhering to **Google Style** documentation layouts
- Enforce a hard line length boundary of **79 characters** (evaluated via Ruff Blue-style rules)

### Docstring Implementation Example

```python
def download_docs(
    self,
    destination_path: str,
    list_docs: list[str] | None = None,
) -> DownloadResultCVM:
    """Downloads official regulatory disclosures from CVM servers.

    Args:
        destination_path: Target local storage repository directory.
        list_docs: Explicit collection of document codes to retrieve. If None, downloads all available filings.

    Returns:
        A DownloadResultCVM tracking object summarizing success metrics and failure records.

    Raises:
        InvalidDocumentName: Raised if an unsupported document string is supplied.
        NetworkError: Raised if connection drops or HTTP transfer timeouts occur.
    """
    pass
```

______________________________________________________________________

## Automated Testing

### Executing the Test Suite

```bash
# Execute complete repository test suite
uv run pytest

# Execute tests alongside coverage report calculation
uv run pytest --cov=src

# Execute strictly fast unit tests
uv run pytest -m unit
```

Prior to submitting any Pull Request, verify quality compliance across the entire verification pipeline:

```bash
uv run pre-commit run --all-files
uv run pytest
```

### Authoring Unit Tests

```python
import pytest
from globaldatafinance import FundamentalStocksDataCVM

@pytest.mark.unit
class TestFundamentalStocksData:
    def test_get_available_docs(self):
        """Verifies successful retrieval of supported document catalog."""
        cvm = FundamentalStocksDataCVM()
        docs = cvm.get_available_docs()

        assert isinstance(docs, dict)
        assert "DFP" in docs
        assert len(docs) > 0
```

______________________________________________________________________

## Git Workflow

### Branch Organization

- `main`: Production-grade stable code release history
- `develop`: Active integration testing and current feature staging
- `feature/feature-name`: Autonomous branch for new capability expansions
- `fix/bug-name`: Targeted remediation branch for resolving bugs

### Commit Formatting

Adopt structured, semantic, and descriptive commit formatting:

```bash
# Good examples
git commit -m "feat: implement asynchronous parallel worker pool for CVM downloads"
git commit -m "fix: resolve socket timeout exception during multi-decade COTAHIST extractions"

# Discouraged examples
git commit -m "update code"
git commit -m "fix bug"
```

### Pull Request Lifecycle

1. Branch off directly from `develop`
2. Implement your code changes or bug remediations
3. Contribute accompanying automated test suites
4. Update canonical documentation files and inline docstrings
5. Submit your Pull Request targeting `develop`

______________________________________________________________________

## Pull Request Checklist

- [ ] Code fully complies with PEP 8 and formatting constraints
- [ ] Explicit type annotations added to all signatures
- [ ] Comprehensive Google-style docstrings authored
- [ ] Test suites authored demonstrating happy/error paths
- [ ] Entire testing verification suite passes cleanly
- [ ] Repository documentation artifacts updated accordingly
- [ ] Pre-commit repository verification hooks run clean without warnings

______________________________________________________________________

## Support Contact

- **GitHub Issues**: [Open an issue](https://github.com/jordanestralioto/Global-Data-Finance/issues)
- **Direct Email**: estraliotojordan@gmail.com
