# Data Types

> Tipo de dado bom reduz storage, melhora indice, simplifica validacao e evita
> bugs silenciosos. Tipo errado transforma semantica em convencao fragil.

## Regra base

Escolha o tipo pelo que o dado significa, nao pelo que e mais rapido de digitar.

- numero de negocio -> tipo numerico, nao string
- booleano -> boolean, nao texto "true/false"
- instante temporal -> tipo temporal nativo, nao texto
- dinheiro -> decimal/numeric exato, nao float
- identificador opaco -> string pode ser correta

## Tabela de escolhas comuns

| Campo / semantica | Prefira | Evite | Motivo |
|---|---|---|---|
| preco, valor, saldo, total | `numeric/decimal` ou inteiro em centavos | `varchar`, `text`, `float` | ordena, compara e soma corretamente |
| flags (`is_active`, `enabled`) | `boolean` | `varchar`, `text`, `int` magico | semantica clara e validacao nativa |
| `created_at`, `paid_at` | `timestamp`/`datetime` nativo; `timestamptz` quando o engine oferecer | `text`, `varchar` | evita parse manual e comparacao errada |
| data sem horario | `date` | `text`, `datetime` quando horario nao importa | expressa regra de negocio com precisao |
| quantidade inteira | `int`/`bigint` | `varchar` | agrega e compara sem cast |
| dinheiro e taxa | `numeric`/`decimal` | `float`, `double` | aritmetica exata |
| texto livre | `text` ou string sem limite artificial | `varchar(n)` sem regra real | limite arbitrario nao melhora performance sozinho |
| enum pequeno | enum nativo ou `check constraint` | string livre | evita estados invalidos |
| id sequencial | `bigint identity` ou equivalente | `int` se risco de overflow | mais folga e padrao moderno |
| id distribuido/exposto | UUIDv7, ULID, string opaca justificada | texto arbitrario sem regra | reduz ambiguidade e melhora rastreabilidade |

## Quando string continua correta

Nem todo campo "parece numero" e numero de negocio:

- telefone
- CEP / postal code
- CPF/CNPJ/documento
- SKU
- codigo externo com zeros a esquerda
- ids opacos de integracoes

Regra pratica: se voce nunca vai somar, subtrair, ordenar numericamente ou usar
faixa aritmetica, string pode ser a semantica certa.

## Anti-patterns classicos

```sql
create table users (
  id text primary key,
  price varchar(20),
  is_active varchar(5),
  created_at text,
  amount float
);
```

Problemas:

- `price varchar(20)`: comparacao lexica, casts repetidos, validacao fraca
- `is_active varchar(5)`: estados invalidos e ambiguidade de casing
- `created_at text`: parse manual, range ruim, timezone fragil
- `amount float`: erro de arredondamento em dinheiro
- `id text primary key`: pode ser correto, mas precisa justificativa explicita

## Exemplo melhor

```sql
create table users (
  id bigint generated always as identity primary key,
  price numeric(10,2) not null,
  is_active boolean not null default true,
  created_at timestamptz not null,
  amount numeric(10,2) not null
);
```

## Heuristicas de review

- Se o nome indica `price`, `amount`, `total`, `balance` ou `value`, desconfie de string.
- Se o nome indica `is_`, `has_`, `enabled`, `active`, `archived`, desconfie de texto.
- Se o nome termina em `_at`, `date`, `time`, `timestamp`, desconfie de texto.
- Se o campo vira filtro ou ordenacao frequente, tipo errado custa ainda mais.

## Nota sobre ORMs

- Prisma: prefira `Decimal`, `Boolean`, `DateTime` e evite `String` generica para tudo.
- Drizzle: prefira `numeric`, `boolean`, `timestamp`/`datetime` com configuracao correta.
- SQLAlchemy: prefira `Numeric`, `Boolean`, `DateTime(timezone=True)` quando houver
  fuso/horario absoluto.
