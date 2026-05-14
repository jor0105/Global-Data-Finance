# tests-pack

## Scope

Cobertura nova ou regressiva, cenarios criticos sem verificacao e confiabilidade de gates.

## Checklist

- `TEST-COVERAGE`: mudanca critica ganhou cobertura proporcional?
- `TEST-REGRESSION`: existe risco de regressao sem teste ou gate correspondente?

## Heuristics

- Falha em gate `blocking` e sempre bloqueante.
- Falha em gate `advisory` deve aparecer no resumo, mas nao bloquear sozinha.
