# Review Plan

- review_id: review-20260506T191637Z
- status: ready
- schema_version: 1.0.0

## RVI-001 · security:trust-boundary
- status: pending
- priority: 100
- pack: security
- files: backend/api/deps/auth.py, src/features/auth/AuthProvider.tsx
- skills: vulnerability-scanner, red-team-tactics
- checklists: SEC-TRUST, SEC-AUTHZ
## RVI-002 · api:contracts
- status: pending
- priority: 80
- pack: api
- files: backend/api/deps/auth.py
- skills: api-patterns
- checklists: API-CONTRACT, API-ERRORS
## RVI-003 · frontend:runtime
- status: pending
- priority: 50
- pack: frontend
- files: src/features/auth/AuthProvider.tsx
- skills: nextjs-react-expert
- checklists: FE-STATE, FE-UX
