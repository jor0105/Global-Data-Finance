# Review Plan

- review_id: review-20260506T191637Z
- status: ready
- schema_version: 1.0.0

## RVI-001 · security:trust-boundary
- status: pending
- priority: 100
- pack: security
- files: src/features/auth/AuthProvider.tsx
- skills: vulnerability-scanner, red-team-tactics
- checklists: SEC-TRUST, SEC-AUTHZ
- expansions:
  - Verificar componente vizinho imediato. -> src/features/auth/AuthGate.tsx
## RVI-002 · frontend:runtime
- status: pending
- priority: 50
- pack: frontend
- files: src/features/auth/AuthProvider.tsx
- skills: nextjs-react-expert
- checklists: FE-STATE, FE-UX
