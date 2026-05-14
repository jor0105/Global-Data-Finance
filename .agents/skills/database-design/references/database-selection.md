# Database Selection

> Escolha engine e topologia a partir de workload, consistencia e operacao.
> Nao escolha banco por moda, SDK favorito ou benchmark sem contexto.

## Perguntas que mudam a decisao

1. O problema principal e OLTP, analytics ou hibrido?
2. A aplicacao precisa de joins fortes, transacoes e constraints ricas?
3. A carga e read-heavy, write-heavy ou bursty?
4. A latencia local/edge importa mais que funcionalidade relacional?
5. Existe requisito de isolamento multi-tenant ou ownership forte?
6. O time consegue operar o banco ou precisa terceirizar isso?
7. O schema vai evoluir com frequencia e exigir migrations seguras?

## Arvore de decisao curta

```text
Comece pelo workload
|
|-- OLTP com joins, constraints e transacoes fortes
|   |-- Self-hosted ou cloud tradicional -> PostgreSQL
|   `-- Managed/serverless -> Postgres managed (ex: Neon, Supabase, RDS, AlloyDB)
|
|-- Analytics local, ETL, regulatorio, exploracao colunar
|   `-- DuckDB / warehouse / lakehouse
|
|-- App simples, single-writer, local-first, embedded
|   `-- SQLite
|
|-- Edge/localidade extrema com relacional simples
|   `-- SQLite edge/Turso com limites claros
|
`-- Distribuicao global primeiro, trade-offs relacionais aceitos
    `-- MySQL distribuidos / NewSQL / arquitetura especializada
```

## Heuristicas praticas

- Se a resposta precisa de FK, `CHECK`, `UNIQUE`, joins complexos e transacao
  consistente, a barra para sair de PostgreSQL e alta.
- Se o problema principal e leitura analitica grande, tabela larga, ETL ou
  exploracao ad hoc, banco transacional sozinho nao substitui um motor colunar.
- SQLite e excelente quando simplicidade e single-process/importancia local
  superam concorrencia de escrita e operacao distribuida.
- "Serverless" resolve operacao, nao modelagem ruim. Migrations inseguras,
  tipos ruins e ownership ausente continuam ruins em banco managed.

## Matriz de escolha rapida

| Contexto | Boa opcao | Trade-off principal |
|---|---|---|
| SaaS transacional com multi-tenant, auth e dashboard | PostgreSQL | Mais disciplina operacional e migrations cuidadosas |
| ETL local, CVM, exploracao analitica | DuckDB | Nao substitui OLTP concorrente |
| Ferramenta local, CLI, app embarcado | SQLite | Concorrencia de escrita limitada |
| Edge-first simples | SQLite edge/Turso | Limites de SQL, locking e ecossistema |
| Distribuicao global extrema | Engine especializada | Custo de consistencia, features relacionais ou operacao |

## Sinais de que a escolha esta errada

- O time evita constraints porque "o banco nao ajuda".
- Workflows criticos viram compensacao manual na app.
- Consultas analiticas pesadas brigam com trafego transacional normal.
- Edge/localidade foi escolhida, mas a aplicacao depende de joins fortes e
  escrita concorrente frequente.

## Quando rotear para outra skill

- Supabase/Postgres com foco em RLS, grants, pooling, `pg_stat_statements` ou
  tuning especifico -> `supabase-postgres-best-practices`
- Contrato de endpoint, shape de erro, paginacao ou streaming -> `api-patterns`
