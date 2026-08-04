# Installation

This guide provides detailed instructions to install and configure the **Global-Data-Finance** library across different runtime environments.

---

## System Requirements

Before installing Global-Data-Finance, verify that your machine meets the following minimum operating requirements:

### Mandatory Requirements

- **Python**: Version 3.12 or higher
- **Operating System**: Linux, macOS, or Windows
- **Disk Space**: Minimum of 2 GB to store large multi-year regulatory and market datasets
- **RAM**: Minimum of 3 GB (6 GB or more recommended when processing extensive multi-year historical quotes)

### Check Python Version

```bash
python --version
# or
python3 --version
```

!!! warning "Python Version"
    Global-Data-Finance strictly requires Python 3.12 or newer. If your system runs an older version, you must upgrade Python before attempting installation.

---

## Installing via pip (Recommended for Consumers)

The simplest way to integrate Global-Data-Finance as a dependency is via PyPI using `pip`:

```bash
pip install globaldatafinance
```

### Installation within a Virtual Environment (Recommended)

To prevent dependency collisions with systemic Python packages or unrelated workspaces, always install Global-Data-Finance inside an isolated virtual environment:

```bash
# Create a dedicated virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install Global-Data-Finance
pip install globaldatafinance
```

### Upgrade to the Latest Release

```bash
pip install --upgrade globaldatafinance
```

---

## Installing via uv (Alternative to pip)

`uv` is an ultra-fast Python package and project manager and serves as the canonical tool for repository development in this project. To add the library to an external project managed by `uv`:

```bash
# Add as a project runtime dependency
uv add globaldatafinance

# Add as a development dependency
uv add --dev globaldatafinance
```

---

## Development Installation

If you intend to modify the library code, run test suites, or submit pull requests:

### 1. Clone the Repository

```bash
git clone https://github.com/jordanestralioto/Global-Data-Finance.git
cd Global-Data-Finance
```

### 2. Install with uv (Recommended for Contributors)

The repository commits an exact dependency lock (`uv.lock`). Running `uv sync` reproduces the exact verification environment utilized by GitHub Actions CI gates.

```bash
# Synchronize dependencies (automatically bootstraps .venv)
uv sync

# Run diagnostic suites inside the managed environment
uv run pytest
uv run pre-commit run --all-files
```

### 3. Install with pip in Editable Mode

```bash
# Create and activate a new virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install library in editable mode
pip install -e .

# Install with development dependency tools
pip install -e ".[dev]"
```

---

## Runtime Dependencies

Global-Data-Finance builds upon an optimized selection of high-performance libraries:

### Mandatory Dependencies

| Library             | Version | Purpose                                    |
| ------------------- | ------- | ------------------------------------------ |
| `httpx`             | ≥0.28.1 | Asynchronous HTTP client with HTTP/2 support |
| `pandas`            | ≥2.3.3  | Data structures and numerical analytics    |
| `polars`            | ≥1.0.0  | High-performance columnar dataframe processing |
| `pyarrow`           | ≥22.0.0 | Native support for Apache Parquet storage  |
| `pydantic-settings` | ≥2.11.0 | Typed runtime configuration and environment validation |
| `psutil`            | ≥5.9.0  | Real-time CPU and RAM monitoring for adaptive throttling |

### Development Dependencies (Optional)

Installed automatically only when bootstrapping development mode:

| Library           | Purpose                        |
| ----------------- | ------------------------------ |
| `pytest`          | Core test execution framework  |
| `pytest-cov`      | Code coverage reporting and threshold gates |
| `pytest-asyncio`  | Asynchronous test fixture support |
| `mypy`            | Static structural type checking |
| `pre-commit`      | Automated code formatting and pre-commit linting |
| `mkdocs`          | Documentation rendering engine |
| `mkdocs-material` | Material design visual theme for MkDocs |

---

## Verifying Your Installation

After installation completes, run these quick smoke tests to confirm functional operation:

### 1. Verify Public Symbol Imports

```python
# Open an interactive Python terminal
python

# Attempt to import public facade entry points
>>> from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3
>>> print("✓ Global-Data-Finance successfully installed and imported!")
```

### 2. Check Package Version

```python
>>> import globaldatafinance
>>> print(globaldatafinance.__version__)
0.1.2
```

### 3. Basic Inspection Test

```python
from globaldatafinance import FundamentalStocksDataCVM

# Instantiate CVM public facade
cvm = FundamentalStocksDataCVM()

# Retrieve supported document classifications
docs = cvm.get_available_docs()
print(f"✓ Found {len(docs)} supported regulatory document types")

# Retrieve permissible historical time windows
years = cvm.get_available_years()
print(f"✓ Available data spanning from {years['General Document Years']} to {years['Current Year']}")
```

If all evaluations above execute cleanly without exceptions, your installation is fully verified! ✅

---

## Troubleshooting

### Error: "No module named 'globaldatafinance'"

**Cause**: The package was installed in a different Python runtime or your virtual environment remains inactive.

**Solution**:

```bash
# Verify active Python interpreter path
which python  # Linux/macOS
where python  # Windows

# Reinstall the library explicitly within active environment
pip install --force-reinstall globaldatafinance
```

### Error: "Python version 3.12 or higher required"

**Cause**: The interpreter executing the command is older than Python 3.12.

**Solution**:

1. Install Python 3.12 or newer from [python.org](https://www.python.org/downloads/).
2. Create a clean virtual environment targeting the compliant binary:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install globaldatafinance
```

### Dependency Resolution Conflicts

**Cause**: An existing package in your system or environment requires incompatible dependency constraints.

**Solution**:

```bash
# Create an entirely isolated virtual environment
python -m venv venv_clean
source venv_clean/bin/activate
pip install globaldatafinance
```

### Permission Denied (Linux/macOS)

**Cause**: Attempting to install libraries into global system directories without administrative permissions.

**Solution**:

```bash
# NEVER execute sudo pip install!
# Always contain installations inside a virtual environment:
python -m venv venv
source venv/bin/activate
pip install globaldatafinance
```

### Corporate Proxy Restrictions

If executing behind a strict corporate web firewall or proxy:

```bash
# Export proxy environmental overrides
export HTTP_PROXY="http://proxy.enterprise.com:8080"
export HTTPS_PROXY="http://proxy.enterprise.com:8080"

# Execute standard pip installation
pip install globaldatafinance
```

---

## Uninstallation

To remove Global-Data-Finance from your current Python environment:

```bash
pip uninstall globaldatafinance
```

---

## Next Steps

With your runtime configured and verified, dive into practical implementations:

- 🚀 **[Quick Start](quickstart.md)** - Essential code snippets and foundational concepts
- 📄 **[CVM Documents](cvm-docs.md)** - Comprehensive documentation of regulatory disclosures
- 📈 **[B3 Quotes](b3-docs.md)** - Complete reference for historical market quote extraction
- 💻 **[Practical Examples](examples.md)** - Production data workflows and pipelines

---

!!! tip "Contributor Tip"
    If you plan to submit improvements or architectural enhancements to the repository, read the [Contribution Guide](../dev-guide/contributing.md) to initialize local git pre-commit verification hooks.
