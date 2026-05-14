# Security Isolation

> Dado sensivel sem ownership explicito vira bug cross-tenant cedo ou tarde. O
> banco precisa saber quem pode ver ou mutar o que, mesmo que a API tambem valide.

## Perguntas de isolamento

1. O dado e publico, por usuario, por workspace ou por tenant?
2. Existe coluna de escopo suficiente para provar ownership?
3. O lookup por ID sozinho pode atravessar fronteira de dados?
4. A integridade do escopo depende de FK/constraint ou so de disciplina da app?

## Principios

- Ownership e parte do schema. `workspace_id`, `tenant_id`, `owner_id` ou
  equivalente nao sao detalhes de endpoint.
- Least privilege comeca na modelagem: tabelas, views e clients devem expor so o
  minimo necessario.
- Predicate no repositorio ou no banco e melhor que filtro tardio na camada de UI.
- Se a entidade nao consegue provar escopo, seu design ainda esta incompleto.

## Controles estruturais comuns

- coluna de escopo obrigatoria
- FK do escopo para entidade pai ou tabela de associacao
- `UNIQUE` composto incluindo escopo quando o dado for local ao tenant
- separacao de tabelas quando os lifecycles de acesso forem muito diferentes

## Lookup perigoso

Padrao ruim:

- `select * from invoices where id = ?`

Padrao melhor:

- `select * from invoices where id = ? and workspace_id = ?`
- policy ou predicate equivalente na camada confiavel mais baixa

## Quando rotear para skill especializada

Se a pergunta virar:

- RLS
- grants
- `service_role`
- tuning de policy
- detalhe de cliente/admin role em Postgres/Supabase

encaminhe para `supabase-postgres-best-practices`.
