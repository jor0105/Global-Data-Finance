# Instalação

Este guia fornece instruções detalhadas para instalar e configurar a biblioteca **Global-Data-Finance** em diferentes ambientes.

---

## Requisitos do Sistema

Antes de instalar o Global-Data-Finance, certifique-se de que seu sistema atende aos seguintes requisitos:

### Requisitos Obrigatórios

- **Python**: Versão 3.12 ou superior
- **Sistema Operacional**: Linux, macOS ou Windows
- **Espaço em Disco**: Mínimo de 2 GB para conseguir baixar todos os dados
- **Memória RAM**: Mínimo de 3 GB (recomendado 6 GB ou mais para grandes volumes)

### Verificar Versão do Python

```bash
python --version
# ou
python3 --version
```

!!! warning "Versão do Python"
O Global-Data-Finance requer Python 3.12 ou superior. Se você possui uma versão anterior, será necessário atualizar o Python antes de prosseguir.

---

## Instalação via pip (Recomendado)

A forma mais simples de instalar o Global-Data-Finance é através do PyPI usando o `pip`:

```bash
pip install globaldatafinance
```

### Instalação em Ambiente Virtual (Recomendado)

É altamente recomendado instalar o Global-Data-Finance em um ambiente virtual para evitar conflitos de dependências:

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Linux/macOS:
source venv/bin/activate

# No Windows:
venv\Scripts\activate

# Instalar Global-Data-Finance
pip install globaldatafinance
```

### Atualizar para Última Versão

```bash
pip install --upgrade globaldatafinance
```

---

## Instalação via Poetry

Se você usa Poetry para gerenciamento de dependências:

```bash
# Adicionar ao projeto
poetry add globaldatafinance

# Ou instalar em modo desenvolvimento
poetry add --group dev globaldatafinance
```

---

## Instalação para Desenvolvimento

Se você deseja contribuir com o projeto ou modificar o código-fonte:

### 1. Clonar o Repositório

```bash
git clone https://github.com/jor0105/Global-Data-Finance.git
cd Global-Data-Finance
```

### 2. Instalar com Poetry (Recomendado)

```bash
# Instalar todas as dependências (incluindo dev)
poetry install

# Ativar ambiente virtual do Poetry
poetry shell
```

### 3. Instalar com pip em Modo Editável

```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Instalar em modo editável
pip install -e .

# Instalar dependências de desenvolvimento
pip install -e ".[dev]"
```

---

## Dependências

O Global-Data-Finance possui as seguintes dependências principais:

### Dependências Obrigatórias

| Biblioteca          | Versão  | Descrição                                  |
| ------------------- | ------- | ------------------------------------------ |
| `httpx`             | ≥0.28.1 | Cliente HTTP assíncrono com suporte HTTP/2 |
| `pandas`            | ≥2.3.3  | Manipulação e análise de dados             |
| `polars`            | ≥1.0.0  | Processamento de dados de alto desempenho  |
| `pyarrow`           | ≥22.0.0 | Suporte para formato Apache Parquet        |
| `pydantic-settings` | ≥2.11.0 | Configuração e validação de dados          |
| `psutil`            | ≥5.9.0  | Utilitários de sistema e processos         |

### Dependências de Desenvolvimento (Opcionais)

Instaladas automaticamente apenas em modo desenvolvimento:

| Biblioteca        | Descrição                      |
| ----------------- | ------------------------------ |
| `pytest`          | Framework de testes            |
| `pytest-cov`      | Cobertura de testes            |
| `pytest-asyncio`  | Suporte a testes assíncronos   |
| `mypy`            | Verificação de tipos estáticos |
| `pre-commit`      | Hooks de pré-commit            |
| `mkdocs`          | Gerador de documentação        |
| `mkdocs-material` | Tema Material para MkDocs      |

---

## Verificação da Instalação

Após a instalação, verifique se tudo está funcionando corretamente:

### 1. Verificar Importação

```python
# Abrir Python interativo
python

# Tentar importar a biblioteca
>>> from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3
>>> print("✓ Global-Data-Finance instalado com sucesso!")
```

### 2. Verificar Versão

```python
>>> import globaldatafinance
>>> print(globaldatafinance.__version__)
0.1.0
```

### 3. Teste Básico

```python
from globaldatafinance import FundamentalStocksDataCVM

# Criar instância
cvm = FundamentalStocksDataCVM()

# Verificar documentos disponíveis
docs = cvm.get_available_docs()
print(f"✓ Encontrados {len(docs)} tipos de documentos disponíveis")

# Verificar anos disponíveis
years = cvm.get_available_years()
print(f"✓ Dados disponíveis de {years['General Document Years']} até {years['Current Year']}")
```

Se todos os comandos acima executarem sem erros, a instalação foi bem-sucedida! ✅

---

## Solução de Problemas

### Erro: "No module named 'globaldatafinance'"

**Causa**: A biblioteca não foi instalada corretamente ou o ambiente virtual não está ativado.

**Solução**:

```bash
# Verificar se está no ambiente virtual correto
which python  # Linux/macOS
where python  # Windows

# Reinstalar a biblioteca
pip install --force-reinstall globaldatafinance
```

### Erro: "Python version 3.12 or higher required"

**Causa**: Versão do Python é anterior a 3.12.

**Solução**:

1. Instale Python 3.12 ou superior do [site oficial](https://www.python.org/downloads/)
2. Crie um novo ambiente virtual com a versão correta:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install globaldatafinance
```

### Erro de Dependências

**Causa**: Conflito com outras bibliotecas instaladas.

**Solução**:

```bash
# Criar ambiente virtual limpo
python -m venv venv_clean
source venv_clean/bin/activate
pip install globaldatafinance
```

### Erro de Permissão (Linux/macOS)

**Causa**: Tentativa de instalação sem permissões adequadas.

**Solução**:

```bash
# NÃO use sudo pip install!
# Em vez disso, use ambiente virtual:
python -m venv venv
source venv/bin/activate
pip install globaldatafinance
```

### Problemas com Proxy Corporativo

Se você está atrás de um proxy corporativo:

```bash
# Configurar proxy
export HTTP_PROXY="http://proxy.empresa.com:8080"
export HTTPS_PROXY="http://proxy.empresa.com:8080"

# Instalar com pip
pip install globaldatafinance
```

---

## Desinstalação

Para remover o Global-Data-Finance do seu sistema:

```bash
pip uninstall globaldatafinance
```

---

## Próximos Passos

Agora que você instalou o Global-Data-Finance com sucesso, explore:

- 🚀 **[Início Rápido](quickstart.md)** - Primeiros passos e exemplos básicos
- 📄 **[Documentos CVM](cvm-docs.md)** - Guia completo da API CVM
- 📈 **[Cotações B3](b3-docs.md)** - Guia completo da API B3
- 💻 **[Exemplos Práticos](examples.md)** - Casos de uso reais

---

!!! tip "Dica para Desenvolvedores"
Se você planeja contribuir com o projeto, consulte o [Guia de Contribuição](../dev-guide/contributing.md) para configurar seu ambiente de desenvolvimento completo.
