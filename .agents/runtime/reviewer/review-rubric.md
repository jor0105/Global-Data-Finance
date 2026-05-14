# Review Rubric

Esta rubrica e asset interna do `reviewer`. Ela define checklist IDs suportados, calibracao de severidade e confidence, e a politica minima de bloqueio do veredito.

## Checklist IDs

- `SEC-TRUST`
- `SEC-AUTHZ`
- `API-CONTRACT`
- `API-ERRORS`
- `DATA-CONTRACT`
- `DATA-QUERY`
- `FE-STATE`
- `FE-UX`
- `TEST-COVERAGE`
- `TEST-REGRESSION`

## Severity

- `blocker`: quebra comportamento, contrato, gate bloqueante ou fronteira de confianca.
- `warning`: risco material, regressao plausivel ou cobertura insuficiente em caminho importante.
- `nit`: melhoria opcional de consistencia, legibilidade ou cleanup local.

## Confidence

- `high`: evidencia direta no diff ou em gate deterministico.
- `medium`: sinal forte com pequena dependencia de contexto adjacente.
- `low`: suspeita plausivel que ainda depende de confirmacao adicional.

## Blocking Policy

- `blocker` com `high` ou `medium` bloqueia o veredito.
- `warning` nunca bloqueia sozinho, mas permanece visivel no resumo final.
- `nit` nunca bloqueia e serve apenas como orientacao.
