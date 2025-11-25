# Uso Avançado

Técnicas avançadas e customização do Global-Data-Finance.

---

## Core Utilities

### Sistema de Logging

Habilite logging profissional para rastreamento e debugging:

```python
from globaldatafinance.core import setup_logging, get_logger, log_execution_time

# Configurar logging
setup_logging(level="INFO", log_file="app.log")

# Obter logger
logger = get_logger(__name__)

# Logging estruturado
logger.info(
    "Download iniciado",
    extra={"doc_type": "DFP", "year": 2023}
)

# Performance timing
with log_execution_time(logger, "Download CVM", total=5):
    cvm.download(...)
```

[Ver documentação completa →](logging-system.md)

### Configuração Global

Customize network settings via environment variables:

```bash
# Aumentar timeout para conexões lentas
export DATAFINANCE_NETWORK_TIMEOUT=900

# Mais tentativas de retry
export DATAFINANCE_NETWORK_MAX_RETRIES=10

# Backoff mais agressivo
export DATAFINANCE_NETWORK_RETRY_BACKOFF=3.0
```

```python
from globaldatafinance.core.config import settings

# Verificar configurações atuais
print(f"Timeout: {settings.network.timeout}s")
print(f"Max retries: {settings.network.max_retries}")
```

[Ver documentação completa →](configuration.md)

### Resource Monitoring

Monitore e gerencie recursos automaticamente:

```python
from globaldatafinance.core.utils.resource_monitor import (
    ResourceMonitor,
    ResourceState,
    ResourceLimits
)

# Criar monitor
monitor = ResourceMonitor()

# Verificar estado
state = monitor.check_resources()
if state == ResourceState.CRITICAL:
    print("Recursos críticos!")

# Calcular workers seguros
safe_workers = monitor.get_safe_worker_count(max_workers=16)
print(f"Usando {safe_workers} workers")

# Aguardar recursos disponíveis
monitor.wait_for_resources(timeout_seconds=120)
```

[Ver documentação completa →](resource-monitoring.md)

### Retry Strategy

Implemente retry customizado:

```python
from globaldatafinance.core.utils.retry_strategy import RetryStrategy
import time

strategy = RetryStrategy(
    initial_backoff=1.0,
    max_backoff=30.0,
    multiplier=2.0
)

max_retries = 5
for attempt in range(max_retries):
    try:
        result = risky_operation()
        break
    except Exception as e:
        if not strategy.is_retryable(e):
            raise

        if attempt < max_retries - 1:
            backoff = strategy.calculate_backoff(attempt)
            print(f"Retry {attempt + 1} após {backoff}s...")
            time.sleep(backoff)
```

[Ver documentação completa →](retry-strategy.md)

---

## Customização de Adapters

### Criar Adapter Personalizado

```python
from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.interfaces import (
    DownloadDocsCVMRepository
)
from globaldatafinance.brazil.cvm.fundamental_stocks_data.domain import DownloadResultCVM

class MyCustomAdapter(DownloadDocsCVMRepository):
    """Adapter personalizado para download."""

    def download_docs(
        self,
        destination_path: str,
        dict_zip_to_download: Dict[str, List[int]]
    ) -> DownloadResultCVM:
        """Implementação personalizada de download."""
        # Sua lógica aqui
        return DownloadResultCVM(...)

# Uso
from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.use_cases import (
    DownloadDocumentsUseCaseCVM
)

adapter = MyCustomAdapter()
use_case = DownloadDocumentsUseCaseCVM(adapter)
result = use_case.execute(...)
```

---

## Logging Avançado

### Configuração Personalizada

```python
import logging
from globaldatafinance.core import get_logger

# Criar logger personalizado
logger = get_logger("meu_modulo")

# Adicionar handler para arquivo
file_handler = logging.FileHandler("globaldatafinance.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Usar
logger.info("Iniciando processamento...")
```

---

## Processamento Paralelo

### Múltiplos Anos em Paralelo

```python
from concurrent.futures import ProcessPoolExecutor
from globaldatafinance import HistoricalQuotesB3

def extract_year(year):
    b3 = HistoricalQuotesB3()
    return b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=year,
        last_year=year,
        output_filename=f"acoes_{year}"
    )

years = range(2020, 2024)
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(extract_year, years))

for year, result in zip(years, results):
    print(f"{year}: {result['total_records']:,} registros")
```

---

## Integração com Frameworks

### Apache Airflow

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from globaldatafinance import FundamentalStocksDataCVM

def download_cvm_task():
    cvm = FundamentalStocksDataCVM()
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2023
    )

with DAG(
    'cvm_download_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily'
) as dag:

    download = PythonOperator(
        task_id='download_cvm',
        python_callable=download_cvm_task
    )
```

### Prefect

```python
from prefect import flow, task
from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3

@task
def download_cvm():
    cvm = FundamentalStocksDataCVM()
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2023
    )

@task
def extract_b3():
    b3 = HistoricalQuotesB3()
    return b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=2023
    )

@flow
def financial_data_pipeline():
    download_cvm()
    result = extract_b3()
    return result

# Executar
if __name__ == "__main__":
    financial_data_pipeline()
```

---

## Otimizações de Performance

### Uso Eficiente de Memória

```python
import polars as pl

# Ler apenas colunas necessárias
df = pl.read_parquet(
    "cotahist.parquet",
    columns=["data", "codigo_negociacao", "preco_fechamento"]
)

# Filtrar durante leitura
df = pl.scan_parquet("cotahist.parquet") \
    .filter(pl.col("codigo_negociacao") == "PETR4") \
    .collect()
```

### Processamento em Chunks

```python
import pandas as pd

# Processar arquivo grande em chunks
for chunk in pd.read_parquet(
    "cotahist.parquet",
    chunksize=100000
):
    # Processar chunk
    process_chunk(chunk)
```

---

## Monitoramento e Métricas

### Tracking de Progresso

```python
from tqdm import tqdm
from globaldatafinance import HistoricalQuotesB3

b3 = HistoricalQuotesB3()

years = range(2020, 2024)
for year in tqdm(years, desc="Extraindo anos"):
    result = b3.extract(
        path_of_docs="/data/cotahist",
        assets_list=["ações"],
        initial_year=year,
        last_year=year
    )
```

---

Veja também:

- [Arquitetura](architecture.md)
- [Exemplos Práticos](../user-guide/examples.md)
