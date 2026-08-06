# Cotações Históricas B3

Guia completo para usar a API `HistoricalQuotesB3` e extrair cotações históricas da B3 (Brasil, Bolsa, Balcão) a partir de arquivos COTAHIST.

---

## Visão Geral

A classe `HistoricalQuotesB3` fornece uma interface poderosa para processar arquivos COTAHIST da B3, extraindo cotações históricas de diferentes classes de ativos e convertendo-as para o formato Parquet otimizado para análise.

### Características

- ✅ Extração de múltiplas classes de ativos
- ✅ Processamento de alto desempenho (modo fast/slow)
- ✅ Conversão automática para formato Parquet
- ✅ Suporte a dados desde 1986
- ✅ Filtragem inteligente por tipo de ativo
- ✅ Progress tracking detalhado

---

## Classes de Ativos Disponíveis

A B3 disponibiliza cotações históricas para as seguintes classes de ativos:

| Código               | Descrição           | Mercados Incluídos                        |
| -------------------- | ------------------- | ----------------------------------------- |
| **ações**            | Ações               | Mercado à vista (010) e fracionário (012) |
| **etf**              | ETFs                | Exchange Traded Funds                     |
| **opções**           | Opções              | Calls (070) e Puts (080)                  |
| **termo**            | Mercado a Termo     | Contratos a termo                         |
| **exercicio_opcoes** | Exercício de Opções | Exercício de opções                       |
| **forward**          | Mercado Forward     | Contratos forward                         |
| **leilao**           | Leilão              | Mercado de leilão                         |

!!! info "Dados Históricos"
Cotações históricas da B3 estão disponíveis desde **1986** até o ano atual.

---

## Uso Básico

### Importação

```python
from globaldatafinance import HistoricalQuotesB3
```

### Criar Instância

```python
b3 = HistoricalQuotesB3()
```

### Extração Simples

```python
# Extrair cotações de ações do ano atual
result = b3.extract(
    path_of_docs="/home/usuario/cotahist_zips",
    assets_list=["ações"],
    initial_year=2023
)

print(f"✓ Extraídos {result['total_records']:,} registros")
```

---

## Métodos Principais

### `extract()`

Extrai cotações históricas de arquivos COTAHIST ZIP para formato Parquet.

#### Assinatura

```python
def extract(
    self,
    path_of_docs: str,
    assets_list: List[str],
    initial_year: Optional[int] = None,
    last_year: Optional[int] = None,
    destination_path: Optional[str] = None,
    output_filename: str = "cotahist_extracted",
    processing_mode: str = "fast",
) -> Dict[str, Any]
```

#### Parâmetros

| Parâmetro          | Tipo        | Obrigatório | Descrição                                             |
| ------------------ | ----------- | ----------- | ----------------------------------------------------- |
| `path_of_docs`     | `str`       | ✅ Sim      | Diretório contendo arquivos COTAHIST ZIP              |
| `assets_list`      | `List[str]` | ✅ Sim      | Lista de classes de ativos a extrair                  |
| `initial_year`     | `int`       | ❌ Não      | Ano inicial (padrão: 1986)                            |
| `last_year`        | `int`       | ❌ Não      | Ano final (padrão: ano atual)                         |
| `destination_path` | `str`       | ❌ Não      | Diretório de saída (padrão: mesmo que `path_of_docs`) |
| `output_filename`  | `str`       | ❌ Não      | Nome do arquivo de saída sem extensão                 |
| `processing_mode`  | `str`       | ❌ Não      | Modo de processamento: `"fast"` ou `"slow"`           |

#### Retorno

Dicionário com as seguintes chaves:

| Chave           | Tipo        | Descrição                                  |
| --------------- | ----------- | ------------------------------------------ |
| `success`       | `bool`      | `True` se extração foi bem-sucedida        |
| `message`       | `str`       | Mensagem resumida do resultado             |
| `total_files`   | `int`       | Total de arquivos ZIP processados          |
| `success_count` | `int`       | Arquivos processados com sucesso           |
| `error_count`   | `int`       | Arquivos com erro                          |
| `total_records` | `int`       | Total de registros extraídos               |
| `output_file`   | `str`       | Caminho completo do arquivo Parquet gerado |
| `errors`        | `List[str]` | Lista de erros (se houver)                 |

#### Exemplos

**Exemplo 1: Extração básica de ações**

```python
b3 = HistoricalQuotesB3()

result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2022,
    last_year=2023
)

if result['success']:
    print(f"✓ Arquivo gerado: {result['output_file']}")
    print(f"✓ Total de registros: {result['total_records']:,}")
```

**Exemplo 2: Múltiplas classes de ativos**

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf", "opções"],
    initial_year=2020,
    last_year=2023,
    output_filename="multi_ativos_2020_2023"
)
```

**Exemplo 3: Modo de baixa performance (economia de recursos)**

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2023,
    processing_mode="slow"  # Usa menos CPU/RAM
)
```

**Exemplo 4: Destino personalizado**

```python
result = b3.extract(
    path_of_docs="/data/cotahist_zips",
    destination_path="/data/cotacoes_extraidas",
    assets_list=["ações", "etf"],
    initial_year=2023,
    output_filename="acoes_etf_2023"
)
# Arquivo salvo em: /data/cotacoes_extraidas/acoes_etf_2023.parquet
```

---

### `get_available_assets()`

Retorna lista de todas as classes de ativos disponíveis.

#### Assinatura

```python
def get_available_assets(self) -> List[str]
```

#### Retorno

Lista de strings com códigos das classes de ativos.

#### Exemplo

```python
b3 = HistoricalQuotesB3()
assets = b3.get_available_assets()

print("Classes de ativos disponíveis:")
for asset in assets:
    print(f"  • {asset}")
```

**Saída**:

```
Classes de ativos disponíveis:
  • ações
  • etf
  • opções
  • termo
  • exercicio_opcoes
  • forward
  • leilao
```

---

### `get_available_years()`

Retorna informações sobre o intervalo de anos disponível.

#### Assinatura

```python
def get_available_years(self) -> Dict[str, int]
```

#### Retorno

Dicionário com:

| Chave            | Descrição                    |
| ---------------- | ---------------------------- |
| `"minimal_year"` | Ano mínimo disponível (1986) |
| `"current_year"` | Ano atual                    |

#### Exemplo

```python
b3 = HistoricalQuotesB3()
years = b3.get_available_years()

print(f"Dados disponíveis de {years['minimal_year']} até {years['current_year']}")
```

**Saída**:

```
Dados disponíveis de 1986 até ano atual
```

---

## Modos de Processamento

A extração suporta dois modos de processamento:

### Modo Fast (Padrão) ⚡

- **Performance**: Alto desempenho
- **CPU**: Uso intensivo (multi-core)
- **RAM**: Maior consumo de memória
- **Recomendado para**: Máquinas com bons recursos, processamento de grandes volumes

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    processing_mode="fast"  # Padrão
)
```

### Modo Slow 🐢

- **Performance**: Moderada
- **CPU**: Uso reduzido (single-core ou poucos cores)
- **RAM**: Menor consumo de memória
- **Recomendado para**: Máquinas com recursos limitados, processamento em background

```python
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    processing_mode="slow"
)
```

### Comparação de Performance

| Modo     | Throughput medido      | CPU   | Pico de RAM | Recomendado        |
| -------- | ---------------------- | ----- | ----------- | ------------------ |
| **fast** | ~12.317 reg/s          | Alto  | ~4.260 MB   | ✅ Sim (padrão)    |
| **slow** | ~8.557 reg/s           | Baixo | ~1.571 MB   | Recursos limitados |

---

## Exemplos Avançados

### Extração de Todos os Ativos

```python
from globaldatafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()

# Obter todas as classes de ativos
all_assets = b3.get_available_assets()

# Extrair tudo
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=all_assets,  # Todas as classes
    initial_year=2023,
    output_filename="todos_ativos_2023"
)

print(f"✓ Extraídos {result['total_records']:,} registros de {len(all_assets)} classes")
```

### Extração Incremental por Ano

```python
from globaldatafinance import HistoricalQuotesB3
import os

b3 = HistoricalQuotesB3()
base_path = "/data/cotahist"
output_path = "/data/cotacoes_extraidas"

# Extrair cada ano separadamente
for year in range(2020, 2024):
    output_file = f"acoes_{year}"

    result = b3.extract(
        path_of_docs=base_path,
        destination_path=output_path,
        assets_list=["ações"],
        initial_year=year,
        last_year=year,
        output_filename=output_file
    )

    if result['success']:
        print(f"✓ {year}: {result['total_records']:,} registros")
    else:
        print(f"✗ {year}: Erro na extração")
```

### Validação Antes da Extração

```python
from globaldatafinance import HistoricalQuotesB3
import os

b3 = HistoricalQuotesB3()
path_docs = "/data/cotahist"

# 1. Verificar se diretório existe
if not os.path.exists(path_docs):
    print(f"✗ Diretório não encontrado: {path_docs}")
    exit(1)

# 2. Verificar se há arquivos COTAHIST
zip_files = [f for f in os.listdir(path_docs) if f.startswith("COTAHIST") and f.endswith(".ZIP")]

if not zip_files:
    print(f"✗ Nenhum arquivo COTAHIST encontrado em {path_docs}")
    exit(1)

print(f"✓ Encontrados {len(zip_files)} arquivos COTAHIST")

# 3. Validar classes de ativos
requested_assets = ["ações", "etf"]
available_assets = b3.get_available_assets()

invalid_assets = [a for a in requested_assets if a not in available_assets]
if invalid_assets:
    print(f"✗ Ativos inválidos: {invalid_assets}")
    print(f"Ativos disponíveis: {available_assets}")
    exit(1)

# 4. Prosseguir com extração
result = b3.extract(
    path_of_docs=path_docs,
    assets_list=requested_assets,
    initial_year=2023
)
```

---

## Tratamento de Erros

### Exceções Comuns

| Exceção               | Quando ocorre                    | Como tratar                            |
| --------------------- | -------------------------------- | -------------------------------------- |
| `EmptyAssetListError` | `assets_list` está vazio         | Fornecer pelo menos um ativo           |
| `InvalidAssetsName`   | Ativo inválido em `assets_list`  | Verificar com `get_available_assets()` |
| `InvalidFirstYear`    | `initial_year` fora do intervalo | Usar 1986 ≤ ano ≤ ano atual            |
| `InvalidLastYear`     | `last_year` inválido             | Usar `initial_year` ≤ ano ≤ ano atual  |
| `EmptyDirectoryError` | Diretório sem arquivos COTAHIST  | Verificar caminho e arquivos           |
| `ExtractionError`     | Erro ao processar ZIP            | Verificar integridade dos arquivos     |

---

## Formato dos Arquivos COTAHIST

### Nomenclatura

Os arquivos COTAHIST seguem o padrão:

```
COTAHIST_AXXXX.ZIP
```

Onde `XXXX` é o ano (ex: `COTAHIST_A2023.ZIP`).

### Onde Obter

Os arquivos COTAHIST podem ser baixados do site oficial da B3:

🔗 **[https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)**

### Estrutura Interna

Cada arquivo ZIP contém um arquivo TXT com layout de largura fixa:

```
COTAHIST_A2023.ZIP
└── COTAHIST_A2023.TXT  (arquivo de texto com largura fixa)
```

O Global-Data-Finance processa automaticamente este formato e converte para Parquet.

---

## Estrutura do Arquivo Parquet Gerado

### Colunas

O arquivo Parquet gerado contém as seguintes colunas:

| Coluna                 | Tipo      | Descrição                              |
| ---------------------- | --------- | -------------------------------------- |
| `data_pregao`          | `date`    | Data do pregão                         |
| `codigo_bdi`           | `string`  | Código BDI                             |
| `ticker`               | `string`  | Código de negociação (ex: PETR4)       |
| `tipo_mercado`         | `string`  | Tipo de mercado                        |
| `nome_resumido`        | `string`  | Nome resumido da empresa               |
| `especificacao_papel`  | `string`  | Especificação do papel (ex: ON, PN)    |
| `preco_abertura`       | `decimal` | Preço de abertura                      |
| `preco_maximo`         | `decimal` | Preço máximo do dia                    |
| `preco_minimo`         | `decimal` | Preço mínimo do dia                    |
| `preco_medio`          | `decimal` | Preço médio do dia                     |
| `preco_fechamento`     | `decimal` | Preço de fechamento                    |
| `melhor_oferta_compra` | `decimal` | Melhor oferta de compra                |
| `melhor_oferta_venda`  | `decimal` | Melhor oferta de venda                 |
| `numero_negocios`      | `int`     | Número de negócios efetuados           |
| `quantidade_total`     | `int`     | Quantidade total de títulos negociados |
| `volume_total`         | `decimal` | Volume total financeiro                |
| `data_vencimento`      | `date`    | Data de vencimento (opções/termo)      |
| `fator_cotacao`        | `int`     | Fator de cotação                       |
| `codigo_isin`          | `string`  | Código ISIN                            |
| `numero_distribuicao`  | `int`     | Número de distribuição                 |

### Leitura com Pandas

```python
import pandas as pd

df = pd.read_parquet("/data/cotacoes_extraidas/cotahist_extracted.parquet")

print(df.head())
print(f"\nShape: {df.shape}")
print(f"Período: {df['data_pregao'].min()} a {df['data_pregao'].max()}")
```

### Leitura com Polars (Mais Rápido)

```python
import polars as pl

df = pl.read_parquet("/data/cotacoes_extraidas/cotahist_extracted.parquet")

print(df.head())
print(f"\nShape: {df.shape}")
print(f"Memória: {df.estimated_size('mb'):.2f} MB")
```

---

## Boas Práticas

### 1. Use Modo Fast para Grandes Volumes

```python
# ✅ Recomendado para grandes volumes
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=1986,  # 23+ anos
    processing_mode="fast"
)
```

### 2. Separe Extrações por Classe de Ativo

```python
# ✅ Melhor: arquivos separados por classe
for asset in ["ações", "etf", "opções"]:
    result = b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=[asset],
        initial_year=2023,
        output_filename=f"{asset}_2023"
    )

# ❌ Evite: tudo em um arquivo (pode ficar muito grande)
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf", "opções", "termo", "forward"],
    initial_year=1986,  # 38+ anos!
    output_filename="tudo"
)
```

### 3. Verifique Espaço em Disco

```python
import shutil

stats = shutil.disk_usage("/data")
free_gb = stats.free / (1024**3)

if free_gb < 5:
    print(f"⚠️  Pouco espaço: {free_gb:.2f} GB")
    # Use modo slow ou processe menos anos
else:
    # Prosseguir normalmente
    pass
```

---

## Próximos Passos

- 📄 **[Documentos CVM](cvm-docs.md)** - Aprenda a baixar documentos CVM
- 💻 **[Exemplos Práticos](examples.md)** - Veja casos de uso completos
- 🔧 **[API Reference](../reference/b3-api.md)** - Documentação técnica detalhada
- ❓ **[FAQ](faq.md)** - Perguntas frequentes

---

!!! tip "Dica de Análise"
Após extrair para Parquet, use Polars para análises de alto desempenho. É significativamente mais rápido que Pandas para grandes volumes de dados.
