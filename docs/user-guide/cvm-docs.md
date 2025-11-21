# Documentos CVM

Guia completo para usar a API `FundamentalStocksDataCVM` e baixar documentos fundamentalistas da Comissão de Valores Mobiliários (CVM).

---

## Visão Geral

A classe `FundamentalStocksDataCVM` fornece uma interface simples e poderosa para baixar documentos oficiais da CVM, incluindo demonstrações financeiras, formulários de referência e outros documentos regulatórios de empresas brasileiras de capital aberto.

### Características

- ✅ Download automático de múltiplos tipos de documentos
- ✅ Suporte a intervalos de anos flexíveis
- ✅ Extração automática para formato Parquet (opcional)
- ✅ Download paralelo de alto desempenho (3-5x mais rápido)
- ✅ Tratamento robusto de erros e retry automático
- ✅ Logging detalhado do progresso

---

## Tipos de Documentos Disponíveis

A CVM disponibiliza os seguintes tipos de documentos:

| Código   | Nome Completo                       | Descrição                              | Disponível desde |
| -------- | ----------------------------------- | -------------------------------------- | ---------------- |
| **DFP**  | Demonstração Financeira Padronizada | Balanços anuais completos              | 1998             |
| **ITR**  | Informação Trimestral               | Demonstrações financeiras trimestrais  | 2011             |
| **FRE**  | Formulário de Referência            | Informações detalhadas sobre a empresa | 1998             |
| **FCA**  | Formulário Cadastral                | Dados cadastrais da empresa            | 1998             |
| **CGVN** | Código de Governança                | Práticas de governança corporativa     | 2018             |
| **VLMO** | Valores Mobiliários                 | Informações sobre valores mobiliários  | 2018             |
| **IPE**  | Informações Periódicas e Eventuais  | Documentos periódicos e eventuais      | 1998             |

!!! info "Dados Históricos"
A maioria dos documentos está disponível desde 1998, exceto ITR (2011) e CGVN/VLMO (2018).

---

## Uso Básico

### Importação

```python
from datafinance import FundamentalStocksDataCVM
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

---

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

---

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

---

### `get_available_years()`

Retorna informações sobre os anos disponíveis para cada tipo de documento.

#### Assinatura

```python
def get_available_years(self) -> Dict[str, int]
```

#### Retorno

Dicionário com informações de anos disponíveis:

| Chave                       | Descrição                                |
| --------------------------- | ---------------------------------------- |
| `"Geral Docs"`              | Ano mínimo para documentos gerais (1998) |
| `"ITR Documents"`           | Ano mínimo para ITR (2011)               |
| `"CGVN and VLMO Documents"` | Ano mínimo para CGVN/VLMO (2018)         |
| `"Current Year"`            | Ano atual                                |

#### Exemplo

```python
cvm = FundamentalStocksDataCVM()
years = cvm.get_available_years()

print(f"Documentos gerais disponíveis desde: {years['Geral Docs']}")
print(f"ITR disponível desde: {years['ITR Documents']}")
print(f"Ano atual: {years['Current Year']}")
```

---

## Exemplos Avançados

### Download Incremental

Baixar apenas anos que ainda não foram baixados:

```python
import os
from datafinance import FundamentalStocksDataCVM

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
from datafinance import FundamentalStocksDataCVM

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

if requested_year < years_info['Geral Docs']:
    print(f"⚠️  Ano {requested_year} não disponível (mínimo: {years_info['Geral Docs']})")
else:
    # Prosseguir com download
    cvm.download(
        destination_path="/data/cvm",
        list_docs=valid_docs,
        initial_year=requested_year
    )
```

### Download com Logging Personalizado

```python
from datafinance import FundamentalStocksDataCVM
from datafinance.core import setup_logging
import logging

# Configurar logging detalhado
setup_logging(level="DEBUG")

# Adicionar handler personalizado
logger = logging.getLogger("datafinance")
file_handler = logging.FileHandler("cvm_download.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Executar download
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2022
)

print("✓ Log salvo em: cvm_download.log")
```

---

## Tratamento de Erros

### Exceções Comuns

A API pode lançar as seguintes exceções:

| Exceção                       | Quando ocorre                           | Como tratar                                |
| ----------------------------- | --------------------------------------- | ------------------------------------------ |
| `InvalidDocName`              | Tipo de documento inválido              | Verificar lista com `get_available_docs()` |
| `InvalidFirstYear`            | Ano inicial fora do intervalo           | Verificar anos com `get_available_years()` |
| `InvalidLastYear`             | Ano final inválido ou menor que inicial | Validar intervalo de anos                  |
| `NetworkError`                | Erro de conexão                         | Verificar internet e tentar novamente      |
| `TimeoutError`                | Timeout na requisição                   | Aumentar timeout ou tentar mais tarde      |
| `InvalidDestinationPathError` | Caminho de destino inválido             | Verificar permissões e caminho             |

### Exemplo de Tratamento Completo

```python
from datafinance import FundamentalStocksDataCVM
from datafinance.brazil.cvm.fundamental_stocks_data.exceptions import (
    InvalidDocName,
    InvalidFirstYear,
    InvalidLastYear
)
from datafinance.macro_exceptions import (
    NetworkError,
    TimeoutError,
    InvalidDestinationPathError
)

cvm = FundamentalStocksDataCVM()

try:
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP", "ITR"],
        initial_year=2020,
        last_year=2023
    )
    print("✓ Download concluído com sucesso!")

except InvalidDocName as e:
    print(f"✗ Tipo de documento inválido: {e}")
    print("Documentos disponíveis:", list(cvm.get_available_docs().keys()))

except InvalidFirstYear as e:
    print(f"✗ Ano inicial inválido: {e}")
    years = cvm.get_available_years()
    print(f"Anos disponíveis: {years['Geral Docs']} - {years['Current Year']}")

except InvalidLastYear as e:
    print(f"✗ Ano final inválido: {e}")

except NetworkError as e:
    print(f"✗ Erro de rede: {e}")
    print("Verifique sua conexão com a internet")

except TimeoutError as e:
    print(f"✗ Timeout: {e}")
    print("Tente novamente mais tarde ou verifique sua conexão")

except InvalidDestinationPathError as e:
    print(f"✗ Caminho de destino inválido: {e}")
    print("Verifique se o diretório existe e você tem permissões de escrita")

except Exception as e:
    print(f"✗ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
```

---

## Estrutura dos Arquivos Baixados

### Organização de Diretórios

Após o download, os arquivos são organizados da seguinte forma:

```
destination_path/
├── dfp_cia_aberta_2020.zip
├── dfp_cia_aberta_2021.zip
├── dfp_cia_aberta_2022.zip
├── dfp_cia_aberta_2023.zip
├── itr_cia_aberta_2020.zip
├── itr_cia_aberta_2021.zip
└── ...
```

### Conteúdo dos Arquivos ZIP

Cada arquivo ZIP contém múltiplos arquivos CSV com dados estruturados:

```
dfp_cia_aberta_2023.zip
├── dfp_cia_aberta_2023.csv              # Dados principais
├── dfp_cia_aberta_BPA_con_2023.csv      # Balanço Patrimonial Ativo Consolidado
├── dfp_cia_aberta_BPP_con_2023.csv      # Balanço Patrimonial Passivo Consolidado
├── dfp_cia_aberta_DRE_con_2023.csv      # Demonstração do Resultado
├── dfp_cia_aberta_DFC_MD_con_2023.csv   # Fluxo de Caixa (Método Direto)
├── dfp_cia_aberta_DFC_MI_con_2023.csv   # Fluxo de Caixa (Método Indireto)
├── dfp_cia_aberta_DVA_con_2023.csv      # Demonstração do Valor Adicionado
└── ...
```

### Extração Automática para Parquet

Quando `automatic_extractor=True`, os arquivos são convertidos para Parquet:

```
destination_path/
├── dfp_cia_aberta_2023/
│   ├── dfp_cia_aberta_2023.parquet
│   ├── dfp_cia_aberta_BPA_con_2023.parquet
│   ├── dfp_cia_aberta_BPP_con_2023.parquet
│   └── ...
└── ...
```

---

## Boas Práticas

### 1. Use Intervalos de Anos Razoáveis

```python
# ❌ Evite baixar muitos anos de uma vez
cvm.download(
    destination_path="/data",
    list_docs=["DFP"],
    initial_year=1998,  # 25+ anos!
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

### 4. Implemente Retry Logic

```python
import time
from datafinance import FundamentalStocksDataCVM
from datafinance.macro_exceptions import NetworkError, TimeoutError

def download_with_retry(max_retries=3):
    cvm = FundamentalStocksDataCVM()

    for attempt in range(max_retries):
        try:
            cvm.download(
                destination_path="/data/cvm",
                list_docs=["DFP"],
                initial_year=2022
            )
            print("✓ Download concluído!")
            return True

        except (NetworkError, TimeoutError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"⚠️  Tentativa {attempt + 1} falhou: {e}")
                print(f"Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)
            else:
                print(f"✗ Falha após {max_retries} tentativas")
                return False

download_with_retry()
```

---

## Performance

### Modo de Download

O `FundamentalStocksDataCVM` usa `AsyncDownloadAdapterCVM` por padrão, que oferece:

- ⚡ **3-5x mais rápido** que download sequencial
- 🔄 **Retry automático** em caso de falhas
- 📊 **Progress tracking** detalhado
- 🧵 **8 workers paralelos** (configurável)

### Benchmarks

Tempo aproximado para download de DFP (1 ano):

| Método                  | Tempo | Velocidade         |
| ----------------------- | ----- | ------------------ |
| Download sequencial     | ~60s  | 1x (baseline)      |
| AsyncDownloadAdapterCVM | ~15s  | **4x mais rápido** |

---

## Próximos Passos

- 📈 **[Cotações B3](b3-docs.md)** - Aprenda a extrair cotações históricas
- 💻 **[Exemplos Práticos](examples.md)** - Veja casos de uso completos
- 🔧 **[API Reference](../reference/cvm-api.md)** - Documentação técnica detalhada
- ❓ **[FAQ](faq.md)** - Perguntas frequentes

---

!!! tip "Dica de Performance"
Para análises de dados, sempre use `automatic_extractor=True`. O formato Parquet é muito mais eficiente que CSV para leitura e processamento.
