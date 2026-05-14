---
name: supabase-postgres-best-practices
description: >
  Use para Supabase/Postgres com queries, schema, índices, RLS, grants, service role,
  tenant isolation, pooling e segurança de dados. Ative quando o usuário mencionar
  Supabase, políticas RLS, Postgres lento, grants, service_role ou vazamento multi-tenant.
---

# Supabase Postgres Best Practices



## Fundamentos

- **Supabase não é um banco genérico:** Ele injeta regras de Autenticação (`auth.uid()`) diretamente nas lógicas de tabela via RLS (Row Level Security).
- **Service Role Key (Perigo Absoluto):** A chave `SUPABASE_SERVICE_ROLE_KEY` bypassa TODA segurança RLS. Ela deve viver **APENAS** no backend (ex: em workers Python fechados) e **Nunca** no frontend (`src/`). Usar Service Role no frontend vaza a raiz do sistema.
- **Tenant Isolation:** Em contextos B2B ou SaaS multi-tenant, toda tabela sensível deve possuir uma coluna de escopo (ex: `workspace_id`, `tenant_id`). A RLS deve verificar `auth.uid() IN (select user_id from workspace_users where workspace_users.workspace_id = table.workspace_id)`.

## Procedimento
1. **Auditoria Obrigatória de RLS:** Toda nova tabela criada deve vir acompanhada do comando `ALTER TABLE nome_da_tabela ENABLE ROW LEVEL SECURITY;`.
2. **Criação de Policies (RLS):**
   - Evite "Policies God Mode". Crie uma policy para `SELECT`, uma para `INSERT`, etc.
   - Utilize a função nativa `auth.uid()` para restringir o escopo da query automaticamente no banco.
3. **Migrações Controladas:**
   - Nunca edite diretamente via interface visual (Studio) do Supabase. Crie arquivos de migração controlados no repositório.
4. **Proteção Contra Supabase Python Client Leak:**
   - Quando usar Python no backend `backend/app/`, as instâncias do cliente Supabase criadas com Token de Usuário devem ser efémeras e restritas à Request HTTP para não vazar a sessão de um cliente para outro por injeção de dependência suja.

## Exemplos

### Caso positivo
**Entrada:** Usuário trabalha com Supabase/Postgres, RLS, índices, grants ou queries lentas.
**Saída esperada:** Aplicar práticas específicas de Supabase/Postgres e carregar referência certa por tema.

### Caso negativo
**Entrada:** Usuário usa MySQL/SQLite sem Supabase.
**Por quê não:** Use `database-design` para schema, tipos de dados, constraints, migrations, ownership e consistencia de forma engine-agnostic.

## Evals de trigger

Deve acionar:
- "RLS está lenta no Supabase"
- "grants e indexes no Postgres Supabase"

Não deve acionar:
- "MongoDB schema"
- "CSS responsivo"

## Referências

Os caminhos abaixo são relativos a esta pasta. Leia apenas o arquivo relevante para o problema em mãos; não carregue todo o diretório.

| Problema | Arquivo |
|---|---|
| Visão geral, índice e convenções do pacote | `references/README.md` |
| Como contribuir ou criar novas referências | `references/_contributing.md`, `references/_template.md` |
| Índice de seções disponíveis | `references/_sections.md` |
| Full-text search e JSONB | `references/advanced-full-text-search.md`, `references/advanced-jsonb-indexing.md` |
| Pooling, limites, idle timeout e prepared statements | `references/conn-pooling.md`, `references/conn-limits.md`, `references/conn-idle-timeout.md`, `references/conn-prepared-statements.md` |
| Batch inserts, N+1, paginação e upsert | `references/data-batch-inserts.md`, `references/data-n-plus-one.md`, `references/data-pagination.md`, `references/data-upsert.md` |
| Locks, deadlocks e filas com skip locked | `references/lock-advisory.md`, `references/lock-deadlock-prevention.md`, `references/lock-short-transactions.md`, `references/lock-skip-locked.md` |
| EXPLAIN, pg_stat_statements e vacuum/analyze | `references/monitor-explain-analyze.md`, `references/monitor-pg-stat-statements.md`, `references/monitor-vacuum-analyze.md` |
| Tipos de índices, missing indexes e índices parciais/compostos/covering | `references/query-index-types.md`, `references/query-missing-indexes.md`, `references/query-partial-indexes.md`, `references/query-composite-indexes.md`, `references/query-covering-indexes.md` |
| Constraints, tipos, FKs, nomes, partição e primary keys | `references/schema-constraints.md`, `references/schema-data-types.md`, `references/schema-foreign-key-indexes.md`, `references/schema-lowercase-identifiers.md`, `references/schema-partitioning.md`, `references/schema-primary-keys.md` |
| Grants, RLS básica e performance de RLS | `references/security-privileges.md`, `references/security-rls-basics.md`, `references/security-rls-performance.md` |
