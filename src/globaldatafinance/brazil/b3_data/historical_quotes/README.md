# Módulo de Cotações Históricas (B3)

> [!NOTE]
> Este módulo faz parte da suíte `Global-Data-Finance` e é especializado na extração de alta performance de dados históricos da B3 (antiga Bovespa).

O módulo `historical_quotes` implementa uma solução robusta baseada em **Clean Architecture** para processar arquivos da série histórica (COTAHIST) da B3. Ele abstrai a complexidade do layout posicional de arquivos legados, oferecendo uma interface moderna e tipada para extração de dados financeiros.

## 🎯 Objetivos e Valor

- **Abstração de Layout**: Remove a necessidade de conhecer o layout posicional (bytes/offsets) dos arquivos da B3.
- **Performance**: Utiliza estratégias de leitura otimizada e escrita em formato colunar (Parquet).
- **Integridade**: Validação estrita de parâmetros de entrada e tratamento de erros específico de domínio.
- **Filtragem por Tipo de Ativo**: Capacidade de filtrar a extração por tipos de ativos (ações, ETF, opções, etc.).

## 🏗️ Arquitetura

A arquitetura segue o padrão de camadas concêntricas, garantindo que as regras de negócio não dependam de detalhes de implementação.

```text
+---------------------------------------------------------+
|                    Application Layer                    |
|          [ ExtractHistoricalQuotesUseCaseB3 ]           |
+---------------------------+-----------------------------+
                            |
            +---------------+---------------+
            v                               v
+-----------------------+       +-------------------------+
|     Domain Layer      |       |   Infrastructure Layer  |
| [DocsToExtractorB3]   |       | [CotahistParserB3]      |
| [AvailableAssets...]  |       | [ParquetWriterB3]       |
+-----------------------+       | [ZipFileReaderB3]       |
                                +-------------------------+
```

### Componentes Chave

| Componente                         | Camada      | Responsabilidade                                                           |
| ---------------------------------- | ----------- | -------------------------------------------------------------------------- |
| `ExtractHistoricalQuotesUseCaseB3` | Application | Orquestra o fluxo de extração, conectando parser, leitor e escritor.       |
| `DocsToExtractorB3`                | Domain      | Entidade que encapsula e valida os parâmetros de configuração da extração. |
| `CotahistParserB3`                 | Infra       | Traduz linhas de texto posicional em dicionários Python estruturados.      |
| `ParquetWriterB3`                  | Infra       | Gerencia a escrita eficiente em arquivos Parquet com compressão.           |

## 🚀 Guia de Uso

### Pré-requisitos

Certifique-se de ter os arquivos `COTAHIST_A{ANO}.ZIP` baixados em um diretório acessível.

### Exemplo Completo

```python
import asyncio
from globaldatafinance.brazil.b3_data.historical_quotes.application.use_cases import ExtractHistoricalQuotesUseCaseB3
from globaldatafinance.brazil.b3_data.historical_quotes.domain import DocsToExtractorB3

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

O módulo expõe exceções específicas em `globaldatafinance.brazil.b3_data.historical_quotes.exceptions`:

- `InvalidFirstYear` / `InvalidLastYear`: Erros de validação de intervalo temporal.
- `InvalidAssetsName`: Ticker fornecido não segue o padrão esperado.
- `EmptyAssetListError`: Tentativa de processamento com lista de ativos inválida.

## 🔧 Troubleshooting

> [!WARNING] > **Erro: Arquivo não encontrado**
> Verifique se o nome do arquivo em `set_documents_to_download` corresponde exatamente ao arquivo no disco (case-sensitive no Linux).

> [!TIP] > **Performance**
> Para grandes volumes de dados (todos os ativos de vários anos), prefira processar ano a ano ou utilizar máquinas com mais memória RAM se usar o modo `fast`.
