# Como Contribuir

Guia para contribuir com o projeto Global-Data-Finance.

______________________________________________________________________

## Configurando Ambiente de Desenvolvimento

### 1. Fork e Clone

```bash
# Fork no GitHub, depois:
git clone https://github.com/jordanestralioto/Global-Data-Finance.git
cd Global-Data-Finance
```

### 2. Instalar Dependências

`uv` é o gestor canônico do projeto (`uv.lock` é commitado). Requer **Python 3.12+**.

```bash
# Sincronizar exatamente o ambiente aprovado pelo lockfile (cria .venv)
uv sync --locked --all-extras --dev

# Para rodar comandos sem sincronização implícita:
uv run --locked --no-sync pytest
uv run --locked --no-sync mypy src
```

### 3. Instalar Pre-commit Hooks

```bash
uv run --locked --no-sync pre-commit install --install-hooks
```

______________________________________________________________________

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
        InvalidDocumentName: Se tipo de documento for inválido.
        NetworkError: Se houver erro de rede.
    """
    pass
```

______________________________________________________________________

## Testes

### Executar Testes

```bash
# Todos os testes
uv run --locked --no-sync pytest

# Com cobertura
uv run --locked --no-sync pytest --cov

# Apenas unitários
uv run --locked --no-sync pytest -m unit
```

Antes de abrir PR, rode o pipeline completo:

```bash
uv run --locked --no-sync pre-commit run --all-files --show-diff-on-failure
uv run --locked --no-sync pytest
```

### Quality Gates Locais

O hook `pre-commit` valida o índice staged e mantém a atualização de
dependências fora do fluxo de commit. Ele nunca executa `uv sync`, `uv lock`
ou atualização de versões: `uv lock --check` apenas comprova a coerência atual
do lockfile. O hook `pre-push` executa as verificações mais caras de tipos,
cobertura e vulnerabilidades antes de publicar uma branch.

Quando uma dependência precisar mudar, faça isso explicitamente, revise o
diff de `uv.lock`, sincronize o ambiente e só então faça o commit:

```bash
uv lock
uv sync --locked --all-extras --dev
git add pyproject.toml uv.lock
```

Os gates de diff, integridade de testes e sintaxe shell examinam apenas o
conteúdo staged durante um commit. O CI executa os mesmos scripts sobre a faixa
de commits da pull request ou do push, portanto um `SKIP` de diff sem arquivos
staged não equivale a aprovação de CI.

`check-harness-sync` é manual porque verifica espelhos de clientes de agentes
que não existem em um checkout limpo. Execute-o apenas ao manter esses
espelhos:

```bash
uv run --locked --no-sync pre-commit run check-harness-sync --hook-stage manual
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

______________________________________________________________________

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
git commit -m "feat: add asynchronous parallel worker pool for CVM downloads"
git commit -m "fix: resolve socket timeout during multi-year COTAHIST extraction"

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

______________________________________________________________________

## Checklist de PR

- [ ] Código segue PEP 8
- [ ] Type hints adicionados
- [ ] Docstrings completas
- [ ] Testes adicionados
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Pre-commit hooks passando

______________________________________________________________________

## Contato

- GitHub Issues: [Abrir issue](https://github.com/jordanestralioto/Global-Data-Finance/issues)
- Email: estraliotojordan@gmail.com
