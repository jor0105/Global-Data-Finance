# Exceções

Catálogo completo de exceções do Global-Data-Finance.

______________________________________________________________________

## Exceções Globais (`macro_exceptions`)

### `NetworkError`

```python
class NetworkError(Exception):
    """Erro de rede durante download."""
```

**Quando ocorre**: Problemas de conexão HTTP

**Como tratar**:

```python
try:
    cvm.download(...)
except NetworkError as e:
    print(f"Erro de rede: {e}")
    # Verificar conexão e tentar novamente
```

### `TimeoutError`

```python
class TimeoutError(Exception):
    """Timeout em requisição."""
```

**Quando ocorre**: Requisição excede tempo limite

### `ExtractionError`

```python
class ExtractionError(Exception):
    """Erro ao extrair arquivo."""
```

**Quando ocorre**: Falha ao extrair ZIP ou processar dados

### `EmptyDirectoryError`

```python
class EmptyDirectoryError(Exception):
    """Diretório vazio ou sem arquivos esperados."""
```

**Quando ocorre**: Diretório não contém arquivos necessários

### `InvalidDestinationPathError`

```python
class InvalidDestinationPathError(ValueError):
    """Caminho de destino inválido."""
```

**Quando ocorre**: Caminho não existe ou sem permissões

### `DiskFullError`

```python
class DiskFullError(OSError):
    """Disco cheio."""
```

**Quando ocorre**: Espaço insuficiente em disco

### `SecurityError`

```python
class SecurityError(Exception):
    """Violação de segurança."""
```

**Quando ocorre**: Tentativa de acesso não autorizado

______________________________________________________________________

## Exceções CVM

### `InvalidDocumentName`

```python
class InvalidDocumentName(Exception):
    """Tipo de documento inválido."""
```

**Quando ocorre**: Documento não está na lista de disponíveis

**Como tratar**:

```python
try:
    cvm.download(list_docs=["INVALID"])
except InvalidDocumentName:
    docs = cvm.get_available_docs()
    print(f"Documentos válidos: {list(docs.keys())}")
```

### `InvalidFirstYear`

```python
class InvalidFirstYear(Exception):
    """Ano inicial inválido."""
```

**Quando ocorre**: Ano < mínimo ou > atual

### `InvalidLastYear`

```python
class InvalidLastYear(Exception):
    """Ano final inválido."""
```

**Quando ocorre**: Ano < initial_year ou > atual

### `EmptyDocumentListError`

```python
class EmptyDocumentListError(Exception):
    """Lista de documentos vazia."""
```

**Quando ocorre**: `list_docs` é lista vazia

______________________________________________________________________

## Exceções B3

### `InvalidAssetsName`

```python
class InvalidAssetsName(Exception):
    """Classe de ativo inválida."""
```

**Quando ocorre**: Ativo não está na lista de disponíveis

**Como tratar**:

```python
try:
    b3.extract(assets_list=["invalid"])
except InvalidAssetsName:
    assets = b3.get_available_assets()
    print(f"Ativos válidos: {assets}")
```

### `EmptyAssetListError`

```python
class EmptyAssetListError(Exception):
    """Lista de ativos vazia."""
```

**Quando ocorre**: `assets_list` é lista vazia

______________________________________________________________________

## Hierarquia de Exceções

```
Exception
├── NetworkError
├── TimeoutError
├── ExtractionError
│   └── CorruptedZipError
├── SecurityError
├── InvalidDocumentName
├── InvalidFirstYear
├── InvalidLastYear
├── InvalidAssetsName
├── EmptyAssetListError
├── EmptyDocumentListError
└── EmptyDirectoryError

ValueError
└── InvalidDestinationPathError

OSError
└── DiskFullError
```

______________________________________________________________________

## Exemplo de Tratamento Completo

```python
from globaldatafinance import FundamentalStocksDataCVM
from globaldatafinance.brazil.cvm.fundamental_stocks_data.errors import (
    InvalidDocumentName,
    InvalidFirstYear,
    InvalidLastYear,
)
from globaldatafinance.macro_exceptions import (
    NetworkError,
    TimeoutError,
    DiskFullError,
)

cvm = FundamentalStocksDataCVM()

try:
    cvm.download(
        destination_path="/data/cvm",
        list_docs=["DFP"],
        initial_year=2022
    )
except InvalidDocumentName as e:
    print(f"Documento inválido: {e}")
except InvalidFirstYear as e:
    print(f"Ano inválido: {e}")
except NetworkError as e:
    print(f"Erro de rede: {e}")
except TimeoutError as e:
    print(f"Timeout: {e}")
except DiskFullError as e:
    print(f"Disco cheio: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
```

> Exceções específicas de cada fonte vivem em `errors.py` dentro da própria fonte (ex.: `brazil.cvm.fundamental_stocks_data.errors`, `brazil.b3_data.historical_quotes.errors`).

______________________________________________________________________

Veja também:

- [API CVM](cvm-api.md)
- [API B3](b3-api.md)
- [FAQ](../user-guide/faq.md)
