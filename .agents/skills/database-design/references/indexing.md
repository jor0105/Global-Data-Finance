# Indexing

> Indice serve a uma query real. Se voce nao consegue citar o `WHERE`, `JOIN`
> ou `ORDER BY`, provavelmente ainda nao sabe qual indice quer.

## Perguntas obrigatorias antes de sugerir indice

1. Qual e a query ou familia de queries?
2. Ha igualdade, range, join ou sort?
3. Qual coluna tem seletividade real?
4. A tabela e read-heavy ou write-heavy?
5. O indice evita scan relevante ou so mascara query ruim?

## Tipos de indice por problema

| Tipo | Use quando | Evite quando |
|---|---|---|
| `B-tree` | igualdade, range, sort, joins gerais | voce ainda nao sabe a query |
| Composto | filtros multi-coluna previsiveis | so porque "todas as colunas importam" |
| Parcial | query filtra sempre o mesmo subconjunto | predicado raro ou instavel |
| Covering / `INCLUDE` | precisa reduzir lookup adicional | tabela pequena ou query rara |
| `GIN` | arrays, JSON, full-text, membership | filtros escalares simples |
| `GiST` | geoespacial, ranges e operadores especializados | uso geral sem operador compativel |
| `BRIN` | tabelas muito grandes ordenadas por append | dados pequenos ou desordenados |
| `Hash` | igualdade pura em engines que justificam | como padrao sem motivo forte |

## Regras de ouro

- Colunas de igualdade tendem a vir antes das de range no indice composto.
- `ORDER BY` so ajuda quando o indice conversa com o filtro e com a ordem.
- FK relevante quase sempre pede indice proprio.
- Dois indices separados raramente substituem bem um composto pensado para a
  query dominante.
- Cada indice extra custa escrita, storage, vacuum/manutencao e cognicao.

## Quando considerar indice parcial

Bom fit:

- `deleted_at is null`
- `status = 'active'`
- filas ou pedidos com subconjunto quente
- `UNIQUE` condicionais em recursos soft-deleted

Mau fit:

- filtro muda a toda hora
- condicao cobre quase toda a tabela
- a app nao consegue garantir uso consistente do predicado

## Covering e index-only

Considere quando:

- a query le poucas colunas alem das chaves de filtro
- o caminho e muito frequente
- o ganho compensa o custo adicional do indice

Nao trate `INCLUDE` como ornamentacao. Ele existe para um caminho quente bem
identificado.

## Anti-patterns

- indexar toda coluna "importante"
- ignorar seletividade e cardinalidade
- criar indice antes de entender `EXPLAIN ANALYZE`
- esquecer indice de FK usada em join, delete cascade ou lookup frequente
- usar JSON document para fugir de modelagem e depois tentar salvar tudo com GIN
