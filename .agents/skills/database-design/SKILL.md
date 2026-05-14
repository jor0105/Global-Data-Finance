---
name: database-design
description: >
  Use para desenhar, revisar ou refatorar schema, constraints, tipos de dados,
  indices, migrations, estrategia de acesso e consistencia de banco, focadas totalmente em banco de dados. Ative quando
  o usuario pedir "desenha o modelo", "essa query esta lenta", "qual indice eu uso?",
  "como faco a migration?", "isso deveria ser tabela ou JSON?", "esse campo devia ser
  string ou numero?", ou quando houver decisao estrutural de persistencia. Se o foco
  principal for RLS, grants, service_role, pooling ou tuning especifico de
  Supabase/Postgres, prefira `supabase-postgres-best-practices`.
---

# Database Design

## Fundamentos nao-obvios

Absorva estes pontos antes de propor qualquer solucao. Eles concentram os erros
mais caros, menos visiveis e mais comuns em modelagem e evolucao de banco real:

**Schema nasce dos acessos, nao do habito:** comecar pelo diagrama sem entender
o que precisa ser lido, filtrado, ordenado, agregado e escrito cria modelos
elegantes no papel e caros no runtime. Pergunte primeiro quais sao os fluxos
criticos de leitura, escrita e isolamento.

**Tipo de dado e contrato de negocio:** `price` como texto, `is_active` como
string e `created_at` como texto nao sao detalhes cosmeticos. Eles quebram
integridade, pioram comparacoes, desperdicam indice e tornam bugs mais faceis.
Use tipos que expressem semantica nativamente.

**Constraint no banco vale mais que boa intencao na aplicacao:** `NOT NULL`,
`UNIQUE`, `CHECK`, FK e chaves compostas evitam estados invalidos mesmo quando
o caller, o job ou o script de manutencao erram. Regra importante que so existe
no codigo de aplicacao ainda esta vulneravel.

**Indice e imposto sobre escrita:** cada indice melhora alguns caminhos de
leitura e piora inserts, updates, storage e manutencao. O criterio nunca deve
ser "coluna importante"; deve ser `WHERE`, `JOIN`, `ORDER BY`, seletividade e
frequencia real da query.

**Migration e parte do design, nao pos-script:** coluna nova, rename, backfill,
`NOT NULL`, `DROP COLUMN` e novos indices mudam risco operacional. Se a resposta
nao disser como o rollout acontece, o desenho ainda esta incompleto.

**Isolamento de dados deve viver na camada mais baixa confiavel:** lookup direto
por ID sem ownership, escopo de tenant ou predicate equivalente e um bug de
design de dados, nao so de API. Se a mudanca toca dados sensiveis, modele
ownership e tenant scope desde o schema.

**Consistencia concorrente precisa de owner explicito:** se dois atores podem
escrever o mesmo recurso, escolha cedo se a garantia vira de `UNIQUE`, transacao,
upsert, lock otimista ou lock pessimista. Nao deixe colisao silenciosa como
comportamento padrao.

---

## Roteamento para referencias

Os caminhos abaixo sao relativos a esta pasta. Leia apenas os arquivos relevantes
para o problema em maos:

| Problema | Arquivo |
|---|---|
| Escolher engine, topologia e limites de consistencia/operacao | `references/database-selection.md` |
| Desenhar entidades, relacionamentos, ownership, constraints e lifecycle | `references/schema-design.md` |
| Escolher tipos de dados corretos para semantica, storage e performance | `references/data-types.md` |
| Definir indices por filtro, sort, join e seletividade | `references/indexing.md` |
| Planejar migrations seguras e rollout aditivo | `references/migrations.md` |
| Investigar query lenta e diagnosticar gargalo | `references/optimization.md` |
| Escolher ORM, query builder ou SQL raw | `references/orm-selection.md` |
| Modelar isolamento, ownership e superficie de dados | `references/security-isolation.md` |
| Escolher estrategia de consistencia e concorrencia | `references/consistency-concurrency.md` |
| Consultar matriz operacional e roteamento para skills vizinhas | `references/reference.md` |
| Ver exemplos completos de resposta e modelagem | `references/examples.md` |

Se o problema tocar RLS, grants, `service_role`, pooling, `pg_stat_statements`,
locks ou tuning claramente especifico de Postgres/Supabase, leia ou encaminhe
para `../supabase-postgres-best-practices/SKILL.md` antes de aprofundar.

## Procedimento

1. Identifique workload, ownership e contexto de engine antes do desenho.
   Pergunte mentalmente: OLTP ou analytics? multi-tenant? alta escrita? edge?
   precisa de joins fortes? ha requisito de auditoria ou historico? o banco ja
   existe ou a mudanca e incremental?

2. Liste os caminhos criticos de acesso antes do ERD.
   Cubra pelo menos:
   - leituras mais frequentes
   - filtros e ordenacao dominantes
   - escritas concorrentes
   - agregacoes ou relatorios pesados
   - requisitos de isolamento por usuario, workspace ou tenant

3. Desenhe entidades, chaves e tipos como contrato de negocio.
   Defina PK, FK, nulidade, `UNIQUE`, `CHECK`, colunas de escopo, audit fields e
   tipos corretos antes de discutir ORM ou indices.

4. Escolha constraints e estrategia de consistencia explicitamente.
   Se a corretude depende de unicidade, ordenacao de estado, saldo, deduplicacao
   ou escrita idempotente, diga qual controle vive no banco e qual fica na app.

5. Escolha indices pela forma da query, nao pela coluna isolada.
   Para cada query critica, responda: igualdade? range? join? sort? indice parcial?
   composto? covering? `GIN/GiST/BRIN`? FK sem indice?

6. Planeje rollout e migration junto com a resposta.
   Diferencie claramente:
   - schema novo
   - schema legado com backfill
   - rename seguro
   - enforce tardio de `NOT NULL`
   - operacao destrutiva adiada

7. Roteie profundidade especifica de engine quando necessario.
   `database-design` fecha a decisao estrutural. Quando o gargalo virar
   comportamento especifico de Supabase/Postgres, delegate para a skill
   especializada em vez de duplicar detalhes de RLS, grants ou tuning fino.

8. Se a tarefa tocar schema, migration ou troubleshooting estrutural, rode
   `python scripts/schema_checker.py <path>` como triagem heuristica.
   Use o resultado como checklist inicial, nao como veredito final.

---

## Formato de saida recomendado

Quando a conversa pedir desenho, review ou correcao estrutural de banco, prefira
responder neste shape:

```yaml
database_design_review:
  workload:
    shape: <oltp|analytics|hybrid>
    write_profile: <read-heavy|balanced|write-heavy>
    engine_context: <postgres|mysql|sqlite|duckdb|unknown>
  access_patterns:
    critical_reads:
      - <query ou fluxo>
    critical_writes:
      - <mutacao ou job>
    isolation_scope: <user|workspace|tenant|public|mixed>
  schema:
    entities:
      - <entidade e papel>
    relationships:
      - <fk, cardinalidade, ownership>
    data_types:
      - <campo, tipo escolhido, anti-pattern evitado>
  integrity:
    constraints:
      - <pk, fk, unique, check, not null>
    consistency_strategy:
      - <transaction|unique|upsert|optimistic|pessimistic>
  indexing:
    required:
      - <indice e query atendida>
    avoided:
      - <indice descartado e motivo>
  security_isolation:
    controls:
      - <ownership, tenant scope, least privilege>
    route_to_specialized_skill: <quando aplicavel>
  migration_rollout:
    plan:
      - <passo de rollout>
    risky_operations:
      - <drop/not null/rename/index>
  diagnostics:
    evidence_needed:
      - <explain analyze, row counts, query shape, workload real>
  negative_tests:
    - <tenant errado>
    - <tipo invalido>
    - <concorrencia ou duplicidade>
  notes:
    - <trade-off ou risco remanescente>
```

Se o usuario pediu implementacao, use esse shape como checklist interno e entao
edite o codigo diretamente.

## Scripts

- `scripts/schema_checker.py`: triagem heuristica de schema, migration e tipos
  suspeitos. Nao prova performance real, nao valida RLS por completo e nao
  substitui review contextual.

## Exemplos

### Caso positivo - modelagem read-heavy

**Entrada:** "Preciso modelar pedidos, itens e pagamentos com historico rapido do cliente."
**Saida esperada:** identificar leituras criticas, propor entidades e ownership,
escolher PK/FK/tipos, ligar indices as queries centrais e descrever migration
aditiva se o schema ja existir.

### Caso positivo - tipo de dado corrigido cedo

**Entrada:** "Hoje `price` e `created_at` sao strings. Isso esta ok?"
**Saida esperada:** apontar problema de semantica, performance e validacao;
sugerir tipo numerico exato para dinheiro e tipo temporal apropriado; explicar
quando string seria aceitavel para identificadores nao aritmeticos.

### Caso positivo - query lenta com indice composto

**Entrada:** "Minha query filtra por `workspace_id` e `status`, ordena por `created_at`."
**Saida esperada:** pedir shape da query, cardinalidade e ordenacao; sugerir
indice composto ou parcial alinhado ao `WHERE`/`ORDER BY`; evitar resposta
generica de criar indice em cada coluna isolada.

### Caso positivo - migration arriscada desacoplada

**Entrada:** "Vou renomear a coluna e dar `DROP COLUMN` da antiga no mesmo deploy."
**Saida esperada:** recusar rollout destrutivo em uma etapa; propor add/copy/read
switch/drop tardio ou plano equivalente e explicitar risco operacional.

### Caso negativo - problema especifico de Supabase/Postgres

**Entrada:** "Minha policy RLS no Supabase esta lenta e preciso revisar grants."
**Por que nao:** o problema principal nao e modelagem geral; encaminhe para
`supabase-postgres-best-practices`.

### Caso negativo - tarefa fora de persistencia estrutural

**Entrada:** "Escreve um SELECT simples com WHERE."
**Por que nao:** nao ha decisao estrutural de schema, tipo, migration ou indice.
Responda diretamente ou use skill de query se houver necessidade analitica maior.

---

## Evals de trigger

**Deve acionar:**

- "Desenha o schema dessa feature multi-tenant."
- "Essa query esta lenta; qual indice faz sentido?"
- "Esse campo deveria ser `numeric` ou string?"
- "Como faco uma migration segura para renomear essa coluna?"
- "Vale ORM aqui ou SQL raw?"
- "Preciso decidir constraints e ownership dessa entidade."

**Nao deve acionar:**

- "RLS do Supabase esta lenta e acho que a policy esta ruim."
  *(near-miss: toca banco, mas o centro e tuning/RLS especifico de Supabase/Postgres)*
- "Como estruturo esse endpoint REST?"
  *(near-miss: contrato de API, nao design de banco)*
- "Escreve um SELECT com WHERE e ORDER BY."
  *(fora do escopo estrutural)*
- "Ajusta o layout mobile dessa tela."
  *(fora do escopo)*

---

## Evals de workflow

### Cenario: modelagem read-heavy

**Entrada:** "Nova feature de pedidos com dashboard que lista pedidos por cliente e status."

Assertions:

- [ ] resposta comeca pelos acessos criticos antes do ERD
- [ ] define ownership, PK/FK e tipo de dado relevante
- [ ] propoe indice ligado ao filtro e ordenacao reais
- [ ] menciona rollout se o schema nao for greenfield

### Cenario: tipo de dado incorreto

**Entrada:** "Hoje `amount` e `is_active` sao `varchar`."

Assertions:

- [ ] identifica problema de semantica e integridade
- [ ] sugere tipo numerico/boolean apropriado
- [ ] distingue numero de negocio de identificador que deve continuar string
- [ ] referencia `references/data-types.md` ou aplica seus criterios

### Cenario: migration destrutiva

**Entrada:** "Vou adicionar `NOT NULL` e apagar a coluna antiga no mesmo deploy."

Assertions:

- [ ] sinaliza risco operacional
- [ ] propoe sequencia aditiva ou rollout em fases
- [ ] nao trata `DROP COLUMN` unico como padrao seguro
- [ ] referencia `references/migrations.md` ou aplica seus criterios

### Cenario: escolha de indice

**Entrada:** "Filtro por `workspace_id`, `status` e ordenacao por `created_at desc`."

Assertions:

- [ ] pede ou infere shape da query antes de sugerir indice
- [ ] considera indice composto ou parcial
- [ ] nao sugere indice por coluna de forma automatica
- [ ] referencia `references/indexing.md` ou aplica seus criterios

### Cenario: consistencia concorrente

**Entrada:** "Dois jobs podem gravar a mesma conciliacao ao mesmo tempo."

Assertions:

- [ ] escolhe estrategia explicita de consistencia
- [ ] usa `UNIQUE`, upsert, transacao ou lock com criterio
- [ ] nao deixa deduplicacao so na aplicacao
- [ ] referencia `references/consistency-concurrency.md` ou aplica seus criterios

### Cenario: roteamento para skill especializada

**Entrada:** "Preciso otimizar policy RLS e grants no Supabase."

Assertions:

- [ ] reconhece que o problema principal saiu do escopo generalista
- [ ] encaminha para `supabase-postgres-best-practices`
- [ ] nao tenta substituir detalhe especifico de engine com conselho generico

---

## Checklist antes de entregar

- [ ] Workload e engine context identificados
- [ ] Leituras, escritas e isolamento criticos mapeados
- [ ] PK, FK, nulidade, `UNIQUE`, `CHECK` e ownership pensados explicitamente
- [ ] Tipos de dados escolhidos pela semantica, nao por conveniencia
- [ ] Indices ligados a `WHERE`, `JOIN` e `ORDER BY` reais
- [ ] Risco de N+1, over-indexing e JSON/document abuse revisado
- [ ] Estrategia de consistencia concorrente definida quando houver escrita disputada
- [ ] Migration e rollout descritos junto com o schema
- [ ] Problemas especificos de Supabase/Postgres roteados para skill especializada
- [ ] `scripts/schema_checker.py` rodado quando a tarefa tocar schema ou migration
