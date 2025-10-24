- Criar validação se path realmente é path
- Criar pastas para cada doc princiapal da cvm. Ex: DFP e ITR. Todos os docs desses zips devem estar nessas pastas


### 4. **Use Cases Poderiam Ser Mais Granulares**

**Atual:**
`DownloadDocumentsUseCase` faz muita coisa:
- Valida inputs
- Cria diretórios
- Gera URLs
- Delega download

**Sugestão:**
Quebre em use cases menores (SRP - Single Responsibility Principle):

```python
# use_cases/
validate_download_request.py    # Valida inputs
generate_download_urls.py        # Gera URLs
prepare_download_directory.py   # Cria dir
execute_download.py              # Orquestra tudo

class ExecuteDownloadUseCase:
    def __init__(
        self,
        validator: ValidateDownloadRequest,
        url_generator: GenerateDownloadUrls,
        dir_preparer: PrepareDownloadDirectory,
        downloader: DownloadDocsCVMRepository
    ):
        ...

    def execute(self, request: DownloadRequest) -> DownloadResult:
        # Orquestra chamadas aos outros use cases
        self.validator.execute(request)
        urls = self.url_generator.execute(request)
        self.dir_preparer.execute(request.path)
        return self.downloader.download_docs(request.path, urls)
```

**Benefícios:**
- Cada use case é testável isoladamente
- Reutilização (ex: `GenerateDownloadUrls` usado em outros fluxos)
- Facilita adicionar novos comportamentos (ex: retry logic)

---

### 5. **Presentation Layer Pode Ter Múltiplas Interfaces**

**Atual:**
Apenas `FundamentalStocksData` (API Python).

**Sugestão de Expansão:**
```python
presentation/
  api/
    cvm_client.py           # API Python (atual)
  cli/
    main.py                 # CLI com Typer/Click
  web/
    api_rest.py             # FastAPI REST endpoints
  sdk/
    async_client.py         # Cliente assíncrono
```

**Exemplo CLI:**
```python
# cli/main.py
import typer

app = typer.Typer()

@app.command()
def download(
    path: str = typer.Option(..., help="Destination path"),
    docs: List[str] = typer.Option(["DFP"], help="Document types"),
    start_year: int = 2020,
    end_year: int = 2023
):
    """Download CVM documents via CLI"""
    cvm = FundamentalStocksData()
    result = cvm.download(path, docs, start_year, end_year)
    typer.echo(f"✅ Downloaded {result.success_count} files")

if __name__ == "__main__":
    app()
```

**Uso:**
```bash
$ datafin download --path /data --docs DFP ITR --start-year 2020
```

---

### 6. **Logging Strategy Precisa Evolução**

**Atual:**
```python
logger = logging.getLogger(__name__)
logger.info("Starting download...")
```

**Problemas:**
- Sem configuração centralizada
- Sem diferentes níveis por ambiente (dev/prod)
- Sem structured logging

**Solução Recomendada:**
```python
# src/core/logging_config.py
import logging
import sys
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False
) -> None:
    """Configure logging para toda aplicação"""

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    if structured:
        # Use structlog para JSON logs
        import structlog
        structlog.configure(...)
    else:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )

# Em __init__.py da biblioteca
from .core.logging_config import setup_logging
setup_logging()
```

**Uso:**
```python
from datafin import setup_logging

# Em produção
setup_logging(level="WARNING", log_file="/var/log/datafin.log", structured=True)

# Em desenvolvimento
setup_logging(level="DEBUG")
```

---

### 7. **Falta Camada de Cache/Storage**

**Problema:**
Toda vez que roda, baixa tudo de novo do servidor CVM.

**Solução:**
Adicione uma camada de cache/storage:

```python
# domain/interfaces/storage_repository.py
class StorageRepository(ABC):
    @abstractmethod
    def exists(self, file_path: str) -> bool: pass

    @abstractmethod
    def get_metadata(self, file_path: str) -> FileMetadata: pass

    @abstractmethod
    def is_outdated(self, file_path: str, max_age_days: int) -> bool: pass

# infra/storage/
local_filesystem_storage.py    # Cache local
s3_storage.py                   # Upload para S3
database_metadata_storage.py   # Metadados em BD

# Use case com cache
class DownloadDocumentsWithCacheUseCase:
    def execute(self, request):
        urls = self.url_generator.execute(request)

        # Filtrar URLs já baixadas e não outdated
        urls_to_download = [
            url for url in urls
            if not self.storage.exists(url)
            or self.storage.is_outdated(url, max_age_days=30)
        ]

        return self.downloader.download_docs(path, urls_to_download)
```

**Benefícios:**
- Economiza banda
- Downloads mais rápidos
- Possibilidade de trabalhar offline

---

### 8. **Configuração External Hardcoded**

**Problema Atual:**
```python
# hardcoded em vários lugares
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 1
DEFAULT_MAX_BACKOFF = 60
```

**Solução:**
Use um sistema de configuração centralizado:

```python
# config/settings.py
from pydantic import BaseSettings

class DownloadSettings(BaseSettings):
    max_retries: int = 3
    initial_backoff: float = 1.0
    max_backoff: float = 60.0
    max_workers: int = 8
    timeout: int = 300

    class Config:
        env_prefix = "DATAFIN_"  # Permite DATAFIN_MAX_RETRIES=5

class Settings(BaseSettings):
    download: DownloadSettings = DownloadSettings()
    log_level: str = "INFO"
    cache_enabled: bool = True
    cache_dir: str = "~/.datafin/cache"

# Singleton
settings = Settings()
```

**Uso:**
```python
# Via código
from datafin.config import settings
adapter = WgetDownloadAdapter(max_retries=settings.download.max_retries)

# Via env vars
$ export DATAFIN_MAX_RETRIES=10
$ export DATAFIN_LOG_LEVEL=DEBUG
$ python meu_script.py
```

---

### 9. **Adicionar Observability (Métricas)**

Para uma biblioteca de produção, considere adicionar:

```python
# infra/metrics/prometheus_metrics.py
from prometheus_client import Counter, Histogram

download_counter = Counter(
    'datafin_downloads_total',
    'Total downloads',
    ['doc_type', 'status']
)

download_duration = Histogram(
    'datafin_download_duration_seconds',
    'Download duration',
    ['doc_type']
)

# Use no adapter
class WgetDownloadAdapter:
    def download_docs(self, ...):
        with download_duration.labels(doc_name).time():
            result = ...
            download_counter.labels(doc_name, 'success').inc(result.success_count)
            download_counter.labels(doc_name, 'failure').inc(result.error_count)
```

---

## 📊 Arquitetura Recomendada Final

```
src/
  core/                          # Núcleo da biblioteca
    config.py                    # Configurações centralizadas
    logging_config.py            # Setup de logging
    types.py                     # Type aliases compartilhados

  brazil/
    cvm/
      fundamental_stocks/
        domain/                  # Regras de negócio puras
          entities/
            document_type.py     # Value Objects ricos
            year_range.py
            download_request.py
          services/              # Domain services
            url_generator.py
          value_objects/

        application/             # Casos de uso
          interfaces/
            download_repository.py
            storage_repository.py
          use_cases/
            validate_request.py
            generate_urls.py
            download_documents.py
            cache_documents.py

        infrastructure/          # Implementações concretas
          download/
            wget_adapter.py
            threadpool_adapter.py
            aria2_adapter.py
          storage/
            local_fs_storage.py
            s3_storage.py
          cache/
            redis_cache.py

        exceptions/              # Todas as exceções CVM
          domain.py
          validation.py
          infra.py
          network.py

  common/                        # Exceções globais
    exceptions.py

  presentation/                  # Interfaces externas
    api/
      client.py                  # API Python
    cli/
      main.py                    # CLI com Typer
    web/
      api.py                     # FastAPI endpoints
```

---

## 🎯 Recomendações Prioritárias

### 🔥 **Faça AGORA (Curto Prazo)**

1. **Padronizar nomes de pastas** (português → inglês)
2. **Criar Value Objects** no domain (DocumentType, YearRange)
3. **Centralizar configuração** (Settings com pydantic)
4. **Reorganizar exceções** (CVM-specific juntas)

### ⚠️ **Faça LOGO (Médio Prazo)**

5. **Adicionar CLI** (Typer/Click)
6. **Implementar cache layer**
7. **Quebrar DownloadDocumentsUseCase** em use cases menores
8. **Adicionar logging estruturado**

### 💡 **Considere (Longo Prazo)**

9. **FastAPI REST API**
10. **Async client** (aiohttp)
11. **Métricas Prometheus**
12. **Dashboard Web** (Streamlit/Dash)

---

## 🏆 Veredicto Final

**SUA ARQUITETURA ESTÁ 8/10 EXCELENTE!**

### Pontos Fortes:
✅ Clean Architecture bem implementada
✅ Repository Pattern exemplar
✅ Type safety e validação
✅ Cobertura de testes
✅ Múltiplos adapters (wget, threadpool, aria2)
✅ Documentação clara

### Melhorias Críticas:
⚠️ **Padronizar nomenclatura** (inglês em todo projeto)
⚠️ **Enriquecer domain model** (Value Objects)
⚠️ **Adicionar cache layer**
⚠️ **Centralizar configuração**

---

## 🚀 Próximos Passos Sugeridos

1. **Semana 1-2:** Refatoração de nomenclatura + Value Objects
2. **Semana 3-4:** Sistema de configuração + Cache layer
3. **Mês 2:** CLI + Async support
4. **Mês 3+:** REST API + Dashboard

Sua base está **sólida e escalável**. Com essas melhorias, terá uma biblioteca de **nível enterprise** para webscraping financeiro! 🎉
