# Módulo de Dados Fundamentais (CVM)

> [!NOTE]
> Este módulo integra a suíte `Global-Data-Finance` e fornece uma interface robusta para automação de downloads de documentos regulatórios da CVM (Comissão de Valores Mobiliários).

O módulo `fundamental_stocks_data` foi projetado para simplificar a aquisição de dados públicos de companhias abertas brasileiras. Ele gerencia a complexidade de URLs dinâmicas, estrutura de diretórios e resiliência de rede, tudo encapsulado em uma arquitetura limpa e extensível.

## 🎯 Objetivos e Valor

- **Automação Confiável**: Elimina o trabalho manual de buscar arquivos no site da CVM.
- **Gestão de Falhas**: Sistema robusto de retentativas e relatório detalhado de erros.
- **Organização Automática**: Estrutura os arquivos baixados por tipo e ano, facilitando o consumo posterior.
- **Extensibilidade**: Arquitetura baseada em interfaces permite trocar facilmente o mecanismo de download (ex: `requests`, `httpx`, `aiohttp`).

## 🏗️ Arquitetura

O fluxo de execução é orquestrado pelo caso de uso `DownloadDocumentsUseCaseCVM`, que coordena a geração de URLs, validação de caminhos e a execução do download via repositório.

```text
+---------------------------------------+
|           Application Layer           |
|     [DownloadDocumentsUseCaseCVM]     |
|      /           |            \       |
| [GenerateUrls]   |      [VerifyPaths] |
+------------------|--------------------+
                   |
                   v
+------------------|--------------------+
|             Domain Layer              |
|   [DownloadDocsCVMRepositoryCVM] <....|....+
|        [DownloadResultCVM]            |    :
+---------------------------------------+    :
                                             :
+---------------------------------------+    :
|         Infrastructure Layer          |    :
|        [CVMRepositoryAdapter] .........+...:
|        /                    \         |
|  [FileSystem]          [Network]      |
+---------------------------------------+
```

### Componentes Chave

| Camada             | Componente                    | Tipo       | Responsabilidade                                                             |
| ------------------ | ----------------------------- | ---------- | ---------------------------------------------------------------------------- |
| **Application**    | `DownloadDocumentsUseCaseCVM` | Use Case   | Orquestra todo o fluxo de download, validações e chamadas de infraestrutura. |
| **Application**    | `GenerateUrlsUseCaseCVM`      | Service    | Constrói URLs de download a partir de `DictZipsToDownloadCVM`.               |
| **Application**    | `VerifyPathsUseCasesCVM`      | Service    | Cria e valida a estrutura de diretórios de destino.                          |
| **Domain**         | `DownloadResultCVM`           | Entity     | Resultado agregado contendo sucessos, falhas e contadores.                   |
| **Domain**         | `DictZipsToDownloadCVM`       | Repository | Fornece o mapeamento de documentos → URLs por ano.                           |
| **Infrastructure** | `CVMRepositoryAdapter`        | Adapter    | Implementa `DownloadDocsCVMRepositoryCVM` usando `AsyncDownloadAdapterCVM`.  |
| **Infrastructure** | `AsyncDownloadAdapterCVM`     | Adapter    | Realiza downloads assíncronos com retry/back‑off e validação de integridade. |
| **Infrastructure** | `ParquetExtractorAdapterCVM`  | Adapter    | Converte CSVs dentro do ZIP para Parquet com garantia de transação atômica.  |


## 🚀 Guia de Uso

### Exemplo Completo

```python
from globaldatafinance.brazil.cvm.fundamental_stocks_data.application.use_cases import DownloadDocumentsUseCaseCVM
from globaldatafinance.brazil.cvm.fundamental_stocks_data.infra.adapters import CVMRepositoryAdapter

def baixar_dados_cvm():
    # 1. Preparação da Infraestrutura
    # O adaptador implementa a interface de repositório usando requests/urllib
    repository = CVMRepositoryAdapter()

    # 2. Inicialização do Caso de Uso
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

Exceções comuns definidas em `globaldatafinance.brazil.cvm.fundamental_stocks_data.exceptions.exceptions_domain`:

- `InvalidRepositoryTypeError`: O repositório injetado não implementa a interface correta.
- `MissingDownloadUrlError`: Não foi possível gerar uma URL para o documento/ano solicitado.
- `InvalidDocName`: O tipo de documento solicitado não é reconhecido pelo sistema.

## 🔧 Troubleshooting

> [!CAUTION] > **Bloqueio de IP**
> O site da CVM pode bloquear IPs que realizam muitas requisições em curto período. O adaptador de infraestrutura deve implementar "backoff" ou pausas entre requisições.

> [!TIP] > **Estrutura de Pastas**
> O sistema cria automaticamente subpastas para cada tipo de documento dentro de `destination_path`. Não é necessário criá-las manualmente.

## 🔎 Como funciona a extração dos arquivos da CVM

A extração dos arquivos baixados da CVM é realizada pelo **ParquetExtractorAdapterCVM**, que implementa a interface de extração de arquivos (`FileExtractorRepositoryCVM`). O fluxo completo pode ser resumido nos passos abaixo:

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
