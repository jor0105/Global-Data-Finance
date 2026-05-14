# Async Operations And Webhooks

> Se a resposta não cabe com segurança no ciclo de um request normal, modele o
> trabalho como job, stream ou callback explícito.

## Quando usar `202 Accepted`

Use `202 Accepted` quando o servidor aceitou a solicitação, mas a conclusão real
acontecerá depois:

- export de dados
- geração de relatório
- ingestão via provider externo
- processamento em fila
- ações que podem exceder timeout do cliente, proxy ou worker

```http
POST /api/v1/report-exports
Idempotency-Key: 0f1b4f9d-0b53-4d4f-9167-8dfeeb3d9a2d

→ 202 Accepted
Location: /api/v1/report-export-jobs/job_123
```

## Recurso de job

O recurso de job deve ser explícito, estável e seguro:

```json
{
  "data": {
    "id": "job_123",
    "status": "running",
    "created_at": "2026-05-05T13:00:00Z",
    "started_at": "2026-05-05T13:00:01Z",
    "finished_at": null,
    "result_url": null,
    "error": null
  }
}
```

Estados comuns:
- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`

## Polling

Polling é aceitável quando:

- o cliente já mantém sessão com a API
- a frequência pode ser controlada
- o tempo de conclusão é incerto, mas finito

Boas práticas:
- exponha `Retry-After` quando fizer sentido
- use backoff no cliente
- não peça polling agressivo em intervalos fixos sem motivo

## Webhooks de saída

Ao notificar outro sistema:

- assine o payload ou a string canônica do evento
- inclua `event_id`, `event_type`, `occurred_at`
- documente retries e janelas de redelivery
- trate webhooks como entrega ao menos uma vez, não exatamente uma vez

## Webhook receiver

Ao receber webhook de terceiros:

- valide assinatura com segredo compartilhado ou chave pública
- valide timestamp/janela de replay quando o provedor suportar
- deduplique por `event_id`
- responda rápido; empurre processamento pesado para fila/job interno
- trate o endpoint como trust boundary especial, não como POST público comum

## Idempotência e deduplicação

Retry de cliente e redelivery de webhook são fatos normais. Proteja:

- criação crítica com `Idempotency-Key`
- receiver com storage de `event_id`
- workers com reprocessamento seguro

## Anti-patterns

**Esperar 60 segundos para depois devolver 500:** o cliente não sabe se houve
execução parcial, timeout intermediário ou retry seguro.

**Confiar em IP de origem como autenticação de webhook:** origem de rede sozinha
não é prova suficiente para evento financeiro ou operacional sensível.

**Executar tudo no request do webhook:** aumenta timeout, retry em cascata e risco
de duplicação.

## Checklist

- Operações longas usam job, stream ou callback conscientemente
- `202 Accepted` aponta para recurso de status previsível
- Webhooks têm assinatura, replay tolerance e deduplicação
- Retry e idempotência estão modelados explicitamente
- Processamento pesado não bloqueia desnecessariamente o request de entrada
