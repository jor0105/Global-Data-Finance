# Progress Bar Implementation

## Overview

O `ThreadPoolDownloadAdapter` agora inclui uma **barra de progresso simples e elegante** que mostra o avanço dos downloads em tempo real.

### ✨ Características:

- ✅ **Sem dependências externas** — Usa apenas `sys` e `time` (built-in do Python)
- ✅ **Thread-safe** — Funciona corretamente com múltiplas threads
- ✅ **Limpeza automática** — Respeita quando há 0 arquivos
- ✅ **Visual limpo** — Uso de caracteres Unicode (█ e ░)

## Como Funciona

### Exemplo de saída:

```
Downloading [████████████░░░░░░░░░░░░░░░░░░] 15/50 (30%)
Downloading [██████████████████████████████░░] 49/50 (98%)
Downloading [████████████████████████████████] 50/50 (100%)
```

### Dentro do código:

```python
# Barra criada automaticamente
progress_bar = SimpleProgressBar(
    total=total_files,
    desc="Downloading",
    width=30
)

# Atualiza a cada arquivo baixado
for future in as_completed(futures):
    # ... processar download ...
    progress_bar.update(1)  # ← Incrementa barra

# Finaliza com nova linha
progress_bar.close()
```

## Implementação Técnica

### Classe `SimpleProgressBar`:

```python
class SimpleProgressBar:
    """Simple progress bar without external dependencies."""

    def __init__(self, total: int, desc: str = "", width: int = 40):
        # total: número total de items
        # desc: prefixo (ex: "Downloading")
        # width: largura da barra em caracteres

    def update(self, amount: int = 1):
        # Incrementa progresso

    def close(self):
        # Finaliza e pula para próxima linha
```

## Por que Sem tqdm?

| Aspecto            | tqdm                      | SimpleProgressBar  |
| ------------------ | ------------------------- | ------------------ |
| **Tamanho**        | ~50KB                     | 0 bytes (built-in) |
| **Dependência**    | Sim (precisa instalar)    | Não (Python puro)  |
| **Funcionalidade** | Muito mais                | Simples e focado   |
| **Overhead**       | Médio                     | Mínimo             |
| **Filosofia**      | "Uma lib para cada coisa" | Minimalismo        |

**Decisão**: Para esta biblioteca, **menos é mais**. SimpleProgressBar é perfeito para o caso de uso.

## Exemplos de Uso

### Exemplo 1: Uso básico (automático)

```python
from src.presentation.cvm_docs import FundamentalStocksData

cvm = FundamentalStocksData()
result = cvm.download(
    destination_path="/data",
    doc_types=["DFP"],
    start_year=2020,
    end_year=2023
)
# Saída:
# Downloading [████████░░░░░░░░░░░░░░░░░░░░░░] 30/100 (30%)
```

### Exemplo 2: Customizar o adaptador

```python
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import ThreadPoolDownloadAdapter
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCase

adapter = ThreadPoolDownloadAdapter(max_workers=16)
use_case = DownloadDocumentsUseCase(adapter)
result = use_case.execute(
    destination_path="/data",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)
# Barra de progresso aparece automaticamente
```

### Exemplo 3: Com tratamento de erros

```python
from src.presentation.cvm_docs import FundamentalStocksData

cvm = FundamentalStocksData()
try:
    result = cvm.download(
        destination_path="/data",
        doc_types=["DFP"],
        start_year=2020,
        end_year=2023
    )
    # Saída com barra de progresso durante o download

    print(f"\nCompleted: {result.success_count}/{result.success_count + result.error_count}")
    if result.has_errors():
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
except Exception as e:
    print(f"Download failed: {e}")
```

## Comportamento Terminal

### Antes (sem barra):

```
# Sem feedback visual
[... esperar muito tempo ...]
Downloaded X files successfully
```

### Agora (com barra):

```
Downloading [██████░░░░░░░░░░░░░░░░░░░░░░░░░░] 10/50 (20%)
Downloading [████████████░░░░░░░░░░░░░░░░░░░░] 25/50 (50%)
Downloading [████████████████████░░░░░░░░░░░░] 40/50 (80%)
Downloading [████████████████████████████████] 50/50 (100%)
```

## Compatibilidade

- ✅ **Linux/macOS**: Funciona perfeitamente
- ✅ **Windows**: Funciona (pode ter suporte limitado a Unicode, fallback automático)
- ✅ **Jupyter/IPython**: Funciona (output em notebook)
- ✅ **CI/CD (GitHub Actions, etc)**: Funciona (safe para pipes)
- ✅ **Python 3.8+**: Totalmente compatível

## Performance

- ✅ **Overhead zero** quando `total=0`
- ✅ **Update O(1)** — incremento instantâneo
- ✅ **Print rate-limited** — não ficará louco com atualizações (bounded por I/O do terminal)

## Se Precisar de Mais Funcionalidades

Se no futuro precisar de features avançadas (ex: múltiplas barras, ETA detalhado, cores):

1. Considere adicionar `tqdm` então (é a escolha padrão da comunidade)
2. Ou expanda `SimpleProgressBar` conforme necessário

Mas por enquanto, **SimpleProgressBar é suficiente e mantém a biblioteca limpa!**

---

## Resumo

✅ **Barra de progresso implementada** — Sem dependências extras
✅ **Feedback visual** — Usuário vê o avanço do download
✅ **Código limpo** — Apenas Python puro
✅ **Performance** — Overhead mínimo

**Resultado**: Experiência muito melhor que antes, sem adicionar complexidade ou dependências! 🚀
