# Aria2c - Complete Guide for DataFinance Users

## O que é Aria2?

**Aria2** é um utilitário de linha de comando leve, multi-protocolo e multi-source para download de arquivos.

### Características principais:

- **Downloads paralelos**: Baixa múltiplos arquivos simultaneamente
- **Segmentação por arquivo**: Divide arquivos grandes em partes e baixa em paralelo
- **Multi-conexão**: Usa múltiplas conexões com o mesmo servidor
- **Resume/Continuação**: Pode retomar downloads incompletos
- **Eficiência**: Usa muito menos memória que navegadores
- **Protocolos**: Suporta HTTP/HTTPS, FTP, BitTorrent, Metalink
- **Retry automático**: Tenta novamente em caso de erro
- **Controle fino**: Opciones avançadas de configuração

### Comparação com wget/requests:

| Aspecto | wget | requests (ThreadPool) | aria2 |
|--------|------|----------------------|-------|
| Conexões por arquivo | 1 | 1 | N (paralelas) |
| Múltiplos arquivos | Sequencial | Paralelo (threads) | Paralelo (nativo) |
| Overhead de memória | Baixo | Médio | Baixo |
| Velocidade (muitos arquivos) | Lenta | Média | Muito rápida |
| Velocidade (arquivos grandes) | Lenta | Média | Muito rápida |
| Complexity | Baixa | Média | Média |
| Dependência | Binário | Python (built-in) | Binário externo |

---

## Instalação

### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install aria2
```

### Linux (Fedora/RHEL):
```bash
sudo dnf install aria2
```

### macOS:
```bash
brew install aria2
```

### Windows:
1. Baixe o instalador em: https://github.com/aria2/aria2/releases
2. Ou use Chocolatey: `choco install aria2`
3. Ou use Scoop: `scoop install aria2`

### Docker:
```bash
docker run -it aria2/aria2 aria2c --version
```

### Verificar instalação:
```bash
aria2c --version
```

---

## Como Usar aria2c via CLI

### Sintaxe básica:

#### Download simples:
```bash
aria2c "http://example.com/file.zip"
```

#### Download com opções:
```bash
aria2c \
  "http://example.com/file1.zip" \
  "http://example.com/file2.zip" \
  --dir=/path/to/dest \
  --max-concurrent-downloads=8 \
  --split=4 \
  --max-connection-per-server=4
```

#### Download de lista (arquivo com URLs):
```bash
# Criar arquivo urls.txt com uma URL por linha:
cat > urls.txt << EOF
http://example.com/file1.zip
http://example.com/file2.zip
http://example.com/file3.zip
EOF

# Baixar todos:
aria2c -i urls.txt --dir=/path/to/dest
```

### Opções principais:

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `-d, --dir` | Diretório de destino | `.` (atual) |
| `-i, --input-file` | Arquivo com lista de URLs | - |
| `--max-concurrent-downloads` | Max downloads simultâneos | 5 |
| `--max-connection-per-server` | Conexões por servidor | 1 |
| `--split` | Número de segmentos por arquivo | 5 |
| `--min-split-size` | Tamanho mínimo para segmentação | 20M |
| `--connect-timeout` | Timeout de conexão (segundos) | 60 |
| `--max-tries` | Tentativas máximas | 5 |
| `--retry-wait` | Espera entre tentativas (segundos) | 0 |
| `--continue` | Retomar downloads interrompidos | true |
| `--allow-overwrite` | Sobrescrever arquivos existentes | false |
| `--auto-file-renaming` | Renomear se existir | true |
| `--quiet` | Modo silencioso | false |
| `--show-console-readout` | Mostrar progresso | true |

### Exemplos práticos:

**1. Baixar 1000 arquivos em paralelo:**
```bash
aria2c -i urls.txt \
  -d /data/downloads \
  --max-concurrent-downloads=16 \
  --split=8 \
  --min-split-size=1M
```

**2. Baixar com retry agressivo:**
```bash
aria2c "http://unstable-server.com/file.zip" \
  --max-tries=10 \
  --retry-wait=5 \
  --connect-timeout=30
```

**3. Baixar com limite de bandwidth:**
```bash
aria2c \
  --dir=/data \
  --max-overall-download-limit=10M \
  --max-download-limit=5M \
  -i urls.txt
```

**4. Continuar download interrompido:**
```bash
# Primer comando (pode ser interrompido com Ctrl+C):
aria2c -i urls.txt --dir=/data

# Depois, para continuar:
aria2c -i urls.txt --dir=/data --continue
```

---

## Usando Aria2cAdapter em Python

### Importar e criar instância:

```python
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import Aria2cAdapter
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCase

# Criar adaptador com configuração padrão
adapter = Aria2cAdapter()

# Ou com configuração customizada
adapter = Aria2cAdapter(
    max_concurrent_downloads=16,  # 16 downloads simultâneos
    connections_per_server=8,  # 8 conexões por servidor
    min_split_size="500K",  # Splitar arquivos maiores que 500KB
    timeout=60,  # 60 segundos de timeout
    max_tries=5,  # Tentar até 5 vezes
    retry_wait=3  # Esperar 3 segundos entre tentativas
)
```

### Usar via use case:

```python
use_case = DownloadDocumentsUseCase(adapter)

result = use_case.execute(
    destination_path="/home/user/cvm_data",
    doc_types=["DFP", "ITR"],
    start_year=2020,
    end_year=2023
)

print(f"Downloaded: {result.success_count}")
print(f"Errors: {result.error_count}")
```

### Usar via FundamentalStocksData (com customização):

```python
from src.presentation.cvm_docs import FundamentalStocksData
from src.brazil.dados_cvm.fundamental_stocks_data.infra.adapters import Aria2cAdapter
from src.brazil.dados_cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCase

# Criar adapter customizado
aria2_adapter = Aria2cAdapter(max_concurrent_downloads=10)

# Criar use case com o adapter
download_use_case = DownloadDocumentsUseCase(aria2_adapter)

# Usar na biblioteca
from src.brazil.dados_cvm.fundamental_stocks_data.application.interfaces import DownloadDocsCVMRepository

# Nota: A classe FundamentalStocksData usa WgetDownloadAdapter por padrão.
# Para usar Aria2cAdapter, você precisaria estender FundamentalStocksData
# ou usar a use case diretamente:

result = download_use_case.execute(
    destination_path="/data/cvm",
    doc_types=["DFP"],
    start_year=2022,
    end_year=2023
)
```

---

## Monitoramento e Logging

### Ver progresso em tempo real:

```bash
aria2c -i urls.txt --show-console-readout=true
```

### Salvar log:

```bash
aria2c -i urls.txt --log="/var/log/aria2.log"
```

### Modo debug:

```bash
aria2c \
  -i urls.txt \
  --console-log-level=debug \
  --quiet=false
```

---

## Performance Tuning

### Para muitos arquivos pequenos (< 10MB):
```bash
aria2c -i urls.txt \
  --max-concurrent-downloads=32 \
  --split=2 \
  --min-split-size=5M
```

### Para alguns arquivos grandes (> 100MB):
```bash
aria2c -i urls.txt \
  --max-concurrent-downloads=4 \
  --split=16 \
  --min-split-size=1M \
  --max-connection-per-server=16
```

### Para servidores com limite de conexões:
```bash
aria2c -i urls.txt \
  --max-concurrent-downloads=2 \
  --max-connection-per-server=2 \
  --max-tries=10 \
  --retry-wait=5
```

### Para rede instável:
```bash
aria2c -i urls.txt \
  --connect-timeout=60 \
  --read-timeout=60 \
  --max-tries=20 \
  --retry-wait=10 \
  --low-speed-limit=1024 \
  --low-speed-time=120
```

---

## Troubleshooting

### Erro: "aria2c: command not found"
**Solução**: Instale aria2
```bash
# Ubuntu/Debian:
sudo apt-get install aria2

# Verifique:
aria2c --version
```

### Erro: "403 Forbidden" ou "401 Unauthorized"
**Possíveis causas**:
- URL expirada ou sem permissão
- Servidor bloqueando múltiplas conexões
- User-Agent bloqueado

**Soluções**:
```bash
aria2c \
  "http://example.com/file.zip" \
  --user-agent="Mozilla/5.0" \
  --max-concurrent-downloads=1 \
  --max-connection-per-server=1
```

### Erro: "Connection reset by peer"
**Causa**: Servidor rejeitando múltiplas conexões simultâneas
**Solução**:
```bash
aria2c \
  "http://example.com/file.zip" \
  --max-connection-per-server=1 \
  --max-tries=10
```

### Download muito lento
**Soluções**:
1. Aumentar workers: `--max-concurrent-downloads=16`
2. Aumentar split: `--split=8`
3. Verificar banda: `speedtest-cli` ou `iperf3`
4. Testar servidor diferente

### Download para após uns arquivos
**Causa**: Timeout ou limite de servidor
**Solução**:
```bash
aria2c -i urls.txt \
  --connect-timeout=60 \
  --read-timeout=60 \
  --max-tries=10 \
  --continue
```

---

## Comparação: ThreadPool vs Aria2c

### Quando usar ThreadPoolDownloadAdapter:
- ✅ Ambiente restrito (sem permissão para instalar)
- ✅ Arquivos pequenos/médios (< 100MB)
- ✅ Simplicidade é prioritária
- ✅ Não quer depender de binários externos
- ✅ Precisa de integração fácil em Python

### Quando usar Aria2cAdapter:
- ✅ Volumes muito grandes (1000+ arquivos)
- ✅ Arquivos grandes (> 100MB)
- ✅ Quer máxima velocidade
- ✅ Pode controlar dependências de sistema
- ✅ Precisa de multipart automático por arquivo
- ✅ Retoma downloads interrompidos

---

## Recursos Adicionais

- **Documentação oficial**: https://aria2.github.io/
- **GitHub**: https://github.com/aria2/aria2
- **Manual de opciones**: `man aria2c` (em Linux/Mac)
- **Opções avançadas**: https://aria2.github.io/manual/en/html/aria2c.html

---

## Resumo

| Aspecto | ThreadPool | Aria2c |
|--------|-----------|--------|
| **Facilidade de instalação** | ✅ Já incluso | ⚠️ Requer instalação |
| **Velocidade** | ✅ Boa | ✅✅ Excelente |
| **Multipart por arquivo** | ❌ Não | ✅ Sim |
| **Retoma downloads** | ⚠️ Parcial | ✅ Completo |
| **Integração Python** | ✅ Nativa | ✅ Via subprocess |
| **Portabilidade** | ✅ Alta | ⚠️ Requer binário |
| **Uso de memória** | ✅ Eficiente | ✅✅ Muito eficiente |
| **Controle fino** | ⚠️ Médio | ✅ Excelente |

**Recomendação**: Comece com **ThreadPool**. Se precisar de mais velocidade e puder instalar aria2, migre para **Aria2c**.
