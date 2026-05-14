---
title: Apply Principle of Least Privilege
impact: MEDIUM
impactDescription: Reduced attack surface, better audit trail
tags: privileges, security, roles, permissions
---

## Apply Principle of Least Privilege

Grant only the minimum permissions required. Never use superuser for application queries.

Use this reference when reviewing grants, service-role usage, migrations, database clients, or any privilege boundary between browser, edge/API server, Python backend, and Postgres.

**Incorrect (overly broad permissions):**

```sql
-- Application uses superuser connection
-- Or grants ALL to application role
grant all privileges on all tables in schema public to app_user;
grant all privileges on all sequences in schema public to app_user;

-- Any SQL injection becomes catastrophic
-- drop table users; cascades to everything
```

**Correct (minimal, specific grants):**

```sql
-- Create role with no default privileges
create role app_readonly nologin;

-- Grant only SELECT on specific tables
grant usage on schema public to app_readonly;
grant select on public.products, public.categories to app_readonly;

-- Create role for writes with limited scope
create role app_writer nologin;
grant usage on schema public to app_writer;
grant select, insert, update on public.orders to app_writer;
grant usage on sequence orders_id_seq to app_writer;
-- No DELETE permission

-- Login role inherits from these
create role app_user login password 'xxx';
grant app_writer to app_user;
```

Revoke public defaults:

```sql
-- Revoke default public access
revoke all on schema public from public;
revoke all on all tables in schema public from public;
```

Supabase security prompts:

- Treat `service_role` as a privileged server-only credential. It must not appear in frontend code, browser-visible env vars, logs, problem details, or client bundles.
- Distinguish `anon`, `authenticated`, migration/admin, and service-role clients in code review.
- Verify broad grants are paired with RLS when exposed to `authenticated` or `anon`.
- Prefer capability-specific server operations over passing privileged database clients through generic user-controlled handlers.
- Revoke defaults before granting scoped access, especially for schemas that store sessions, audit traces, workspace API keys, user settings, or private analysis.

Audit evidence:

- Env names and import paths show privileged clients are server-only.
- SQL grants are specific to schema/table/action and do not rely on `grant all`.
- User-facing paths call authenticated/tenant-scoped clients, not admin clients.
- Logs and errors do not reveal service-role credentials or connection strings.

Reference: [Roles and Privileges](https://supabase.com/blog/postgres-roles-and-privileges)
