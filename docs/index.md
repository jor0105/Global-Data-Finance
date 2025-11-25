# Global-Data-Finance

<div align="center">

**Biblioteca Python profissional para extração e processamento de dados financeiros globais com arquitetura limpa e alto desempenho.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/globaldatafinance.svg)](https://pypi.org/project/globaldatafinance/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/jor0105/Global-Data-Finance/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Começar Agora](user-guide/quickstart.md){ .md-button .md-button--primary } [Ver no GitHub](https://github.com/jor0105/Global-Data-Finance){ .md-button }

</div>

---

## 🚀 Visão Geral

**Global-Data-Finance** é uma solução robusta de engenharia de dados financeiros, projetada para simplificar drasticamente o acesso a dados regulatórios (CVM) e de mercado (B3).

Diferente de scripts frágeis ou soluções ad-hoc, esta biblioteca foi construída com **Clean Architecture** e princípios de engenharia de software sólida, oferecendo:

<div class="grid cards" markdown>

- ## :material-flash: **Alta Performance**

  Downloads paralelos e processamento otimizado (até 10x mais rápido).

- ## :material-database: **Dados Prontos**

  Extração nativa para **Parquet**, ideal para análise com Pandas/Polars.

- ## :material-shield-check: **Confiabilidade**

  Sistema de retries inteligente, validação de dados e tratamento de erros robusto.

- ## :material-code-json: **Developer Experience**
  API intuitiva, totalmente tipada (Type Hints) e com logging detalhado.

</div>

---

## 🎯 O Que Você Pode Fazer?

### 1. Documentos CVM (Regulatórios)

Baixe e processe documentos oficiais de companhias listadas na bolsa brasileira.

- **DFP** (Demonstrações Financeiras Padronizadas)
- **ITR** (Informações Trimestrais)
- **FRE** (Formulário de Referência)
- **FCA** (Formulário Cadastral)
- E muito mais...

[Explorar Documentos CVM](user-guide/cvm-docs.md){ .md-button }

### 2. Cotações Históricas B3 (Mercado)

Processe a série histórica completa da B3 (COTAHIST) com eficiência.

- **Ações** (Mercado à vista e fracionário)
- **ETFs** (Exchange Traded Funds)
- **Opções** (Calls e Puts)
- **Futuros e Termo**

[Explorar Cotações B3](user-guide/b3-docs.md){ .md-button }

---

## ⚡ Exemplo Rápido

```python
from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3

# 1. Baixar demonstrações financeiras (CVM)
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="./dados_cvm",
    list_docs=["DFP", "ITR"],
    initial_year=2023,
    automatic_extractor=True # Converte para Parquet
)

# 2. Extrair cotações de ações (B3)
b3 = HistoricalQuotesB3()
b3.extract(
    path_of_docs="./dados_brutos_b3",
    destination_path="./dados_processados",
    assets_list=["ações"],
    initial_year=2023,
    processing_mode="fast"
)
```

---

## 📚 Navegação da Documentação

### Para Usuários

- **[Instalação](user-guide/installation.md)**: Guia passo a passo de configuração.
- **[Início Rápido](user-guide/quickstart.md)**: Tutorial "Hello World" e primeiros passos.
- **[Exemplos Práticos](user-guide/examples.md)**: Casos de uso reais e receitas de código.
- **[FAQ](user-guide/faq.md)**: Perguntas frequentes e resolução de problemas.

### Para Desenvolvedores

- **[Arquitetura](dev-guide/architecture.md)**: Entenda o design interno (Clean Architecture).
- **[Referência da API](dev-guide/api-reference.md)**: Documentação técnica detalhada de classes e métodos.
- **[Contribuindo](dev-guide/contributing.md)**: Como ajudar a evoluir o projeto.

---

## 📄 Licença

Este projeto é open-source e distribuído sob a licença **Apache 2.0**.
Consulte o arquivo [LICENSE](https://github.com/jor0105/Global-Data-Finance/blob/main/LICENSE) para mais detalhes.

<div align="center">
    <sub>Copyright © 2025 Jordan Estralioto</sub>
</div>
