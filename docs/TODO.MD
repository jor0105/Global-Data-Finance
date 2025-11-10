
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
            download_counter.labels(doc_name, 'success').inc(result.success_count_downloads)
            download_counter.labels(doc_name, 'failure').inc(result.error_count_downloads)
```

---

### 💡 **Considere (Longo Prazo)**

9. **FastAPI REST API**
10. **Async client** (aiohttp)
11. **Métricas Prometheus**
12. **Dashboard Web** (Streamlit/Dash)
