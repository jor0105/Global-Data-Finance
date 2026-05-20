# Módulo de Dados Fundamentais (CVM)

> [!NOTE]
> Este módulo integra a suíte `Global-Data-Finance` e fornece uma interface robusta para automação de downloads de documentos regulatórios da CVM (Comissão de Valores Mobiliários).

O módulo `fundamental_stocks_data` foi projetado para simplificar a aquisição de dados públicos de companhias abertas brasileiras. Ele gerencia a complexidade de URLs dinâmicas, estrutura de diretórios e resiliência de rede, tudo encapsulado em uma arquitetura limpa e extensível.

## 🎯 Objetivos e Valor

- **Automação Confiável**: Elimina o trabalho manual de buscar arquivos no site da CVM.
- **Gestão de Falhas**: Sistema robusto de retentativas e relatório detalhado de erros.
- **Organização Automática**: Estrutura os arquivos baixados por tipo e ano, facilitando o consumo posterior.
- **Extensibilidade**: adapter HTTP concreto (`AsyncDownloadAdapterCVM`) construído diretamente. Quando uma segunda implementação aparecer (ex.: `WgetDownloadAdapter`), extrair um `Protocol` é trivial.

## 🏗️ Arquitetura

Layout plano de 5 módulos (sem subcamadas `domain`/`application`/`infra`):

```text
brazil/cvm/fundamental_stocks_data/
├── core.py     # AvailableDocsCVM, AvailableYearsCVM, DictZipsToDownloadCVM, DownloadResultCVM, UrlDocsCVM
├── client.py   # DownloadDocumentsUseCaseCVM (orquestrador), GenerateUrlsUseCaseCVM, VerifyPathsUseCasesCVM, etc.
├── http.py     # AsyncDownloadAdapterCVM (httpx async + retry/back-off + integrity check)
├── extract.py  # ParquetExtractorAdapterCVM (CSV → Parquet com rollback atômico)
└── errors.py   # InvalidDocName, InvalidFirstYear, InvalidLastYear, MissingDownloadUrlError, etc.
```

`DownloadDocumentsUseCaseCVM` orquestra: geração de URLs (`GenerateUrlsUseCaseCVM`), validação de paths (`VerifyPathsUseCasesCVM` — raise `SecurityError` em `/etc`, `/sys`, `/proc`, `/dev`, `/boot`, `/root`) e o download via `AsyncDownloadAdapterCVM` injetado.

### Componentes Chave

| Módulo       | Componente                    | Tipo                  | Responsabilidade                                                                     |
| ------------ | ----------------------------- | --------------------- | ------------------------------------------------------------------------------------ |
| `client.py`  | `DownloadDocumentsUseCaseCVM` | Orquestrador (classe) | Coordena geração de URLs, validação de paths e execução de download. Stateful.       |
| `client.py`  | `GenerateUrlsUseCaseCVM`      | Use case              | Constrói URLs de download a partir de `DictZipsToDownloadCVM`.                       |
| `client.py`  | `VerifyPathsUseCasesCVM`      | Use case              | Cria estrutura de diretórios de destino. Raise `SecurityError` em paths sensíveis.   |
| `core.py`    | `DownloadResultCVM`           | Result object         | Resultado agregado contendo sucessos, falhas e contadores (`elapsed_time` incluso).  |
| `core.py`    | `DictZipsToDownloadCVM`       | Value object          | Mapeamento documento → URLs por ano.                                                  |
| `http.py`    | `AsyncDownloadAdapterCVM`     | Adapter concreto      | Downloads assíncronos com retry/back‑off e validação de integridade.                  |
| `extract.py` | `ParquetExtractorAdapterCVM`  | Adapter concreto      | Converte CSVs dentro do ZIP para Parquet com transação atômica (rollback no erro).    |


## 🚀 Guia de Uso

### Exemplo Completo

```python
from globaldatafinance.brazil.cvm.fundamental_stocks_data import (
    AsyncDownloadAdapterCVM,
    DownloadDocumentsUseCaseCVM,
)

def baixar_dados_cvm():
    # 1. Adapter HTTP concreto (httpx async + retry + integrity check)
    repository = AsyncDownloadAdapterCVM()

    # 2. Orquestrador
    downloader = DownloadDocumentsUseCaseCVM(repository=repository)

    print("Iniciando downloads...")

    # 3. Execução
    try:
        resultado = downloader.execute(
            destination_path="./dados_cvm",  # Diretório raiz para salvar
            list_docs=["DFP", "ITR", "FRE"], # Tipos de documentos
            initial_year=2022,               # Ano inicial
            last_year=2023                   # Ano final
        )

        # 4. Análise dos Resultados
        print(f"\nResumo da Operação:")
        print(f"✅ Sucessos: {resultado.success_count_downloads}")
        print(f"❌ Falhas: {resultado.error_count_downloads}")

        if resultado.failed_downloads:
            print("\nDetalhes das falhas:")
            for doc, erro in resultado.failed_downloads.items():
                print(f" - {doc}: {erro}")

    except Exception as e:
        print(f"Erro crítico na execução: {e}")

if __name__ == "__main__":
    baixar_dados_cvm()
```

## ⚙️ Referência da API

### `DownloadDocumentsUseCaseCVM.execute`

| Parâmetro          | Tipo        | Obrigatório | Descrição                                                                                                          |
| ------------------ | ----------- | ----------- | ------------------------------------------------------------------------------------------------------------------ |
| `destination_path` | `str`       | Sim         | Caminho base onde as pastas por documento serão criadas.                                                           |
| `list_docs`        | `List[str]` | Não         | Lista de códigos de documentos. Valores válidos: `DFP`, `ITR`, `FRE`, `FCA`, `CGVN`, `IPE`, `VLMO`. Padrão: todos. |
| `initial_year`     | `int`       | Não         | Ano de início da coleta.                                                                                           |
| `last_year`        | `int`       | Não         | Ano final da coleta.                                                                                               |

#### Tipos de Documentos Disponíveis

| Código | Nome                                   | Descrição                      |
| ------ | -------------------------------------- | ------------------------------ |
| `DFP`  | Demonstrações Financeiras Padronizadas | Balanço, DRE, DFC, DVA (anual) |
| `ITR`  | Informações Trimestrais                | Demonstrações trimestrais      |
| `FRE`  | Formulário de Referência               | Informações corporativas       |
| `FCA`  | Formulário Cadastral                   | Dados cadastrais               |
| `CGVN` | Código de Governança                   | Governança corporativa         |
| `IPE`  | Informações Eventuais                  | Atas, fatos relevantes         |
| `VLMO` | Valores Mobiliários                    | Títulos negociados             |

### `DownloadResultCVM` (Retorno)

Objeto retornado pelo método `execute`, contendo:

- `successful_downloads` (`List[str]`): Lista com os caminhos completos dos arquivos baixados.
- `failed_downloads` (`Dict[str, str]`): Dicionário onde a chave é o identificador do documento e o valor é a mensagem de erro.
- `success_count_downloads` (`int`): Contagem total de sucessos.
- `error_count_downloads` (`int`): Contagem total de erros.

### Tratamento de Erros

Exceções definidas em `globaldatafinance.brazil.cvm.fundamental_stocks_data.errors` (re-exportadas pelo `__init__.py` da fonte):

- `MissingDownloadUrlError`: não foi possível gerar uma URL para o documento/ano solicitado.
- `InvalidDocName`: tipo de documento não reconhecido.
- `InvalidFirstYear` / `InvalidLastYear`: ano inválido ou fora do range suportado.
- `SecurityError` (de `macro_exceptions`): tentativa de escrita em path sensível (`/etc`, `/sys`, `/proc`, `/dev`, `/boot`, `/root`) — defesa em `VerifyPathsUseCasesCVM`.

> Nota: `InvalidRepositoryTypeError` foi removido junto com a ABC `DownloadDocsCVMRepositoryCVM` quando o refactor anti-overengineering eliminou a indireção sem polimorfismo real. `mypy` já cobre o caso, e o adapter concreto (`AsyncDownloadAdapterCVM`) é construído diretamente.

## 🔧 Troubleshooting

> [!CAUTION] > **Bloqueio de IP**
> O site da CVM pode bloquear IPs que realizam muitas requisições em curto período. O adaptador de infraestrutura deve implementar "backoff" ou pausas entre requisições.

> [!TIP] > **Estrutura de Pastas**
> O sistema cria automaticamente subpastas para cada tipo de documento dentro de `destination_path`. Não é necessário criá-las manualmente.

## 🔎 Como funciona a extração dos arquivos da CVM

A extração é realizada pelo **`ParquetExtractorAdapterCVM`** em `extract.py` — adapter concreto (sem ABC) chamado diretamente pelo facade quando `automatic_extractor=True`. O fluxo completo é:

1. **Listagem dos CSVs dentro do ZIP**
   - O adaptador delega a `ExtractorAdapter.list_files_in_zip` para obter a lista de arquivos com extensão `.csv` presentes no ZIP.
2. **Conversão individual para Parquet**
   - Para cada CSV, o método `extract_csv_from_zip_to_parquet` converte o conteúdo para Parquet usando o `ExtractorAdapter`. O caminho de destino é construído a partir do nome do CSV (`<nome>.parquet`).
3. **Rastreamento de arquivos criados**
   - Só após a verificação de existência (`parquet_path.exists()`) o caminho é adicionado à lista `created_files`. Isso garante que apenas arquivos realmente gravados sejam considerados para rollback.
4. **Transação atômica (all‑or‑nothing)**
   - Se **qualquer** arquivo falhar, o método `__rollback_extraction` é acionado. Ele remove todos os arquivos listados em `created_files` e lança `ExtractionError` com um resumo das falhas.
5. **Tratamento de exceções específicas**
   - `CorruptedZipError` – ZIP inválido ou corrompido.
   - `DiskFullError` – Falta de espaço em disco (propagado imediatamente).
   - `ExtractionError` – Qualquer erro durante a conversão, que dispara o rollback.
6. **Limpeza e logging**
   - O método `__cleanup_files` centraliza a remoção de arquivos, registrando sucessos e erros. O logger fornece detalhes de cada etapa, facilitando a depuração.

### Por que essa abordagem?

- **Atomicidade**: garante que o diretório de destino nunca fique em estado parcial, essencial para pipelines de dados que dependem de consistência.
- **Escalabilidade**: o processamento em chunks (`chunk_size`) permite lidar com arquivos CSV de grande porte sem esgotar a memória.
- **Resiliência**: back‑off e retries são implementados no adaptador de download; na extração, falhas são capturadas e revertidas de forma controlada.

> **Nota**: Caso deseje desabilitar a extração automática (por exemplo, para apenas baixar os ZIPs), basta configurar o cliente `FundamentalStocksDataCVM` com `automatic_extractor=False`.
