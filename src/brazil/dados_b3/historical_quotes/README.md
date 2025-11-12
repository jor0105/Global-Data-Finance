# 📊 Historical Quotes Extraction Module (COTAHIST)

Sistema robusto e escalável para extração de dados históricos de cotações da B3 (Brasil, Bolsa, Balcão) a partir dos arquivos COTAHIST em formato ZIP.

**Status:** ✅ Production Ready | **Versão:** 1.1.0

## 📑 Índice

1. [Características](#-características)
2. [Instalação](#-instalação)
3. [Guia de Uso](#-guia-de-uso)
4. [Arquitetura](#-arquitetura-do-módulo)
5. [Classes de Ativos](#-classes-de-ativos-suportadas)
6. [Modos de Processamento](#-modos-de-processamento)
7. [Formato dos Dados](#-formato-dos-dados-cotahist)
8. [Exemplos Avançados](#-exemplos-avançados)
9. [Troubleshooting](#-troubleshooting)
10. [API Reference](#-api-reference)

---

## ✨ Características

- ⚡ **Arquitetura Limpa**: Separação clara entre Domain, Application e Infrastructure
- 🎯 **SOLID Principles**: Design robusto e maintível
- 🔄 **Processamento Assíncrono**: Paralelo com `asyncio` e controle de concorrência
- 🎮 **Controle de Recursos**: Modos `fast` e `slow` para otimizar CPU/RAM
- 🔒 **Type-Safe**: Type hints completos + protocolos para máxima segurança
- 💯 **Precisão Numérica**: Uso de `Decimal` para conversão correta de valores
- 📦 **Formato Parquet**: Saída otimizada com Polars + compressão Snappy
- ⚙️ **Streaming**: Leitura de ZIP sem extrair para disco
- 🛡️ **Tratamento de Erros**: Capturas de erros granulares com recovery

---

## 📦 Instalação

### Pré-requisitos

- Python 3.10+
- pip ou poetry

### Passos

```bash
# 1. Instalar dependências obrigatórias
pip install polars pyarrow

# 2. (Opcional) Verificar instalação
python -c "import polars as pl; print(f'Polars {pl.__version__}')"
```

### Estrutura Esperada

```
seu_projeto/
├── src/
│   ├── brazil/
│   │   └── dados_b3/
│   │       └── historical_quotes/  ← Este módulo
│   ├── macro_infra/
│   │   └── extractor_file.py       ← Dependência
│   └── macro_exceptions/
│       └── macro_exceptions.py     ← Dependência
├── pyproject.toml
└── README.md
```

---

## 🚀 Guia de Uso

### Uso Básico (3 linhas)

```python
from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)

# 1. Criar configuração validada
docs = CreateDocsToExtractUseCase(
    path_of_docs='/data/zips',          # Onde estão os ZIPs
    assets_list=['ações'],               # Quais ativos
    initial_year=2023,                   # De que ano
    last_year=2023                       # Até que ano
).execute()

# 2. Executar extração (síncrono)
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='fast',              # fast ou slow
    output_filename='cotahist.parquet'   # Nome do arquivo de saída
)

# 3. Usar resultado
print(f"✅ Extraídos {result['total_records']} registros")
print(f"📁 Salvo em: {result['output_file']}")
```

**Saída esperada:**

```
✅ Extraídos 1250 registros
📁 Salvo em: /data/zips/cotahist.parquet
```

---

### Uso com Múltiplos Ativos

```python
docs = CreateDocsToExtractUseCase(
    path_of_docs='/data/b3_zips',
    assets_list=['ações', 'etf', 'opções'],  # ← Múltiplos ativos
    initial_year=2020,
    last_year=2024,
    destination_path='/output',             # ← Saída em outro local
    output_filename='cotahist_full.parquet',
    processing_mode='slow'                  # ← Modo econômico
).execute()

result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='slow'
)
```

---

### Uso Assíncrono Avançado

```python
import asyncio

async def main():
    docs = CreateDocsToExtractUseCase(
        path_of_docs='/data/zips',
        assets_list=['ações'],
        initial_year=2023,
        last_year=2023
    ).execute()

    # Usar versão assíncrona (melhor performance)
    result = await ExtractHistoricalQuotesUseCase().execute(
        docs_to_extract=docs,
        processing_mode='fast'
    )

    return result

# Executar
result = asyncio.run(main())
```

---

### Usar com Teus Dados (Exemplo Real)

Suponha que tens arquivos em `/home/jordan/Programação/DataFinance/dados/b3`:

```python
from pathlib import Path
from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)

# Setup
data_path = Path.home() / "Programação/DataFinance/dados/b3"
output_path = Path.home() / "Programação/DataFinance/output"

# Criar configuração
docs = CreateDocsToExtractUseCase(
    path_of_docs=str(data_path),
    assets_list=['ações'],
    initial_year=2023,
    last_year=2024,
    destination_path=str(output_path)
).execute()

# Extrair
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='fast'
)

# Validar
if result['success']:
    print(f"✅ Sucesso!")
    print(f"   - Arquivos processados: {result['success_count']}/{result['total_files']}")
    print(f"   - Registros extraídos: {result['total_records']}")
    print(f"   - Localização: {result['output_file']}")
else:
    print(f"❌ Falha!")
    print(f"   - Erros: {result['errors']}")
```

---

## 🏗️ Arquitetura do Módulo

```
historical_quotes/
│
├── domain/                    ← Lógica de negócio (adora de dependências)
│   ├── entities/
│   │   └── docs_to_extractor.py      Entity com parâmetros validados
│   │
│   ├── value_objects/
│   │   ├── available_assests.py      Mapeia assets → TPMERC codes
│   │   ├── available_years.py        Valida e normaliza anos
│   │   ├── output_filename.py        Valida nome do arquivo
│   │   ├── processing_mode.py        Valida modo (fast/slow)
│   │   └── extract_result.py         Resultado de extração
│   │
│   └── exceptions/
│       └── exception_domain.py       Exceções de negócio
│
├── application/               ← Use cases (orquestra domain + infra)
│   └── use_cases/
│       ├── extract_historical_quotes_use_case.py     Main
│       ├── docs_to_extraction_use_case.py           Preparação
│       ├── set_assets_use_case.py                   Valida ativos
│       ├── range_years_use_case.py                  Valida anos
│       ├── set_docs_to_download_use_case.py         Encontra ZIPs
│       ├── validate_destination_path_use_case.py    Valida destino
│       └── get_available_*.py                       Queries
│
└── infra/                     ← Implementações (técnicas externas)
    ├── extraction_service.py           Orquestra extração assíncrona
    ├── extraction_service_factory.py   Factory pattern
    ├── zip_reader.py                   Lê ZIP em memória
    ├── cotahist_parser.py              Parse formato COTAHIST
    ├── parquet_writer.py               Escreve Parquet
    ├── file_system_service.py          Operações I/O
    └── __init__.py
```

**Fluxo de Dependências (DIP):**

```
Presentation → Application → Domain
                   ↓
            Infrastructure (injetado)
```

---

## 📊 Classes de Ativos Suportadas

| Classe             | TPMERC   | Descrição                                 | Exemplo        |
| ------------------ | -------- | ----------------------------------------- | -------------- |
| `ações`            | 010, 020 | Ações (lote padrão + fracionário)         | PETR4, VALE3   |
| `etf`              | 010, 020 | Fundos de Índice                          | IVVB11, EGIE11 |
| `opções`           | 070, 080 | Opções de compra (070) e venda (080)      | PETRM21C26     |
| `termo`            | 030      | Mercado a Termo                           | PETR4 (termo)  |
| `exercicio_opcoes` | 012, 013 | Exercício de opções (call 012, put 013)   | (interno)      |
| `forward`          | 050, 060 | Forward com ganho (050) e movimento (060) | (derivativo)   |
| `leilao`           | 017      | Leilão                                    | (especial)     |

**Verificar assets disponíveis:**

```python
from src.brazil.dados_b3.historical_quotes.domain import AvailableAssets

assets = AvailableAssets.get_available_assets()
print(assets)  # ['ações', 'etf', 'opções', 'termo', ...]
```

---

## ⚙️ Modos de Processamento

### 🚀 FAST Mode (Recomendado para Máquinas Potentes)

```python
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='fast'  # ← Default
)
```

**Características:**

- ✅ Até **10 arquivos** processados em paralelo
- ✅ Tempo: ~30 segundos para 10 ZIPs
- ⚠️ CPU: 80-100% utilização
- ⚠️ RAM: Até 2GB picos

**Ideal para:**

- Servidores dedicados
- Extração one-time
- Máquinas com 8+ cores

---

### 🐢 SLOW Mode (Recomendado para Máquinas Limitadas)

```python
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='slow'
)
```

**Características:**

- ✅ Até **2 arquivos** processados em paralelo
- ✅ Tempo: ~3 minutos para 10 ZIPs
- ✅ CPU: 10-20% utilização
- ✅ RAM: ~500MB estável

**Ideal para:**

- Máquinas com 2-4 cores
- Processamento em background
- Servidores compartilhados

---

## 📝 Formato dos Dados COTAHIST

### Estrutura do Arquivo

```
Arquivo ZIP
└── TXT_YYYYMM.txt (formato COTAHIST)
    ├── Linha 1:    [00] Header
    ├── Linha 2-N:  [01] Cotações (245 bytes cada)
    └── Linha N+1:  [99] Trailer
```

### Layout Fixo (245 bytes)

```
Posição   | Campos                | Descrição
----------|----------------------|--------------------
01-02     | TIPREG               | 00=Header, 01=Quote, 99=Trailer
03-10     | DATA_PREGAO          | YYYYMMDD (data da sessão)
11-12     | CODBDI               | Código BDI
13-24     | CODNEG (Ticker)      | Ex: PETR4, VALE3
25-27     | TPMERC (Filtro!)     | 010=Ação, 070=Call, etc
28-39     | NOMRES               | Nome resumido da empresa
40-49     | ESPECI               | Especificação do papel
...       | PREÇOS (abertura, máx, mín, fechamento)
...       | VOLUME               | Quantidade e valor
203-210   | DATVEN               | Data de vencimento (opções)
231-242   | CODISI               | Código ISIN
243-245   | DISMES               | Número de distribuição
```

### Campos Extraídos no Output

```python
{
    'data_pregao': date(2023, 1, 2),       # Data da negociação
    'codbdi': '01',
    'codneg': 'PETR4',                      # Ticker
    'tpmerc': '010',                        # Tipo de mercado
    'nomres': 'PETROBRAS ON',               # Nome resumido
    'especi': '',                           # Especificação
    'preabe': Decimal('27.53'),             # Preço abertura
    'premax': Decimal('27.85'),             # Preço máximo
    'premin': Decimal('27.30'),             # Preço mínimo
    'premed': Decimal('27.55'),             # Preço médio
    'preult': Decimal('27.76'),             # Preço fechamento
    'preofc': Decimal('27.76'),             # Melhor oferta compra
    'preofv': Decimal('27.77'),             # Melhor oferta venda
    'totneg': 45230,                        # Número de negócios
    'quatot': 123456789,                    # Quantidade total
    'voltot': Decimal('3415670123.45'),     # Volume financeiro
    'datven': None,                         # Data vencimento (opções)
    'fatcot': 1,                            # Fator de cotação
    'codisi': 'BRVALEACNOR9',               # Código ISIN
    'dismes': 0
}
```

**Notas importantes:**

- ✅ Preços usam `Decimal` para precisão
- ✅ Datas convertidas para `date` objects
- ✅ Volumes como `int` para integridade
- ✅ `None` para campos vazios/não aplicáveis

---

## 💾 Formato de Saída (Parquet)

```python
# Arquivo: cotahist.parquet

# Esquema:
# data_pregao:      date32
# codneg:           string (index)
# tpmerc:           string
# nomres:           string
# preabe:           decimal128(18,2)
# premax:           decimal128(18,2)
# premin:           decimal128(18,2)
# preult:           decimal128(18,2)
# totneg:           int32
# quatot:           int64
# voltot:           decimal128(18,2)
# ... (todos os campos)

# Compressão: Snappy (balanceado)
# Tamanho típico: 200KB para 1000 registros
```

**Ler resultado com Pandas:**

```python
import pandas as pd

df = pd.read_parquet('cotahist.parquet')
print(df.info())
print(df.head())

# Filtrar
ações_petr = df[df['codneg'] == 'PETR4']
print(ações_petr[['data_pregao', 'preult', 'voltot']])
```

---

## 🔍 Exemplos Avançados

### Exemplo 1: Extração com Validação

```python
from pathlib import Path
from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)

try:
    # 1. Validar entrada
    docs = CreateDocsToExtractUseCase(
        path_of_docs='/data/zips',
        assets_list=['ações'],
        initial_year=2023,
        last_year=2023,
        destination_path='/output'
    ).execute()

    print(f"✓ Configuração validada")
    print(f"  - Assets: {docs.set_assets}")
    print(f"  - Anos: {list(docs.range_years)}")
    print(f"  - Arquivos: {len(docs.set_documents_to_download)}")

    # 2. Extrair
    result = ExtractHistoricalQuotesUseCase().execute_sync(
        docs_to_extract=docs,
        processing_mode='fast'
    )

    # 3. Validar resultado
    if result['success']:
        print(f"\n✅ Extração concluída!")
        print(f"  - Registros: {result['total_records']}")
        print(f"  - Arquivo: {result['output_file']}")
    else:
        print(f"\n❌ Erros detectados:")
        for arquivo, erro in result['errors'].items():
            print(f"  - {arquivo}: {erro}")

except ValueError as e:
    print(f"❌ Erro de validação: {e}")
except FileNotFoundError as e:
    print(f"❌ Arquivo não encontrado: {e}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
```

---

### Exemplo 2: Processamento em Batch de Múltiplos Anos

```python
from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCase,
    ExtractHistoricalQuotesUseCase,
)

# Processar cada ano separadamente
for year in range(2020, 2024):
    print(f"\n📅 Processando {year}...")

    docs = CreateDocsToExtractUseCase(
        path_of_docs='/data/b3_zips',
        assets_list=['ações', 'etf'],
        initial_year=year,
        last_year=year,
        destination_path='/output',
        output_filename=f'cotahist_{year}.parquet'
    ).execute()

    result = ExtractHistoricalQuotesUseCase().execute_sync(
        docs_to_extract=docs,
        processing_mode='fast'
    )

    print(f"   ✓ {result['total_records']} registros")
```

---

### Exemplo 3: Verificar Assets Disponíveis

```python
from src.brazil.dados_b3.historical_quotes.domain import AvailableAssets

# 1. Ver todos os assets disponíveis
print("Assets disponíveis:")
for asset in AvailableAssets.get_available_assets():
    print(f"  - {asset}")

# 2. Ver mapping de TPMERC
codes = AvailableAssets.get_target_tmerc_codes({'ações', 'etf'})
print(f"\nCódigos TPMERC para 'ações' e 'etf': {codes}")
# Output: {'010', '020'}
```

---

## 🐛 Troubleshooting

### ❌ "No ZIP files found for the specified years"

**Causa:** Arquivos não encontrados no diretório

**Solução:**

```python
from pathlib import Path

# Verificar estrutura de diretórios
data_dir = Path('/data/b3_zips')
print("Arquivos no diretório:")
for f in data_dir.glob('*.zip'):
    print(f"  - {f.name}")

# Nota: Nomes esperados: cotahist_2023.zip, cotahist_202301.zip, etc
```

---

### ❌ "ImportError: polars is required"

**Causa:** Polars não instalado

**Solução:**

```bash
pip install polars pyarrow
```

---

### ❌ "DiskFullError: No space left on device"

**Causa:** Disco cheio

**Solução:**

```bash
# Verificar espaço
df -h /output

# Limpar arquivos temporários
rm -rf /tmp/cotahist_*
```

---

### ⚠️ "Slow processing on multi-core machine"

**Causa:** Usando `mode='slow'` em máquina potente

**Solução:**

```python
# Usar modo fast
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='fast'  # ← Mude para fast
)
```

---

### 📊 Memory issues com datasets grandes

**Causa:** Muitos arquivos em paralelo

**Solução:**

```python
# Processar em chunks
docs = CreateDocsToExtractUseCase(
    path_of_docs='/data',
    assets_list=['ações'],
    initial_year=2023,
    last_year=2023
).execute()

# Usar slow mode
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='slow'  # ← Economiza memória
)
```

---

## 📚 API Reference

### `CreateDocsToExtractUseCase`

```python
class CreateDocsToExtractUseCase:
    def __init__(
        self,
        path_of_docs: str,
        assets_list: List[str],
        initial_year: int,
        last_year: int,
        destination_path: Optional[str] = None,
        output_filename: str = "cotahist_extracted",
        processing_mode: str = "fast"
    )

    def execute(self) -> DocsToExtractor:
        """Valida todos os parâmetros e retorna Entity"""
```

**Parâmetros:**

- `path_of_docs` (str): Diretório com arquivos ZIP
- `assets_list` (List[str]): ['ações', 'etf', ...] - ver tabela de assets
- `initial_year` (int): Ano inicial (inclusive)
- `last_year` (int): Ano final (inclusive)
- `destination_path` (Optional[str]): Onde salvar (default: path_of_docs)
- `output_filename` (str): Nome do arquivo Parquet (default: "cotahist_extracted")
- `processing_mode` (str): "fast" ou "slow" (default: "fast")

**Retorna:**

- `DocsToExtractor`: Entity com parâmetros validados

**Levanta:**

- `ValueError`: Se parâmetros inválidos
- `FileNotFoundError`: Se path_of_docs não existe

---

### `ExtractHistoricalQuotesUseCase`

```python
class ExtractHistoricalQuotesUseCase:
    async def execute(
        self,
        docs_to_extract: DocsToExtractor,
        processing_mode: str = "fast",
        output_filename: str = "cotahist_extracted.parquet"
    ) -> Dict[str, Any]

    def execute_sync(
        self,
        docs_to_extract: DocsToExtractor,
        processing_mode: str = "fast",
        output_filename: str = "cotahist_extracted.parquet"
    ) -> Dict[str, Any]
```

**Retorna:**

```python
{
    'success': bool,                    # Sucesso geral
    'message': str,                     # Mensagem descritiva
    'total_files': int,                 # Total de ZIPs
    'success_count': int,               # ZIPs processados
    'error_count': int,                 # ZIPs com erro
    'total_records': int,               # Registros extraídos
    'errors': Dict[str, str],           # Erros por arquivo
    'output_file': str                  # Caminho do Parquet
}
```

---

### `AvailableAssets`

```python
class AvailableAssets:
    @classmethod
    def get_available_assets(cls) -> List[str]:
        """Retorna lista de assets suportados"""

    @classmethod
    def get_target_tmerc_codes(cls, set_assets: Set[str]) -> Set[str]:
        """Mapeia assets para códigos TPMERC"""
```

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest tests/brazil/dados_b3/historical_quotes/ -v

# Testes específicos
pytest tests/brazil/dados_b3/historical_quotes/test_extraction.py -v

# Com coverage
pytest tests/brazil/dados_b3/historical_quotes/ --cov
```

---

## 🔗 Documentação Adicional

- 📖 [Arquitetura Detalhada](../../docs/ARCHITECTURE_HISTORICAL_QUOTES.md)
- 📋 [Layout COTAHIST](../../docs/context/HistoricalQuoteB3.md)
- 🔗 [B3 - Histórico de Cotações](http://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)

---

## 📄 License & Contribuição

Este módulo faz parte do projeto **DataFinance**.

Para contribuir:

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/sua-feature`
3. Commit: `git commit -m 'Add: descrição'`
4. Push: `git push origin feature/sua-feature`
5. Abra um Pull Request

---

## 💡 Tips & Tricks

### ✅ Melhor Performance

```python
# Use modo 'fast' em máquinas potentes
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='fast'
)
```

### ✅ Economizar Memória

```python
# Use modo 'slow' em máquinas limitadas
result = ExtractHistoricalQuotesUseCase().execute_sync(
    docs_to_extract=docs,
    processing_mode='slow'
)
```

### ✅ Processar Grandes Volumes

```python
# Processe por ano para evitar picos de memória
for year in range(2020, 2024):
    docs = CreateDocsToExtractUseCase(
        ..., initial_year=year, last_year=year
    ).execute()
    result = ExtractHistoricalQuotesUseCase().execute_sync(...)
```

---

**Última atualização:** Novembro 2025
**Versão:** 1.1.0
**Status:** ✅ Produção
