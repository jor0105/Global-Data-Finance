# API CVM - Referência Técnica

Documentação técnica detalhada da API CVM.

---

## FundamentalStocksDataCVM

### Classe Principal

```python
class FundamentalStocksDataCVM:
    """Interface de alto nível para documentos CVM."""
```

### Métodos

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

**Descrição**: Baixa documentos CVM para diretório especificado.

**Parâmetros**:

| Nome                  | Tipo                  | Obrigatório | Padrão  | Descrição                              |
| --------------------- | --------------------- | ----------- | ------- | -------------------------------------- |
| `destination_path`    | `str`                 | Sim         | -       | Diretório de destino                   |
| `list_docs`           | `Optional[List[str]]` | Não         | `None`  | Tipos de documentos (None = todos)     |
| `initial_year`        | `Optional[int]`       | Não         | `None`  | Ano inicial (None = mínimo disponível) |
| `last_year`           | `Optional[int]`       | Não         | `None`  | Ano final (None = ano atual)           |
| `automatic_extractor` | `bool`                | Não         | `False` | Extrair para Parquet                   |

**Exceções**:

- `InvalidDocName`: Tipo de documento inválido
- `InvalidFirstYear`: Ano inicial inválido
- `InvalidLastYear`: Ano final inválido
- `NetworkError`: Erro de rede
- `TimeoutError`: Timeout
- `InvalidDestinationPathError`: Caminho inválido

**Exemplo**:

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

**Descrição**: Retorna mapeamento de códigos para descrições de documentos.

**Retorno**: Dicionário `{código: descrição}`

**Exemplo**:

```python
docs = cvm.get_available_docs()
# {'DFP': 'Demonstração Financeira Padronizada', ...}
```

#### `get_available_years()`

```python
def get_available_years(self) -> Dict[str, int]
```

**Descrição**: Retorna informações sobre anos disponíveis.

**Retorno**: Dicionário com chaves:

- `"General Document Years"`: Ano mínimo para docs gerais (2010)
- `"ITR Document Years"`: Ano mínimo para ITR (2011)
- `"CGVN and VMLO Document Years"`: Ano mínimo para CGVN/VLMO (2018)
- `"Current Year"`: Ano atual

**Exemplo**:

```python
years = cvm.get_available_years()
# {'General Document Years': 2010, 'ITR Document Years': 2011, ...}
```

---

## Tipos de Documentos

| Código | Nome Completo                       | Desde |
| ------ | ----------------------------------- | ----- |
| DFP    | Demonstração Financeira Padronizada | 2010  |
| ITR    | Informação Trimestral               | 2011  |
| FRE    | Formulário de Referência            | 2010  |
| FCA    | Formulário Cadastral                | 2010  |
| CGVN   | Código de Governança                | 2018  |
| VLMO   | Valores Mobiliários                 | 2018  |
| IPE    | Informações Periódicas e Eventuais  | 2010  |

---

Veja também:

- [Guia de Uso CVM](../user-guide/cvm-docs.md)
- [Exceções](exceptions.md)
