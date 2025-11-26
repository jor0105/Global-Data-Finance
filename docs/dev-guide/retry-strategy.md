# Retry Strategy

Documentação da estratégia de retry do Global-Data-Finance.

---

## Visão Geral

A classe `RetryStrategy` determina quais exceções garantem retry e calcula o tempo de backoff exponencial.

---

## Características

- ✅ **Inteligente**: Apenas retries em erros transientes
- ✅ **Backoff Exponencial**: Aumenta tempo de espera progressivamente
- ✅ **Configurável**: Backoff inicial, máximo e multiplicador customizáveis
- ✅ **Type-safe**: Usa hierarquia de exceções do projeto

---

## Exceções Retryable

### Sempre Retryable

- `NetworkError` - Erros de rede
- `TimeoutError` - Timeout de requisições

### Baseado em Mensagem

Erros com keywords retryáveis na mensagem:

- `"timeout"`
- `"connection refused"`
- `"connection reset"`
- `"connection aborted"`
- `"temporarily"`
- `"unavailable"`
- `"try again"`

### Nunca Retryable

- `PathPermissionError` - Sem permissão
- `DiskFullError` - Disco cheio
- `ValueError` - Erro de validação

---

## API

### Criar Instância

```python
from globaldatafinance.core.utils.retry_strategy import RetryStrategy

strategy = RetryStrategy(
    initial_backoff=1.0,    # Backoff inicial (segundos)
    max_backoff=60.0,       # Backoff máximo (segundos)
    multiplier=2.0          # Multiplicador exponencial
)
```

### Verificar se Exceção é Retryable

```python
from globaldatafinance.macro_exceptions import NetworkError

try:
    download_file()
except Exception as e:
    if strategy.is_retryable(e):
        print("Erro retryable, tentando novamente")
    else:
        print("Erro não-retryable, parando")
        raise
```

### Calcular Backoff

```python
# Calcula tempo de espera para cada tentativa
for retry_count in range(3):
    backoff = strategy.calculate_backoff(retry_count)
    print(f"Tentativa {retry_count + 1}: esperar {backoff}s")
```

**Saída (initial=1.0, multiplier=2.0)**:

```
Tentativa 1: esperar 1.0s
Tentativa 2: esperar 2.0s
Tentativa 3: esperar 4.0s
```

---

## Exemplo de Uso

### Retry Manual com Backoff

```python
from globaldatafinance.core.utils.retry_strategy import RetryStrategy
from globaldatafinance.macro_exceptions import NetworkError
import time

strategy = RetryStrategy(
    initial_backoff=1.0,
    max_backoff=30.0,
    multiplier=2.0
)

max_retries = 3

for attempt in range(max_retries):
    try:
        result = download_file()
        break  # Sucesso
    except Exception as e:
        if not strategy.is_retryable(e):
            raise  # Erro não-retryable

        if attempt < max_retries - 1:
            backoff = strategy.calculate_backoff(attempt)
            print(f"Tentativa {attempt + 1} falhou. Aguardando {backoff}s...")
            time.sleep(backoff)
        else:
            raise  # Esgotou tentativas
```

---

## Uso Automático nos Adapters

Os adapters de download usam `RetryStrategy` automaticamente:

```python
# AsyncDownloadAdapterCVM já implementa retry com backoff
cvm = FundamentalStocksDataCVM()
cvm.download(...)  # Retry automático em erros de rede
```

O adapter faz:

1. Tenta download
2. Se falhar, verifica se é retryable
3. Calcula backoff
4. Aguarda e tenta novamente
5. Repete até max_retries ou sucesso

---

## Configuração de Retry

Via configuração global:

```bash
# Máximo de retries
export DATAFINANCE_NETWORK_MAX_RETRIES=5

# Multiplicador de backoff
export DATAFINANCE_NETWORK_RETRY_BACKOFF=2.0
```

---

## Exceções do Projeto

O `RetryStrategy` usa as exceções definidas em `macro_exceptions`:

```python
from globaldatafinance.macro_exceptions import (
    NetworkError,          # Erro de rede
    TimeoutError,          # Timeout
    PathPermissionError,   # Sem permissão
    DiskFullError          # Disco cheio
)
```

---

Veja também:

- [Exceções](../reference/exceptions.md)
- [Configuration](advanced-usage.md#configuracao-global)
- [Advanced Usage](advanced-usage.md)
