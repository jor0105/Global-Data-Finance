# Consistency And Concurrency

> Quando duas escritas disputam o mesmo recurso, o default silencioso costuma ser
> bug. Escolha explicitamente como o banco ajuda a manter corretude.

## Ferramentas de consistencia

| Ferramenta | Boa para | Limite |
|---|---|---|
| `UNIQUE` | deduplicacao e chave natural | nao resolve regras multi-linha sozinho |
| `CHECK` | range e invariantes simples | nao cobre consulta cruzada complexa |
| Transacao | grupo de mudancas atomicas | pede cuidado com lock e duracao |
| Upsert | idempotencia e escrita repetivel | depende de chave de conflito boa |
| Lock otimista | conflitos raros e UX tolerante a retry | exige versionamento/precondicao |
| Lock pessimista | secao critica curta e disputa real | pode reduzir throughput e gerar espera |

## Regras praticas

- Se a duplicidade e proibida, procure uma constraint antes de logica manual.
- Se dois jobs podem criar o mesmo registro, `UNIQUE` + upsert costuma ser melhor
  que "checa e depois insere".
- Transacao longa prende lock e amplia risco operacional. Mantenha secao critica
  curta sempre que possivel.
- Lock pessimista e ferramenta de precisao, nao default.
- Se o conflito pode ser resolvido por retry, lock otimista ou versionamento
  costuma ser mais barato operacionalmente.

## Exemplos de boas perguntas

- "Qual coluna ou combinacao representa identidade unica desse evento?"
- "Qual escrita precisa ser idempotente?"
- "Existe saldo, sequencia ou estado que nao pode divergir sob concorrencia?"

## Anti-patterns

- deduplicacao so na app
- confiar em clock ou cache local para evitar corrida
- tratar lock como detalhe de ORM
- usar trigger/worker compensatorio para corrigir regra que deveria ser constraint
