# Resource Monitoring

Documentação do sistema de monitoramento de recursos do Global-Data-Finance.

---

## Visão Geral

O `ResourceMonitor` é um sistema avançado de monitoramento de CPU e memória que:

- ✅ **Singleton**: Uma única instância global
- ✅ **Automático**: Ajusta workers e batch sizes baseado em recursos disponíveis
- ✅ **Circuit Breaker**: Para operações quando recursos estão críticos
- ✅ **Garbage Collection**: GC automático quando memória está alta

---

## Estados de Recursos

| Estado        | Descrição                | Ação                          |
| ------------- | ------------------------ | ----------------------------- |
| **HEALTHY**   | Recursos normais         | Nenhuma ação necessária       |
| **WARNING**   | Recursos acima de 70-80% | Considera ativar GC           |
| **CRITICAL**  | Recursos acima de 85-90% | Reduz workers/batch, força GC |
| **EXHAUSTED** | Recursos acima de 95%    | Ativa circuit breaker         |

---

## Configuração

### ResourceLimits

```python
from globaldatafinance.core.utils.resource_monitor import ResourceLimits

limits = ResourceLimits(
    memory_warning_threshold=70.0,      # % de memória para WARNING
    memory_critical_threshold=85.0,     # % de memória para CRITICAL
    memory_exhausted_threshold=95.0,    # % de memória para EXHAUSTED
    cpu_warning_threshold=80.0,         # % de CPU para WARNING
    cpu_critical_threshold=90.0,        # % de CPU para CRITICAL
    min_free_memory_mb=100,             # MB mínimo de memória livre
    auto_gc_on_warning=True,            # GC automático em WARNING
    circuit_breaker_cooldown_seconds=10,# Cooldown do circuit breaker
    circuit_breaker_enabled=True        # Habilitar circuit breaker
)
```

---

## API

### Criar Instância (Singleton)

```python
from globaldatafinance.core.utils.resource_monitor import ResourceMonitor

# Obter instância (sempre a mesma)
monitor = ResourceMonitor()

# Ou com limites customizados
limits = ResourceLimits(memory_warning_threshold=60.0)
monitor = ResourceMonitor(limits)
```

### Verificar Estado atual

```python
state = monitor.check_resources()
print(state)  # HEALTHY, WARNING, CRITICAL, ou EXHAUSTED
```

### Calcular Workers Seguros

```python
# Número seguro de workers baseado em recursos
safe_workers = monitor.get_safe_worker_count(max_workers=16)
print(f"Usando {safe_workers} workers")
```

### Calcular Batch Size Seguro

```python
# Tamanho de batch seguro baseado em memória
safe_batch = monitor.get_safe_batch_size(desired_batch_size=10000)
print(f"Batch size: {safe_batch}")
```

### Aguardar Recursos Disponíveis

```python
from globaldatafinance.core.utils.resource_monitor import ResourceState

# Aguardar até que recursos melhorem
success = monitor.wait_for_resources(
    required_state=ResourceState.WARNING,
    timeout_seconds=60
)

if success:
    print("Recursos disponíveis")
else:
    print("Timeout aguardando recursos")
```

### Memória do Processo Atual

```python
memory_mb = monitor.get_process_memory_mb()
print(f"Processo usando {memory_mb:.2f} MB")
```

---

## Uso Automático nos Adapters

O `ResourceMonitor` é usado automaticamente pelos adapters de download:

```python
# AsyncDownloadAdapterCVM usa ResourceMonitor para:
# - Ajustar número de workers dinamicamente
# - Reduzir batch size quando memória está alta
# - Pausar downloads quando recursos críticos

cvm = FundamentalStocksDataCVM()
cvm.download(...)  # Resource monitoring automático
```

---

## Exemplo Manual

```python
from globaldatafinance.core.utils.resource_monitor import (
    ResourceMonitor,
    ResourceState
)

monitor = ResourceMonitor()

# Checar antes de operação pesada
state = monitor.check_resources()

if state == ResourceState.EXHAUSTED:
    print("Recursos críticos! Aguardando...")
    monitor.wait_for_resources(timeout_seconds=120)

# Ajustar workers baseado em recursos
workers = monitor.get_safe_worker_count(max_workers=16)
process_data(workers=workers)

# Verificar memória do processo
memory = monitor.get_process_memory_mb()
print(f"Processo usando {memory:.2f} MB")
```

---

## Dependência

Requer `psutil`:

```bash
pip install psutil
```

Se `psutil` não estiver disponível, o monitor funciona em modo degradado (sempre retorna HEALTHY).

---

Veja também:

- [Retry Strategy](retry-strategy.md)
- [Advanced Usage](advanced-usage.md)
