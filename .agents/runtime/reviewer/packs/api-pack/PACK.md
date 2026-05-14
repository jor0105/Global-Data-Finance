# api-pack

## Scope

Contratos HTTP, parsing, validacao, erros, SSE e compatibilidade de payload.

## Checklist

- `API-CONTRACT`: request/response mudou de forma compativel?
- `API-ERRORS`: falhas retornam status e mensagem consistentes?
- `API-BOUNDARY`: o handler impede input ambiguo ou invalido?

## Heuristics

- `warning` para erros de robustez sem quebra direta confirmada.
- `blocker` para quebra de contrato, parse inseguro ou regressao deterministica.
