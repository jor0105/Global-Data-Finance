# 📊 Global-Data-Finance

<div align="center">

**Biblioteca Python profissional para extração e processamento de dados financeiros globais com arquitetura limpa e alto desempenho.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/globaldatafinance.svg)](https://pypi.org/project/globaldatafinance/)
[![License](https://img.shields.io/github/license/jor0105/Global-Data-Finance.svg)](https://github.com/jor0105/Global-Data-Finance/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)

[Documentação](https://jor0105.github.io/Global-Data-Finance/) • [Exemplos](#-exemplos-de-uso) • [API Reference](https://jor0105.github.io/Global-Data-Finance/reference/cvm-api/) • [Contribuir](#-contribuindo)

</div>

---

## 🎯 Sobre

**Global-Data-Finance** é uma biblioteca Python moderna e de alto desempenho projetada para facilitar a extração, normalização e processamento de dados financeiros e econômicos de mercados globais. Seguindo os princípios de **Clean Architecture** e **SOLID**, oferece interfaces intuitivas para acessar dados fundamentalistas da CVM e cotações históricas da B3.

### Por que usar?

- ✅ **Arquitetura Limpa**: Código testável, manutenível e escalável
- ✅ **Alto Desempenho**: Múltiplos adapters de download (3-10x mais rápido)
- ✅ **Formato Parquet**: Exportação otimizada para análise de dados
- ✅ **Type Safety**: Suporte completo a type hints
- ✅ **Logging Integrado**: Rastreamento detalhado de operações
- ✅ **Testado Extensivamente**: Suite completa de testes
- ✅ **API Simples**: Interface de alto nível fácil de usar

---

## ✨ Features

### 📈 Fontes de Dados

| Fonte                | Status     | Descrição                               |
| -------------------- | ---------- | --------------------------------------- |
| **CVM - Documentos** | ✅ Estável | DFP, ITR, FRE, FCA, CGVN, VLMO, IPE     |
| **B3 - Cotações**    | ✅ Estável | Histórico completo de ações, ETFs, BDRs |

### 🚀 Adapters de Download

| Adapter                     | Velocidade       | Dependências | Status     |
| --------------------------- | ---------------- | ------------ | ---------- |
| **WgetDownloadAdapter**     | ⭐ 1x (baseline) | wget         | ✅ Estável |
| **AsyncDownloadAdapterCVM** | ⭐⭐⭐ 3-5x      | httpx        | ✅ Padrão  |
| **Aria2cAdapter**           | ⭐⭐⭐⭐⭐ 5-10x | aria2c       | ✅ Estável |

### 📊 Recursos Avançados

- **Download Paralelo**: Múltiplos workers para máxima performance
- **Extração Automática**: Conversão direta para formato Parquet
- **Validação de Inputs**: Verificação automática de documentos e anos
- **Tratamento de Erros**: Exceções específicas e detalhadas
- **Modo de Processamento**: Fast, normal e custom para B3
- **Filtros Avançados**: Por tipo de ativo, período e mais

---

## 🚀 Instalação Rápida

### Pré-requisitos

- Python 3.12 ou superior
- pip (geralmente incluído com Python)

### Instalação via PyPI (Usuários)

```bash
# Instalação básica
pip install globaldatafinance

# OU com Poetry
poetry add globaldatafinance
```

### Configuração

Não há configuração necessária! A biblioteca está pronta para uso imediato.

### Instalação para Desenvolvimento (Contribuidores)

Se você deseja contribuir com o projeto:

```bash
# Clone o repositório
git clone https://github.com/jor0105/Global-Data-Finance.git
cd Global-Data-Finance

# Instale com Poetry
poetry install

# Execute os testes
poetry run pytest

# Configure pre-commit hooks
poetry run pre-commit install
```

📖 [Guia completo para contribuidores →](https://jor0105.github.io/Global-Data-Finance/dev-guide/contributing/)

---

## 💡 Quick Start

### Exemplo Básico - Documentos CVM

```python
from globaldatafinance import FundamentalStocksDataCVM

# Criar cliente CVM
cvm = FundamentalStocksDataCVM()

# Baixar documentos
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR"],
    initial_year=2020,
    last_year=2023,
    automatic_extractor=True  # Extrai para Parquet automaticamente
)
```

### Exemplo Básico - Cotações B3

```python
from globaldatafinance import HistoricalQuotesB3

# Criar cliente B3
b3 = HistoricalQuotesB3()

# Extrair cotações
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf"],
    initial_year=2020,
    processing_mode="fast"
)

print(f"✓ Extraídos {result['total_records']:,} registros")
```

### Formas de Import

```python
# Opção 1: Import direto (recomendado)
from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3

# Opção 2: Import específico do módulo Brazil
from globaldatafinance.brazil import FundamentalStocksDataCVM, HistoricalQuotesB3
```

Ambas as formas funcionam perfeitamente e retornam as mesmas classes!

---

## 📋 Exemplos de Uso

### Exemplo 1: Download com Máxima Performance

```python
from globaldatafinance import FundamentalStocksDataCVM

# Usar adapter padrão (AsyncDownloadAdapterCVM - 3-5x mais rápido)
cvm = FundamentalStocksDataCVM()

result = cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR", "FRE"],
    initial_year=2018,
    last_year=2023,
    automatic_extractor=True
)

# Analisar resultados
print(f"✓ Arquivos baixados: {result.success_count_downloads}")
print(f"✗ Erros encontrados: {result.error_count_downloads}")

for doc_name, years in result.successful_downloads.items():
    print(f"  {doc_name}: {years}")
```

### Exemplo 2: Usando Aria2c (Máxima Velocidade)

```python
from globaldatafinance.brazil.cvm.fundamental_stocks_data.infra.adapters import Aria2cAdapter
from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCaseCVM

# Instalar aria2c primeiro:
# Linux: sudo apt-get install aria2
# macOS: brew install aria2

# Usar Aria2c (5-10x mais rápido)
adapter = Aria2cAdapter(max_concurrent_downloads=16)
use_case = DownloadDocumentsUseCaseCVM(adapter)

result = use_case.execute(
    destination_path="/data/cvm",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)

print(f"Download concluído em tempo recorde! ⚡")
```

### Exemplo 3: Cotações B3 com Filtros

```python
from globaldatafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()

# Extrair apenas ações e ETFs
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf"],
    initial_year=2020,
    last_year=2023,
    processing_mode="fast"
)

# Acessar dados
print(f"Total de registros: {result['total_records']:,}")
print(f"Período: {result['period']}")
print(f"Ativos únicos: {result['unique_assets']}")

# Dados estão em formato Parquet
df = result['dataframe']
print(df.head())
```

### Exemplo 4: Documentos CVM Disponíveis

```python
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()

# Tipos de documentos disponíveis
docs_disponiveis = {
    "DFP": "Demonstrações Financeiras Padronizadas (2010+)",
    "ITR": "Informações Trimestrais (2011+)",
    "FRE": "Formulário de Referência (2010+)",
    "FCA": "Formulário Cadastral (2010+)",
    "CGVN": "Código de Governança (2018+)",
    "VLMO": "Valores Mobiliários (2018+)",
    "IPE": "Documentos Periódicos e Eventuais (2010+)"
}

# Baixar múltiplos tipos
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR", "FRE"],
    initial_year=2020,
    last_year=2023
)
```

### Exemplo 5: Tratamento de Erros

```python
from globaldatafinance import FundamentalStocksDataCVM
from globaldatafinance.brazil.cvm.fundamental_stocks_data.exceptions import (
    InvalidDocName,
    InvalidFirstYear
)
from globaldatafinance.macro_exceptions import (
    NetworkError,
    TimeoutError,
    PermissionError
)

cvm = FundamentalStocksDataCVM()

try:
    result = cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2020,
        last_year=2023
    )

    # Verificar se houve erros
    if result.has_errors:
        for error in result.errors:
            print(f"⚠️ Erro: {error}")

except InvalidDocName as e:
    print(f"❌ Documento inválido: {e}")
except InvalidFirstYear as e:
    print(f"❌ Ano inválido: {e}")
except NetworkError as e:
    print(f"❌ Erro de rede: {e}")
except TimeoutError as e:
    print(f"❌ Timeout: {e}")
except PermissionError as e:
    print(f"❌ Permissão negada: {e}")
```

---

## 🏗️ Arquitetura

Este projeto segue **Clean Architecture** e **SOLID Principles**:

```
src/
├── brazil/
│   ├── cvm/
│   │   └── fundamental_stocks_data/
│   │       ├── domain/              # Entidades e regras de negócio
│   │       ├── application/         # Casos de uso e interfaces
│   │       ├── infra/               # Adapters e implementações
│   │       └── exceptions/          # Exceções específicas
│   └── b3/
│       └── historical_quotes/
│           ├── domain/
│           ├── application/
│           └── infra/
├── presentation/                    # API de alto nível
└── macro_exceptions/                # Exceções globais
```

### Diagrama de Camadas

```
┌─────────────────────────────────────┐
│        PRESENTATION                 │  ← FundamentalStocksDataCVM
│     (High-level API)                │     HistoricalQuotesB3
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        APPLICATION                  │  ← Use Cases & Interfaces
│    (Business Logic)                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │  ← Entities & Value Objects
│    (Core Business)                  │
└──────────────▲──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │  ← Adapters (Wget, Async, Aria2c)
│  (External Services)                │
└─────────────────────────────────────┘
```

**Benefícios**: Testável, Flexível, Escalável e Manutenível

📖 [Documentação completa da arquitetura](https://jor0105.github.io/Global-Data-Finance/dev-guide/architecture/)

---

## 📚 Documentação

### Guia do Usuário

- 📖 [Instalação](https://jor0105.github.io/Global-Data-Finance/user-guide/installation/)
- 🚀 [Início Rápido](https://jor0105.github.io/Global-Data-Finance/user-guide/quickstart/)
- 📄 [Documentos CVM](https://jor0105.github.io/Global-Data-Finance/user-guide/cvm-docs/)
- 📈 [Cotações B3](https://jor0105.github.io/Global-Data-Finance/user-guide/b3-docs/)
- 💡 [Exemplos Práticos](https://jor0105.github.io/Global-Data-Finance/user-guide/examples/)
- ❓ [FAQ](https://jor0105.github.io/Global-Data-Finance/user-guide/faq/)

### Guia do Desenvolvedor

- 🏗️ [Arquitetura](https://jor0105.github.io/Global-Data-Finance/dev-guide/architecture/)
- 📖 [Referência da API](https://jor0105.github.io/Global-Data-Finance/dev-guide/api-reference/)
- 🤝 [Como Contribuir](https://jor0105.github.io/Global-Data-Finance/dev-guide/contributing/)
- 🧪 [Testes](https://jor0105.github.io/Global-Data-Finance/dev-guide/testing/)
- 🔧 [Uso Avançado](https://jor0105.github.io/Global-Data-Finance/dev-guide/advanced-usage/)

### Referência Técnica

- 📚 [API CVM](https://jor0105.github.io/Global-Data-Finance/reference/cvm-api/)
- 📊 [API B3](https://jor0105.github.io/Global-Data-Finance/reference/b3-api/)
- ⚠️ [Exceções](https://jor0105.github.io/Global-Data-Finance/reference/exceptions/)
- 📋 [Formatos de Dados](https://jor0105.github.io/Global-Data-Finance/reference/data-formats/)

### Build Local da Documentação

```bash
poetry run mkdocs serve
# Acesse: http://localhost:8000
```

---

## 🔧 Configuração Avançada

### Comparação de Adapters

| Adapter                     | Velocidade       | Dependências | Melhor Para        |
| --------------------------- | ---------------- | ------------ | ------------------ |
| **WgetDownloadAdapter**     | ⭐ 1x (baseline) | wget         | Compatibilidade    |
| **AsyncDownloadAdapterCVM** | ⭐⭐⭐ 3-5x      | httpx        | **Recomendado** ✅ |
| **Aria2cAdapter**           | ⭐⭐⭐⭐⭐ 5-10x | aria2c       | Máxima velocidade  |

### Configuração do AsyncDownloadAdapterCVM (Padrão)

```python
from globaldatafinance import FundamentalStocksDataCVM

# Já vem configurado por padrão!
cvm = FundamentalStocksDataCVM()

# Download paralelo com 8 workers
result = cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR"],
    initial_year=2020,
    last_year=2023
)
```

### Configuração do Aria2cAdapter (Máxima Performance)

```bash
# Instalar aria2c
# Linux
sudo apt-get install aria2

# macOS
brew install aria2

# Windows: https://github.com/aria2/aria2/releases
```

```python
from globaldatafinance.brazil.cvm.fundamental_stocks_data.infra.adapters import Aria2cAdapter
from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCaseCVM

# Configurar com 16 downloads simultâneos
adapter = Aria2cAdapter(
    max_concurrent_downloads=16,
    connections_per_file=8,
    min_split_size="1M"
)

use_case = DownloadDocumentsUseCaseCVM(adapter)

result = use_case.execute(
    destination_path="/data/cvm",
    doc_types=["DFP", "ITR", "FRE"],
    start_year=2018,
    end_year=2023
)
```

### Configuração de Logging

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Os adapters registrarão automaticamente informações sobre downloads
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
cvm.download(...)  # Logs automáticos
```

---

## 📊 API Reference

### FundamentalStocksDataCVM

```python
FundamentalStocksDataCVM()
```

#### Métodos Principais

| Método                                                                                      | Retorno             | Descrição             |
| ------------------------------------------------------------------------------------------- | ------------------- | --------------------- |
| `download(destination_path, list_docs, initial_year, last_year, automatic_extractor=False)` | `DownloadResultCVM` | Baixar documentos CVM |

#### Parâmetros do `download()`

- **destination_path** (`str`): Caminho de destino para salvar arquivos
- **list_docs** (`list[str]`): Lista de documentos (DFP, ITR, FRE, etc.)
- **initial_year** (`int`): Ano inicial (2010+)
- **last_year** (`int`): Ano final
- **automatic_extractor** (`bool`, opcional): Extrair para Parquet automaticamente

### HistoricalQuotesB3

```python
HistoricalQuotesB3()
```

#### Métodos Principais

| Método                                                                                       | Retorno | Descrição                   |
| -------------------------------------------------------------------------------------------- | ------- | --------------------------- |
| `extract(path_of_docs, assets_list, initial_year, last_year=None, processing_mode="normal")` | `dict`  | Extrair cotações históricas |

#### Parâmetros do `extract()`

- **path_of_docs** (`str`): Caminho dos arquivos COTAHIST
- **assets_list** (`list[str]`): Lista de ativos (ações, etf, bdr, etc.)
- **initial_year** (`int`): Ano inicial
- **last_year** (`int`, opcional): Ano final (padrão: ano atual)
- **processing_mode** (`str`, opcional): "fast", "normal" ou "custom"

📖 [Documentação completa da API](https://jor0105.github.io/Global-Data-Finance/reference/cvm-api/)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos:

1. **Fork** o repositório

2. **Crie uma branch**: `git checkout -b feature/nova-feature`

3. **Implemente** seguindo os padrões existentes

4. **Adicione testes**: Garanta cobertura adequada

5. **Execute os checks**:

   ```bash
   # Instalar pre-commit hooks
   poetry run pre-commit install

   # Executar todos os checks
   poetry run pre-commit run --all-files

   # Executar testes com cobertura
   poetry run pytest --cov=src
   ```

6. **Envie um Pull Request**

### Adicionando um Novo Adapter

1. Crie um novo adapter em `src/brazil/cvm/fundamental_stocks_data/infra/adapters/`
2. Implemente a interface `DownloadDocsCVMRepository`
3. Adicione testes em `tests/infra/adapters/`

Exemplo:

```python
from src.brazil.cvm.fundamental_stocks_data.application.interfaces import DownloadDocsCVMRepository

class MeuAdapter(DownloadDocsCVMRepository):
    def download_docs(self, your_path: str, dict_zip_to_download: dict) -> DownloadResultCVM:
        # Sua implementação
        pass
```

📖 [Guia completo de contribuição](https://jor0105.github.io/Global-Data-Finance/dev-guide/contributing/)

---

## 🧪 Testes & Quality Checks

Este projeto mantém altos padrões de qualidade:

### Executar Testes

```bash
# Todos os testes
poetry run pytest

# Com cobertura
poetry run pytest --cov=src

# Apenas testes unitários
poetry run pytest -m unit

# Testes específicos
poetry run pytest tests/brazil/cvm/
```

### Pre-commit Hooks

Verificadores automáticos antes de cada commit:

```bash
# Instalar
poetry run pre-commit install

# Executar manualmente
poetry run pre-commit run --all-files
```

### Quality Checks

- ✅ Formatação (Black)
- ✅ Linting (Ruff, Flake8)
- ✅ Type checking (mypy)
- ✅ Security (Bandit)
- ✅ Docstring validation (pydocstyle)

---

## 🗺️ Roadmap

### Próximas Funcionalidades

- [ ] CLI com typer para linha de comando
- [ ] Cache local de arquivos baixados
- [ ] Suporte a dados dos EUA (SEC, FRED)
- [ ] Dashboard web com Streamlit
- [ ] Rate limiting para requisições
- [ ] Exportação para múltiplos formatos (CSV, JSON, SQL)
- [ ] Integração com cloud storage (S3, GCS)

### Possíveis Adapters

- [ ] CloudStorageAdapter (upload para S3/GCS)
- [ ] DatabaseAdapter (persistência direto em BD)
- [ ] CacheAdapter (cache local inteligente)

---

## 📄 Licença

Este projeto está licenciado sob a **Apache License 2.0** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 📞 Suporte

- 📖 [Documentação Completa](https://jor0105.github.io/Global-Data-Finance/)
- 🐛 [Reportar Bugs](https://github.com/jor0105/Global-Data-Finance/issues)
- 💬 [Discussões](https://github.com/jor0105/Global-Data-Finance/discussions)
- 📧 Email: estraliotojordan@gmail.com

---

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jor0105](https://github.com/jor0105)
- Email: estraliotojordan@gmail.com

---

## 📚 Referências

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [CVM - Dados Abertos](https://dados.cvm.gov.br/)
- [B3 - Dados Históricos](http://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

<div align="center">

**Versão:** 0.1.0
**Última atualização:** 24/11/2025
**Status:** 🚀 Projeto ativo! Aberto para contribuições e sugestões.

⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!

</div>
