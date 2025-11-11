# Guia de Processamento: Arquivos COTAHIST (Historical Quotes B3)

Este guia detalha a estrutura do arquivo `COTAHIST.AAAA.TXT`, com base no layout oficial da B3. O objetivo é fornecer as especificações necessárias para construir um parser em Python e preparar os dados para análise, inclusive por uma IA.

O arquivo é um **texto de largura fixa**, com cada linha possuindo **245 bytes**.

---

## 1. Estrutura Geral do Arquivo

O arquivo é composto por três tipos de registros (linhas), identificados pelos dois primeiros caracteres de cada linha:

* **Registro `00` - Header:** A primeira linha do arquivo. Contém metadados como nome do arquivo e data de geração.
* **Registro `01` - Cotações:** O corpo principal do arquivo. Cada linha representa os dados de negociação de um único papel (ativo) em um determinado dia. **Este é o foco da sua extração.**
* **Registro `99` - Trailer (Rodapé):** A última linha do arquivo. Contém um resumo, como o número total de registros (linhas) no arquivo.

Seu script Python deve ler o arquivo linha por linha e, primeiramente, verificar o campo `TIPREG` (posições 1-2) para decidir qual lógica de parsing aplicar (Header, Cotação ou Trailer).

---

## 2. Layout do Registro 01 (Dados de Cotação)

Este é o registro mais importante. A tabela abaixo detalha os campos-chave que você precisará extrair de cada linha do tipo `01`.

| Campo (Field) | Pos. Inicial | Pos. Final | Tam. | Tipo (Formato) | Descrição |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `TIPREG` | 01 | 02 | 2 | $N(02)$ | Fixo "01" |
| `DATA DO PREGÃO` | 03 | 10 | 8 | $N(08)$ | Data (YYYYMMDD) |
| `CODBDI` | 11 | 12 | 2 | $X(02)$ | Código BDI (Ver Tabela de Lookup) |
| `CODNEG` | 13 | 24 | 12 | $X(12)$ | Código de Negociação (Ticker) |
| `TPMERC` | 25 | 27 | 3 | $N(03)$ | Tipo de Mercado (Ver Tabela de Lookup) |
| `NOMRES` | 28 | 39 | 12 | $X(12)$ | Nome resumido da empresa |
| `ESPECI` | 40 | 49 | 10 | $X(10)$ | Especificação do Papel (Ver Tabela) |
| `PREABE` | 57 | 69 | 13 | (11)V99 | Preço de Abertura |
| `PREMAX` | 70 | 82 | 13 | (11)V99 | Preço Máximo |
| `PREMIN` | 83 | 95 | 13 | (11)V99 | Preço Mínimo |
| `PREMED` | 96 | 108 | 13 | (11)V99 | Preço Médio |
| `PREULT` | 109 | 121 | 13 | (11)V99 | Preço de Fechamento (Último) |
| `PREOFC` | 122 | 134 | 13 | (11)V99 | Melhor Oferta de Compra |
| `PREOFV` | 135 | 147 | 13 | (11)V99 | Melhor Oferta de Venda |
| `TOTNEG` | 148 | 152 | 5 | $N(05)$ | Número de Negócios Efetuados |
| `QUATOT` | 153 | 170 | 18 | $N(18)$ | Quantidade Total de Títulos Negociados |
| `VOLTOT` | 171 | 188 | 18 | (16)V99 | Volume Total de Títulos Negociados |
| `DATVEN` | 203 | 210 | 8 | $N(08)$ | Data de Vencimento (Opções/Termo) |
| `FATCOT` | 211 | 217 | 7 | $N(07)$ | Fator de Cotação (e.g., '1' ou '1000') |
| `CODISI` | 231 | 242 | 12 | $X(12)$ | Código ISIN |
| `DISMES` | 243 | 245 | 3 | $9(03)$ | Número de Distribuição do Papel |

---

## 3. Ponto Crítico: Interpretação de Tipos de Dados

A maior dificuldade no parsing deste arquivo é a correta conversão dos tipos de dados numéricos.

* **$N(X)$ ou $X(X)$:** Campos numéricos (`N`) ou alfanuméricos (`X`) simples. Podem ser lidos como strings.
* **(X)V99:** (e.g., `PREULT`) Representa um número com **2 casas decimais**. O valor `(11)V99` significa que o campo tem 13 caracteres no total (11 inteiros + 2 decimais). O valor `0000001234567` deve ser lido como `12345.67`.
* **(X)V06:** (e.g., `PTOEXE`) Representa um número com **6 casas decimais**.

**Ação em Python:** Para converter um campo (X)V99 (lido como string), você deve dividi-lo por 100. Para (X)V06, divida por 1.000.000. O uso da biblioteca `Decimal` é **altamente recomendado** para evitar erros de precisão com `float`.

```python
# Exemplo de conversão de PREULT (posições 109-121)
from decimal import Decimal

linha = "..." # Uma linha de registro 01
str_preult = linha[108:121] # Em Python, o índice final é exclusivo
# str_preult conterá algo como "0000000456789"
# Converte para Decimal('4567.89')
decimal_preult = Decimal(str_preult) / Decimal('100')
