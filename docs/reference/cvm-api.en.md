# CVM API - Technical Specification

Detailed technical specification governing the CVM corporate disclosure API.

---

## FundamentalStocksDataCVM

### Primary Class Definition

```python
class FundamentalStocksDataCVM:
    """High-level facade for CVM financial statement ingestion."""
```

### Public Methods

#### `download()`

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

**Description**: Downloads official CVM disclosure packages into a targeted filesystem directory.

**Parameters**:

| Parameter             | Type                  | Required | Default | Description                              |
| --------------------- | --------------------- | -------- | ------- | ---------------------------------------- |
| `destination_path`    | `str`                 | Yes      | -       | Target local filesystem output folder    |
| `list_docs`           | `Optional[List[str]]` | No       | `None`  | Targeted document codes (None = fetch all)|
| `initial_year`        | `Optional[int]`       | No       | `None`  | Starting year (None = earliest available)|
| `last_year`           | `Optional[int]`       | No       | `None`  | Ending fiscal year (None = current year) |
| `automatic_extractor` | `bool`                | No       | `False` | Automatically convert to Parquet files   |

**Raised Exceptions**:

- `InvalidDocumentName`: Supplied document code string falls outside whitelist
- `InvalidFirstYear`: Requested initial year below historic floor or above upper boundaries
- `InvalidLastYear`: Ending year preceded initial year or surpassed active year limits
- `NetworkError`: HTTP communication or TLS handshake connection loss encountered
- `TimeoutError`: Socket read timeout reached while communicating with servers
- `InvalidDestinationPathError`: Destination filesystem directory access blocked or restricted

**Execution Example**:

```python
cvm = FundamentalStocksDataCVM()
cvm.download(
    destination_path="/data/cvm",
    list_docs=["DFP", "ITR"],
    initial_year=2022,
    last_year=2023,
    automatic_extractor=True
)
```

#### `get_available_docs()`

```python
def get_available_docs(self) -> Dict[str, str]
```

**Description**: Retrieves mapping catalog connecting short acronym codes to full Portuguese administrative descriptions.

**Return Structure**: Dictionary `{acronym_code: full_legal_title}`

**Execution Example**:

```python
docs = cvm.get_available_docs()
# Returns: {'DFP': 'Demonstração Financeira Padronizada', ...}
```

#### `get_available_years()`

```python
def get_available_years(self) -> Dict[str, int]
```

**Description**: Queries structural historical year boundary metrics across supported filing categories.

**Return Structure**: Dictionary featuring the following keys:

- `"General Document Years"`: Earliest year for general accounting forms (2010)
- `"ITR Document Years"`: Earliest year for interim quarterly reports (2011)
- `"CGVN and VMLO Document Years"`: Earliest year for governance disclosures (2018)
- `"Current Year"`: Real-time operational system year limit

**Execution Example**:

```python
years = cvm.get_available_years()
# Returns: {'General Document Years': 2010, 'ITR Document Years': 2011, ...}
```

---

## Supported Document Classifications

| Acronym Code | Complete Legal Title                  | Available Since |
| ------------ | ------------------------------------- | --------------- |
| DFP          | Demonstração Financeira Padronizada   | 2010            |
| ITR          | Informação Trimestral                 | 2011            |
| FRE          | Formulário de Referência              | 2010            |
| FCA          | Formulário Cadastral                  | 2010            |
| CGVN         | Código de Governança                  | 2018            |
| VLMO         | Valores Mobiliários                   | 2018            |
| IPE          | Informações Periódicas e Eventuais    | 2010            |

---

## Related Documentation

- [CVM User Guide](../user-guide/cvm-docs.md)
- [Exception Hierarchy](exceptions.md)
