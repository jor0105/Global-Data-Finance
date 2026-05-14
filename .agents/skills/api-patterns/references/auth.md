# Authentication Patterns

> Escolha e revise auth por trust boundary, tipo de caller e dado protegido.

## Guia de seleção

| Padrão | Quando usar | Foco de revisão de segurança |
|---|---|---|
| **Bearer/JWT** | Membros autenticados, APIs stateless | Assinatura, expiração, issuer/audience, claims mínimos, replay |
| **Session** | App shell no browser, fluxos Supabase Auth | Bootstrap, refresh, invalidação no logout, comportamento pós-expiração |
| **OAuth 2.0** | Integração com terceiros | Redirect URI, state/PKCE, armazenamento de token, escopo mínimo |
| **API Keys** | API pública do workspace, server-to-server | Escopo, rotação, hash/storage, rate limit, revogação, tenant binding |
| **Passkey** | Auth sem senha | Origin binding, recovery flow, controles de enrollment |

## Superfícies de auth no projeto

- Membros do dashboard usam Bearer auth para APIs de conversação sob `/api/v1/conversations`.
- Callers do workspace/API pública usam `X-API-Key`; sempre vincule a chave ao workspace/tenant e evite ambiguidade com impersonação de usuário.
- Endpoints de dados do backend Python são proxiados sob `/api/python`; o proxy não pode permitir que input do usuário selecione hosts upstream arbitrários ou contorne a fronteira de auth do frontend.
- Streams SSE (ex: message streaming) devem autorizar antes de abrir o stream e encerrar imediatamente após revogação de sessão ou mismatch de tenant.
- Problem details em REST/HTTP seguem RFC 7807 sem vazar tokens, API keys, URLs upstream, stack traces ou payloads sensíveis de providers.

## Princípios Bearer/JWT

- Verifique assinatura e algoritmo usando apenas as chaves esperadas.
- Valide expiração, issuer, audience, subject e claims de tenant/workspace onde aplicável.
- Mantenha claims mínimos — nunca armazene segredos, API keys ou dados financeiros em tokens.
- Trate tokens ausentes, malformados, expirados e de tenant errado como casos de teste distintos, mas retorne erros sanitizados.
- Nunca aceite `user_id` fornecido pelo cliente como prova de autorização quando um subject de token/sessão está disponível — esse é o anti-pattern mais comum de BOLA.

## Princípios de API Key

- Armazene apenas hashes de API keys ou referências gerenciadas pelo provider.
- Escopie keys por workspace, capability, ambiente e rate limit.
- Rejeite keys inválidas antes de fazer trabalho caro (chamada a provider, query pesada).
- Redija keys em logs, traces, problem details, browser storage e artefatos de auditoria.
- Valide comportamento de revogação e rotação com teste negativo explícito.

## Caso negativo crítico

**Entrada:** endpoint recebe `{ "user_id": 42 }` no body e usa esse valor para buscar dados.
**Por quê falha:** qualquer caller pode forjar o `user_id`. A identidade deve vir sempre
do subject do token validado no middleware — nunca do payload da requisição.
