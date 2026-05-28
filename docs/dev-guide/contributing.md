# Como Contribuir

Guia para contribuir com o projeto Global-Data-Finance.

---

## Configurando Ambiente de Desenvolvimento

### 1. Fork e Clone

```bash
# Fork no GitHub, depois:
git clone https://github.com/jor0105/Global-Data-Finance.git
cd Global-Data-Finance
```

### 2. Instalar Dependências

`uv` é o gestor canônico do projeto (`uv.lock` é commitado). Requer **Python 3.12+**.

```bash
# Sincronizar dependências (cria .venv automaticamente)
uv sync

# Para rodar comandos no ambiente:
uv run pytest
uv run mypy src
```

### 3. Instalar Pre-commit Hooks

```bash
uv run pre-commit install
```

---

## Padrões de Código

### Style Guide

- Seguir **PEP 8**
- Usar **type hints** em todo código
- Docstrings no formato **Google Style**
- Máximo de 79 caracteres por linha (ruff, Blue-style formatting)

### Exemplo de Docstring

```python
def download_docs(
    self,
    destination_path: str,
    list_docs: list[str] | None = None,
) -> DownloadResultCVM:
    """Baixa documentos CVM.

    Args:
        destination_path: Diretório onde salvar arquivos.
        list_docs: Lista de tipos de documentos. Se None, baixa todos.

    Returns:
        Objeto DownloadResultCVM com resultados do download.

    Raises:
        InvalidDocName: Se tipo de documento for inválido.
        NetworkError: Se houver erro de rede.
    """
    pass
```

---

## Testes

### Executar Testes

```bash
# Todos os testes
uv run pytest

# Com cobertura
uv run pytest --cov=src

# Apenas unitários
uv run pytest -m unit
```

Antes de abrir PR, rode o pipeline completo:

```bash
uv run pre-commit run --all-files
uv run pytest
```

### Escrever Testes

```python
import pytest
from globaldatafinance import FundamentalStocksDataCVM

@pytest.mark.unit
class TestFundamentalStocksData:
    def test_get_available_docs(self):
        """Testa obtenção de documentos disponíveis."""
        cvm = FundamentalStocksDataCVM()
        docs = cvm.get_available_docs()

        assert isinstance(docs, dict)
        assert "DFP" in docs
        assert len(docs) > 0
```

---

## Workflow Git

### Branches

- `main`: Código estável
- `develop`: Desenvolvimento
- `feature/nome-feature`: Novas funcionalidades
- `fix/nome-bug`: Correções de bugs

### Commits

Use mensagens descritivas:

```bash
# Bom
git commit -m "feat: adiciona suporte a download paralelo"
git commit -m "fix: corrige erro de timeout em downloads grandes"

# Evite
git commit -m "update"
git commit -m "fix bug"
```

### Pull Requests

1. Crie branch a partir de `develop`
2. Faça suas alterações
3. Adicione testes
4. Atualize documentação
5. Abra PR para `develop`

---

## Checklist de PR

- [ ] Código segue PEP 8
- [ ] Type hints adicionados
- [ ] Docstrings completas
- [ ] Testes adicionados
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Pre-commit hooks passando

---

## Contato

- GitHub Issues: [Abrir issue](https://github.com/jor0105/Global-Data-Finance/issues)
- Email: estraliotojordan@gmail.com
