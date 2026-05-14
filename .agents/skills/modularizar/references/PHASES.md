# Modularizar Phases

Use este checklist para sanear e modularizar um `god code` sem esconder impacto em callers, contratos e utilitários compartilhados.

## Gate sequence

1. **Fase 1A**: diagnostique o alvo e preencha o inventário obrigatório no plano.
2. **Gate 1**: peça aprovação explícita do usuário.
3. **Fase 1B**: execute apenas o saneamento profundo aprovado.
4. **Fase 2A**: proponha a modularização pós-limpeza no mesmo plano.
5. **Gate 2**: peça aprovação explícita do usuário.
6. **Fase 2B**: execute a modularização aprovada e valide o resultado final.

## Gate 1

Antes da Fase 1B:

- Inicialize ou atualize `modularizar_<target-basename>.md`.
- Preencha `## 3. Contract and Migration Baseline`.
- Preencha todas as subseções de `## 4. Phase 1A - Deep Remediation Proposal`.
- Registre cada categoria do inventário. Quando não houver achado material, ainda assim crie um bloco com `Finding status: no-finding` usando os valores sentinela oficiais do `PLAN_TEMPLATE.md`, em vez de deixar a categoria implícita.
- Liste impactos em callers, imports, exports e símbolos públicos sempre que existirem.
- Registre a aprovação do usuário em `- GATE_1_APPROVED: YES`.
- Valide com:
  - `bash .agents/skills/modularizar/scripts/modularizar_guard.sh validate-plan --phase phase1 --target <file-or-module>`

Esse gate existe para impedir que limpeza, migração e otimização avancem com risco ainda tácito. Se o plano não estiver fechado aqui, a execução tende a espalhar mudanças antes de termos um contrato auditável.

## Fase 1B

Objetivo:

- Remover duplicação interna.
- Trocar duplicação por utilitário compartilhado já existente quando ele já cobre o comportamento necessário ou exigir menos mudança líquida do que criar outro helper.
- Criar utilitário compartilhado novo apenas quando o plano registrar os consumidores futuros e a redução de duplicação material que justifica essa extração.
- Aplicar otimizações materiais de complexidade com evidência.
- Limpar comentários obsoletos ou ruins.
- Corrigir naming e visibilidade.
- Migrar callers e contratos necessários para concluir a limpeza.

Ao terminar:

- Atualize `## 5. Phase 1B - Deep Remediation Execution Log`.
- Marque `- PHASE_1_EXECUTED: YES`.
- Registre arquivos alterados, símbolos promovidos, callers migrados e evidência de validação.
- No report final, registre um bloco em `4.1` para cada `Inventory item` aprovado. Quando a conclusão do item for `no-change`, use também os valores sentinela oficiais do `OUTPUT_TEMPLATE.md`.

## Gate 2

Antes da Fase 2B:

- Preencha `## 6. Phase 2A - Modularization Proposal`.
- Descreva entrypoints públicos, módulos internos, símbolos públicos e símbolos internos.
- Justifique por que cada entrypoint continua público e por que cada símbolo promovido realmente precisa sair do escopo interno.
- Registre como imports, exports e callers serão migrados.
- Registre a aprovação do usuário em `- GATE_2_APPROVED: YES`.
- Valide com:
  - `bash .agents/skills/modularizar/scripts/modularizar_guard.sh validate-plan --phase phase2 --target <file-or-module>`

Esse gate existe para separar saneamento de extração estrutural. Sem ele, o agente pode modularizar cedo demais e transformar dúvidas de contrato em churn de arquivos.

## Fase 2B

Objetivo:

- Extrair módulos por responsabilidade real.
- Preservar como público apenas o que ainda tem callers ativos, serve como gateway de migração ou está explicitamente planejado para reuso entre módulos.
- Promover a público apenas o que se tornou reutilizável.
- Remover arquivos legados ou reduzi-los a gateways quando isso facilitar a migração.

Ao terminar:

- Atualize `## 7. Phase 2B - Modularization Execution Log`.
- Marque `- PHASE_2_EXECUTED: YES`.
- Gere `modularizar_<target-basename>-output.md` a partir de `references/OUTPUT_TEMPLATE.md`.
- No report final, registre um bloco em `5.3` para cada `Planned step` aprovado. Se o passo for ajustado, deixe explícito o motivo da diferença.

## Final validation

- Rode a validação final via `lint-and-validate`, preferindo `npm run ai:verify`.
- Preencha a seção final do report com comandos, resultado e resumo de evidência.
- Finalize com:
  - `bash .agents/skills/modularizar/scripts/modularizar_guard.sh validate-report --target <file-or-module>`

O fluxo só termina quando Gate 1, Fase 1B, Gate 2, Fase 2B e validação final estiverem registrados como concluídos. Essa disciplina mantém o diff explicável para review, rollback e reaproveitamento futuro da skill.
