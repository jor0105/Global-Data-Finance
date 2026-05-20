# Design: Refactor anti-overengineering

## Context

A biblioteca `globaldatafinance` é uma lib Python distribuída via PyPI cuja superfície pública é estritamente **2 classes** (`FundamentalStocksDataCVM`, `HistoricalQuotesB3`), declaradas em `src/globaldatafinance/__init__.py`. Internamente, evoluiu para Clean Architecture estrita com 4 camadas (`domain` / `application` / `infra` / `exceptions`) replicadas por fonte de dados, totalizando **109 arquivos `.py` em 42 diretórios** (medido por `find src -type f -name '*.py' | wc -l` e `find src -mindepth 1 -type d -not -name __pycache__ | wc -l` na `develop`).

Evidência concreta do desbalanço entre superfície e estrutura (todos os caminhos relativos a `src/globaldatafinance/`):

- **2 ABCs com 1 única implementação cada**:
  - `brazil/cvm/fundamental_stocks_data/application/interfaces/download_repository.py` (25L) → única impl em `infra/adapters/requests_adapter/async_download_adapter.py::AsyncDownloadAdapterCVM`
  - `brazil/cvm/fundamental_stocks_data/application/interfaces/file_extractor_repository.py` (20L) → única impl em `infra/adapters/extractors_docs_adapter/parquet_extractor.py::ParquetExtractorAdapterCVM`
  - `DownloadDocumentsUseCaseCVM.__init__` ainda faz `isinstance(repository, DownloadDocsCVMRepositoryCVM)` e levanta `InvalidRepositoryTypeError`, defesa que `mypy` já garantiria.
- **15 use case classes, 14 com `execute` único**, padrão "função embrulhada em classe". Caso extremo: `brazil/b3_data/historical_quotes/application/use_cases/set_assets_use_case.py` (26L) — `@staticmethod execute` delegando 1:1 a `AvailableAssetsServiceB3.validate_and_create_asset_set`.
- **Factory de 1 linha útil**: `brazil/b3_data/historical_quotes/infra/extraction_service_factory.py` (50L) cuja lógica real é `mode = ProcessingModeEnumB3(processing_mode.lower())` e construir `ExtractionServiceB3(...)`.
- **Cascata de `__init__.py`** re-exportando `ExtractHistoricalQuotesUseCaseB3` por 5 níveis (`use_cases/` → `application/` → `historical_quotes/` → `b3_data/` → `brazil/`), com a API pública não expondo nenhum desses caminhos.

Onde a complexidade é **legítima** (preservar intocado):

- `brazil/b3_data/historical_quotes/infra/extraction_service.py` (688L), `parquet_writer.py` (461L), `cotahist_parser.py` (308L) — streaming, threadpool, flush por memória, parsing posicional.
- `brazil/cvm/fundamental_stocks_data/infra/adapters/requests_adapter/async_download_adapter.py` (514L) — httpx async, retry, integrity.
- `core/`, `macro_infra/`, `macro_exceptions/` — utilitários compartilhados (resource monitor, retry strategy, logging).
- Facades públicos: `application/cvm_docs/fundamental_stocks_data.py` (285L), `application/b3_docs/historical_quotes.py` (392L) e seus formatters.

Restrições não-negociáveis (referência: `proposal.md`, `AGENTS.md`, `.agents/rules/GLOBAL_RULE.md`, `pyproject.toml`, `pytest.ini`):

- API pública é contrato semver: `from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3` permanece **bit-idêntica** em assinatura, retorno e exceções.
- Validação repo-native via `uv run pre-commit run --all-files` e `uv run pytest` (cobertura `fail_under = 70`, `--strict-markers --strict-config --maxfail=1`).
- Hard blocks do GLOBAL_RULE: sem reescrita de histórico, sem `git reset --hard`, sem `--force-push`. Só commits aditivos e revertíveis individualmente.
- `ruff` com `line-length = 79`, single quotes, Blue-style. `mypy` `python_version = "3.12"`. Sem mudança em `pyproject.toml` de dependências.

## Goals / Non-Goals

**Goals:**

- Reduzir `src/globaldatafinance/**/*.py` em **≥40%** vs baseline (109 arquivos), sem queda de cobertura abaixo de `fail_under = 70`. Reconciliação realista: ~12–13 arquivos finais nas 2 fontes refatoradas (CVM ~5 + B3 ~7–8) somados a ~37 arquivos inalterados (`core/`, `macro_*/`, facades públicos, pendentes-de-promoção mantidos in-place per D8) ≈ ~50–55 totais. Gate operacional: `(baseline - final) / baseline ≥ 0.40`, não "exatamente 40 arquivos".
- Colapsar, por fonte de dados, as 4 camadas Clean Arch em uma estrutura plana de **5–8 módulos por fonte** (CVM ~5; B3 ~7–8 ao preservar `cotahist_parser.py` / `parquet_writer.py` / `extraction_service.py` intactos): `core.py` (dataclasses/enums/validators puros) + `client.py` (orquestração) + `http.py` ou `extract.py` (adapters concretos) + `errors.py`, mais os módulos pesados de parsing/IO preservados quando aplicável.
- Eliminar **2 ABCs sem polimorfismo real**, **1 factory** sem variabilidade e **~10 use cases triviais** (1 método público delegando a 1 colaborador).
- Achatar a cascata de `__init__.py` a 1 nível por subpasta de fonte, com re-export apenas do necessário pelo facade público.
- Preservar o **eixo de extensibilidade real** (pasta por fonte/país) e o paradigma de "adicionar nova fonte = adicionar nova pasta-irmã".
- Atualizar `AGENTS.md` (seção Architecture Map + Layering Rules) e `docs/dev-guide/architecture.md` para refletir o novo padrão; READMEs internos por feature ajustados.
- Cada fase do refactor é **revertível por commit individual** (`git revert <sha>` basta) e validada antes do avanço para a próxima.

**Non-Goals:**

- **Não alterar a API pública** (`FundamentalStocksDataCVM`, `HistoricalQuotesB3`): assinaturas, retorno, exceções e nomes preservados.
- **Não tocar parsing/IO pesado**: `extraction_service.py`, `parquet_writer.py`, `cotahist_parser.py`, `async_download_adapter.py`, `parquet_extractor.py` são movidos sem mudança de comportamento. Mudança permitida: remover herança de ABC e ajustar imports.
- **Não tocar `core/`, `macro_infra/`, `macro_exceptions/`**: são utilitários compartilhados que pagam o próprio custo.
- **Não mudar formato Parquet de saída**, modos `fast`/`slow`, retry strategy, resource monitor, logging, comportamento async/concurrent.
- **Não adicionar novas fontes** (US, EU, etc.), novos adapters, novos formatos. Refactor é exclusivamente estrutural.
- **Não renomear** `FundamentalStocksDataCVM` ou `HistoricalQuotesB3`.
- **Não reescrever testes que continuam válidos** — apenas ajustar imports e remover testes que cobrem símbolos extintos (ABCs, factory).
- **Não deletar legado** (`brazil/b3_data/{Dados_B3_Acoes, Dados_B3_FIIs, Opcoes_B3}`, `brazil/gerais/`, `brazil/app_geral.py`) — apenas classificar/isolar.
- **Não alterar `pyproject.toml`** em dependências; só ajustar `tool.ruff.lint.per-file-ignores` se houver realocação de paths legados.

## Decisions

### D1 — Achatar 4 camadas em 1 camada plana por fonte (não 2 camadas, não monolito)

**Decisão**: Cada fonte (`brazil/cvm/fundamental_stocks_data/`, `brazil/b3_data/historical_quotes/`) passa a ter um diretório plano com 5–8 módulos nomeados pelo papel funcional — CVM ~5 (`core.py`, `client.py`, `http.py`, `extract.py`, `errors.py`); B3 ~7–8 (`core.py`, `client.py`, `extract.py`, `errors.py`, mais `cotahist_parser.py` / `parquet_writer.py` / `extraction_service.py` preservados como arquivos próprios por causa do peso).

**Rationale**:

- Para 1 implementação por papel, a separação em 4 camadas só adiciona traversal de diretórios e cadeia de `__init__.py`, sem ganho de isolamento, troca de implementação ou inversão de dependência observável.
- A separação por **papel funcional** (`core` = dados puros, `client` = orquestração, `http`/`extract` = adapters, `errors` = exceções) preserva legibilidade e fronteira lógica sem replicar a hierarquia inteira de Clean Arch.
- O **eixo de extensibilidade real** da lib é "uma pasta por fonte/país", não "uma camada por tipo de objeto". Esse eixo permanece intacto.

**Alternativas consideradas**:

- *(a) Manter Clean Arch atual*: rejeitada — custo estrutural (109 arquivos) sem benefício mensurável para uma lib de 2 entrypoints.
- *(b) Achatar para 1 arquivo por fonte*: rejeitada — 1500–2500 LoC em arquivo único prejudica navegação; ferramentas de busca (grep/IDE) ficam mais lentas; testes mirror perdem granularidade.
- *(c) Achatar para 2 camadas (`api/` + `infra/`)*: considerada — mais conservadora, mas continua exigindo 2 níveis de diretório e `__init__.py` por nível. A versão plana com nomes por papel é mais simples sem perder organização.

### D2 — Remover ABCs com implementação única (duck typing)

**Decisão**: Excluir `DownloadDocsCVMRepositoryCVM` e `FileExtractorRepositoryCVM`. As classes concretas (`AsyncDownloadAdapterCVM`, `ParquetExtractorAdapterCVM`) deixam de herdar de ABC e são usadas diretamente. O `isinstance(repository, DownloadDocsCVMRepositoryCVM)` em `DownloadDocumentsUseCaseCVM.__init__` desaparece junto com `InvalidRepositoryTypeError`.

**Rationale**:

- Polimorfismo só vale se houver ≥2 implementações reais ou intenção concreta de adicionar uma. Não é o caso (verificado por `grep -rEn "DownloadDocsCVMRepositoryCVM\|FileExtractorRepositoryCVM" src tests` — só 1 impl por contrato).
- O `isinstance` defensivo esconde erros que `mypy` (já configurado em `python_version = "3.12"`) pega em type-check estático.
- Tests que precisam injetar mock podem usar `monkeypatch` ou stub duck-typed (classe simples sem herança) — pattern já presente em outros testes do repo.

**Alternativas consideradas**:

- *(a) Manter ABCs "para o futuro"*: rejeitada — YAGNI; custo cognitivo presente para benefício hipotético; quando uma 2ª implementação aparecer, extrair ABC é trivial.
- *(b) Substituir ABC por `typing.Protocol`*: considerada — adiciona structural typing sem herança. Mas continua sendo cerimônia sem polimorfismo real e exige importar `Protocol` em testes. Decisão: deixar para quando houver demanda concreta.
- *(c) Manter ABC mas remover `isinstance` defensivo*: rejeitada — meio-termo que preserva o pior dos dois mundos.

### D3 — Use cases de 1 método público viram funções de módulo; classes só onde há estado

**Decisão**: 14 dos 15 use case classes (todos os que têm 1 método público `execute`, frequentemente `@staticmethod`) viram funções top-level no módulo `client.py` da fonte. Classes são preservadas onde há **estado real reutilizável**: especificamente o orquestrador `ExtractHistoricalQuotesUseCaseB3` (que segura `zip_reader + parser + writer + processing_mode`) → renomeado para `ExtractHistoricalQuotesClientB3`.

**Rationale**:

- Classe com 1 método e sem estado é função com cerimônia adicional. O custo é construção desnecessária (`UseCase().execute(...)`) e duplicação de docstring entre `__init__` e `execute`.
- Onde há estado (o orquestrador segura ~4 colaboradores e os reutiliza entre chamadas), classe ainda paga o próprio custo — fica como classe.
- Para descobrir o limiar: regra prática é "se a inicialização é não-trivial e os colaboradores são usados em múltiplas chamadas, é classe". Caso contrário, é função.

**Alternativas consideradas**:

- *(a) Manter todos como classes*: rejeitada — replica o problema.
- *(b) Converter tudo em funções incluindo o orquestrador*: rejeitada — perde a possibilidade de injetar adapters customizados via construtor (que o facade público faz), e força funções com 4–5 parâmetros sempre.
- *(c) Usar `@dataclass(frozen=True)` para o orquestrador*: considerada — funcionaria, mas classe normal com `__init__` explícito é mais idiomática para objetos com responsabilidade comportamental.

### D4 — Eliminar `ExtractionServiceFactoryB3`; facade constrói direto

**Decisão**: `ExtractionServiceFactoryB3` (50L) é removida. O facade `HistoricalQuotesB3` (em `application/b3_docs/historical_quotes.py`) ou o `client.py` constrói `ExtractionServiceB3(zip_reader, parser, writer, ProcessingModeEnumB3(mode.lower()))` diretamente.

**Rationale**:

- O trabalho da factory é essencialmente converter modo + construir o service. O contrato público de validação **não** pertence à factory: ele já é exercido antes, em `ValidateExtractionConfigUseCaseB3`/`ExtractionConfigServiceB3`, e o erro observado pelo usuário é `InvalidProcessingMode`, não `ValueError`.
- Factory paga seu custo quando há ≥2 caminhos de construção não-triviais (ex.: build-from-config vs build-from-cli). Não é o caso.

**Alternativas consideradas**:

- *(a) Manter factory*: rejeitada — overhead sem benefício.
- *(b) Mover lógica para `classmethod ExtractionServiceB3.create(...)`*: considerada — preserva o ponto de entrada nomeado, evita poluir o facade com construção do service. **Aceita como opção alternativa**: o implementador pode escolher essa rota se a chamada direta do facade ficar verbosa demais, desde que a validação pública continue passando por `ValidateExtractionConfigUseCaseB3`/equivalente e preserve `InvalidProcessingMode`. Decisão final: a critério do implementador, registrar no commit qual foi adotada.

### D5 — Preservar infra pesada (parsing + IO) sem mudança de comportamento

**Decisão**: `extraction_service.py` (688L), `parquet_writer.py` (461L), `cotahist_parser.py` (308L), `async_download_adapter.py` (514L), `parquet_extractor.py` (252L) são **movidos sem alteração de comportamento**. Mudanças permitidas: (a) remover herança de ABC; (b) ajustar imports relativos para o novo nível de diretório; (c) ajustar anotação de tipo de parâmetros que referenciavam ABC para apontar à classe concreta.

**Defesas de segurança preservadas como contrato**: as defesas contra path-traversal — `VerifyPathsUseCasesCVM.__validate_path_security` (`brazil/cvm/fundamental_stocks_data/application/use_cases/verify_paths_use_cases.py:91-114`, levanta `SecurityError` ao escrever em `/etc /sys /proc /dev /boot /root`) e `FileSystemServiceB3._validate_path_safety` (`brazil/b3_data/historical_quotes/infra/file_system_service.py:23-58`, mesma defesa via `relative_to` resistente a symlink) — **fazem parte do contrato observável** das classes públicas `FundamentalStocksDataCVM.download(destination_path=...)` e `HistoricalQuotesB3.extract(path_of_docs=...)`. No caso B3, a proteção é observável porque `CreateSetToDownloadUseCaseB3` chama `FileSystemServiceB3.validate_directory_path(path_of_docs)` antes da enumeração dos ZIPs. São cobertas por `tests/application/cvm_docs/test_path_traversal.py` (7 cenários) e por `tests/brazil/b3_data/historical_quotes/infra/test_file_system_service.py` antes do flattening da árvore de testes da Fase 1. Migração é **bit-idêntica**: ao colapsar `application/use_cases/` e `infra/` em `client.py`/`core.py`, a lógica completa do método deve ser preservada e a chamada deve continuar **antes** de qualquer `mkdir` ou enumeração de arquivos. Critério 4 (suíte completa) detecta regressão; o teste de path-traversal **não pode ser editado** durante a migração — só ajustes de import path e a realocação planejada em Fase 1.

**Rationale**:

- Toda a complexidade legítima da lib vive nesses 5 arquivos: streaming, threadpool, retry, integrity, atomic extraction, resource monitoring. Mexer aqui é risco de regressão sem benefício estrutural.
- Os testes de comportamento desses módulos (parser, writer, extraction service, adapter) continuam válidos sem alteração de assert; só ajuste de import path.
- Defesas de segurança (path-traversal) têm a mesma natureza: código pequeno mas **contratualmente carregado**; confundir com cerimônia (mesmo padrão mental que justifica remover `InvalidRepositoryTypeError`) seria regressão silenciosa de defesa.

**Alternativas consideradas**:

- *(a) Quebrar `extraction_service.py` (688L) em arquivos menores*: rejeitada — fora do escopo do refactor estrutural; é refactor interno do módulo, decisão separada.
- *(b) Fundir parser+writer+service em um único `extract.py`*: rejeitada — passaria de ~1500L; legibilidade pior.

### D6 — Cascata de `__init__.py` reduzida a 1 nível por subpasta direta

**Decisão**: Re-exports vivem em **dois pontos canônicos**: (1) `src/globaldatafinance/__init__.py` (raiz do pacote, expõe a API pública), e (2) `__init__.py` da pasta de cada fonte (`brazil/cvm/fundamental_stocks_data/__init__.py`, `brazil/b3_data/historical_quotes/__init__.py`), expondo apenas o que o facade público precisa para construir o cliente. Os `__init__.py` intermediários (`brazil/__init__.py`, `brazil/cvm/__init__.py`, `brazil/b3_data/__init__.py`) ficam mínimos — `brazil/__init__.py` mantém apenas o `__getattr__` lazy que já existe para resolver `FundamentalStocksDataCVM` / `HistoricalQuotesB3`. `__init__.py` de subpastas que deixam de existir (`application/`, `domain/`, `infra/`, `exceptions/`) são removidos junto com as pastas.

**Rationale**:

- Re-export de um símbolo por 5 níveis é traversal redundante sem ganho de discoverability — quem importa via API pública usa o ponto raiz; quem importa interno usa o caminho profundo direto.
- Reduzir a 2 níveis (raiz + por-feature) preserva a fronteira lógica "pasta = fonte" sem multiplicar pontos de manutenção.

**Alternativas consideradas**:

- *(a) Eliminar todos os `__init__.py` intermediários, transformando em namespace packages*: rejeitada — incompatível com `hatchling` + `src/` layout atual; risco de quebrar discovery.
- *(b) Manter cascata atual*: rejeitada — é o problema.

### D7 — Manter `brazil/<país>/<fonte>/` como eixo de extensibilidade

**Decisão**: A árvore `brazil/cvm/fundamental_stocks_data/` e `brazil/b3_data/historical_quotes/` é preservada como **pasta**, mas com conteúdo interno plano. Novas fontes (ex.: futuras `usa/sec/...`, `eu/esma/...`) seguem o mesmo padrão: nova pasta-irmã com módulos planos `core.py` / `client.py` / `http.py` / `errors.py`.

**Rationale**:

- A real extensibilidade da lib é "adicionar fonte" (CVM, B3, futuras SEC/ESMA), não "trocar implementação dentro de uma fonte". O eixo correto é geográfico/regulatório, não de camadas.
- Pasta por fonte mantém boundary físico para isolamento (testes, docs, ownership), sem custo da Clean Arch interna.

**Alternativas consideradas**:

- *(a) Mover fontes para `src/globaldatafinance/sources/<source>/`*: considerada — neutra, mas exige rename de tudo. Custo > benefício marginal.
- *(b) Fundir CVM+B3 em `brazil/`*: rejeitada — dilui o boundary e dificulta adicionar fontes de outros países depois.

### D8 — Pastas pendentes de promoção: in-place, sem mover

**Decisão**: `brazil/b3_data/{Dados_B3_Acoes, Dados_B3_FIIs, Opcoes_B3}`, `brazil/gerais/` e `brazil/app_geral.py` ficam **intocados no path atual** durante este refactor: não são deletados, não são movidos, não recebem prefixo `_legacy/`. Estão fora do escopo estrutural desta change; serão promovidos à API pública em changes OpenSpec futuras (uma por fonte), oportunidade em que cada caminho receberá tratamento próprio (correção de imports quebrados em `app_geral.py`, inclusão de testes, adoção do padrão `core.py`/`client.py`, integração ao facade público).

**Rationale**:

- Prefixar `_legacy/` sinaliza deprecação — exatamente o oposto da intenção declarada pelo owner do projeto (essas fontes vão crescer, não diminuir).
- Mover qualquer um desses paths agora adiciona blast radius e diff sem benefício: nenhum é importado pela API pública, pelos `examples/`, pelos testes ou pelo facade interno (verificado por `grep -rEn "brazil\.b3_data\.Dados_B3_Acoes|brazil\.b3_data\.Dados_B3_FIIs|brazil\.b3_data\.Opcoes_B3|brazil\.gerais|brazil\.app_geral" src tests docs examples`). O status quo já é "isolado por inatividade".
- Mantê-los visíveis no path original preserva descoberta natural quando a próxima change de promoção começar (ex.: uma change `b3-acoes-cadastrais` ataca diretamente `brazil/b3_data/Dados_B3_Acoes/`).
- `tool.ruff.lint.per-file-ignores` em `pyproject.toml` (que já trata 2 dos arquivos como exceção) **não precisa ser tocado** nesta change — paths não mudam.

**Alternativas consideradas**:

- *(a) Mover para `src/globaldatafinance/_legacy/`*: rejeitada — sinaliza deprecação e exige migrar `per-file-ignores`.
- *(b) Renomear para `_pending/`*: considerada — comunica intenção melhor, mas ainda adiciona diff de caminhos sem ganho estrutural. Rejeitada.
- *(c) Deletar*: fora de escopo — decisão semver-relevante e contraria a intenção declarada do owner.

**Out-of-scope desta change** (caberá a uma futura change "promote-legacy-sources" ou changes dedicadas por fonte):

- Consertar imports quebrados em `brazil/app_geral.py` (referencia diretórios inexistentes `Capital_Social_B3_Acoes`, `cotacao_mt5`, `Status_Invest_Acoes`).
- Aplicar o padrão `core.py`/`client.py`/`http.py` às pastas promovidas.
- Adicionar testes para cada fonte promovida.
- Atualizar `__init__.py` raiz para re-exportar novas classes públicas.

### D9 — Fases independentes, revertíveis por commit individual

**Decisão**: Implementação em 4 fases (B3 → CVM → limpeza de `__init__`/legado → docs+auditoria) precedidas por Fase 0 (baseline + tag `refactor-baseline-pre`). Cada fase é **1 commit** (ou commits aditivos coerentes) e passa `uv run pre-commit run --all-files` + `uv run pytest` antes do merge da próxima.

**Rationale**:

- Big-bang em 1 PR único é difícil de revisar e impossível de reverter parcialmente. Fases pequenas com critério de validação explícito reduzem risco e permitem `git revert <sha>` granular.
- Ordem B3 → CVM porque B3 é o caso mais inflado (30 arquivos → ~8): se o padrão sobrevive a B3, sobrevive a CVM. Inverter aumenta retrabalho.
- Fase 0 com `git tag refactor-baseline-pre` permite rollback completo via `git reset` (executado **apenas** por pedido explícito do usuário, conforme `GLOBAL_RULE.md`).

**Alternativas consideradas**:

- *(a) Tudo em 1 PR*: rejeitada — irrevisable.
- *(b) Fase única "remover ABCs" sem achatamento*: considerada como caminho conservador. Rejeitada porque deixa o problema central (cascata + use cases) intacto; refactor pela metade tende a virar débito permanente.

**Capability Isolation Guarantee**: Cada fase é uma **fronteira contratual**. O commit (ou conjunto de commits coerentes) de cada fase modifica **apenas**:

- (a) os arquivos sob `src/globaldatafinance/brazil/<país>/<capability>/` daquela fase (B3 na Fase 1; CVM na Fase 2);
- (b) o re-export correspondente em `src/globaldatafinance/brazil/__init__.py`;
- (c) o facade público da capability em `src/globaldatafinance/application/<facade>/<capability>.py`;
- (d) os testes do escopo da capability em `tests/brazil/<...>/<capability>/` e `tests/application/<facade>/`.

Não é permitido **misturar mudanças entre capabilities** no mesmo commit (ex.: tocar B3 e CVM juntos). Utilidades genéricas (`core/`, `macro_infra/`, `macro_exceptions/`) permanecem intactas em todas as fases. Quem revisa o PR vê o blast radius restrito àquela capability.

### D10 — Testes acompanham via mirror; testes de cerimônia são deletados

**Decisão**: Testes em `tests/` seguem a nova estrutura como mirror (mesmo padrão atual). Três categorias de mudança:

1. **Manter intactos** (apenas ajustar `from X import ...`): tests de comportamento real — adapter HTTP, extraction service, parquet writer, parquet extractor, value objects, validators.
2. **Reescrever** (manter assert, trocar setup): tests que injetam mock via ABC → migrar para fake duck-typed ou `monkeypatch`. Caso explícito: `tests/brazil/cvm/fundamental_stocks_data/application/use_cases/test_download_documents_use_case.py`.
3. **Deletar**: tests que só validavam contrato de ABC (`test_download_repository.py` 385L, `test_file_extractor.py` 228L) ou de factory extinta (`test_extraction_service_factory.py`). O comportamento que esses testes "cobriam" é exercitado pelos testes do adapter concreto / extraction service.

**Rationale**:

- Coverage `fail_under = 70` é critério-objetivo. Remover testes que cobrem código removido é matemática neutra (numerador e denominador caem juntos).
- Não reescrever testes válidos preserva a confiança histórica de "esses testes pegavam esses bugs antes do refactor; continuam pegando".

**Alternativas consideradas**:

- *(a) Manter testes de ABC para "documentação"*: rejeitada — testar contrato de ABC removida é teste de fantasma; quebra na primeira mudança de assinatura.
- *(b) Escrever Protocol tests com `mypy`*: considerada para futuro; fora de escopo aqui.

## Risks / Trade-offs

Riscos materiais com mitigação explícita (formato `[Risk] → Mitigation`):

- **[R1] Testes que mockam via ABC quebram em lote.** `tests/brazil/cvm/fundamental_stocks_data/application/use_cases/test_download_documents_use_case.py` usa `class MockRepository(DownloadDocsCVMRepositoryCVM)`; deixa de funcionar quando a ABC some.
  → **Mitigação**: o test é reescrito no **mesmo commit** que remove a ABC. Substitui herança por classe stub simples (duck-typed) ou `monkeypatch.setattr` no método do adapter real. Listado explicitamente no `tasks.md` (Fase 2).

- **[R2] Imports profundos em testes apontam para paths extintos.** Auditoria com `grep -rEln "from globaldatafinance\.brazil.*application\.interfaces|from globaldatafinance\.brazil.*application\.use_cases" tests` retorna **11 arquivos** (não 1, como originalmente estimado): 8 em `tests/brazil/b3_data/historical_quotes/application/`, 2 em `tests/brazil/cvm/fundamental_stocks_data/infra/adapters/` e 1 em `tests/application/cvm_docs/test_path_traversal.py`. Total de ocorrências (linhas): 11 via `grep -rEln ... | wc -l`.
  → **Mitigação**: o `--maxfail=1` no `pytest.ini` força detecção na primeira falha. Cada teste recebe o novo import no commit que removeu o path antigo. Auditoria obrigatória: rodar `grep -rEln "from globaldatafinance\.brazil.*application\.interfaces|from globaldatafinance\.brazil.*application\.use_cases" tests` **antes** de cada fase para enumerar o universo atual e **depois** para confirmar zero. O blast radius cobre ambas as fases (B3 e CVM), portanto a auditoria entra nas Fases 1 e 2.

- **[R3] Patches em `ExtractionServiceFactoryB3` (~11 ocorrências em testes B3).** `tests/brazil/b3_data/historical_quotes/application/test_extract_historical_quotes_use_case.py` tem múltiplos `patch('...ExtractionServiceFactoryB3')` — todos quebram quando a factory some.
  → **Mitigação**: search/replace coordenado no mesmo commit; `mock_factory.create.return_value = mock_service` vira `mock_extraction_service.return_value = mock_service`. Listado em `tasks.md` (Fase 1).

- **[R4] `mypy` reclama de novas assinaturas.** Trocar `repository: DownloadDocsCVMRepositoryCVM` por `adapter: AsyncDownloadAdapterCVM` muda mensagens de erro de type-check.
  → **Mitigação**: `uv run pre-commit run --all-files` ao fim de **cada passo** dentro da fase, não só ao fim da fase. `pyproject.toml` tem `disallow_untyped_defs = false`, então fases intermediárias são toleradas.

- **[R5] Coverage cai abaixo de 70% por remoção de testes de ABC.** Tirar `test_download_repository.py` (385L) e `test_file_extractor.py` (228L) reduz testes verdes; a queda de denominador (linhas cobertas) compensa, mas o saldo líquido não é garantido.
  → **Mitigação**: monitorar coverage a cada commit de fase. Se cair abaixo de 70%, escrever 1–2 testes mínimos para `client.py` (função `download_documents`) antes do commit final da fase. Coverage report comparado com baseline da Fase 0.

- **[R6] `brazil/__init__.py` quebra imports antigos não-públicos.** Símbolos `DownloadDocsCVMRepositoryCVM`, `FileExtractorRepositoryCVM`, `*UseCase*`, `ExtractionServiceFactoryB3` deixam de ser re-exportados.
  → **Mitigação**: `__init__.py` só re-exporta o que o **facade público** precisa — auditado pela inspeção de `application/cvm_docs/fundamental_stocks_data.py` e `application/b3_docs/historical_quotes.py`. Quem importava paths internos eram os testes (já enumerados) — não há caller externo na PyPI release atual.

- **[R7] `elapsed_time` em `DownloadResultCVM` precisa ser preservado.** `DownloadDocumentsUseCaseCVM` atual mede `time.time()` antes/depois e seta `result.elapsed_time` — o `DownloadResultFormatter` lê esse campo.
  → **Mitigação**: a função substituta `download_documents` em `client.py` mantém a medição explícita. Verificado por `grep -n "elapsed_time" src tests` — formatter e testes confirmam dependência.

- **[R8] `AvailableAssetsServiceB3.get_tpmerc_codes_for_assets` usa `print(...)` (linha 114 de `available_assets_service.py`).** Viola regra do `CLAUDE.md` (somente `logger` fora de formatters). Já está no código antes do refactor.
  → **Mitigação**: corrigir para `logger.warning(...)` no commit que move o arquivo para `core.py` (Fase 1). É 2 linhas de mudança; risco zero.

- **[R9] `brazil/app_geral.py` está quebrado e nunca importado (`ImportError` se chamado).** Importa `Capital_Social_B3_Acoes`, `cotacao_mt5`, `Status_Invest_Acoes` — diretórios inexistentes.
  → **Mitigação**: classificar como legado na Fase 3. Não bloqueia o refactor; é evidência adicional de que essa parte da árvore está abandonada.

- **[R10] ~~`tool.ruff.lint.per-file-ignores`~~** — **N/A nesta change**. D8 foi resolvido para in-place; paths legados não mudam, portanto os `per-file-ignores` continuam apontando para os caminhos corretos sem alteração em `pyproject.toml`.

- **[R11] Defesas de path-traversal podem ser silenciosamente removidas durante o colapso de camadas.** `VerifyPathsUseCasesCVM.__validate_path_security` (`brazil/cvm/.../verify_paths_use_cases.py:91-114`) e `FileSystemServiceB3._validate_path_safety` (`brazil/b3_data/.../file_system_service.py:23-58`) levantam `SecurityError` para paths em `/etc /sys /proc /dev /boot /root`. Ao migrar `verify_paths_use_cases.py` (CVM) e `file_system_service.py` (B3) para `client.py`/`core.py`, o método com double-underscore mascarado pode ser confundido com cerimônia (mesmo padrão mental que justifica remover `InvalidRepositoryTypeError`). Critérios 1, 3 e 5 não detectam (assinatura/smoke binário/import público inalterados); só Critério 4 pega — e ali o teste pode ser "ajustado" se o implementador interpretar errado.
  → **Mitigação**: (a) D5 atualizado para reconhecer essas defesas como contrato preservado; (b) tarefas explícitas em Fase 1 (B3) e Fase 2 (CVM) determinam preservar bit-idêntica a função e o call-site **antes** de qualquer `mkdir`; (c) gate dedicado nas Fases 1, 2 e Final: `uv run pytest tests/application/cvm_docs/test_path_traversal.py` e o teste B3 equivalente após a realocação planejada devem passar **sem edição do corpo dos testes**; (d) audit final na Fase 6 usa escopo focado na capability — `grep -rEcn "SecurityError" src/globaldatafinance/brazil/cvm/fundamental_stocks_data src/globaldatafinance/brazil/b3_data/historical_quotes tests/application/cvm_docs tests/brazil/b3_data/historical_quotes | awk -F: '{sum+=$NF} END {print sum}'` — evitando ruído de `macro_exceptions`.

Trade-offs aceitos (custos conscientes do design):

- **Perda de "preparação para múltiplas implementações"**: se um dia precisar de `WgetDownloadAdapter` além do async, será preciso extrair ABC/Protocol naquele momento. Custo: 1 commit extra no futuro. Benefício hoje: −60 arquivos.
- **Imports internos não-versionados quebram**: qualquer dependente externo que tenha importado `globaldatafinance.brazil.cvm.fundamental_stocks_data.application.use_cases.*` (sem garantia de estabilidade) quebra. Justificativa: nunca foi superfície semver; o `__init__.py` raiz é o único contrato.
- **`tasks.md` da Fase 4 tem trabalho de docs**: atualizar `AGENTS.md`, `docs/dev-guide/architecture.md` e 2 READMEs internos é manual. Custo: 1 fase dedicada. Benefício: docs não viram fonte de confusão.

## Migration Plan

Migração em 4 fases sequenciais + Fase 0 (baseline) + Final Phase (validação consolidada). Detalhe operacional (passos numerados, comandos, critérios de aceite) vive em `tasks.md`; aqui ficam os marcos arquiteturais.

| Fase | Escopo | Commit-tipo | Rollback |
|---|---|---|---|
| 0 | Baseline: `git status` limpo, tag `refactor-baseline-pre`, baseline `pre-commit`+`pytest`+contagem | `chore(refactor): baseline before anti-overengineering pass` | tag preserva snapshot |
| 1 | B3 `historical_quotes`: colapsar `domain/`+`application/`+`infra/`+`exceptions/` em `core.py`+`client.py`+`extract.py`+`errors.py`+`cotahist_parser.py`+`parquet_writer.py`+`extraction_service.py`. Remover factory. | `refactor(b3): collapse historical_quotes layers to flat module structure` | `git revert <sha-fase-1>` |
| 2 | CVM `fundamental_stocks_data`: colapsar camadas, remover 2 ABCs + `InvalidRepositoryTypeError`, converter use cases em funções. | `refactor(cvm): collapse fundamental_stocks_data layers, drop single-impl ABCs` | `git revert <sha-fase-2>` |
| 3 | Limpar cascata de `__init__.py`. Pastas pendentes de promoção (D8) ficam in-place — apenas confirmar via grep que continuam sem callers internos e adicionar nota explicativa em `AGENTS.md`/`architecture.md`. | `refactor: prune __init__ cascade` | `git revert <sha-fase-3>` |
| 4 | Atualizar `AGENTS.md`, `docs/dev-guide/architecture.md`, READMEs internos. Rodar suíte completa + integration. Auditoria final. | `docs: align AGENTS and dev-guide with flat per-source layout` | `git revert <sha-fase-4>` |

### Behavioral Equivalence Criteria per Capability

Cada fase que modifica uma capability (Fase 1 = B3, Fase 2 = CVM) só fecha quando **os 5 critérios abaixo passam, sem exceção**. Não há "passa parcial" nem "corrijo depois".

**Pré-Fase 0 — Gravar baselines** (uma única vez, antes da Fase 0 começar):

- `openspec/changes/refactor-anti-overengineering/baseline/api_surface.json` — snapshot da **superfície pública sancionada do facade**:
  - **Exports top-level**: `sorted(globaldatafinance.__all__)` — captura apenas os nomes oficialmente re-exportados pelo pacote raiz.
  - **Assinaturas públicas**: `inspect.signature` dos métodos públicos de `FundamentalStocksDataCVM` e `HistoricalQuotesB3` (`download`, `extract`, `get_available_docs`, `get_available_years`, `get_available_assets`).
  - **Representação pública**: `repr(FundamentalStocksDataCVM())` e `repr(HistoricalQuotesB3())`.
  - **Exclusões deliberadas**: não serializar `__doc__`, exceções inferidas por parsing de código, nem `dir(instance)`; esses itens congelariam detalhes incidentais do objeto e criariam falso contrato semver. Garantias comportamentais de exceção ficam nos delta specs e nos testes direcionados.
  Gerado por script idempotente `scripts/capture_api_surface.py` (criado nesta change).
- `openspec/changes/refactor-anti-overengineering/baseline/coverage_per_capability.json` — coverage report do baseline segmentado por capability (`tests/brazil/b3_data + tests/application/b3_docs` e `tests/brazil/cvm + tests/application/cvm_docs`). Gerado por `uv run pytest --cov=...` por subconjunto.
- `openspec/changes/refactor-anti-overengineering/baseline/pytest_inventory.txt` — saída de `uv run pytest --collect-only -q`, lista canônica de todos os testes coletados.

Esses 3 arquivos são **artefatos versionados** da change (commitados no PR da Fase 0). Cada fase posterior compara contra eles.

**Critério 1 — API surface lock (zero diff)**

```bash
uv run python scripts/capture_api_surface.py > /tmp/api_surface_post.json
diff openspec/changes/refactor-anti-overengineering/baseline/api_surface.json /tmp/api_surface_post.json
# Esperado: diff vazio (exit 0)
```

Qualquer diff bloqueia a fase. Mudança em exports top-level, `repr` ou assinatura pública é violação direta do non-goal "não alterar API pública". Exceções e regras comportamentais continuam congeladas pelos delta specs e pelos testes direcionados.

**Critério 2 — Per-capability test gate (coverage não regride no escopo isolado)**

Para Fase 1 (B3):

```bash
uv run pytest tests/brazil/b3_data tests/application/b3_docs \
  --cov=src/globaldatafinance/brazil/b3_data \
  --cov=src/globaldatafinance/application/b3_docs \
  --cov-report=json:/tmp/cov_b3_post.json --cov-report=term-missing -q

# Comparação numérica machine-readable (não vibe-check):
uv run python -c "
import json, sys
base = json.load(open('openspec/changes/refactor-anti-overengineering/baseline/coverage_per_capability.json'))['b3']['totals']['percent_covered']
post = json.load(open('/tmp/cov_b3_post.json'))['totals']['percent_covered']
print(f'baseline={base:.2f}% post={post:.2f}% delta={post-base:+.2f}pp')
sys.exit(0 if post >= base else 1)
"
# Esperado: todos os testes passam; exit 0 (post ≥ base).
```

Para Fase 2 (CVM): mesma estrutura apontando para `tests/brazil/cvm` + `tests/application/cvm_docs` e cobertura em `src/globaldatafinance/brazil/cvm` + `src/globaldatafinance/application/cvm_docs`, com `--cov-report=json:/tmp/cov_cvm_post.json` e o mesmo bloco de comparação Python apontando para a chave `cvm`.

Coverage **não pode cair vs baseline da capability** registrado em `baseline/coverage_per_capability.json` (formato canônico: `{"b3": {<json from coverage>}, "cvm": {<json from coverage>}}`). Esta regra **é mais estrita que o `fail_under = 70` do `pytest.ini`**: se a capability hoje está em 85% e cair para 72% (ainda acima do floor global), a fase é bloqueada. O floor de 70% é o piso do projeto inteiro; a regra de não-regressão por capability é a salvaguarda específica deste refactor. Se cair (R5), escrever testes mínimos para a nova superfície (`client.py` da capability) **antes** de fechar a fase.

**Critério 3 — Behavioral smoke local (sem rede, bit-equivalente)**

Para cada capability, um script de smoke que exercita o caminho público com fixtures locais (sem rede):

- `scripts/smoke_b3.py` — usa um ZIP COTAHIST de teste presente em `tests/fixtures/` **ou** gerado deterministicamente pelo próprio script (bytes fixos, sem `random` / `time` / timestamps embutidos; se gerado, conteúdo precisa ser hash-estável entre execuções). Chama `HistoricalQuotesB3().extract(...)` para diretório temporário e captura: (a) lista **basename-only** de arquivos Parquet gerados (sem path absoluto — F2 mitigation); (b) hash SHA256 de cada arquivo; (c) schema dos Parquet (colunas + dtypes via `pyarrow.parquet.read_schema`). Saída em JSON com chaves ordenadas. **Determinismo (obrigatório):**
  - Construir entradas do ZIP via `zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))` explícito; nunca usar `ZipFile.write(path)` que herda `mtime` do filesystem.
  - Ao escrever Parquet, controlar não-determinismo do `pyarrow.parquet.write_table`: usar `compression='snappy'` (estável) ou `'none'`; passar `write_statistics=False` para evitar variância de estatísticas (min/max/null_count) em execuções repetidas; passar `use_dictionary=False` se a ordem do dicionário variar (verificar com 2 execuções).
  - Não capturar timestamps (`os.path.getmtime`, `datetime.now()`) na saída.
  - Normalizar paths em (a) com `os.path.basename(...)` antes de serializar.
  **Pré-condição da Fase 0**: rodar o script duas vezes consecutivas no estado baseline e confirmar saída bit-idêntica antes de gravar `baseline/smoke_b3.json` — se as duas execuções diferirem, o script tem fonte de não-determinismo e precisa ser corrigido antes de seguir.
- `scripts/smoke_cvm.py` — análogo, mas chamando `FundamentalStocksDataCVM` com um ZIP CVM de fixture local. Para `download(...)`, **usar `httpx.MockTransport`** com resposta fixa (preferido — exercita o caminho que o refactor mais ataca: download → use-case → adapter wiring); a alternativa "só `get_available_docs()` + `get_available_years()`" é insuficiente porque não cobre o flow de download/extracção. Mesmas regras de determinismo do smoke B3.

Baselines gerados na Fase 0 (`baseline/smoke_b3.json`, `baseline/smoke_cvm.json`). Critério:

```bash
uv run python scripts/smoke_b3.py > /tmp/smoke_b3_post.json
diff openspec/changes/refactor-anti-overengineering/baseline/smoke_b3.json /tmp/smoke_b3_post.json
# Esperado: diff vazio
```

Bit-equivalência do output Parquet é a garantia mais forte de "comportamento idêntico" — qualquer regressão silenciosa em parser/writer aparece aqui.

**Critério 4 — Suíte completa verde**

```bash
uv run pre-commit run --all-files
uv run pytest
```

Ambos verdes. `--maxfail=1` no `pytest.ini` força detecção precoce.

**Critério 5 — Smoke público (import + construção)**

```bash
uv run python -c "from globaldatafinance import FundamentalStocksDataCVM, HistoricalQuotesB3; print(FundamentalStocksDataCVM().__class__.__name__, HistoricalQuotesB3().__class__.__name__)"
# Esperado: FundamentalStocksDataCVM HistoricalQuotesB3
```

Mais o smoke de import dos exemplos:

```bash
uv run python -c "import pathlib; p=pathlib.Path('examples/cvm_docs.py'); compile(p.read_text(), str(p), 'exec')"
uv run python -c "import pathlib; p=pathlib.Path('examples/historical_quotes.py'); compile(p.read_text(), str(p), 'exec')"
```

**Hard rule (não-negociável)**:

> **Fase N+1 não inicia enquanto Fase N tiver qualquer critério acima pendente.** Sem exceção. Sem "corrijo na próxima fase". Se um critério falhar após o commit da fase, a única ação permitida é (a) commit aditivo na mesma branch corrigindo, ou (b) `git revert <sha-fase-N>`. Avanço lateral para a próxima capability é proibido.

Para Fases 3 e 4 (limpeza de `__init__` + docs), os critérios 1, 4 e 5 continuam obrigatórios. Critérios 2 e 3 são opcionais (a Fase 3 não toca código de capability; a Fase 4 só toca docs).

**Rollback de emergência** (somente com pedido explícito do usuário, per `GLOBAL_RULE.md`):

```bash
git reset --hard refactor-baseline-pre
```

**Final Phase** consolida: `git diff --name-only refactor-baseline-pre..HEAD`, re-rodar `pre-commit` nos arquivos alterados, `pytest` completo (incluindo `-m integration`), auditoria de contagem (one-liner da Fase 6 em `tasks.md`), confirmar que nenhum check ficou pendente.

## Open Questions

1. ~~`_legacy/` vs in-place?~~ **Resolvida** (ver D8 atualizado): pastas pendentes de promoção ficam in-place. Sem move, sem prefixo `_legacy/`, sem mudança em `pyproject.toml`. Consertar/promover é responsabilidade de changes OpenSpec futuras dedicadas a cada fonte.

2. **`classmethod ExtractionServiceB3.create(...)` ou construção direta no facade?** (D4 alternativa b) Ambos são aceitáveis; o implementador decide com base na verbosidade resultante no `application/b3_docs/historical_quotes.py`. Registrar no commit.

3. ~~`print(...)` em `available_assets_service.py:114`?~~ **Resolvida**: dentro do escopo. A correção `print(...)` → `logger.warning(...)` é feita no commit que move o arquivo para `core.py` (Fase 1, passo 1.1) — 2 linhas, risco zero, contexto correto (arquivo já está sendo tocado).

4. **Nomes finais dos módulos planos (`core.py`, `client.py`, `http.py`, `extract.py`, `errors.py`):** o design fixa o **padrão**, mas o implementador pode renomear 1–2 (ex.: `services.py` em vez de `client.py`) se a leitura ficar mais natural para uma fonte específica. Registrar no commit.

5. **Quebrar `extraction_service.py` (688L)?** Está fora do escopo (D5). Se durante o refactor ficar evidente que o módulo é grande demais para coexistir com `client.py`, manter como arquivo próprio (`extraction_service.py` no nível plano) — **não** colapsar em `extract.py`. Decisão técnica de leitura.
