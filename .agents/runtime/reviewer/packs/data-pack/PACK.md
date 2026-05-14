# data-pack

## Scope

Schemas, queries, RLS, mapeamentos, cache e integridade de dados.

## Checklist

- `DATA-CONTRACT`: schema ou shape mudou com compatibilidade clara?
- `DATA-QUERY`: query continua correta, eficiente e com filtros defensivos?
- `DATA-RLS`: policy e ownership continuam coerentes?

## Heuristics

- Mudancas em query ou schema que alteram retorno esperado sobem para `warning` ou `blocker`.
