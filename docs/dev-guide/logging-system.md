# Sistema de Logging

Documentação completa do sistema de logging avançado do Global-Data-Finance.

---

## Visão Geral

O Global-Data-Finance possui um sistema de logging centralizado e profissional que oferece:

- ✅ **Lazy initialization** - Logging desabilitado por padrão (biblioteca-friendly)
- ✅ **Console e arquivo** - Handlers configuráveis
- ✅ **Níveis customizáveis** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **Performance timing** - Context managers para medir tempo de execução
- ✅ **Structured logging** - Logs com dados contextuais
- ✅ **Variáveis de ambiente** - Configuração via environment variables

---

## Arquitetura

### Componentes Principais

```
src/core/logging_config.py
├── setup_logging()           # Inicialização do logging
├── get_logger()              # Obter logger por módulo
├── log_execution_time()      # Context manager para timing
├── log_with_context()        # Logging estruturado
├── LoggingSettings           # Configurações
├── StructuredFormatter       # Formatter customizado
└── ContextFilter             # Filtro de contexto
```

---

## Uso Básico

### 1. Habilitar Logging

Por padrão, o logging está **desabilitado**. Para habilitar:

```python
from globaldatafinance.core import setup_logging

# Habilitar logging com nível INFO
setup_logging(level="INFO")
```

### 2. Obter Logger em um Módulo

```python
from globaldatafinance.core import get_logger

logger = get_logger(__name__)
logger.info("Processamento iniciado")
logger.debug("Detalhes de debug")
logger.warning("Aviso importante")
logger.error("Erro ocorreu")
```

### 3. Logging Estruturado

```python
logger.info(
    "Arquivo processado",
    extra={
        "filename": "data.csv",
        "records": 1000,
        "elapsed_ms": 250
    }
)
```

**Saída**:

```
2025-11-25 17:30:00 | INFO     | meu_modulo | Arquivo processado | filename=data.csv | records=1000 | elapsed_ms=250
```

---

## Configuração

### Níveis de Log

| Nível        | Uso                                   | Exemplo                                            |
| ------------ | ------------------------------------- | -------------------------------------------------- |
| **DEBUG**    | Informações detalhadas para debugging | Valores de variáveis, fluxo de execução            |
| **INFO**     | Confirmação de funcionamento normal   | "Download iniciado", "Arquivo salvo"               |
| **WARNING**  | Alerta de situação inesperada         | "Arquivo já existe", "Timeout, tentando novamente" |
| **ERROR**    | Erro que não impede execução          | "Falha ao baixar arquivo X"                        |
| **CRITICAL** | Erro grave que pode parar aplicação   | "Disco cheio", "Sem memória"                       |

### Configuração via Código

```python
from globaldatafinance.core import setup_logging

# Configuração básica
setup_logging(level="INFO")

# Com arquivo de log
setup_logging(
    level="DEBUG",
    log_file="/var/log/datafin.log"
)

# Formato detalhado (com linhas e funções)
setup_logging(
    level="DEBUG",
    use_detailed_format=True
)
```

### Configuração via Variáveis de Ambiente

```bash
# Nível de log
export DATAFIN_LOG_LEVEL=DEBUG

# Arquivo de log
export DATAFIN_LOG_FILE=/var/log/datafin.log

# Formato detalhado
export DATAFIN_LOG_DETAILED_FORMAT=true

# Structured logging (JSON - futuro)
export DATAFIN_LOG_STRUCTURED=true
```

```python
from globaldatafinance.core import setup_logging

# Usa configurações das variáveis de ambiente
setup_logging()
```

---

## Recursos Avançados

### Performance Timing

Use o context manager `log_execution_time()` para medir tempo de operações:

```python
from globaldatafinance.core import log_execution_time, get_logger

logger = get_logger(__name__)

with log_execution_time(logger, "Parse ZIP file", filename="data.zip"):
    parse_file("data.zip")
```

**Saída**:

```
Starting: Parse ZIP file | operation=Parse ZIP file | filename=data.zip
Completed: Parse ZIP file | operation=Parse ZIP file | elapsed_seconds=2.45 | filename=data.zip
```

Se ocorrer erro:

```
Failed: Parse ZIP file | operation=Parse ZIP file | elapsed_seconds=1.23 | error=File not found | filename=data.zip
```

### Logging com Contexto

```python
from globaldatafinance.core import log_with_context, get_logger

logger = get_logger(__name__)

log_with_context(
    logger,
    "info",
    "Download concluído",
    url="https://example.com/file.zip",
    size_mb=125.5,
    duration_seconds=45
)
```

### Verificar se Logging está Configurado

```python
from globaldatafinance.core import is_logging_configured, setup_logging

if not is_logging_configured():
    setup_logging(level="INFO")
```

### Obter Configurações Atuais

```python
from globaldatafinance.core import get_logging_settings

settings = get_logging_settings()
print(f"Nível atual: {settings.level}")
print(f"Arquivo de log: {settings.log_file}")
print(f"Formato detalhado: {settings.detailed_format}")
```

---

## Exemplos Práticos

### Exemplo 1: Logging em Aplicação

```python
from globaldatafinance import FundamentalStocksDataCVM
from globaldatafinance.core import setup_logging, get_logger

# Habilitar logging
setup_logging(level="INFO", log_file="app.log")

logger = get_logger(__name__)
logger.info("Aplicação iniciada")

# Usar a biblioteca
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP"],
    initial_year=2023
)

logger.info("Aplicação finalizada")
```

### Exemplo 2: Debug de Problemas

```python
from globaldatafinance import HistoricalQuotesB3
from globaldatafinance.core import setup_logging

# Nível DEBUG para troubleshooting
setup_logging(
    level="DEBUG",
    log_file="/tmp/debug.log",
    use_detailed_format=True  # Inclui linhas e funções
)

b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações"],
    initial_year=2023
)
```

### Exemplo 3: Logging Customizado em Módulo Próprio

```python
# meu_script.py
from globaldatafinance import FundamentalStocksDataCVM
from globaldatafinance.core import (
    setup_logging,
    get_logger,
    log_execution_time
)

# Configurar logging
setup_logging(level="INFO")

# Criar logger para este módulo
logger = get_logger(__name__)

def processar_dados():
    logger.info("Iniciando processamento")

    with log_execution_time(logger, "Download CVM"):
        cvm = FundamentalStocksDataCVM()
        cvm.download(
            destination_path="/data/cvm",
            list_docs=["DFP"],
            initial_year=2023
        )

    logger.info("Processamento concluído")

if __name__ == "__main__":
    processar_dados()
```

---

## Formatos de Log

### Formato Padrão

```
2025-11-25 17:30:00 | INFO     | módulo.nome | Mensagem de log
```

### Formato Detalhado

Inclui número de linha e nome da função:

```
2025-11-25 17:30:00 | INFO     | módulo.nome:123 | função_nome | Mensagem de log
```

### Formato com Dados Contextuais

```
2025-11-25 17:30:00 | INFO     | módulo | Mensagem | campo1=valor1 | campo2=valor2
```

---

## Boas Práticas

### 1. Sempre use `get_logger(__name__)`

```python
# ✅ Correto - hierarquia de nomes
logger = get_logger(__name__)

# ❌ Evite - nome hardcoded
logger = get_logger("meu_logger")
```

### 2. Use Níveis Apropriados

```python
# ✅ Correto
logger.debug("Valor da variável x: %s", x)
logger.info("Download iniciado")
logger.warning("Arquivo já existe, pulando")
logger.error("Falha ao processar arquivo", exc_info=True)

# ❌ Evite - nível errado
logger.info("Valor de debug: %s", x)  # Use DEBUG
logger.error("Arquivo processado")     # Use INFO
```

### 3. Use Structured Logging

```python
# ✅ Correto - dados estruturados
logger.info(
    "Arquivo processado",
    extra={"filename": "data.csv", "size_mb": 10.5}
)

# ❌ Evite - string interpolation
logger.info(f"Arquivo data.csv processado, tamanho: 10.5 MB")
```

### 4. Use Context Manager para Timing

```python
# ✅ Correto - medição automática
with log_execution_time(logger, "Download"):
    download_files()

# ❌ Evite - medição manual
start = time.time()
download_files()
logger.info(f"Levou {time.time() - start}s")
```

---

## Troubleshooting

### Não vejo nenhum log

```python
# Certifique-se de chamar setup_logging()
from globaldatafinance.core import setup_logging
setup_logging(level="INFO")
```

### Logs duplicados

```python
# Não chame setup_logging() múltiplas vezes
# Se precisar reconfigurar, é seguro chamar novamente
setup_logging(level="DEBUG")  # Reconfigura
```

### Logging em arquivo não funciona

```python
# Verifique permissões do diretório
setup_logging(level="INFO", log_file="/var/log/app.log")

# Se não tiver permissão, use /tmp ou diretório home
setup_logging(level="INFO", log_file="/tmp/app.log")
```

---

## Referências

- [Documentação Oficial Python Logging](https://docs.python.org/3/library/logging.html)
- [Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Structured Logging](https://www.structlog.org/)

---

Veja também:

- [Configuração](advanced-usage.md#configuracao-global) - Configurações globais
- [Advanced Usage](advanced-usage.md) - Uso avançado do sistema
