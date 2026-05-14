# Modularizar Examples

Use estes exemplos para entender como a skill deve propor e executar as duas fases.

## Example 1: Phase 1A proposal for a React god component

```markdown
## 4. Phase 1A - Deep Remediation Proposal

### 4.2 Internal duplicates

#### Inventory item P1-INT-01
- Finding status: finding
- Location: `src/features/chat/ui/ChatContainer.tsx`
- Problem: três blocos repetem a normalização de mensagens e o cálculo de status.
- Proposed change: consolidar em uma única função interna antes da modularização.
- Files affected: `src/features/chat/ui/ChatContainer.tsx`
- Contract/import/export impact: nenhum contrato público muda nesta etapa.
- Risk: regressão em estados de loading e empty state.
- Validation: testes de render e fluxo de mensagens.
- Rollback: restaurar a função duplicada original no alvo.

### 4.3 Shared utility reuse or justified new shared utility

#### Inventory item P1-SHARED-01
- Finding status: finding
- Location: `src/features/chat/ui/ChatContainer.tsx`
- Existing utility or abstraction to reuse, or why none is sufficient: `src/shared/lib/formatDateLabel.ts`
- Future consumers after extraction: `ChatContainer.tsx` e `ChatMessage.tsx`
- Problem: o componente replica a mesma lógica de formatação de data já disponível no shared.
- Proposed change: migrar para o utilitário existente e remover a implementação local.
- Files affected: `src/features/chat/ui/ChatContainer.tsx`
- Contract/import/export impact: adiciona import compartilhado; sem API pública nova nesta etapa.
- Risk: divergência de locale se o utilitário compartilhado tiver premissas diferentes.
- Validation: teste de snapshots e casos de data.
- Rollback: reintroduzir a formatação local temporariamente.
```

## Example 2: Phase 1B execution that updates callers

```markdown
## 5. Phase 1B - Deep Remediation Execution Log

- PHASE_1_EXECUTED: YES
- Phase 1 execution summary: duplicações internas removidas, data label migrado para utilitário compartilhado e dois callers atualizados.
- Files changed in Phase 1: `ChatContainer.tsx`, `formatDateLabel.ts`, `ChatMessage.tsx`
- Shared utilities reused or created: reutilizado `formatDateLabel`
- Imports/exports migrated in Phase 1: export nomeado de helper interno removido
- Callers migrated in Phase 1: `ChatMessage.tsx` passou a consumir o utilitário compartilhado
- Public symbols promoted in Phase 1: nenhum
- Validation evidence for Phase 1: testes de chat e typecheck local
- Residual risks after Phase 1: comportamento de timezone ainda depende da fixture atual
```

## Example 3: Phase 2A proposal with public symbol promotion

```markdown
## 6. Phase 2A - Modularization Proposal

### 6.1 Final module map
- Final public entrypoints: `src/features/chat/ui/ChatContainer/index.ts`
- Public entrypoint justification: `ChatPage.tsx` e `ChatPane.tsx` continuam consumindo esse path durante a migração.
- Internal modules and responsibilities: `ChatContainer.tsx` coordena layout; `message-list.tsx` renderiza lista; `message-actions.ts` centraliza handlers
- Symbols promoted to public: `buildMessageGroups`
- Promotion justification: o helper passa a ser consumido por mais de um módulo de chat após a extração.
- Symbols kept internal: `resolveScrollAnchor`, `renderEmptyState`
- Why symbols stay internal: continuam acoplados a detalhes de renderização do container.

### 6.3 Step-by-step extraction sequence
#### Planned step P2-STEP-01
- Extraction order: 1
- Files touched: `ChatContainer.tsx`, `message-list.tsx`
- Responsibility moved: renderização da lista
- Public/private symbol impact: nenhum símbolo novo exposto
- Validation checkpoint: testes de render
- Why this step comes now: separa a maior responsabilidade visual antes de mexer nos exports

#### Planned step P2-STEP-02
- Extraction order: 2
- Files touched: `index.ts`, `message-actions.ts`
- Responsibility moved: handlers e export público final
- Public/private symbol impact: `buildMessageGroups` passa a ser exportado
- Validation checkpoint: typecheck e smoke de chat
- Why this step comes now: depende da lista já extraída para estabilizar o entrypoint final
```

## Example 4: Phase 2B report with migration evidence

```markdown
## 4. Phase 1B Report

### 4.1 Remediation items executed

#### Executed item P1-INT-01
- Inventory item ID: P1-INT-01
- Execution status: executed
- Files changed: `ChatContainer.tsx`
- Summary: consolidação da lógica duplicada de grouping
- Contract/import/export impact: nenhum
- Caller migration impact: nenhum
- Public symbol impact: preparou a extração futura de `buildMessageGroups`
- Validation evidence: testes de chat e typecheck
- Rollback note: restaurar helper local e branches antigos

#### Executed item P1-COMMENT-01
- Inventory item ID: P1-COMMENT-01
- Execution status: no-change
- Files changed: none
- Summary: revisão confirmou que os comentários restantes ainda descrevem o fluxo atual
- Contract/import/export impact: none
- Caller migration impact: none
- Public symbol impact: none
- Validation evidence: revisão manual do trecho
- Rollback note: not applicable

## 5. Phase 2B Report

### 5.2 Migration evidence
- Public symbols promoted: `buildMessageGroups`
- Symbols kept internal: `resolveScrollAnchor`, `renderEmptyState`
- Import/export migrations applied: callers do feature chat apontam para o novo entrypoint
- Caller migrations applied: `ChatPage.tsx`, `ChatPane.tsx`

### 5.3 Step execution evidence

#### Executed step P2-STEP-01
- Step ID: P2-STEP-01
- Execution status: executed
- Files changed: `ChatContainer.tsx`, `message-list.tsx`
- Summary: renderização da lista extraída para módulo dedicado
- Validation evidence: testes de render e smoke de chat
- Rollback note: reverter para a composição anterior do container
```

## Example 5: Near-miss that should not use this skill

**Entrada:** "Quero repensar a arquitetura do chat, da auditoria e do runtime em vários bounded contexts."

**Por quê não:** Isso não é saneamento de um `god code` delimitado. O problema dominante é arquitetura e planejamento amplo.

## Example 6: Category reviewed with no material finding

```markdown
### 4.5 Comment cleanup

#### Inventory item P1-COMMENT-01
- Finding status: no-finding
- Location: `src/features/chat/ui/ChatContainer.tsx`
- Problem: nenhum comentario atual esta obsoleto; a revisao encontrou apenas comentarios ainda aderentes ao fluxo.
- Proposed change: nenhuma alteracao necessaria nesta categoria nesta fase.
- Files affected: none
- Contract/import/export impact: none
- Risk: none material
- Validation: revisao manual do trecho e comparacao com o fluxo atual
- Rollback: not applicable
```

Use este padrão quando a categoria foi analisada de verdade, mas não gerou mudança. O importante é tornar a ausência de alteração auditável, não deixar a seção vazia.

## Example 7: Superficial report that should fail

```markdown
### 4.1 Remediation items executed

- Inventory item ID: P1-INT-01
- Summary: limpeza feita

### 5.3 Step execution evidence

- Step ID: P2-STEP-01
- Summary: módulos extraídos
```

**Por quê falha:** não cria blocos rastreáveis por item e por passo, não registra status de execução, nem evidencia impacto, validação e rollback.
