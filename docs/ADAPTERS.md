# Download Adapters - Quick Reference

## Visão Geral

DataFinance oferece 3 adapters para download de documentos CVM, cada um otimizado para diferentes cenários:

| Adapter                       | Velocidade              | Facilidade   | Dependências | Melhor Para                        |
| ----------------------------- | ----------------------- | ------------ | ------------ | ---------------------------------- |
| **WgetDownloadAdapter**       | ⭐ Lenta                | ⭐⭐⭐ Fácil | wget         | Compatibilidade máxima             |
| **ThreadPoolDownloadAdapter** | ⭐⭐⭐ Rápida           | ⭐⭐⭐ Fácil | requests     | **Maioria dos casos** ✅           |
| **Aria2cAdapter**             | ⭐⭐⭐⭐⭐ Muito rápida | ⭐⭐ Médio   | aria2        | Máxima velocidade, muitos arquivos |

---

## 1. WgetDownloadAdapter (Original)

**Uso**: Download simples, uma por vez, com retry básico.

```python
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import WgetDownloadAdapter

adapter = WgetDownloadAdapter()
result = adapter.download_docs("/path", {"DFP": ["url1", "url2"]})
```

**Prós**:

- ✅ Simples
- ✅ Nenhuma dependência Python extra (wget é padrão em Linux)
- ✅ Comportamento previsível

**Contras**:

- ❌ Lento (sequencial)
- ❌ Sem multipart
- ❌ Sem paralelismo

**Quando usar**: Raramente. Considere ThreadPool ao invés.

---

## 2. ThreadPoolDownloadAdapter (Recomendado) ⭐

**Uso**: Padrão para FundamentalStocksData. Rápido, portável, sem dependências externas.

### Uso simples (padrão):

```python
from src.presentation.cvm_docs import FundamentalStocksData

cvm = FundamentalStocksData()  # Usa ThreadPool internamente
result = cvm.download(
    destination_path="/data",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)
```

### Configuração customizada:

```python
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import ThreadPoolDownloadAdapter
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCase

adapter = ThreadPoolDownloadAdapter(
    max_workers=16,  # Número de threads paralelas
    chunk_size=8192,  # Tamanho dos chunks para streaming
    timeout=30,  # Timeout em segundos
    max_retries=3,  # Tentativas antes de falhar
    initial_backoff=1.0,  # Backoff inicial em segundos
    max_backoff=60.0  # Backoff máximo
)

use_case = DownloadDocumentsUseCase(adapter)
result = use_case.execute(
    destination_path="/data",
    doc_types=["DFP"],
    start_year=2020,
    end_year=2023
)
```

**Prós**:

- ✅ Rápido (8x mais rápido que wget tipicamente)
- ✅ Fácil de configurar
- ✅ Sem dependências externas
- ✅ Retries automáticos com backoff exponencial
- ✅ Streaming eficiente (baixa memória)
- ✅ Compatível com qualquer servidor HTTP

**Contras**:

- ❌ Sem multipart por arquivo (cada arquivo é uma conexão)
- ⚠️ Usa threads (overhead comparado a async)

**Parametros importantes**:

- `max_workers`: 4-16 (mais alto = mais rápido, mas mais carga no servidor)
- `timeout`: 30-60 segundos (depende da rede)
- `max_retries`: 3-5 (mais tentativas em redes instáveis)

**Quando usar**: ✅ **Quase sempre este!**

---

## 3. Aria2cAdapter (Máxima Velocidade)

**Uso**: Volumes muito grandes, arquivos grandes, quando pode instalar aria2.

### Instalação de aria2:

**Ubuntu/Debian**:

```bash
sudo apt-get install aria2
```

**macOS**:

```bash
brew install aria2
```

**Windows**:

- Download: https://github.com/aria2/aria2/releases
- Ou: `choco install aria2`

**Verificar**:

```bash
aria2c --version
```

### Uso simples:

```python
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import Aria2cAdapter
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCase

adapter = Aria2cAdapter()
use_case = DownloadDocumentsUseCase(adapter)
result = use_case.execute(
    destination_path="/data",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)
```

### Configuração customizada:

```python
adapter = Aria2cAdapter(
    max_concurrent_downloads=8,  # Downloads simultâneos
    connections_per_server=4,  # Conexões por servidor
    min_split_size="1M",  # Split files > 1MB
    timeout=300,  # Timeout em segundos (5 min)
    max_tries=5,  # Tentativas
    retry_wait=3  # Espera entre tentativas
)
```

**Prós**:

- ✅ Muito rápido (2-10x mais rápido que ThreadPool em casos ideais)
- ✅ Multipart por arquivo (divide grandes files)
- ✅ Retoma downloads interrompidos
- ✅ Excelente para muitos arquivos (1000+)
- ✅ Controle fino sobre paralelismo

**Contras**:

- ❌ Requer instalação de aria2
- ❌ Não é puro Python (subprocess)
- ⚠️ Mais complexo de configurar

**Quando usar**:

- ✅ Volumes muitos grandes (1000+ arquivos)
- ✅ Arquivos muito grandes (> 500MB)
- ✅ Máxima velocidade é crítica
- ✅ Pode controlar dependências de sistema

**Ver mais**: [ARIA2_GUIDE.md](./ARIA2_GUIDE.md) para detalhes completos.

---

## Escolher o Melhor Adapter

```
Qual é seu caso?
│
├─ "Quero o mais rápido com mínimo esforço"
│  └─> ThreadPoolDownloadAdapter ⭐ RECOMENDADO
│
├─ "Tenho 10.000+ arquivos ou arquivos muito grandes"
│  ├─ "Posso instalar aria2"
│  │  └─> Aria2cAdapter 🚀
│  └─ "Não posso instalar dependencies"
│     └─> ThreadPoolDownloadAdapter com max_workers=16
│
├─ "Preciso de máxima compatibilidade"
│  └─> WgetDownloadAdapter (mas considere ThreadPool)
│
└─ "Estou desenvolvendo/testando"
   └─> ThreadPoolDownloadAdapter (mais previsível)
```

---

## Performance Típica

Downloading 50 DFP files (~500MB total) da CVM em conexão de 10Mbps:

| Adapter                     | Tempo   | Comentário        |
| --------------------------- | ------- | ----------------- |
| wget                        | 10 min  | Sequencial, lento |
| ThreadPool (4 workers)      | 3-4 min | 2.5x mais rápido  |
| ThreadPool (8 workers)      | 2-3 min | 3-5x mais rápido  |
| aria2c (8 conexões)         | 1-2 min | 5-10x mais rápido |
| aria2c (16 conexões, split) | 1 min   | 10x mais rápido   |

**Nota**: Resultados dependem de:

- Velocidade da conexão
- Tamanho dos arquivos
- Servidor (limite de conexões)
- CPU disponível

---

## Exemplos Rápidos

### Exemplo 1: Download básico (padrão)

```python
from src.presentation.cvm_docs import FundamentalStocksData

cvm = FundamentalStocksData()
result = cvm.download(
    destination_path="/home/user/cvm_data",
    doc_types=["DFP"],
    start_year=2020,
    end_year=2023
)
print(f"Downloaded: {result.success_count}")
```

### Exemplo 2: ThreadPool customizado

```python
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import ThreadPoolDownloadAdapter
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCase

adapter = ThreadPoolDownloadAdapter(max_workers=16, timeout=60)
use_case = DownloadDocumentsUseCase(adapter)
result = use_case.execute(
    destination_path="/data",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)
```

### Exemplo 3: Aria2c (máxima velocidade)

```python
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import Aria2cAdapter
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCase

try:
    adapter = Aria2cAdapter(max_concurrent_downloads=16)
    use_case = DownloadDocumentsUseCase(adapter)
    result = use_case.execute(
        destination_path="/data",
        doc_types=["DFP", "ITR"],
        start_year=2020,
        end_year=2023
    )
except RuntimeError as e:
    print(f"aria2c não disponível: {e}")
    # Fallback para ThreadPool
```

### Exemplo 4: Tratamento de erros

```python
result = cvm.download(
    destination_path="/data",
    doc_types=["DFP"],
    start_year=2020,
    end_year=2023
)

if result.has_errors():
    print(f"Erros: {result.error_count}")
    for error in result.errors:
        print(f"  - {error}")

if result.has_successes():
    print(f"Sucesso: {result.success_count}")
    for doc_type, year in result.successful_downloads:
        print(f"  - {doc_type} {year}")
```

---

## Troubleshooting

### ThreadPool é lento

- **Solução**: Aumente `max_workers` (ex: 16, 32)
- **Cuidado**: Servidores podem bloquear muitas conexões

### aria2c não encontrado

```bash
# Instale:
sudo apt-get install aria2  # Linux
brew install aria2  # macOS

# Verifique:
aria2c --version
```

### Download fails com "connection timeout"

- **ThreadPool**: Aumente `timeout` (ex: 60 ao invés de 30)
- **aria2c**: Use `--connect-timeout=60`

### Muitos erros "connection refused"

- **Causa**: Servidor bloqueando múltiplas conexões
- **Solução**: Reduzir `max_workers` ou `connections_per_server` para 1-2

---

## Próximos Passos

1. **Comece com**: ThreadPoolDownloadAdapter (default em FundamentalStocksData)
2. **Se lento**: Aumente `max_workers` para 16-32
3. **Se muito lento**: Instale aria2 e teste Aria2cAdapter
4. **Benchmark**: Veja `examples/adapter_examples.py`

---

## Mais Informações

- **Exemplos completos**: [examples/adapter_examples.py](../examples/adapter_examples.py)
- **Guia aria2**: [docs/ARIA2_GUIDE.md](./ARIA2_GUIDE.md)
- **Source**: [src/brazil/dados_cvm/fundamental_stocks_data/infra/adapters/](../src/brazil/dados_cvm/fundamental_stocks_data/infra/adapters/)
