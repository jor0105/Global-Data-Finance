# Testes

Guia completo sobre testes no Global-Data-Finance.

---

## Estrutura de Testes

```
tests/
├── brazil/
│   ├── b3_data/
│   │   └── historical_quotes/
│   │       ├── domain/
│   │       ├── application/
│   │       └── infra/
│   └── cvm/
│       └── fundamental_stocks_data/
│           ├── domain/
│           ├── application/
│           └── infra/
└── macro_exceptions/
```

---

## Executando Testes

### Todos os Testes

```bash
pytest
```

### Com Cobertura

```bash
pytest --cov=src --cov-report=html
```

### Marcadores

```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Pular testes lentos
pytest -m "not slow"

# Pular testes que precisam de rede
pytest -m "not requires_network"
```

---

## Escrevendo Testes

### Teste Unitário

```python
import pytest
from datafinance.brazil.cvm.fundamental_stocks_data.domain import AvailableDocs
from datafinance.brazil.cvm.fundamental_stocks_data.exceptions import InvalidDocName

@pytest.mark.unit
def test_validate_valid_doc():
    """Testa validação de documento válido."""
    docs = AvailableDocs()
    docs.validate_docs_name("DFP")  # Não deve lançar exceção

@pytest.mark.unit
def test_validate_invalid_doc():
    """Testa validação de documento inválido."""
    docs = AvailableDocs()
    with pytest.raises(InvalidDocName):
        docs.validate_docs_name("INVALID")
```

### Teste de Integração

```python
import pytest
from datafinance import FundamentalStocksDataCVM

@pytest.mark.integration
@pytest.mark.requires_network
def test_get_available_docs():
    """Testa obtenção de documentos disponíveis."""
    cvm = FundamentalStocksDataCVM()
    docs = cvm.get_available_docs()

    assert isinstance(docs, dict)
    assert len(docs) > 0
    assert "DFP" in docs
```

---

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

---

## Cobertura

Objetivo: **>= 80% de cobertura**

```bash
# Gerar relatório
pytest --cov=src --cov-report=term-missing

# Relatório HTML
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## CI/CD

Testes são executados automaticamente em:

- Push para `main` ou `develop`
- Pull Requests
- Releases

---

Veja também:

- [Como Contribuir](contributing.md)
- [Arquitetura](architecture.md)
