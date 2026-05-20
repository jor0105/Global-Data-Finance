# 📊 Global-Data-Finance

> Biblioteca Python para extração e processamento de dados financeiros globais com layout plano por fonte, alta performance e ferramentas extensíveis.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/globaldatafinance.svg)](https://pypi.org/project/globaldatafinance/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/jor0105/Global-Data-Finance/blob/develop/LICENSE)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)

---

## 🎯 O que este sistema oferece?

**Global-Data-Finance** é uma biblioteca Python que permite extrair e processar dados financeiros de forma profissional e escalável:

✅ **Múltiplas fontes de dados**: CVM (regulatório) e B3 (mercado) com layout idêntico por fonte
✅ **Processamento otimizado**: Downloads assíncronos (`httpx[http2]`) com concorrência adaptativa por CPU/RAM
✅ **Formato eficiente**: Extração nativa para Parquet (Pandas/Polars ready)
✅ **Robustez integrada**: Retries com back-off, validação de integridade e rollback atômico
✅ **Layout plano por fonte**: módulos nomeados por papel (CVM: `core.py`, `client.py`, `http.py`, `extract.py`, `errors.py`; B3: `client.py`, `models.py`, `years.py`, `processing.py`, `assets.py`, `filesystem.py`, `errors.py`, mais subpacotes pesados) — sem ABCs sem polimorfismo real

---

## 🚀 Quick Start

### Instalação

```bash
# Como dependência via PyPI
pip install globaldatafinance

# Para desenvolvimento local (uv é o gestor canônico do projeto)
git clone https://github.com/jor0105/Global-Data-Finance.git
cd Global-Data-Finance
uv sync
```

### Configuração

```bash
# Requer Python 3.12+
python --version

# Opcional: configurar logging para ver progresso detalhado
export LOG_LEVEL=INFO
```

### Primeiro Download em 3 Linhas

```python
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="./dados_cvm",
    list_docs=["DFP"],
    initial_year=2023,
    automatic_extractor=True
)
```

---

## ✨ Funcionalidades Principais

### 📈 Múltiplas Fontes de Dados

```python
# CVM - Documentos Regulatórios (DFP, ITR, FRE, FCA, etc.)
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="./dados_cvm",
    list_docs=["DFP", "ITR"],
    initial_year=2023,
    last_year=2024,
    automatic_extractor=True
)

# B3 - Cotações Históricas (Ações, ETFs, Opções, Futuros)
from globaldatafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="./dados_brutos_b3",
    destination_path="./dados_processados",
    assets_list=["ações", "etf"],
    initial_year=2023,
    processing_mode="fast"
)
```

### 🔧 Processamento Inteligente

A biblioteca oferece diferentes modos de processamento para otimizar performance:

```python
# Modo FAST - Processamento em memória (mais rápido)
b3.extract(
    path_of_docs="./dados",
    assets_list=["ações"],
    processing_mode="fast"  # Recomendado para datasets pequenos/médios
)

# Modo SLOW - Processamento incremental (menor uso de memória)
b3.extract(
    path_of_docs="./dados",
    assets_list=["ações"],
    processing_mode="slow"  # Recomendado para datasets grandes
)
```

**Tipos de Ativos Suportados (B3):**

- `ações` - Mercado à vista e fracionário
- `etf` - Exchange Traded Funds
- `opções` - Calls e Puts
- `termo` - Mercado a termo
- `futuro` - Contratos futuros

**Verificar ativos disponíveis:**

```python
b3 = HistoricalQuotesB3()
available_assets = b3.get_available_assets()
print(f"Ativos suportados: {available_assets}")
```

### 📊 Documentos CVM Disponíveis

```python
cvm = FundamentalStocksDataCVM()

# Ver documentos disponíveis
docs = cvm.get_available_docs()
for doc_type, description in docs.items():
    print(f"{doc_type}: {description}")

# Ver anos disponíveis
years = cvm.get_available_years()
print(f"Anos disponíveis: {years['initial_year']} - {years['last_year']}")
```

**Documentos Suportados:**

- `DFP` - Demonstrações Financeiras Padronizadas (anual)
- `ITR` - Informações Trimestrais
- `FRE` - Formulário de Referência
- `FCA` - Formulário Cadastral
- `CGVN` - Comunicado de Governança
- `VLMO` - Valor Mobiliário
- `IPE` - Informações Periódicas e Eventuais

### 💾 Análise de Dados

```python
import pandas as pd

# Ler dados processados (formato Parquet)
df_cotacoes = pd.read_parquet("./dados_processados/cotahist_extracted.parquet")

# Análise básica
print(df_cotacoes.head())
print(df_cotacoes.info())

# Análise de preços médios por ativo
precos_medios = df_cotacoes.groupby("cod_negociacao")["preco_fechamento"].mean()
print(precos_medios.sort_values(ascending=False).head(10))
```

### ⚙️ Configurações Avançadas

```python
import logging

# Configurar nível de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Download com configurações customizadas
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="./dados_cvm",
    list_docs=["DFP", "ITR", "FRE"],
    initial_year=2020,
    last_year=2024,
    automatic_extractor=True  # Converte ZIP para Parquet automaticamente
)
```

---

## 📚 Documentação

### Para Usuários

- **[Instalação](user-guide/installation.md)** - Configure seu ambiente passo a passo
- **[Início Rápido](user-guide/quickstart.md)** - Aprenda os fundamentos
- **[Documentos CVM](user-guide/cvm-docs.md)** - Guia completo de dados regulatórios
- **[Cotações B3](user-guide/b3-docs.md)** - Guia completo de dados de mercado
- **[Exemplos Práticos](user-guide/examples.md)** - Casos de uso reais
- **[FAQ](user-guide/faq.md)** - Perguntas frequentes

### Para Desenvolvedores

- **[Arquitetura](dev-guide/architecture.md)** - Layout plano por fonte e padrões de design
- **[Referência da API](dev-guide/api-reference.md)** - Documentação completa da API
- **[Como Contribuir](dev-guide/contributing.md)** - Guia de contribuição
- **[Testes](dev-guide/testing.md)** - Estratégias de teste e cobertura
- **[Uso Avançado](dev-guide/advanced-usage.md)** - Técnicas avançadas e otimizações

### Referência Técnica

- **[API CVM](reference/cvm-api.md)** - Referência completa da API CVM
- **[API B3](reference/b3-api.md)** - Referência completa da API B3
- **[Exceções](reference/exceptions.md)** - Tratamento de erros e exceções

---

## 🏗️ Por Que Usar Esta Biblioteca?

### Para Empresas

- ✅ **Performance**: Downloads paralelos assíncronos até 10x mais rápidos
- ✅ **Confiabilidade**: Sistema de retries com backoff exponencial
- ✅ **Monitoramento**: Logging detalhado e rastreamento de recursos
- ✅ **Escalabilidade**: Arquitetura preparada para grandes volumes de dados

### Para Desenvolvedores

- ✅ **Layout plano por fonte**: módulos nomeados por papel (CVM: ~7 arquivos; B3: ~10 arquivos + subpacotes pesados) — código fácil de ler e estender
- ✅ **Extensível**: Adicionar uma nova fonte = criar uma pasta-irmã com o mesmo padrão de papéis (granularidade ajustável por tamanho)
- ✅ **Type hints**: Suporte completo para IDEs e type checkers (mypy, pyright)
- ✅ **CI/CD**: Quality checks automáticos com GitHub Actions (`ruff`, `mypy`, `bandit`, `pytest --cov`)

### Para Analistas e Cientistas de Dados

- ✅ **Formato Parquet**: Dados otimizados para análise com Pandas/Polars
- ✅ **API Intuitiva**: Interface simples e direta ao ponto
- ✅ **Dados Limpos**: Processamento e validação automática
- ✅ **Documentação Completa**: Exemplos práticos e casos de uso reais

---

## 📊 Arquitetura

Duas camadas explícitas:

```
┌─────────────────────────────────────────────────────┐
│  FACADE (application/)                              │  ← FundamentalStocksDataCVM
│  Superfície semver-relevante para usuários da lib   │    HistoricalQuotesB3
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  IMPLEMENTAÇÃO POR FONTE                            │  ← brazil/<país>/<fonte>/
│  Módulos por papel: client.py + dados puros +       │    CVM: core.py · client.py · http.py
│  adapters HTTP/extract + errors.py + subpacotes     │         extract.py · errors.py
│  pesados isolados (parsers, writers).               │    B3: client.py · models.py · years.py
│                                                     │        assets.py · filesystem.py · …
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  CROSS-CUTTING                                      │  ← core/ (logging, retry,
│  Utilitários compartilhados, sem lógica de fonte    │    resource_monitor, config)
│                                                     │    macro_infra/, macro_exceptions/
└─────────────────────────────────────────────────────┘
```

**Benefícios:**

- **Leitura direta**: Poucos arquivos por fonte, nomes claros — sem caçar a classe em 4 camadas.
- **Sem ABC de implementação única**: Adapters concretos importados e construídos direto. Quando aparecer uma segunda implementação real, extrair um `typing.Protocol` é trivial.
- **Extensibilidade orientada a fontes**: Adicionar uma fonte = adicionar uma pasta com o mesmo conjunto plano. O ponto de extensão real é a fonte, não o "tipo de objeto".
- **Defesa de path-traversal como contrato**: `VerifyPathsUseCasesCVM` e `validate_directory_path` (B3) levantam `SecurityError` antes de qualquer `mkdir`.

[Saiba mais sobre a arquitetura →](dev-guide/architecture.md)

---

## 🚀 Casos de Uso

### 1. Análise Fundamentalista

```python
from globaldatafinance import FundamentalStocksDataCVM
import pandas as pd

# Baixar demonstrações financeiras
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="./dados_fundamentalistas",
    list_docs=["DFP", "ITR"],
    initial_year=2020,
    automatic_extractor=True
)

# Analisar balanços patrimoniais
df_balanco = pd.read_parquet("./dados_fundamentalistas/DFP_2023.parquet")
print(df_balanco[df_balanco['conta'].str.contains('Ativo Total')])
```

### 2. Backtesting de Estratégias

```python
from globaldatafinance import HistoricalQuotesB3
import pandas as pd

# Extrair cotações históricas
b3 = HistoricalQuotesB3()
b3.extract(
    path_of_docs="./dados_brutos",
    destination_path="./cotacoes",
    assets_list=["ações"],
    initial_year=2020,
    processing_mode="fast"
)

# Carregar e analisar
df = pd.read_parquet("./cotacoes/cotahist_extracted.parquet")
df['data_pregao'] = pd.to_datetime(df['data_pregao'])

# Calcular retornos
df['retorno_diario'] = df.groupby('cod_negociacao')['preco_fechamento'].pct_change()
```

### 3. Pipeline de Dados Automatizado

```python
from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3
import logging

logging.basicConfig(level=logging.INFO)

def pipeline_dados_financeiros():
    """Pipeline completo de extração de dados financeiros"""

    # 1. Dados fundamentalistas (CVM)
    print("Baixando dados CVM...")
    cvm = FundamentalStocksDataCVM()
    cvm.download(
        destination_path="./data/cvm",
        list_docs=["DFP", "ITR"],
        initial_year=2023,
        automatic_extractor=True
    )

    # 2. Cotações históricas (B3)
    print("Processando cotações B3...")
    b3 = HistoricalQuotesB3()
    result = b3.extract(
        path_of_docs="./data/raw/b3",
        destination_path="./data/processed/b3",
        assets_list=["ações", "etf"],
        initial_year=2023,
        processing_mode="fast"
    )

    print(f"Pipeline concluído! Total de registros: {result['total_records']:,}")

if __name__ == "__main__":
    pipeline_dados_financeiros()
```

---

## 🤝 Contribuindo

Quer adicionar uma nova fonte de dados ou melhorar a performance?

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-feature`
3. Implemente seguindo os padrões existentes
4. Execute os testes: `uv run pytest --cov=src`
5. Execute os linters: `uv run pre-commit run --all-files`
6. Envie um Pull Request

[Guia completo de contribuição →](dev-guide/contributing.md)

---

## 📞 Suporte

- 📧 **Email**: estraliotojordan@gmail.com
- 🐛 **Bugs**: [GitHub Issues](https://github.com/jor0105/Global-Data-Finance/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/jor0105/Global-Data-Finance/discussions)
- 📖 **Documentação**: [https://jor0105.github.io/Global-Data-Finance/](https://jor0105.github.io/Global-Data-Finance/)

---

## 📄 Licença

Apache 2.0 - Use livremente em seus projetos comerciais e pessoais.

Consulte o arquivo [LICENSE](https://github.com/jor0105/Global-Data-Finance/blob/develop/LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jor0105](https://github.com/jor0105)
- Email: estraliotojordan@gmail.com
- PyPI: [globaldatafinance](https://pypi.org/project/globaldatafinance/)

---

**Versão:** 0.1.2
**Última atualização:** 26/11/2025
**Status:** 🚀 Projeto em produção! Aberto para contribuições e sugestões.

<div align="center">
    <sub>Copyright © 2025 Jordan Estralioto • Licensed under Apache 2.0</sub>
</div>
