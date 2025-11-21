# DataFinance 📊

**Biblioteca Python profissional para extração e processamento de dados financeiros globais**

[![PyPI version](https://img.shields.io/pypi/v/datafinance.svg)](https://pypi.org/project/datafinance/)
[![Python](https://img.shields.io/pypi/pyversions/datafinance.svg)](https://pypi.org/project/datafinance/)
[![License](https://img.shields.io/github/license/jor0105/Global-Data-Finance.svg)](https://github.com/jor0105/Global-Data-Finance/blob/main/LICENSE)

---

## Visão Geral

**DataFinance** é uma biblioteca Python moderna e de alto desempenho projetada para facilitar a extração, normalização e processamento de dados financeiros e econômicos do mercado brasileiro. Com foco em simplicidade de uso e performance, a biblioteca oferece interfaces intuitivas para acessar dados fundamentalistas da CVM e cotações históricas da B3.

### Características Principais

✨ **Interface Simples e Intuitiva** - API de alto nível fácil de usar  
⚡ **Alto Desempenho** - Processamento otimizado com múltiplos workers  
📊 **Formato Parquet** - Exportação direta para formato otimizado  
🏗️ **Arquitetura Limpa** - Código bem estruturado seguindo princípios SOLID  
🔒 **Type Hints Completos** - Código totalmente tipado  
📝 **Logging Integrado** - Rastreamento detalhado de operações  
🧪 **Testado Extensivamente** - Suite completa de testes

---

## Instalação

### Via pip (PyPI)

```bash
pip install datafinance
```

### Via Poetry

```bash
poetry add datafinance
```

### Requisitos

- Python 3.12 ou superior
- Dependências principais: `httpx`, `pandas`, `polars`, `pyarrow`, `pydantic-settings`

📖 **[Guia completo de instalação](https://jor0105.github.io/Global-Data-Finance/user-guide/installation/)**

---

## Início Rápido

### Documentos CVM

```python
from datafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR"],
    initial_year=2020,
    last_year=2023,
    automatic_extractor=True  # Extrai para Parquet
)
```

### Cotações B3

```python
from datafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf"],
    initial_year=2020,
    processing_mode="fast"
)

print(f"✓ Extraídos {result['total_records']:,} registros")
```

📖 **[Guia de início rápido completo](https://jor0105.github.io/Global-Data-Finance/user-guide/quickstart/)**

---

## Documentação Completa

A documentação completa está disponível em: **[https://jor0105.github.io/Global-Data-Finance/](https://jor0105.github.io/Global-Data-Finance/)**

### Para Usuários

- 📦 **[Instalação](https://jor0105.github.io/Global-Data-Finance/user-guide/installation/)** - Como instalar e configurar
- 🚀 **[Início Rápido](https://jor0105.github.io/Global-Data-Finance/user-guide/quickstart/)** - Primeiros passos
- 📄 **[Documentos CVM](https://jor0105.github.io/Global-Data-Finance/user-guide/cvm-docs/)** - Guia completo da API CVM
- 📈 **[Cotações B3](https://jor0105.github.io/Global-Data-Finance/user-guide/b3-docs/)** - Guia completo da API B3
- 💻 **[Exemplos Práticos](https://jor0105.github.io/Global-Data-Finance/user-guide/examples/)** - Casos de uso reais
- ❓ **[FAQ](https://jor0105.github.io/Global-Data-Finance/user-guide/faq/)** - Perguntas frequentes

### Para Desenvolvedores

- 🏗️ **[Arquitetura](https://jor0105.github.io/Global-Data-Finance/dev-guide/architecture/)** - Estrutura e padrões
- 📖 **[Referência da API](https://jor0105.github.io/Global-Data-Finance/dev-guide/api-reference/)** - Documentação completa
- 🤝 **[Como Contribuir](https://jor0105.github.io/Global-Data-Finance/dev-guide/contributing/)** - Guia para contribuidores
- 🧪 **[Testes](https://jor0105.github.io/Global-Data-Finance/dev-guide/testing/)** - Como executar testes
- 🔧 **[Uso Avançado](https://jor0105.github.io/Global-Data-Finance/dev-guide/advanced-usage/)** - Customização

---

## Estrutura do Projeto

## Início Rápido

### Exemplo Básico

```python
from src.brazil.cvm.fundamental_stocks_data.domain import DictZipsToDownload
from src.brazil.cvm.fundamental_stocks_data.infra.adapters import WgetDownloadAdapter

# 1. Gerar URLs de download
dict_generator = DictZipsToDownload()
dict_zips = dict_generator.get_dict_zips_to_download(
    list_docs=["DFP"],           # Demonstrações Financeiras Padronizadas
    initial_year=2020,
    last_year=2023
)

# 2. Fazer download
adapter = WgetDownloadAdapter()
result = adapter.download_docs(
    your_path="/home/user/downloads",
    dict_zip_to_download=dict_zips
)

# 3. Analisar resultados
print(f"Arquivos baixados: {result.success_count_downloads}")
print(f"Erros encontrados: {result.error_count_downloads}")

for doc_name, years in result.successful_downloads.items():
    print(f"{doc_name}: {years}")

for error in result.errors:
    print(f"Erro: {error}")
```

### Documentos Disponíveis

A biblioteca suporta os seguintes tipos de documentos CVM:

| Código   | Descrição                              | Anos Disponíveis |
| -------- | -------------------------------------- | ---------------- |
| **DFP**  | Demonstrações Financeiras Padronizadas | 2010+            |
| **ITR**  | Informações Trimestrais                | 2011+            |
| **FRE**  | Formulário de Referência               | 2010+            |
| **FCA**  | Formulário Cadastral                   | 2010+            |
| **CGVN** | Código de Governança                   | 2018+            |
| **VLMO** | Valores Mobiliários                    | 2018+            |
| **IPE**  | Documentos Periódicos e Eventuais      | 2010+            |

## Uso Avançado

### ⚡ Download Adapters (Performance)

Global-Data-Finance oferece múltiplos adapters de download, cada um otimizado para diferentes cenários:

#### 1. **AsyncDownloadAdapterCVM** (Recomendado) ⭐

- **Velocidade**: 3-5x mais rápido que wget
- **Características**: Paralelo (8 workers), sem dependências externas
- **Melhor para**: Maioria dos casos, performance vs facilidade
- **Status**: Padrão em `FundamentalStocksDataCVM`

```python
from src.presentation.cvm_docs import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()  # Usa ThreadPool por padrão
result = cvm.download(
    destination_path="/data",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)
print(f"Downloaded {result.success_count_downloads} files")  # 3-5x mais rápido!
```

#### 2. **Aria2cAdapter** (Máxima Velocidade) 🚀

- **Velocidade**: 5-10x mais rápido que wget
- **Características**: Multipart por arquivo, retome automático
- **Requer**: `aria2c` instalado
- **Melhor para**: Grandes volumes, máxima performance

**Instalação de aria2c**:

```bash
# Linux
sudo apt-get install aria2

# macOS
brew install aria2

# Windows: https://github.com/aria2/aria2/releases
```

**Uso**:

```python
from src.brazil.cvm.fundamental_stocks_data.infra.adapters import Aria2cAdapter
from src.brazil.cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCaseCVM

adapter = Aria2cAdapter(max_concurrent_downloads=16)
use_case = DownloadDocumentsUseCaseCVM(adapter)
result = use_case.execute(
    destination_path="/data",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)
```

#### 3. **WgetDownloadAdapter** (Original)

- **Velocidade**: Baseline (1x)
- **Características**: Simples, single-threaded
- **Melhor para**: Compatibilidade máxima

### Comparação de Performance

| Adapter                     | Velocidade       | Dependências | Melhor Para        |
| --------------------------- | ---------------- | ------------ | ------------------ |
| **WgetDownloadAdapter**     | ⭐ 1x (baseline) | wget         | Compatibilidade    |
| **AsyncDownloadAdapterCVM** | ⭐⭐⭐ 3-5x      | requests     | **Recomendado** ✅ |
| **Aria2cAdapter**           | ⭐⭐⭐⭐⭐ 5-10x | aria2c       | Máxima velocidade  |

### Documentação Detalhada de Adapters

- 📖 [docs/ADAPTERS.md](./docs/ADAPTERS.md) - Referência rápida
- 📖 [docs/ARIA2_GUIDE.md](./docs/ARIA2_GUIDE.md) - Guia completo sobre aria2
- 📖 [docs/PERFORMANCE_GUIDE.md](./docs/PERFORMANCE_GUIDE.md) - Guia de performance
- 💻 [examples/adapter_examples.py](./examples/adapter_examples.py) - Exemplos de código

## Uso Avançado

### Validação de Inputs

```python
from src.brazil.cvm.fundamental_stocks_data.domain import (
    AvailableDocs,
    AvailableYears
)

# Validar documentos
docs = AvailableDocs()
try:
    docs.validate_docs_name("DFP")  # Válido
except InvalidDocName as e:
    print(f"Documento inválido: {e}")

# Validar intervalo de anos
years = AvailableYears()
year_range = years.return_range_years(2020, 2023)
print(list(year_range))  # [2020, 2021, 2022, 2023]
```

### Tratamento de Erros

````python
```python
from src.macro_exceptions import (
    NetworkError,
    TimeoutError,
    PermissionError,
    DiskFullError
)
from src.brazil.cvm.fundamental_stocks_data.exceptions import (
    WgetLibraryError,
    InvalidDocName,
    InvalidFirstYear
)

adapter = WgetDownloadAdapter()

try:
    result = adapter.download_docs(path, dict_zips)
except NetworkError as e:
    print(f"Erro de rede: {e}")
except TimeoutError as e:
    print(f"Timeout na conexão: {e}")
except PermissionError as e:
    print(f"Permissão negada: {e}")
except DiskFullError as e:
    print(f"Disco cheio: {e}")
````

````

### Logging

```python
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.info("Iniciando download de documentos")

# O adapter registrará automaticamente informações sobre o download
adapter = WgetDownloadAdapter()
result = adapter.download_docs(path, dict_zips)
````

## Arquitetura

### Padrões Utilizados

#### 1. **Repository Pattern**

```python
# Interface abstrata
class DownloadDocsCVMRepository(ABC):
    @abstractmethod
    def download_docs(...) -> DownloadResultCVM:
        pass

# Implementação
class WgetDownloadAdapter(DownloadDocsCVMRepository):
    def download_docs(...) -> DownloadResultCVM:
        # Implementação concreta
```

#### 2. **Value Objects**

```python
# DictZipsToDownload gera estrutura imutável de URLs
dict_generator = DictZipsToDownload()
dict_zips = dict_generator.get_dict_zips_to_download(...)
```

#### 3. **Result Pattern**

```python
# DownloadResultCVM encapsula sucesso e erros
result = adapter.download_docs(...)
if not result.has_errors:
    # Processar sucessos
else:
    # Tratar erros
```

### Fluxo de Dados

```
┌─────────────────┐
│  Cliente API    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Use Cases (Application)    │
│  - Orquestração             │
│  - Validação de inputs      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Repository Interface       │  ◄── Abstração
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Adapters (Infrastructure)  │
│  - WgetDownloadAdapter      │
│  - RequestsDownloadAdapter  │  (futuro)
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  External Services          │
│  - CVM Server               │
│  - HTTP/HTTPS               │
└─────────────────────────────┘
```

## Desenvolvimento

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=src

# Apenas testes rápidos
pytest -m unit

# Apenas um arquivo
pytest tests/brazil/cvm/fundamental_stocks_data/domain/test_available_docs.py

# Com output detalhado
pytest -v
```

### Estructura de Testes

```
tests/
├── brazil/
│   ├── cvm/
│   │   └── fundamental_stocks_data/
│   │       ├── domain/              # Testes de entidades
│   │       ├── application/         # Testes de casos de uso
│   │       ├── exceptions/          # Testes de exceções
│   │       └── infra/adapters/      # Testes de adapters
│   └── macro_exceptions/            # Testes de exceções globais
```

### Marcadores de Teste

- `@pytest.mark.unit` - Testes unitários (rápidos, isolados)
- `@pytest.mark.integration` - Testes de integração
- `@pytest.mark.slow` - Testes lentos
- `@pytest.mark.requires_network` - Requer conexão de rede

```bash
pytest -m "not requires_network"  # Pular testes que precisam de rede
```

### Adicionar Novas Features

1. **Criar exceção específica** (se necessário)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/exceptions/
   class MyCustomError(Exception):
       pass
   ```

2. **Implementar lógica no domain** (entidades puras)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/domain/
   class MyEntity:
       pass
   ```

3. **Criar interface** (se precisar de múltiplas implementações)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/application/interfaces/
   class MyInterface(ABC):
       @abstractmethod
       def my_method(self):
           pass
   ```

4. **Implementar adapter** (infraestrutura)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/infra/adapters/
   class MyAdapter(MyInterface):
       def my_method(self):
           pass
   ```

5. **Criar testes** (cobertura completa)
   ```python
   # tests/brazil/cvm/fundamental_stocks_data/.../
   class TestMyFeature:
       def test_something(self):
   ```

````

### Adicionar Novas Features

1. **Criar exceção específica** (se necessário)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/exceptions/
   class MyCustomError(Exception):
       pass
````

2. **Implementar lógica no domain** (entidades puras)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/domain/
   class MyEntity:
       pass
   ```

3. **Criar interface** (se precisar de múltiplas implementações)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/application/interfaces/
   class MyInterface(ABC):
       @abstractmethod
       def my_method(self):
           pass
   ```

4. **Implementar adapter** (infraestrutura)

   ```python
   # src/brazil/cvm/fundamental_stocks_data/infra/adapters/
   class MyAdapter(MyInterface):
       def my_method(self):
           pass
   ```

5. **Criar testes** (cobertura completa)
   ```python
   # tests/brazil/cvm/fundamental_stocks_data/.../
   class TestMyFeature:
       def test_something(self):
           pass
   ```

## Configuração de Desenvolvimento

### Pre-commit Hooks

```bash
# Instalar
pre-commit install

# Rodar manualmente
pre-commit run --all-files
```

### Type Checking com mypy

```bash
mypy src/
```

### Formatação com Black

```bash
black src/ tests/
```

### Linting com Pylint/Flake8

```bash
flake8 src/ tests/
```

## Roadmap

### Próximas Funcionalidades

- [ ] Suporte a async/await para downloads paralelos
- [ ] CLI com typer
- [ ] Cache local de arquivos baixados
- [ ] Extrator de dados dos ZIPs
- [ ] Suporte a dados dos EUA (SEC, FRED)
- [ ] Dashboard web com Dash/Streamlit
- [ ] Documentação com MkDocs
- [ ] Rate limiting para requisições

### Possíveis Adapters

- [ ] RequestsAdapter (requests library)
- [ ] AiohttpAdapter (async HTTP)
- [ ] CloudStorageAdapter (upload para S3/GCS)
- [ ] DatabaseAdapter (persistência direto em BD)

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes

- Manter 100% de cobertura de testes
- Seguir PEP 8 com Black formatter
- Adicionar docstrings completas
- Usar type hints em todo código novo
- Atualizar README com novas features

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## Autores

- **Jordan Estralioto** - Desenvolvedor Principal

## Suporte

Para reportar bugs ou sugerir features, abra uma issue no GitHub.

---

**Nota**: Esta biblioteca foi desenvolvida seguindo princípios de Clean Architecture e boas práticas de engenharia de software. Críticas e sugestões são sempre bem-vindas!
