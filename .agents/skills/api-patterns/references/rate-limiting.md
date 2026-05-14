# Rate Limiting Principles

> Limite antes do trabalho caro começar — não depois.

## Regra mais importante

Rate limit deve ser verificado e rejeitado **antes** de qualquer chamada a provider
externo, query pesada ou operação de streaming. Rejeitar depois do custo já ter sido
incorrido protege apenas o cliente, não o sistema.

## Estratégias

| Tipo | Como funciona | Quando usar |
|---|---|---|
| **Token bucket** | Burst permitido, recarrega ao longo do tempo | Maioria das APIs — equilibra UX e proteção |
| **Sliding window** | Distribuição suave sem picos no reset | Limites estritos onde burst é inaceitável |
| **Fixed window** | Contador simples por janela de tempo | Necessidades básicas, fácil de implementar |

## Escopo do limite

O escopo define quem compartilha o contador — erro aqui anula a proteção:

- **Por usuário:** isola abuso individual, mas não protege de múltiplas contas.
- **Por workspace/tenant:** protege recursos compartilhados, mas pode punir usuários legítimos.
- **Por API key:** granularidade máxima para APIs públicas — prefira este para integrações externas.
- **Por IP:** útil apenas como camada adicional, nunca como escopo principal (proxies, NAT).

Combine escopos quando necessário: limite por usuário E por workspace para APIs internas.

## Bypass patterns — o que testar

Estes são os vetores de bypass mais comuns; valide cada um explicitamente:

- **`X-Forwarded-For` forjado:** se o sistema usa esse header para identificar o IP,
  um atacante pode rotacionar IPs no header para escapar do limite por IP.
- **Variação de casing/rota:** `/api/v1/chat` e `/api/V1/Chat` chegam ao mesmo handler
  mas podem ter contadores separados se o rate limiter não normalizar.
- **Aliases de rota:** rotas deprecadas ou aliases que apontam para o mesmo handler
  mas bypass o middleware de rate limit (ver `security-testing.md` → API9: Inventory).
- **Variação de método HTTP:** `GET /resource` e `POST /resource` no mesmo contador ou não?
  Defina explicitamente.
- **Versões de API:** `/v1/` e `/v2/` compartilham limite ou têm contadores separados?
  Documentar e testar.

## Response headers obrigatórios

```
X-RateLimit-Limit:     1000        # máximo de requisições na janela
X-RateLimit-Remaining: 847         # requisições restantes
X-RateLimit-Reset:     1714500000  # timestamp Unix do reset
Retry-After:           30          # segundos até poder tentar novamente (no 429)
```

Retorne `429 Too Many Requests` com `Retry-After` — nunca `403` ou `503` para rate limit.

## Custo diferenciado

Nem toda requisição tem o mesmo custo. Atribua pesos:

```
# Exemplo de política de custo
GET  /messages         → custo 1
POST /messages         → custo 2   (escrita + processamento)
POST /messages/stream  → custo 10  (stream longo + provider externo)
POST /embeddings       → custo 5   (chamada a modelo)
```

Deduza o custo antes de executar — não após. Se o saldo for insuficiente, rejeite
com 429 imediatamente.
