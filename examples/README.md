# Exemplos de Uso - GlobalDataFinance

Esta pasta contém exemplos práticos executáveis para iniciar rapidamente a extração e o processamento de dados financeiros brasileiros usando a biblioteca `globaldatafinance`.

---

## 📌 Diferença Entre as Fontes

- **CVM (`FundamentalStocksDataCVM`)**: Realiza o **download automático** (via HTTP assíncrono) das Demonstrações Financeiras diretamente dos servidores da CVM e converte em arquivos Parquet.
- **B3 (`HistoricalQuotesB3`)**: Faz a **leitura, filtragem e conversão** de arquivos oficiais de cotações históricas (`COTAHIST_AYYYY.ZIP` ou `.TXT`) armazenados em uma pasta local (`path_of_docs`) e consolida em Parquet. *(Nota: A biblioteca não baixa os arquivos COTAHIST da B3, ela processa os arquivos locais existentes).*

---

## 🚀 Como Executar os Exemplos

Todos os exemplos utilizam a ferramenta `uv` para gerenciar dependências e o ambiente virtual de forma rápida e reprodutível.

### 1. Início Rápido com CVM (`01_quickstart_cvm.py`)
Baixa as Demonstrações Financeiras Padronizadas (**DFP**) da CVM do ano de 2023 diretamente da internet e converte automaticamente em arquivos Parquet.

```bash
uv run python examples/01_quickstart_cvm.py
```

---

### 2. Extração Rápida de Ações da B3 (`02_quickstart_b3.py`)
Lê os arquivos de cotações históricas da B3 (**COTAHIST**) presentes na pasta local `./cotahist_b3`, filtra apenas os negócios com **Ações** e gera um arquivo Parquet consolidado.

```bash
uv run python examples/02_quickstart_b3.py
```

---

### 3. Extração Avançada da B3 (`03_opcoes_avancadas_b3.py`)
Demonstra a extração de múltiplos ativos simultâneos (**Ações, ETFs e FIIs**) a partir dos arquivos COTAHIST locais de 2022 e 2023, utilizando o **modo de alto desempenho (`processing_mode="fast"`)**.

```bash
uv run python examples/03_opcoes_avancadas_b3.py
```

---

## 📁 Estrutura dos Arquivos de Saída

Por padrão, os exemplos salvam os dados em formato **Parquet** (ideal para integração com **Polars**, **Pandas** e **PyArrow**):

- `./dados_cvm/`: Contém os arquivos `.parquet` por tipo de relatório da CVM.
- `./dados_b3/`: Contém os arquivos Parquet consolidados com o nome especificado em `output_filename`.

---

## 🔍 Scripts de Validação Interna e Superfície de API

Além dos tutoriais acima, a pasta também contém scripts utilitários de validação interna:

- `smoke_cvm.py`: Teste de fumaça síncrono/assíncrono da CVM.
- `smoke_b3.py`: Teste de fumaça dos motores de extração `fast` e `slow` da B3 (usando fixtures/amostras locais).
- `capture_api_surface.py`: Captura determinística da superfície pública exportada pela biblioteca.

---

## 📚 Mais Documentação

Para acessar a documentação completa da biblioteca e parâmetros avançados:
- [Guia do Usuário CVM](../docs/user-guide/cvm-docs.md)
- [Guia do Usuário B3](../docs/user-guide/b3-docs.md)
- [Exemplos Detalhados na Doc](../docs/user-guide/examples.md)
