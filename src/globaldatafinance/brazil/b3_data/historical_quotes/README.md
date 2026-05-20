# Módulo de Cotações Históricas (B3)

> [!NOTE]
> Este módulo faz parte da suíte `Global-Data-Finance` e é especializado na extração de alta performance de dados históricos da B3 (antiga Bovespa).

O módulo `historical_quotes` implementa uma solução robusta para processar arquivos da série histórica (COTAHIST) da B3. Ele abstrai a complexidade do layout posicional de arquivos legados, oferecendo uma interface moderna e tipada para extração de dados financeiros. Internamente segue o **padrão de módulos planos por fonte** (sem subcamadas `domain`/`application`/`infra`).

## 🎯 Objetivos e Valor

- **Abstração de Layout**: Remove a necessidade de conhecer o layout posicional (bytes/offsets) dos arquivos da B3.
- **Performance**: Utiliza estratégias de leitura otimizada e escrita em formato colunar (Parquet).
- **Integridade**: Validação estrita de parâmetros de entrada e tratamento de erros específico de domínio.
- **Filtragem por Tipo de Ativo**: Capacidade de filtrar a extração por tipos de ativos (ações, ETF, opções, etc.).

## 🏗️ Arquitetura

Layout plano de ~7–8 módulos:

```text
brazil/b3_data/historical_quotes/
├── core.py                # DocsToExtractorB3, AvailableAssetsServiceB3, validators, ProcessingModeEnumB3, validate_directory_path
├── client.py              # ExtractHistoricalQuotesUseCaseB3 (stateful), CreateDocsToExtractUseCaseB3, GetAvailableAssetsUseCaseB3, etc.
├── cotahist_parser.py     # Parsing posicional COTAHIST (preservado — complexidade legítima)
├── parquet_writer/        # Subpacote de escrita Parquet (writer, schema, streaming, disk, constants)
├── extraction_service/    # Subpacote de orquestração (service, batch_parser, zip_processor, buffered_writer, resource_policy, temp_parquet_merge, types)
├── zip_reader.py          # Leitura streaming de ZIP
└── errors.py              # InvalidFirstYear, InvalidLastYear, InvalidAssetsName, EmptyAssetListError, InvalidProcessingMode, etc.
```

`ExtractHistoricalQuotesUseCaseB3` permanece como classe (D3) porque mantém estado: `zip_reader + parser + writer + processing_mode` são reutilizados entre chamadas.

### Componentes Chave

| Módulo                  | Componente                         | Tipo                  | Responsabilidade                                                                       |
| ----------------------- | ---------------------------------- | --------------------- | -------------------------------------------------------------------------------------- |
| `client.py`             | `ExtractHistoricalQuotesUseCaseB3` | Orquestrador (classe) | Conecta parser, leitor e escritor. Mantém estado entre chamadas.                       |
| `client.py`             | `CreateDocsToExtractUseCaseB3`     | Use case              | Constrói `DocsToExtractorB3` validado a partir dos parâmetros públicos do facade.      |
| `core.py`               | `DocsToExtractorB3`                | Value object          | Encapsula e valida parâmetros de configuração da extração (anos, assets, paths).       |
| `core.py`               | `validate_directory_path`          | Helper                | Raise `SecurityError` em `/etc`, `/sys`, `/proc`, `/dev`, `/boot`, `/root` antes de I/O. |
| `cotahist_parser.py`    | `CotahistParserB3`                 | Parser concreto       | Traduz linhas de texto posicional em dicionários Python estruturados.                  |
| `parquet_writer/`       | `ParquetWriterB3`                  | Writer concreto       | Escrita Parquet com compressão (zstd) e statistics. Subpacote (`writer`, `schema`, `streaming`, `disk`, `constants`).  |
| `extraction_service/`   | `ExtractionServiceB3`              | Service concreto      | Streaming/threadpool/flush por memória. Subpacote (`service`, `batch_parser`, `zip_processor`, `buffered_writer`, `resource_policy`, `temp_parquet_merge`, `types`). |

## 🚀 Guia de Uso

### Pré-requisitos

Certifique-se de ter os arquivos `COTAHIST_A{ANO}.ZIP` baixados em um diretório acessível.

### Exemplo Completo

```python
import asyncio
from globaldatafinance.brazil.b3_data.historical_quotes import (
    DocsToExtractorB3,
    ExtractHistoricalQuotesUseCaseB3,
)

async def run_extraction():
    # 1. Configuração da Extração
    # DocsToExtractorB3 valida automaticamente os tipos e caminhos
    config = DocsToExtractorB3(
        path_of_docs="/dados/brutos/b3",        # Onde estão os ZIPs
        destination_path="/dados/processados",  # Onde salvar o Parquet
        range_years=range(2023, 2024),          # Anos a considerar
        set_assets={"ações", "etf"},            # Tipos de ativos (ações, etf, opções, etc.)
        set_documents_to_download={"COTAHIST_A2023.ZIP"} # Arquivos específicos
    )

    # 2. Execução
    use_case = ExtractHistoricalQuotesUseCaseB3()

    try:
        result = await use_case.execute(
            docs_to_extract=config,
            processing_mode="fast",  # 'fast' (memória) ou 'slow' (iterativo)
            output_filename="b3_quotes_2023.parquet"
        )

        print(f"Sucesso! {result['total_records']} registros processados.")

    except Exception as e:
        print(f"Erro durante a extração: {e}")

if __name__ == "__main__":
    asyncio.run(run_extraction())
```

## ⚙️ Referência da API

### `DocsToExtractorB3` (Configuração)

| Campo                       | Tipo       | Descrição                                                                                                                                                                 |
| --------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `path_of_docs`              | `str`      | Caminho absoluto para o diretório contendo os arquivos ZIP.                                                                                                               |
| `destination_path`          | `str`      | Caminho absoluto onde o arquivo Parquet será salvo.                                                                                                                       |
| `range_years`               | `range`    | Intervalo de anos para validação (ex: `range(2020, 2024)`).                                                                                                               |
| `set_assets`                | `Set[str]` | Conjunto de tipos de ativos para filtrar (ex: `{"ações", "etf", "opções"}`). Valores válidos: `ações`, `etf`, `opções`, `termo`, `exercicio_opcoes`, `forward`, `leilao`. |
| `set_documents_to_download` | `Set[str]` | Nomes exatos dos arquivos ZIP a serem processados.                                                                                                                        |

### Tratamento de Erros

O módulo expõe exceções específicas em `globaldatafinance.brazil.b3_data.historical_quotes.errors` (re-exportadas pelo `__init__.py` da fonte):

- `InvalidFirstYear` / `InvalidLastYear`: erros de validação de intervalo temporal.
- `InvalidAssetsName`: ticker fornecido não segue o padrão esperado.
- `EmptyAssetListError`: tentativa de processamento com lista de ativos inválida.
- `InvalidProcessingMode`: `processing_mode` fora de `{'fast', 'slow'}`.
- `SecurityError` (de `macro_exceptions`): tentativa de escrita em path sensível (`/etc`, `/sys`, `/proc`, `/dev`, `/boot`, `/root`) — defesa em `validate_directory_path` (`core.py`).

## 🔧 Troubleshooting

> [!WARNING] > **Erro: Arquivo não encontrado**
> Verifique se o nome do arquivo em `set_documents_to_download` corresponde exatamente ao arquivo no disco (case-sensitive no Linux).

> [!TIP] > **Performance**
> Para grandes volumes de dados (todos os ativos de vários anos), prefira processar ano a ano ou utilizar máquinas com mais memória RAM se usar o modo `fast`.
