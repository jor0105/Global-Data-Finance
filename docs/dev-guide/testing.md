# Testes

Guia completo sobre testes no Global-Data-Finance.

______________________________________________________________________

## Estrutura de Testes

A árvore de testes espelha cada fonte. Os subdiretórios dentro de cada feature são **organizacionais** (agrupam por tópico para legibilidade), não arquiteturais — qualquer teste importa diretamente dos módulos da fonte (`from globaldatafinance.brazil.<país>.<fonte>.<módulo> import ...`).

```
tests/
├── application/                       # tests do facade público
│   ├── cvm_docs/
│   └── b3_docs/
│       └── result_formatters/
├── brazil/
│   ├── b3_data/
│   │   └── historical_quotes/         # layout plano: arquivos test_*.py diretamente na pasta
│   └── cvm/
│       └── fundamental_stocks_data/
│           ├── application/use_cases/ # tests de orquestração (client.py)
│           ├── domain/                # tests de value objects e validators (core.py)
│           ├── infra/adapters/        # tests dos adapters concretos (http.py, extract.py)
│           ├── exceptions/            # tests das exceções (errors.py)
│           └── integration/           # tests integration-marker
├── core/
├── macro_infra/
└── macro_exceptions/
```

______________________________________________________________________

## Executando Testes

### Todos os Testes

```bash
uv run --locked --no-sync pytest
```

### Com Cobertura

A configuração de coverage, incluindo o limite `fail_under = 85`, fica em
`[tool.coverage.report]` no `pyproject.toml`. O `pytest.ini` mantém a
descoberta, os markers e as opções do pytest.

```bash
uv run --locked --no-sync pytest --cov --cov-report=html
```

### Marcadores

Os markers registrados em `pytest.ini` são: `unit`, `integration`, `slow`, `asyncio` (com `--strict-markers`, então qualquer marker não declarado falha).

```bash
# Apenas testes unitários
uv run --locked --no-sync pytest -m unit

# Apenas testes de integração
uv run --locked --no-sync pytest -m integration

# Combinar markers
uv run --locked --no-sync pytest -m "integration and not slow"
```

______________________________________________________________________

## Escrevendo Testes

### Teste Unitário

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
        """Verifica validação de documento válido."""
        validate_docs_name("DFP")  # Passa sem exceção

    def test_validate_invalid_doc(self):
        """Verifica se InvalidDocumentName é lançada para documento inválido."""
        with pytest.raises(InvalidDocumentName):
            validate_docs_name("INVALID")
```

> Tipos e exceções de cada fonte vivem nos módulos da própria fonte: para CVM em `brazil.cvm.fundamental_stocks_data.core` e `brazil.cvm.fundamental_stocks_data.errors`; para B3 a divisão é mais granular — entidades em `models.py`, value objects em `years.py`/`processing.py`, validators de filesystem em `filesystem.py`, asset services em `assets.py`, exceções em `errors.py`.

### Estratégias de Mocking

Para desacoplar chamadas de I/O de rede ou sistema de arquivos, os testes substituem as dependências via stubs com duck typing ou `monkeypatch.setattr`:

```python
class MockRepository:
    def download_docs(self, tasks):
        return DownloadResultCVM(
            success_count_downloads=2,
            error_count_downloads=0,
            successful_downloads=["DFP_2023", "ITR_2023"],
            failed_downloads={},
        )

from globaldatafinance.brazil.cvm.fundamental_stocks_data.client import (
    DownloadDocumentsUseCaseCVM,
)

use_case = DownloadDocumentsUseCaseCVM(MockRepository())
result = use_case.execute(destination_path="/tmp/cvm")
assert result.success_count_downloads == 2
```

### Teste de Integração

```python
import pytest
from globaldatafinance import FundamentalStocksDataCVM

@pytest.mark.integration
class TestFundamentalStocksDataIntegration:
    def test_get_available_docs(self):
        """Testa obtenção de documentos disponíveis."""
        cvm = FundamentalStocksDataCVM()
        docs = cvm.get_available_docs()

        assert isinstance(docs, dict)
        assert len(docs) > 0
        assert "DFP" in docs
```

______________________________________________________________________

## Fixtures

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_dir(tmp_path):
    """Cria diretório temporário para testes."""
    return tmp_path

@pytest.fixture
def sample_zip_file(tmp_path):
    """Cria arquivo ZIP de exemplo."""
    zip_path = tmp_path / "test.zip"
    # Criar ZIP...
    return zip_path
```

______________________________________________________________________

## Cobertura

Objetivo: **>= 85% de cobertura agregada** (enforced via `fail_under = 85` em
`[tool.coverage.report]` no `pyproject.toml`). Esse é também o piso para
módulos novos.

```bash
# Gerar relatório
uv run --locked --no-sync pytest --cov --cov-report=term-missing

# Relatório HTML
uv run --locked --no-sync pytest --cov --cov-report=html
open htmlcov/index.html
```

______________________________________________________________________

## CI/CD

Testes são executados automaticamente em:

- Push para `main` ou `develop`
- Pull Requests
- Releases

______________________________________________________________________

Veja também:

- [Como Contribuir](contributing.md)
- [Arquitetura](architecture.md)
