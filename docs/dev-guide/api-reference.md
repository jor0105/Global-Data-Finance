# Referência da API

Documentação completa da API pública do Global-Data-Finance.

---

## Módulo `datafinance.brazil`

### `FundamentalStocksDataCVM`

Interface para download de documentos CVM.

#### Métodos

**`__init__()`**

```python
def __init__(self) -> None
```

Inicializa o cliente CVM com configurações padrão.

**`download()`**

```python
def download(
    self,
    destination_path: str,
    list_docs: Optional[List[str]] = None,
    initial_year: Optional[int] = None,
    last_year: Optional[int] = None,
    automatic_extractor: bool = False,
) -> None
```

Baixa documentos CVM.

**Parâmetros**:

- `destination_path` (str): Diretório de destino
- `list_docs` (List[str], opcional): Tipos de documentos
- `initial_year` (int, opcional): Ano inicial
- `last_year` (int, opcional): Ano final
- `automatic_extractor` (bool): Extrair para Parquet

**`get_available_docs()`**

```python
def get_available_docs(self) -> Dict[str, str]
```

Retorna tipos de documentos disponíveis.

**`get_available_years()`**

```python
def get_available_years(self) -> Dict[str, int]
```

Retorna informações sobre anos disponíveis.

---

### `HistoricalQuotesB3`

Interface para extração de cotações B3.

#### Métodos

**`__init__()`**

```python
def __init__(self) -> None
```

Inicializa o cliente B3.

**`extract()`**

```python
def extract(
    self,
    path_of_docs: str,
    assets_list: List[str],
    initial_year: Optional[int] = None,
    last_year: Optional[int] = None,
    destination_path: Optional[str] = None,
    output_filename: str = "cotahist_extracted",
    processing_mode: str = "fast",
) -> Dict[str, Any]
```

Extrai cotações históricas.

**Parâmetros**:

- `path_of_docs` (str): Diretório com ZIPs COTAHIST
- `assets_list` (List[str]): Classes de ativos
- `initial_year` (int, opcional): Ano inicial
- `last_year` (int, opcional): Ano final
- `destination_path` (str, opcional): Diretório de saída
- `output_filename` (str): Nome do arquivo
- `processing_mode` (str): "fast" ou "slow"

**Retorno**: Dicionário com chaves `success`, `total_records`, `output_file`, etc.

**`get_available_assets()`**

```python
def get_available_assets(self) -> List[str]
```

Retorna classes de ativos disponíveis.

**`get_available_years()`**

```python
def get_available_years(self) -> Dict[str, int]
```

Retorna intervalo de anos disponível.

---


Veja também:

- [API CVM](../reference/cvm-api.md) - Detalhes técnicos da API CVM
- [API B3](../reference/b3-api.md) - Detalhes técnicos da API B3
