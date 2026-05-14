# Reference

## Mapa rapido do pacote

| Se a duvida for... | Leia |
|---|---|
| engine e topologia | `database-selection.md` |
| entidades, ownership, lifecycle | `schema-design.md` |
| tipo de dado correto | `data-types.md` |
| indice por query shape | `indexing.md` |
| rollout e migration segura | `migrations.md` |
| query lenta e gargalo | `optimization.md` |
| ORM vs query builder vs SQL raw | `orm-selection.md` |
| isolamento e least privilege | `security-isolation.md` |
| consistencia, upsert e lock | `consistency-concurrency.md` |
| exemplos de resposta | `examples.md` |

## Perguntas de triagem

- Qual e o caminho critico de leitura e escrita?
- O dado precisa de ownership ou tenant scope?
- O tipo escolhido expressa a semantica certa?
- A regra de negocio pode virar constraint?
- O rollout esta claro ou a resposta parou no ERD?

## Limites desta skill

- Nao e skill para query trivial, ajuste cosmetico ou review de API.
- Nao substitui tuning detalhado de Supabase/Postgres, RLS, grants ou pooling.
- Nao prova performance sem evidencia de runtime.

## Roteamento para skills vizinhas

- `supabase-postgres-best-practices`
  - use quando o centro do problema for RLS, grants, `service_role`, pooling,
    tuning especifico de Postgres/Supabase, `pg_stat_statements` ou locks finos
- `api-patterns`
  - use quando a decisao central for contrato HTTP, authz de endpoint, paginacao,
    streaming, versionamento ou webhook
- `query-hunter`
  - use quando o pedido for execucao analitica complexa, join/agg real ou plano
    de consulta multi-fonte
- `testing-patterns`
  - use quando a pergunta principal virar como provar isolamento, concorrencia ou
    regressao por testes
