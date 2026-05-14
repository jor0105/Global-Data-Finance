# security-pack

## Scope

Auth, autorizacao, segredos, middleware, uploads, HTML perigoso, RLS e outras fronteiras de confianca.

## Checklist

- `SEC-TRUST`: a mudanca cruza fronteira de confianca?
- `SEC-AUTHZ`: existe verificacao de permissao ou ownership?
- `SEC-SECRETS`: segredo novo ficou exposto, persistido ou logado?

## Heuristics

- Findings criveis com `confidence: high|medium` devem escalar para `security-engineer`.
- `blocker` e a severidade padrao para auth bypass, permission drift ou segredo exposto.
