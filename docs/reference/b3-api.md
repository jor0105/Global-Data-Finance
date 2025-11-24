# API B3 - Referência Técnica

Documentação técnica detalhada da API B3.

---

## HistoricalQuotesB3

### Classe Principal

```python
class HistoricalQuotesB3:
    """Interface de alto nível para cotações B3."""
```

### Métodos

#### `extract()`

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

**Descrição**: Extrai cotações históricas de arquivos COTAHIST.

**Parâmetros**:

| Nome               | Tipo            | Obrigatório | Padrão                 | Descrição                   |
| ------------------ | --------------- | ----------- | ---------------------- | --------------------------- |
| `path_of_docs`     | `str`           | Sim         | -                      | Diretório com ZIPs COTAHIST |
| `assets_list`      | `List[str]`     | Sim         | -                      | Classes de ativos           |
| `initial_year`     | `Optional[int]` | Não         | `1986`                 | Ano inicial                 |
| `last_year`        | `Optional[int]` | Não         | Ano atual              | Ano final                   |
| `destination_path` | `Optional[str]` | Não         | `path_of_docs`         | Diretório de saída          |
| `output_filename`  | `str`           | Não         | `"cotahist_extracted"` | Nome do arquivo             |
| `processing_mode`  | `str`           | Não         | `"fast"`               | Modo: "fast" ou "slow"      |

**Retorno**: Dicionário com chaves:

- `success` (bool): Sucesso da operação
- `message` (str): Mensagem resumida
- `total_files` (int): Total de arquivos processados
- `success_count` (int): Arquivos com sucesso
- `error_count` (int): Arquivos com erro
- `total_records` (int): Total de registros extraídos
- `output_file` (str): Caminho do arquivo Parquet
- `errors` (List[str]): Lista de erros (se houver)

**Exceções**:

- `EmptyAssetListError`: Lista de ativos vazia
- `InvalidAssetsName`: Ativo inválido
- `InvalidFirstYear`: Ano inicial inválido
- `InvalidLastYear`: Ano final inválido
- `EmptyDirectoryError`: Diretório vazio
- `ExtractionError`: Erro na extração

**Exemplo**:

```python
b3 = HistoricalQuotesB3()
result = b3.extract(
    path_of_docs="/data/cotahist",
    assets_list=["ações", "etf"],
    initial_year=2022,
    last_year=2023,
    processing_mode="fast"
)
print(f"Extraídos {result['total_records']:,} registros")
```

#### `get_available_assets()`

```python
def get_available_assets(self) -> List[str]
```

**Descrição**: Retorna lista de classes de ativos disponíveis.

**Retorno**: Lista de strings

**Exemplo**:

```python
assets = b3.get_available_assets()
# ['ações', 'etf', 'opções', ...]
```

#### `get_available_years()`

```python
def get_available_years(self) -> Dict[str, int]
```

**Descrição**: Retorna intervalo de anos disponível.

**Retorno**: Dicionário com chaves:

- `"minimal_year"`: 1986
- `"current_year"`: Ano atual

**Exemplo**:

```python
years = b3.get_available_years()
# {'minimal_year': 1986, 'current_year': ano atual}
```

---

## Classes de Ativos

| Código           | Descrição           | Mercados                         |
| ---------------- | ------------------- | -------------------------------- |
| ações            | Ações               | 010 (à vista), 012 (fracionário) |
| etf              | ETFs                | Exchange Traded Funds            |
| opções           | Opções              | 070 (call), 080 (put)            |
| termo            | Mercado a Termo     | Contratos a termo                |
| exercicio_opcoes | Exercício de Opções | Exercício de opções              |
| forward          | Mercado Forward     | Contratos forward                |
| leilao           | Leilão              | Mercado de leilão                |

---

## Modos de Processamento

| Modo | Performance | CPU   | RAM    | Uso                                |
| ---- | ----------- | ----- | ------ | ---------------------------------- |
| fast | Alta        | Alto  | ~2GB   | Padrão, máquinas com bons recursos |
| slow | Moderada    | Baixo | ~500MB | Recursos limitados                 |

---

Veja também:

- [Guia de Uso B3](../user-guide/b3-docs.md)
- [Exceções](exceptions.md)
- [Formatos de Dados](data-formats.md)
