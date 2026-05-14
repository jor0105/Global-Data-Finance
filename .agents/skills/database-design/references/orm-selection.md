# ORM Selection

> ORM e meio de acesso, nao estrategia de modelagem. Escolha o nivel de abstracao
> que ajuda o fluxo dominante sem esconder demais query shape, migrations e
> ownership do dado.

## Use ORM quando

- o dominio tem CRUD forte e repetitivo
- tipagem/relacoes valem a ergonomia
- o time precisa de migrations, schema-first ou DX melhor
- queries complexas sao minoria e ha escape hatch claro

## Prefira query builder ou SQL raw quando

- o valor esta em query complexa, analytics, CTE, janela ou tuning fino
- o time precisa ver SQL com clareza
- o ORM cria N+1, payload excessivo ou abstracao cara demais
- migrations precisam ser ownership explicito do repositorio

## Matriz rapida

| Opcao | Boa para | Cuidado principal |
|---|---|---|
| Prisma | schema-first, DX, CRUD TS | peso, edge, queries complexas |
| Drizzle | SQL-like, edge, TS enxuto | menos abstractions convenientes |
| Kysely / query builder | SQL type-safe com controle | migrations e relacoes menos guiadas |
| SQLAlchemy | Python com dominio e sessao madura | misuse de lazy loading e N+1 |
| SQL raw | maximo controle e performance | disciplina de tipos, reuse e review |

## Perguntas que fecham a escolha

1. Quem sera dono das migrations?
2. O fluxo dominante e CRUD ou query especializada?
3. O time consegue revisar SQL gerado?
4. Existe escape hatch claro para caminhos quentes?
5. O custo de esconder `JOIN`, `SELECT` e cardinalidade e aceitavel?

## Anti-patterns

- escolher ORM para evitar pensar em schema
- tratar lazy loading como default seguro
- usar ORM pesado em edge sem avaliar bundle/runtime
- dizer "SQL raw e feio" quando a query pede controle explicito
