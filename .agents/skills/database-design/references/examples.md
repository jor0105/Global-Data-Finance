# Examples

> Use estes exemplos quando a conversa pedir um shape concreto de schema, indice,
> migration, tipo de dado ou estrategia de consistencia. Adapte ao engine e ao
> repositorio real.

## Modelagem read-heavy com ownership

**Entrada:** "Preciso modelar pedidos, itens e pagamentos com consulta rapida do historico do cliente."

**Saida esperada:**

```yaml
database_design_review:
  workload:
    shape: oltp
    write_profile: balanced
    engine_context: postgres
  access_patterns:
    critical_reads:
      - listagem de pedidos por customer_id e status
      - historico de pagamentos por pedido
    isolation_scope: workspace
  schema:
    entities:
      - orders: cabecalho do pedido, owner por workspace_id/customer_id
      - order_items: filhos do pedido
      - payments: eventos de pagamento ligados ao pedido
    data_types:
      - total_amount -> numeric(12,2), nao string
      - paid_at -> timestamptz/date-time nativo, nao texto
  integrity:
    constraints:
      - fk order_items.order_id -> orders.id
      - fk payments.order_id -> orders.id
      - not null em ownership e status
  indexing:
    required:
      - (workspace_id, customer_id, status, created_at desc) para listagem principal
      - index em payments.order_id
  migration_rollout:
    plan:
      - greenfield: criar tabelas com constraints e ownership desde o inicio
```

## Tipo de dado errado corrigido cedo

**Entrada:** "Hoje `price`, `is_active` e `created_at` sao strings."

**Saida esperada:**

- `price` ou `amount` devem virar tipo numerico exato, nao string e nao float
- `is_active` deve virar boolean
- `created_at` deve virar tipo temporal nativo
- se o campo for `phone_number`, `postal_code` ou identificador externo, string
  pode continuar correta por nao representar aritmetica

## Query lenta com indice composto

**Entrada:** "Filtro por `workspace_id` e `status`, ordeno por `created_at desc`."

**Saida esperada:**

- pedir a query real ou inferir seu shape
- sugerir indice composto alinhado ao filtro e sort
- avaliar indice parcial se `status = 'active'` for predicado dominante
- evitar resposta generica "crie indice em cada coluna"

## Migration segura para rename

**Entrada:** "Vou renomear `customer_name` para `display_name`."

**Saida esperada:**

1. adicionar coluna nova
2. backfill/copy dos dados
3. app passa a ler/escrever a nova coluna
4. remover a antiga em deploy posterior

Nao tratar `ALTER TABLE ... RENAME COLUMN` como padrao seguro sem avaliar caller,
compatibilidade e janela operacional.

## Consistencia por constraint, nao so por app

**Entrada:** "Dois jobs podem gravar a mesma conciliacao."

**Saida esperada:**

- definir chave natural ou `UNIQUE` que represente duplicidade
- usar upsert ou transacao com criterio
- nao deixar deduplicacao apenas em memoria na aplicacao

## Roteamento correto para skill especializada

**Entrada:** "Minha policy RLS no Supabase esta lenta e suspeito de grants amplos."

**Saida esperada:**

- reconhecer que o centro do problema saiu do escopo generalista
- encaminhar para `supabase-postgres-best-practices`
- manter `database-design` apenas como contexto estrutural se necessario
