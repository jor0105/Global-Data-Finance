# Schema Design

> Modele entidades, ownership e lifecycle antes de falar de ORM. Um schema bom
> torna o caminho correto mais facil que o caminho incorreto.

## Comece pelo que precisa ser protegido e acessado

Para cada entidade, responda:

- quem e o owner do dado
- qual e a unidade de isolamento: usuario, workspace, tenant ou publico
- quais campos sao obrigatorios, derivados ou historicos
- quais relacionamentos precisam de integridade forte
- quais leituras precisam ser simples, frequentes ou ordenadas

## Chaves e relacionamentos

| Decisao | Regra pratica |
|---|---|
| PK | Escolha uma PK simples, estavel e barata para referenciar |
| FK | Toda relacao material precisa de FK ou motivo explicito para nao ter |
| Many-to-many | Use tabela de juncao com PK/UNIQUE que impeca duplicidade |
| One-to-one | Use quando houver lifecycle diferente, segregacao sensivel ou extensao rara |
| Ownership | Coluna de `user_id`, `workspace_id` ou equivalente quando o dado nao for publico |

## Constraints antes de conveniencia

Prefira declarar no banco quando a regra for invariavel:

- `NOT NULL` para campos obrigatorios
- `UNIQUE` para deduplicacao natural
- `CHECK` para enums pequenos, ranges e formatos simples
- FK para integridade referencial

Regra importante: se a resposta so diz "validamos na API", pergunte por que o
banco nao pode impedir o estado invalido.

## Normalizacao vs desnormalizacao

Normalize quando:

- dados se repetem e divergiriam em updates
- o relacionamento e parte do dominio, nao detalhe de renderizacao
- integridade e mais importante que leitura unica

Desnormalize quando:

- o fluxo dominante e read-heavy e o custo de join vira gargalo real
- o campo duplicado e derivado, estavel e barato de recomputar
- a resposta aceita complexidade de sincronizacao conscientemente

Nao use desnormalizacao como desculpa para pular ownership, tipos corretos ou
constraints basicas.

## JSON/document fields com criterio

Use `JSON`/`JSONB` ou equivalente quando:

- o shape e realmente semi-estruturado
- novos atributos aparecem com alta variacao
- consultas profundas sao raras ou muito especificas

Evite quando:

- filtros e joins frequentes dependem dessas chaves
- o dado e fortemente relacional
- a equipe quer "flexibilidade" para fugir de migrations

## Lifecycle e soft delete

- `deleted_at` so vale quando ha requisito de auditoria, restauracao ou retencao.
- Se usar soft delete, leve isso para indices, `UNIQUE` parciais, consultas e
  relatorios. Soft delete mal planejado so desloca bug de lugar.
- Historico/auditoria pede owner, timestamps e estrategia de growth. Nao trate
  tabela de eventos como tabela comum.

## Anti-patterns classicos

- tabela sensivel sem coluna de escopo ou ownership
- FK sem indice nos caminhos dominantes
- campo textual livre representando enum pequeno
- atributo derivado critico sem regra de atualizacao
- entidade "uber" com dezenas de colunas opcionais para contextos distintos
