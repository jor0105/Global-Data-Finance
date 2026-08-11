# Documentos CVM

Guia completo para usar a API `FundamentalStocksDataCVM` e baixar documentos fundamentalistas da Comissão de Valores Mobiliários (CVM).

______________________________________________________________________

## Visão Geral

A classe `FundamentalStocksDataCVM` fornece uma interface simples e poderosa para baixar documentos oficiais da CVM, incluindo demonstrações financeiras, formulários de referência e outros documentos regulatórios de empresas brasileiras de capital aberto.

### Características

- ✅ Download automático de múltiplos tipos de documentos
- ✅ Suporte a intervalos de anos flexíveis
- ✅ Extração automática para formato Parquet (opcional)
- ✅ Download paralelo de alto desempenho (3-5x mais rápido)
- ✅ Tratamento robusto de erros e retry automático
- ✅ Logging detalhado do progresso

______________________________________________________________________

## Tipos de Documentos Disponíveis

A CVM disponibiliza os seguintes tipos de documentos:

| Código   | Nome Completo                       | Descrição                              | Disponível desde |
| -------- | ----------------------------------- | -------------------------------------- | ---------------- |
| **DFP**  | Demonstração Financeira Padronizada | Balanços anuais completos              | 2010             |
| **ITR**  | Informação Trimestral               | Demonstrações financeiras trimestrais  | 2011             |
| **FRE**  | Formulário de Referência            | Informações detalhadas sobre a empresa | 2010             |
| **FCA**  | Formulário Cadastral                | Dados cadastrais da empresa            | 2010             |
| **CGVN** | Código de Governança                | Práticas de governança corporativa     | 2018             |
| **VLMO** | Valores Mobiliários                 | Informações sobre valores mobiliários  | 2018             |
| **IPE**  | Informações Periódicas e Eventuais  | Documentos periódicos e eventuais      | 2010             |

!!! info "Dados Históricos"
A maioria dos documentos está disponível desde 2010, exceto ITR (2011) e CGVN/VLMO (2018).

______________________________________________________________________

## Uso Básico

### Importação

```python
from globaldatafinance import FundamentalStocksDataCVM
```

### Criar Instância

```python
cvm = FundamentalStocksDataCVM()
```

### Download Simples

```python
# Baixar DFP dos últimos 3 anos
cvm.download(
    destination_path="/home/usuario/dados_cvm",
    list_docs=["DFP"],
    initial_year=2021,
    last_year=2023
)
```

______________________________________________________________________

## Métodos Principais

### `download()`

Baixa documentos CVM para um diretório especificado.

#### Assinatura

```python
def download(
    self,
    destination_path: str,
    list_docs: Optional[List[str]] = None,
    initial_year: Optional[int] = None,
    last_year: Optional[int] = None,
    automatic_extractor: bool = False,
) -> None
```

#### Parâmetros

| Parâmetro             | Tipo        | Obrigatório | Descrição                                                     |
| --------------------- | ----------- | ----------- | ------------------------------------------------------------- |
| `destination_path`    | `str`       | ✅ Sim      | Diretório onde os arquivos serão salvos                       |
| `list_docs`           | `List[str]` | ❌ Não      | Lista de tipos de documentos. Se `None`, baixa todos          |
| `initial_year`        | `int`       | ❌ Não      | Ano inicial (inclusive). Se `None`, usa ano mínimo disponível |
| `last_year`           | `int`       | ❌ Não      | Ano final (inclusive). Se `None`, usa ano atual               |
| `automatic_extractor` | `bool`      | ❌ Não      | Se `True`, extrai ZIPs para Parquet automaticamente           |

#### Exemplos

**Exemplo 1: Download básico de DFP**

```python
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2020,
    last_year=2023
)
```

**Exemplo 2: Download de múltiplos documentos**

```python
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR", "FRE"],
    initial_year=2022
)
```

**Exemplo 3: Download com extração automática**

```python
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2022,
    automatic_extractor=True  # Extrai para Parquet
)
```

**Exemplo 4: Download de todos os documentos**

```python
# list_docs=None baixa TODOS os tipos disponíveis
cvm.download(
    destination_path="/data/cvm_completo",
    initial_year=2023
)
```

______________________________________________________________________

### `get_available_docs()`

Retorna todos os tipos de documentos disponíveis com suas descrições.

#### Assinatura

```python
def get_available_docs(self) -> Dict[str, str]
```

#### Retorno

Dicionário mapeando códigos de documentos para descrições completas.

#### Exemplo

```python
cvm = FundamentalStocksDataCVM()
docs = cvm.get_available_docs()

for code, description in docs.items():
    print(f"{code}: {description}")
```

**Saída**:

```
DFP: Demonstração Financeira Padronizada
ITR: Informação Trimestral
FRE: Formulário de Referência
FCA: Formulário Cadastral
CGVN: Código de Governança
VLMO: Valores Mobiliários
IPE: Informações Periódicas e Eventuais
```

______________________________________________________________________

### `get_available_years()`

Retorna informações sobre os anos disponíveis para cada tipo de documento.

#### Assinatura

```python
def get_available_years(self) -> Dict[str, int]
```

#### Retorno

Dicionário com informações de anos disponíveis:

| Chave                            | Descrição                                |
| -------------------------------- | ---------------------------------------- |
| `"General Document Years"`       | Ano mínimo para documentos gerais (2010) |
| `"ITR Document Years"`           | Ano mínimo para ITR (2011)               |
| `"CGVN and VMLO Document Years"` | Ano mínimo para CGVN/VLMO (2018)         |
| `"Current Year"`                 | Ano atual                                |

#### Exemplo

```python
cvm = FundamentalStocksDataCVM()
years = cvm.get_available_years()

print(f"Documentos gerais disponíveis desde: {years['General Document Years']}")
print(f"ITR disponível desde: {years['ITR Document Years']}")
print(f"Ano atual: {years['Current Year']}")
```

______________________________________________________________________

## Exemplos Avançados

### Download Incremental

Baixar apenas anos que ainda não foram baixados:

```python
import os
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()
base_path = "/data/cvm"

# Verificar quais anos já existem
existing_years = set()
if os.path.exists(base_path):
    for filename in os.listdir(base_path):
        if "DFP" in filename:
            # Extrair ano do nome do arquivo
            year = int(filename.split("_")[-1].replace(".zip", ""))
            existing_years.add(year)

# Baixar apenas anos faltantes
current_year = 2023
all_years = set(range(2020, current_year + 1))
missing_years = all_years - existing_years

if missing_years:
    min_year = min(missing_years)
    max_year = max(missing_years)

    cvm.download(
        destination_path=base_path,
        list_docs=["DFP"],
        initial_year=min_year,
        last_year=max_year
    )
else:
    print("✓ Todos os anos já foram baixados")
```

### Download com Validação

Validar documentos antes de baixar:

```python
from globaldatafinance import FundamentalStocksDataCVM

cvm = FundamentalStocksDataCVM()

# Validar tipos de documentos
requested_docs = ["DFP", "ITR", "FRE"]
available_docs = cvm.get_available_docs()

valid_docs = [doc for doc in requested_docs if doc in available_docs]
invalid_docs = [doc for doc in requested_docs if doc not in available_docs]

if invalid_docs:
    print(f"⚠️  Documentos inválidos: {invalid_docs}")
    print(f"✓ Documentos válidos: {valid_docs}")

# Validar anos
years_info = cvm.get_available_years()
requested_year = 2015

if requested_year < years_info['General Document Years']:
    print(f"⚠️  Ano {requested_year} não disponível (mínimo: {years_info['General Document Years']})")
else:
    # Prosseguir com download
    cvm.download(
        destination_path="/data/cvm",
        list_docs=valid_docs,
        initial_year=requested_year
    )
```

______________________________________________________________________

## Tratamento de Erros

### Exceções Comuns

A API pode lançar as seguintes exceções:

| Exceção                       | Quando ocorre                           | Como tratar                                |
| ----------------------------- | --------------------------------------- | ------------------------------------------ |
| `InvalidDocumentName`         | Tipo de documento inválido              | Verificar lista com `get_available_docs()` |
| `InvalidFirstYear`            | Ano inicial fora do intervalo           | Verificar anos com `get_available_years()` |
| `InvalidLastYear`             | Ano final inválido ou menor que inicial | Validar intervalo de anos                  |
| `NetworkError`                | Erro de conexão                         | Verificar internet e tentar novamente      |
| `TimeoutError`                | Timeout na requisição                   | Aumentar timeout ou tentar mais tarde      |
| `InvalidDestinationPathError` | Caminho de destino inválido             | Verificar permissões e caminho             |

______________________________________________________________________

## Estrutura dos Arquivos Baixados

### Organização de Diretórios

Após o download, os arquivos são organizados da seguinte forma:

```

destination_path/
    DFP/
        2020/
            dfp_cia_aberta_2020.zip
        2021/
            dfp_cia_aberta_2021.zip
        2022/
            dfp_cia_aberta_2022.zip
        2023/
            dfp_cia_aberta_2023.zip
    ITR/
        2020/
            itr_cia_aberta_2020.zip
        2021/
            itr_cia_aberta_2021.zip
        2022/
            itr_cia_aberta_2022.zip
        2023/
            itr_cia_aberta_2023.zip
    FRE/
        2020/
            fre_cia_aberta_2020.zip
        2021/
            fre_cia_aberta_2021.zip
        2022/
            fre_cia_aberta_2022.zip
        2023/
            fre_cia_aberta_2023.zip
    FCA/
        2020/
            fca_cia_aberta_2020.zip
        2021/
            fca_cia_aberta_2021.zip
        2022/
            fca_cia_aberta_2022.zip
        2023/
            fca_cia_aberta_2023.zip
    etc...

```

### Conteúdo dos Arquivos ZIP

Cada arquivo ZIP contém múltiplos arquivos CSV com dados estruturados:

```

dfp_cia_aberta_2023.zip
├── dfp_cia_aberta_2023.csv # Dados principais
├── dfp_cia_aberta_BPA_con_2023.csv # Balanço Patrimonial Ativo Consolidado
├── dfp_cia_aberta_BPP_con_2023.csv # Balanço Patrimonial Passivo Consolidado
├── dfp_cia_aberta_DRE_con_2023.csv # Demonstração do Resultado
├── dfp_cia_aberta_DFC_MD_con_2023.csv # Fluxo de Caixa (Método Direto)
├── dfp_cia_aberta_DFC_MI_con_2023.csv # Fluxo de Caixa (Método Indireto)
├── dfp_cia_aberta_DVA_con_2023.csv # Demonstração do Valor Adicionado
└── ...

```

### Extração Automática para Parquet

Quando `automatic_extractor=True`, os arquivos são convertidos para Parquet:

```

destination_path/
├── DFP/
    2023/
    │ ├── dfp_cia_aberta_2023.parquet
    │ ├── dfp_cia_aberta_BPA_con_2023.parquet
    │ ├── dfp_cia_aberta_BPP_con_2023.parquet
    │ └── ...
└── ...

```

______________________________________________________________________

## Boas Práticas

### 1. Use Intervalos de Anos Razoáveis

```python
# ❌ Evite baixar muitos anos de uma vez
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],
    initial_year=2010,  # 25+ anos!
    last_year=2023
)

# ✅ Prefira intervalos menores
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],
    initial_year=2020,  # 3-4 anos
    last_year=2023
)
```

### 2. Verifique Espaço em Disco

```python
import shutil

# Verificar espaço disponível
stats = shutil.disk_usage("/data")
free_gb = stats.free / (1024**3)

if free_gb < 10:
    print(f"⚠️  Pouco espaço disponível: {free_gb:.2f} GB")
else:
    cvm.download(destination_path="/data", ...)
```

### 3. Use Extração Automática para Análise

```python
# Se você vai analisar os dados, use Parquet
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2022,
    automatic_extractor=True  # Muito mais rápido para ler
)
```

______________________________________________________________________

## Performance

### Modo de Download

O `FundamentalStocksDataCVM` usa `AsyncDownloadAdapterCVM` por padrão, que oferece:

- ⚡ **3-5x mais rápido** que download sequencial
- 🔄 **Retry automático** em caso de falhas
- 📊 **Progress tracking** detalhado
- 🧵 **8 workers paralelos** (configurável)

### Benchmarks

**Fluxo completo: download + extração CSV→Parquet (2026-08-06):**

| Docs                | Período   | ZIPs | Parquets |     Linhas |     Saída |    Tempo |  Pico RSS | Erros |
| ------------------- | --------- | ---: | -------: | ---------: | --------: | -------: | --------: | ----: |
| DFP, ITR, FRE, etc. | 2010-2024 |   88 |    1.392 | 63.300.208 | 337,93 MB | 505,04 s | 459,18 MB |     0 |

**Tempo aproximado para download de DFP (1 ano):**

| Método                  | Tempo | Velocidade         |
| ----------------------- | ----- | ------------------ |
| Download sequencial     | ~60s  | 1x (baseline)      |
| AsyncDownloadAdapterCVM | ~15s  | **4x mais rápido** |

______________________________________________________________________

## Próximos Passos

- 📈 **[Cotações B3](b3-docs.md)** - Aprenda a extrair cotações históricas
- 💻 **[Exemplos Práticos](examples.md)** - Veja casos de uso completos
- 🔧 **[API Reference](../reference/cvm-api.md)** - Documentação técnica detalhada
- ❓ **[FAQ](faq.md)** - Perguntas frequentes

______________________________________________________________________

!!! tip "Dica de Performance"
Para análises de dados, sempre use `automatic_extractor=True`. O formato Parquet é muito mais eficiente que CSV para leitura e processamento.
