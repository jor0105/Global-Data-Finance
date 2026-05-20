# Refactor: Anti-overengineering

## Why

A biblioteca evoluiu para Clean Architecture estrita (4 camadas — `domain` / `application` / `infra` / `exceptions` — por fonte de dados), mas sua forma real é uma **lib de ETL com 2 classes públicas** (`FundamentalStocksDataCVM`, `HistoricalQuotesB3`). A cerimônia não paga: hoje são **109 arquivos `.py` em 42 diretórios** (medido por `find src -type f -name '*.py' | wc -l` e `find src -mindepth 1 -type d -not -name __pycache__ | wc -l`) com ABCs de implementação única, use cases que são funções embrulhadas em classes, factories de 1 linha e cascatas de até 5 níveis de `__init__.py` re-exportando a mesma classe. O custo estrutural torna adicionar novas fontes (objetivo declarado do produto) mais lento, não mais rápido — exatamente o oposto da promessa da arquitetura escolhida.

## What Changes

- **Achatar 4 camadas → 2 por fonte**: `core.py` (dataclasses/enums/validators puros) + `client.py` (orquestração como funções de módulo) + `http.py` / `extract.py` (adapters concretos) + `errors.py`. Aplica-se a `brazil/cvm/fundamental_stocks_data/` e `brazil/b3_data/historical_quotes/`.
- **Remover ABCs com implementação única**: `DownloadDocsCVMRepositoryCVM` e `FileExtractorRepositoryCVM` viram classes concretas; injeção continua possível via construtor, sem `isinstance` checks artificiais.
- **Converter use cases de 1 método em funções de módulo**: 14 dos 15 use case classes (ex: `CreateSetAssetsUseCaseB3`, `GetAvailableYearsUseCaseB3`) viram funções. Classes só onde há **estado real** (orquestrador que segura adapter + formatter).
- **Eliminar factories redundantes**: `ExtractionServiceFactoryB3` (50 linhas para 1 cast de enum) vira `classmethod create` no próprio `ExtractionServiceB3` ou some.
- **Fundir domain services + use cases 1:1**: onde um service tem a lógica e um use case só delega (ex: `AvailableAssetsServiceB3` + `CreateSetAssetsUseCaseB3`), vira uma função única.
- **Achatar cascata de `__init__.py`**: re-exports passam a viver apenas no `__init__.py` raiz do package; níveis intermediários são esvaziados.
- **Preservar pastas pendentes de promoção** em `brazil/b3_data/{Dados_B3_Acoes, Dados_B3_FIIs, Opcoes_B3}`, `brazil/gerais/` e `brazil/app_geral.py`: mantidas in-place no path atual, sem mover nem deletar. São fontes que o owner do projeto pretende promover à API pública em changes OpenSpec futuras (uma por fonte); arquivos com imports quebrados (`app_geral.py` referencia diretórios inexistentes) ficam para serem consertados pela change que os promover, não por este refactor estrutural.
- **Preservar intactos**: API pública (`FundamentalStocksDataCVM`, `HistoricalQuotesB3`), formato Parquet de saída, comportamento async/concurrency, código pesado de parsing/IO (`infra/extraction_service.py`, `parquet_writer.py`, `cotahist_parser.py`), utilitários compartilhados (`core/`, `macro_infra/`, `macro_exceptions/`).
- **Preservar contratos observáveis de validação e segurança**: `FundamentalStocksDataCVM.download(...)` continua bloqueando `destination_path` em diretórios sensíveis com `SecurityError`; `HistoricalQuotesB3.extract(...)` continua rejeitando `path_of_docs` resolvido em diretórios sensíveis e `processing_mode` inválido segue levantando `InvalidProcessingMode`.
- **Travar só a superfície pública sancionada do facade**: o gate de compatibilidade congela exports top-level, `repr` e assinaturas dos métodos públicos; colaboradores internos incidentais (ex.: `download_adapter`) não viram contrato semver por acidente.
- **Atualizar documentação interna**: `AGENTS.md` (mapa arquitetural) e `docs/dev-guide/architecture.md` refletem as novas convenções; o exemplo de "como adicionar nova fonte" muda de 4 camadas para 2 módulos.
- **BREAKING (interno apenas)**: imports de símbolos não-públicos (`brazil.cvm.fundamental_stocks_data.application.use_cases.*`, `brazil.b3_data.historical_quotes.domain.services.*`, etc.) deixam de funcionar. Esses caminhos nunca foram parte do contrato semver — a API pública (`from globaldatafinance import ...`) não muda.

## Capabilities

### New Capabilities

> Estas capabilities documentam comportamento público **pré-existente** no código, capturado em spec OpenSpec pela primeira vez. Esta change é estrutural (refactor interno) e **não altera** assinatura, retorno, exceções ou semântica das classes públicas; preserva-as bit-idênticas (verificado pelo "Critério 1 — API surface lock" em `design.md`).

- `cvm-fundamental-stocks-data`: Download em lote e extração para Parquet de documentos regulatórios da CVM (DFP, ITR, FRE, FCA, CGVN, VLMO, IPE) com concorrência assíncrona, retries, validação de integridade e descoberta de anos/tipos disponíveis. Exposto via classe pública `FundamentalStocksDataCVM`.
- `b3-historical-quotes`: Extração de arquivos posicionais COTAHIST (ZIP) da B3 para dataset Parquet consolidado, com filtros por classe de ativo (ações, ETFs, BDRs, opções, termo, futuros), modos `fast`/`slow` e descoberta de anos/ativos disponíveis. Exposto via classe pública `HistoricalQuotesB3`.

### Modified Capabilities

<!-- Vazio: este é o primeiro change OpenSpec do projeto; ainda não há specs existentes para modificar. -->

## Impact

- **Código-fonte afetado**:
  - `src/globaldatafinance/brazil/cvm/fundamental_stocks_data/` — 25 arquivos → ~5–6
  - `src/globaldatafinance/brazil/b3_data/historical_quotes/` — 30 arquivos → ~7–8
  - `src/globaldatafinance/application/` — facades públicos preservados, imports internos reescritos
  - `src/globaldatafinance/brazil/{b3_data/Dados_B3_*, b3_data/Opcoes_B3, gerais, app_geral.py}` — **intocados** nesta change (mantidos in-place; ficam para serem promovidos por changes futuras dedicadas)
  - **Total `src/`**: 109 → ~50–55 arquivos (redução ≥40%; meta operacional, não número-alvo. Reconciliação realista: ~12–13 nas 2 fontes refatoradas + ~37 inalterados em `core/`, `macro_*/`, facades, pendentes-de-promoção mantidos in-place)

- **API pública**: zero mudanças. `from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3` continua o único contrato versionado, com assinaturas e comportamento idênticos.

- **Testes**: `tests/` (59 arquivos) reorganizado em mirror da nova estrutura; testes que dependem de injetar mocks via ABC migram para fakes diretos ou `monkeypatch`. Cobertura `fail_under=70` mantida em todas as fases.

- **Documentação**: `AGENTS.md` e `docs/dev-guide/architecture.md` reescritos para refletir o novo padrão (2 módulos por fonte); seções sobre Clean Arch e padrões de uso são revisadas. `README.md` e `docs/user-guide/` permanecem sem alterações (API pública preservada).

- **Dependências**: nenhuma alteração em `pyproject.toml` (mesmas runtime/dev deps, mesma versão Python 3.12+).

- **Tooling**: nenhuma alteração em `pyproject.toml` — paths das pastas pendentes de promoção permanecem onde estão, então os `per-file-ignores` atuais continuam válidos sem migração.

- **Risco externo**: usuários da PyPI não são afetados (API pública estável). Scripts internos que dependam de caminhos privados (`brazil.cvm.fundamental_stocks_data.application.*`, etc.) precisarão migrar — mas esses caminhos não eram contratuais.
