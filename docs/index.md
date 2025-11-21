# DataFinance

**Biblioteca Python profissional para extração e processamento de dados financeiros globais**

[![PyPI version](https://img.shields.io/pypi/v/datafinance.svg)](https://pypi.org/project/datafinance/)
[![Python](https://img.shields.io/pypi/pyversions/datafinance.svg)](https://pypi.org/project/datafinance/)
[![License](https://img.shields.io/github/license/jor0105/Global-Data-Finance.svg)](https://github.com/jor0105/Global-Data-Finance/blob/main/LICENSE)

---

## Visão Geral

**DataFinance** é uma biblioteca Python moderna e de alto desempenho projetada para facilitar a extração, normalização e processamento de dados financeiros e econômicos do mercado brasileiro. Com foco em simplicidade de uso e performance, a biblioteca oferece interfaces intuitivas para acessar dados fundamentalistas da CVM e cotações históricas da B3.

### Características Principais

✨ **Interface Simples e Intuitiva** - API de alto nível fácil de usar, ideal para análise de dados e pesquisa  
⚡ **Alto Desempenho** - Processamento otimizado com suporte a múltiplos workers e modos de performance  
📊 **Formato Parquet** - Exportação direta para formato Parquet otimizado para análise  
🏗️ **Arquitetura Limpa** - Código bem estruturado seguindo princípios SOLID e Clean Architecture  
🔒 **Type Hints Completos** - Código totalmente tipado para melhor segurança e autocompletar  
📝 **Logging Integrado** - Rastreamento detalhado de operações para debugging e monitoramento  
🧪 **Testado Extensivamente** - Suite completa de testes unitários e de integração

---

## Funcionalidades

### 📄 Documentos Fundamentalistas CVM

Baixe documentos oficiais da Comissão de Valores Mobiliários (CVM) com facilidade:

- **DFP** - Demonstrações Financeiras Padronizadas
- **ITR** - Informações Trimestrais
- **FRE** - Formulário de Referência
- **FCA** - Formulário Cadastral
- E muito mais...

```python
from datafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR"],
    initial_year=2020,
    last_year=2023,
    automatic_extractor=True  # Extrai automaticamente para Parquet
)
```

[Saiba mais sobre Documentos CVM →](user-guide/cvm-docs.md)

### 📈 Cotações Históricas B3

Extraia e processe cotações históricas da B3 (COTAHIST) de forma eficiente:

- Ações (mercado à vista e fracionário)
- ETFs (Exchange Traded Funds)
- Opções (calls e puts)
- Mercado a termo, forward, leilão e mais

```python
from datafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf"],
    initial_year=2020,
    last_year=2023,
    processing_mode="fast"  # Modo de alto desempenho
)
```

[Saiba mais sobre Cotações B3 →](user-guide/b3-docs.md)

---

## Início Rápido

### Instalação

```bash
pip install datafinance
```

### Primeiro Exemplo

```python
from datafinance import FundamentalStocksDataCVM, HistoricalQuotesB3

# Download de documentos CVM
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2022
)

# Extração de cotações B3
b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2022
)

print(f"✓ Extraídos {result['total_records']:,} registros")
```

[Ver guia completo de início rápido →](user-guide/quickstart.md)

---

## Documentação

### Para Usuários

- **[Instalação](user-guide/installation.md)** - Como instalar e configurar a biblioteca
- **[Início Rápido](user-guide/quickstart.md)** - Primeiros passos e exemplos básicos
- **[Documentos CVM](user-guide/cvm-docs.md)** - Guia completo de uso da API CVM
- **[Cotações B3](user-guide/b3-docs.md)** - Guia completo de uso da API B3
- **[Exemplos Práticos](user-guide/examples.md)** - Casos de uso reais e avançados
- **[FAQ](user-guide/faq.md)** - Perguntas frequentes

### Para Desenvolvedores

- **[Arquitetura](dev-guide/architecture.md)** - Estrutura e padrões do projeto
- **[Referência da API](dev-guide/api-reference.md)** - Documentação completa da API
- **[Como Contribuir](dev-guide/contributing.md)** - Guia para contribuidores
- **[Testes](dev-guide/testing.md)** - Como executar e escrever testes
- **[Uso Avançado](dev-guide/advanced-usage.md)** - Customização e extensibilidade

### Referência Técnica

- **[API CVM](reference/cvm-api.md)** - Referência detalhada da API CVM
- **[API B3](reference/b3-api.md)** - Referência detalhada da API B3
- **[Exceções](reference/exceptions.md)** - Catálogo completo de exceções
- **[Formatos de Dados](reference/data-formats.md)** - Estruturas e schemas

---

## Por Que DataFinance?

### 🎯 Simplicidade

Interface de alto nível que abstrai a complexidade do download e processamento de dados financeiros. Você foca na análise, nós cuidamos da infraestrutura.

### ⚡ Performance

Processamento otimizado com suporte a múltiplos workers, modos de performance configuráveis e exportação eficiente para formato Parquet.

### 🏗️ Qualidade

Código profissional seguindo Clean Architecture, 100% tipado, extensivamente testado e com documentação completa.

### 🔧 Extensível

Arquitetura modular baseada em adapters permite fácil customização e adição de novas fontes de dados.

---

## Requisitos

- Python 3.12 ou superior
- Dependências principais:
  - `httpx` - Cliente HTTP assíncrono
  - `pandas` - Manipulação de dados
  - `polars` - Processamento de alto desempenho
  - `pyarrow` - Suporte a formato Parquet
  - `pydantic-settings` - Configuração e validação

---

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](https://github.com/jor0105/Global-Data-Finance/blob/main/LICENSE) para detalhes.

---

## Suporte e Contribuição

- 🐛 **Reportar bugs**: [GitHub Issues](https://github.com/jor0105/Global-Data-Finance/issues)
- 💡 **Sugerir features**: [GitHub Issues](https://github.com/jor0105/Global-Data-Finance/issues)
- 🤝 **Contribuir**: Veja nosso [guia de contribuição](dev-guide/contributing.md)
- 📧 **Contato**: estraliotojordan@gmail.com

---

## Autor

**Jordan Estralioto** - Desenvolvedor Principal

---

!!! tip "Próximos Passos" - 📚 Comece pelo [Guia de Instalação](user-guide/installation.md) - 🚀 Veja o [Início Rápido](user-guide/quickstart.md) - 💻 Explore os [Exemplos Práticos](user-guide/examples.md)
