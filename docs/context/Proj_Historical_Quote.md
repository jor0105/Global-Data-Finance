# Descrição do Projeto: Extrator Assimétrico e Flexível de Cotações (COTAHIST)

### 1. Objetivo Principal

Desenvolver um script Python de alta performance e configurável para processar arquivos `.zip` (COTAHIST) da B3. O script deve aceitar entradas amigáveis (ex: 'ações', 'etf'), traduzi-las internamente para os códigos de mercado B3 (`TPMERC`), filtrar os dados em memória e salvar o resultado em Parquet. O script deve permitir ao usuário controlar o nível de consumo de recursos (CPU/Memória) através de modos de processamento.

### 2. Entradas (Inputs)

O script receberá três entradas principais:

1.  **`zip_files_list` (Lista de Caminhos):** Uma lista Python contendo os caminhos completos para os arquivos `.zip` (ex: `['/data/COTAHIST.2023.ZIP', '/data/COTAHIST.2024.ZIP']`).
2.  **`target_asset_classes` (Lista de Classes de Ativos):** Uma lista Python de strings amigáveis.
    * Exemplo: `['ações', 'etf', 'opções']`
3.  **`processing_mode` (Modo de Processamento):** Uma string que define a estratégia de alocação de recursos.
    * `'fast'` (Rápido): Prioriza velocidade, consumindo mais CPU e Memória RAM.
    * `'slow'` (Lento): Prioriza baixo consumo de recursos, executando mais lentamente.

### 3. Requisitos de Processamento

#### 3.1. Mapeamento Interno de Ativos (Tradução)
Antes de iniciar o processamento, o script deve traduzir a lista `target_asset_classes` em um conjunto (set) de códigos `TPMERC` técnicos da B3. O script deve conter este dicionário de mapeamento:

* **'ações'**: Mapeia para `['010', '020']` (Mercado à Vista Lote Padrão e Fracionário).
* **'etf'**: Mapeia para `['010', '020']` (ETFs são negociados nos mesmos mercados que as ações).
* **'opções'**: Mapeia para `['070', '080']` (Opções de Compra e Venda).
* **'termo'**: Mapeia para `['030']` (Mercado a Termo).
* *(Adicionar outros mapeamentos conforme necessário)*

O script deve consolidar os códigos resultantes em um conjunto único para filtragem (ex: `['ações', 'etf']` resulta no conjunto `{'010', '020'}`).

#### 3.2. Processamento Assíncrono e Controle de Recursos
O script deve usar `asyncio` para concorrência. O `processing_mode` controlará o nível de paralelismo:

* **Modo `'fast'`:** Usará um alto nível de concorrência (ex: `asyncio.Semaphore` com limite alto ou `asyncio.gather` para todos os arquivos de uma vez). Isso resulta em picos de CPU (parsing) e RAM (múltiplos dataframes em memória).
* **Modo `'slow'`:** Usará um baixo nível de concorrência (ex: `asyncio.Semaphore(2)`) para processar apenas alguns arquivos `.zip` por vez, garantindo baixo uso de CPU e RAM.

#### 3.3. Leitura em Memória (Sem Descompressão em Disco)
Para cada arquivo `.zip` da lista:
* O arquivo `.zip` será aberto em memória (usando `zipfile`).
* O arquivo `.TXT` interno será lido linha por linha (streamed) diretamente da memória.

#### 3.4. Parsing e Filtragem (Layout `COTAHIST`)
Para cada linha lida do arquivo `.TXT`:
1.  **Verificar Tipo de Registro:** Ler posições 1-2 (`TIPREG`).
2.  **Ignorar Header/Trailer:** Se `TIPREG` for `00` ou `99`, ignorar.
3.  **Processar Registros de Cotação (`01`):**
    * Extrair o tipo de mercado `TPMERC` (posições 25-27).
    * Limpar o `TPMERC` (ex: `.strip()`).
4.  **Lógica de Extração Condicional:**
    * **Se** o `TPMERC` **não** estiver no conjunto de códigos mapeados internamente (ver 3.1), descartar a linha.
    * **Se** o `TPMERC` **estiver** no conjunto, realizar o *parsing completo* da linha (extrair Data, Ticker, Preços, Volume, etc.).

#### 3.5. Transformação de Dados
Durante o parsing completo (somente para os dados filtrados):
* **Decimais:** Converter campos de preço (formato `(11)V99`) dividindo por 100.
* **Datas:** Converter campos de data (YYYYMMDD) para `datetime`.
* **Inteiros:** Converter volume e quantidade para `int`.
* **Strings:** Limpar campos de texto (como `CODNEG`).

### 4. Saída (Output)

Salvar os dados filtrados e transformados em **formato Parquet**. A estratégia de salvamento pode ser um arquivo único ou múltiplos arquivos particionados (ex: por ano ou classe de ativo).

### 5. Pilha de Tecnologia Sugerida
* **`asyncio`** (com `asyncio.Semaphore` para controle de concorrência).
* **`zipfile`**: Para leitura dos `.zip` em memória.
* **`polars`** ou **`pandas`** (com `pyarrow`): Para estruturação dos dados e salvamento em Parquet.
