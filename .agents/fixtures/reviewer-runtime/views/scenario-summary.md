# Review Runtime Scenario Demo

Este arquivo e gerado pelo teste de cenarios para demonstrar o fluxo do reviewer.

## Cenario 1 - Codigo simples arrumado

- objective: Comprovar que um ajuste pequeno e limpo termina aprovado.
- change_type: bug-fix
- scope: Review completo de um unico arquivo simples.
- changed_files: src/features/chat/components/ChatInput.tsx
- review_id: review-20260423T002233Z
- plan_items: 1
- final_verdict: APPROVED
- summary_view: /home/jordan/Programação/FinAI/.agents/fixtures/reviewer-runtime/simple-clean/views/review-summary.md

## Cenario 2 - Revisao parcial dentro de refatoracao grande

- objective: Comprovar que o reviewer pode focar em apenas dois arquivos.
- change_type: refactor
- scope: Mesmo em uma refatoracao maior, o review ficou limitado aos dois arquivos passados em changed_files.
- changed_files: src/features/chat/components/ChatInput.tsx, src/features/chat/components/ChatMessage.tsx
- review_id: review-20260423T002233Z
- plan_items: 1
- final_verdict: APPROVED
- summary_view: /home/jordan/Programação/FinAI/.agents/fixtures/reviewer-runtime/partial-refactor/views/review-summary.md

## Cenario 3 - Escalonamento de seguranca

- objective: Comprovar que mudancas sensiveis bloqueiam APPROVED ate a resolucao do handoff.
- change_type: refactor
- scope: Mudanca em auth com handoff explicito para security-engineer.
- changed_files: backend/api/deps/auth.py, src/features/auth/AuthProvider.tsx
- review_id: review-20260423T002233Z
- plan_items: 3
- final_verdict: SECURITY_REVIEW_REQUIRED -> APPROVED
- summary_view: /home/jordan/Programação/FinAI/.agents/fixtures/reviewer-runtime/review-item-security/views/review-summary.md
- blocking_reasons:
  - Escalonamento de seguranca ainda aberto: pending
- security_touch_result: yes
- security_lifecycle: pending -> cleared
