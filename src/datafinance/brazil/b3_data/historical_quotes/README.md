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
- 📦 **Formato Parquet**: Saída otimizada com Polars + compressão ZSTD
- ⚙️ **Streaming**: Leitura de ZIP sem extrair para disco
- 🛡️ **Tratamento de Erros**: Capturas de erros granulares com recovery

---

## 📦 Instalação

### Pré-requisitos

- Python 3.12+
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

### Quickstart (alto nível recomendado)

A forma mais simples é usar a interface de alto nível em `presentation/b3_docs`:

```python
from src.presentation import HistoricalQuotes

# 1) Criar cliente
b3 = HistoricalQuotes()

# 2) Extrair
result = b3.extract(
    path_of_docs='/data/zips',           # Onde estão os .zip do COTAHIST
    assets_list=['ações'],               # Quais classes de ativos juntar no documento
    initial_year=2023,                   # Ano inicial (inclusive)
    last_year=2023,                      # Ano final (inclusive)
    destination_path='/data/output',     # Onde salvar o .parquet (opcional)
    output_filename='cotahist',          # Sem extensão; .parquet é adicionado
    processing_mode='fast'               # 'fast' (padrão) ou 'slow'
)

print(result['message'])
print('Arquivo:', result['output_file'])
```

Também é possível usar os casos de uso diretamente (baixo nível):

### Usar com Teus Dados (Exemplo Real)

Suponha que tens arquivos em `/home/jordan/Programação/DataFinance/dados/b3`:

```python
from pathlib import Path
from src.presentation.b3_docs import HistoricalQuotes

# Setup
data_path = Path.home() / "Programação/DataFinance/dados/b3"
output_path = Path.home() / "Programação/DataFinance/output"

# Extrair (alto nível)
result = HistoricalQuotes().extract(
    path_of_docs=str(data_path),
    assets_list=['ações'],
    initial_year=2023,
    last_year=2024,
    destination_path=str(output_path),
    output_filename='cotahist'
    processing_mode='fast',
)

# Validar
if result['success']:
    print("✅ Sucesso!")
    print(f"   - Arquivos processados: {result['success_count']}/{result['total_files']}")
    print(f"   - Registros extraídos: {result['total_records']}")
    print(f"   - Localização: {result['output_file']}")
else:
    print("❌ Concluído com erros")
    print(f"   - Erros: {result['errors']}")
```

---

## 🏗️ Arquitetura do Módulo

```
historical_quotes/
│
├── domain/                    ← Lógica de negócio (pura)
│   ├── entities/
│   │   └── docs_to_extractor.py            Entity com parâmetros validados
│   ├── builders/
│   │   └── docs_to_extractor_builder.py    Builder da entity
│   ├── services/
│   │   ├── available_assets_service.py     Mapeia assets → TPMERC codes
│   │   └── year_validation_service.py      Regras/validação de anos
│   ├── value_objects/
│   │   ├── processing_mode.py              Enum: fast/slow
│   │   └── year_range.py                   Faixa de anos validada
│   └── exceptions/                         Exceções de domínio
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
| `opções`           | 070, 080 | Opções de compra (070) e venda (080)      | PETRM21        |
| `termo`            | 030      | Mercado a Termo                           | PETR4 (termo)  |
| `exercicio_opcoes` | 012, 013 | Exercício de opções (call 012, put 013)   | (interno)      |
| `forward`          | 050, 060 | Forward com ganho (050) e movimento (060) | (derivativo)   |
| `leilao`           | 017      | Leilão                                    | (especial)     |

**Verificar assets disponíveis:**

```python
from src.brazil.dados_b3.historical_quotes import GetAvailableAssetsUseCaseB3

assets = GetAvailableAssetsUseCaseB3.execute()
print(assets)  # ['ações', 'etf', 'opções', 'termo', ...]
```

---

## ⚙️ Modos de Processamento

### 🚀 FAST Mode (Recomendado para Máquinas Potentes)

```python
result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
    docs_to_extract=docs,
    processing_mode='fast'  # ← Default
)
```

**Características (fast):**

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
result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
    docs_to_extract=docs,
    processing_mode='slow'
)
```

**Características (slow):**

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

### Campos extraídos no output (chaves reais)

```python
{
    'data_pregao': date(2023, 1, 2),        # Data da negociação
    'codigo_bdi': '01',
    'ticker': 'PETR4',                       # Código de negociação
    'tipo_mercado': '010',                   # TPMERC
    'nome_resumido': 'PETROBRAS ON',
    'especificacao_papel': '',
    'preco_abertura': Decimal('27.53'),
    'preco_maximo': Decimal('27.85'),
    'preco_minimo': Decimal('27.30'),
    'preco_medio': Decimal('27.55'),
    'preco_fechamento': Decimal('27.76'),
    'melhor_oferta_compra': Decimal('27.76'),
    'melhor_oferta_venda': Decimal('27.77'),
    'numero_negocios': 45230,
    'quantidade_total': 123456789,
    'volume_total': Decimal('3415670123.45'),
    'data_vencimento': None,
    'fator_cotacao': 1,
    'codigo_isin': 'BRVALEACNOR9',
    'numero_distribuicao': 0
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

# Compressão: ZSTD (equilíbrio tamanho/velocidade)
# Tamanho típico: 200KB para 1000 registros
```

**Ler resultado com Pandas:**

```python
import pandas as pd

df = pd.read_parquet('cotahist.parquet')
print(df.info())
print(df.head())

# Filtrar
acoes_petr = df[df['ticker'] == 'PETR4']
print(acoes_petr[['data_pregao', 'preco_fechamento', 'volume_total']])
```

---

## 🔍 Exemplos Avançados

### Exemplo 1: Extração com Validação (baixo nível)

```python
from pathlib import Path
from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCaseB3,
    ExtractHistoricalQuotesUseCaseB3,
)

try:
    # 1. Validar entrada
    docs = CreateDocsToExtractUseCaseB3(
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
    result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
        docs_to_extract=docs,
        processing_mode='fast',
        output_filename='cotahist.parquet'
    )

    # 3. Validar resultado (use error_count para checar sucesso)
    if result['error_count'] == 0:
        print("\n✅ Extração concluída!")
        print(f"  - Registros: {result['total_records']}")
        print(f"  - Arquivo: {result['output_file']}")
    else:
        print("\n❌ Erros detectados:")
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

### Exemplo 2: Processamento em Batch de Múltiplos Anos (baixo nível)

```python
from src.brazil.dados_b3.historical_quotes.application import (
    CreateDocsToExtractUseCaseB3,
    ExtractHistoricalQuotesUseCaseB3,
)

# Processar cada ano separadamente
for year in range(2020, 2024):
    print(f"\n📅 Processando {year}...")

    docs = CreateDocsToExtractUseCaseB3(
        path_of_docs='/data/b3_zips',
        assets_list=['ações', 'etf'],
        initial_year=year,
        last_year=year,
        destination_path='/output'
    ).execute()

    result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
        docs_to_extract=docs,
        processing_mode='fast',
        output_filename=f'cotahist_{year}.parquet'
    )

    print(f"   ✓ {result['total_records']} registros")
```

---

### Exemplo 3: Verificar Assets Disponíveis

```python
from src.brazil.dados_b3.historical_quotes import GetAvailableAssetsUseCaseB3
from src.brazil.dados_b3.historical_quotes.domain import AvailableAssetsServiceB3

# 1. Ver todos os assets disponíveis (use case)
print("Assets disponíveis:")
for asset in GetAvailableAssetsUseCaseB3.execute():
    print(f"  - {asset}")

# 2. Ver mapping de TPMERC (serviço de domínio)
codes = AvailableAssetsServiceB3.get_tpmerc_codes_for_assets({'ações', 'etf'})
print(f"\nCódigos TPMERC para 'ações' e 'etf': {codes}")
assert codes == {'010', '020'}
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
result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
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
docs = CreateDocsToExtractUseCaseB3(
    path_of_docs='/data',
    assets_list=['ações'],
    initial_year=2023,
    last_year=2023
).execute()

# Usar slow mode
result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
    docs_to_extract=docs,
    processing_mode='slow'  # ← Economiza memória
)
```

---

## 📚 API Reference

### `CreateDocsToExtractUseCaseB3`

```python
class CreateDocsToExtractUseCaseB3:
    def __init__(
        self,
        path_of_docs: str,
        assets_list: List[str],
        initial_year: int,
        last_year: int,
        destination_path: Optional[str] = None,
    )

    def execute(self) -> DocsToExtractorB3:
        """Valida parâmetros e retorna a entity"""
```

**Parâmetros:**

- `path_of_docs` (str): Diretório com arquivos ZIP
- `assets_list` (List[str]): ['ações', 'etf', ...] - ver tabela de assets
- `initial_year` (int): Ano inicial (inclusive)
- `last_year` (int): Ano final (inclusive)
- `destination_path` (Optional[str]): Onde salvar (default: path_of_docs)

**Retorna:**

- `DocsToExtractorB3`: Entity com parâmetros validados

**Levanta:**

- `ValueError`: Se parâmetros inválidos
- `FileNotFoundError`: Se path_of_docs não existe

---

### `ExtractHistoricalQuotesUseCaseB3`

```python
class ExtractHistoricalQuotesUseCaseB3:
    async def execute(
        self,
        docs_to_extract: DocsToExtractorB3,
        processing_mode: str = "fast",
        output_filename: str = "cotahist_extracted.parquet"
    ) -> Dict[str, Any]

    def execute_sync(
        self,
        docs_to_extract: DocsToExtractorB3,
        processing_mode: str = "fast",
        output_filename: str = "cotahist_extracted.parquet"
    ) -> Dict[str, Any]
```

**Retorna:**

````python
{
    'total_files': int,                 # Total de ZIPs encontrados
    'success_count': int,               # ZIPs processados com sucesso
    'error_count': int,                 # ZIPs com erro
    'total_records': int,               # Registros extraídos (somatório dos batches)
    'batches_written': int,             # Quantidade de batches gravados
    'errors': Dict[str, str],           # Erros por arquivo
    'output_file': str                  # Caminho do Parquet final
}

Obs.: os campos `success` e `message` são adicionados pela camada de apresentação
(`HistoricalQuotesResultFormatter.enrich_result`). Ao usar o `HistoricalQuotes`
de alto nível, esses campos já virão preenchidos.

### `GetAvailableAssetsUseCaseB3`

```python
class GetAvailableAssetsUseCaseB3:
    @staticmethod
    def execute() -> List[str]:
        """Retorna lista de assets suportados"""
````

### `GetAvailableYearsUseCaseB3`

```python
class GetAvailableYearsUseCaseB3:
    def get_minimal_year(self) -> int: ...
    def get_atual_year(self) -> int: ...
```

````

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
````

---

## 🧪 Testes

```bash
# Executar todos os testes do módulo
pytest tests/brazil/dados_b3/historical_quotes -v

# Testes da camada de apresentação (alto nível)
pytest tests/presentation/b3_docs -v

# Com coverage (opcional)
pytest -q --cov
```

---

## 🔗 Documentação Adicional

- 📋 Layout COTAHIST (especificação oficial da B3)
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
result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
    docs_to_extract=docs,
    processing_mode='fast'
)
```

### ✅ Economizar Memória

```python
# Use modo 'slow' em máquinas limitadas
result = ExtractHistoricalQuotesUseCaseB3().execute_sync(
    docs_to_extract=docs,
    processing_mode='slow'
)
```

### ✅ Processar Grandes Volumes

```python
# Processe por ano para evitar picos de memória
for year in range(2020, 2024):
    docs = CreateDocsToExtractUseCaseB3(
        ..., initial_year=year, last_year=year
    ).execute()
    result = ExtractHistoricalQuotesUseCaseB3().execute_sync(...)
```

---

**Última atualização:** Novembro 2025
**Versão:** 1.1.0
**Status:** ✅ Produção
