---
name: modularizar
description: >
  Use para sanear god files, god components e módulos monolíticos quando o
  refactor exigir migração auditável de callers/imports/exports, risco
  estrutural explícito, ou gates de aprovação antes de espalhar mudanças.
  Ative quando o usuário pedir "quebra esse arquivo gigante", "remove
  duplicação e separa em módulos", "extrai utilitários compartilhados desse
  bloco", ou trouxer um alvo delimitado com acoplamento, repetição e impacto
  rastreável fora do arquivo. Não use para refactor local de baixo risco só
  porque o arquivo é grande.
---

# Modularizar

## Fundamentos

- **Saneie antes de modularizar:** trate repetição, complexidade, comentários ruins, naming fraco e visibilidade inadequada antes de quebrar o arquivo em partes. Isso evita espalhar problemas antigos por vários módulos novos.
- **Reaproveite antes de extrair:** se a duplicação já foi resolvida em outro ponto do repositório, prefira migrar para a abstração existente em vez de criar mais um helper local.
- **Otimize com evidência:** proponha melhorias de complexidade e Big-O quando o ganho esperado for claro, com impacto, risco e validação registrados no plano.
- **Pode quebrar e migrar:** a skill pode atualizar callers, imports, exports, entrypoints e utilitários compartilhados quando isso deixar o design final melhor, desde que cada mudança fique registrada e aprovada.
- **Promova o que virar reutilizável:** símbolos extraídos que passam a servir outros módulos devem virar públicos. O restante pode continuar interno para não inflar a API sem motivo.
- **Faça a limpeza completa:** comentários obsoletos, redundantes ou pouco profissionais devem ser removidos ou reescritos; nomes ambíguos ou anti-profissionais devem ser corrigidos.
- **Modularize por responsabilidade real:** a divisão final deve refletir fronteiras de responsabilidade, não apenas uma quebra mecânica em pastas.

## Procedimento

1. Trate todo caso como workflow faseado. Não há subfluxo leve sem gates.
2. Na **Fase 1A**, rode `bash .agents/skills/modularizar/scripts/modularizar_guard.sh init-plan --target <file-or-module> --task <task-name> --author developer-engineer` e preencha `modularizar_<target-basename>.md`.
3. Na **Fase 1A**, complete o inventário obrigatório:
   - duplicatas internas
   - duplicatas que devem ser trocadas por utilitário já existente
   - candidatos de otimização de complexidade e Big-O
   - comentários a remover ou reescrever
   - nomes e visibilidades que precisam ficar mais profissionais
   - mudanças em callers, imports, exports ou arquivos compartilhados necessárias para concluir a limpeza
4. Registre cada categoria de forma explícita no plano. Se uma categoria não tiver achado material, ainda assim crie um item com `Finding status: no-finding` usando o formato oficial do template; no report final, espelhe esse caso como `Execution status: no-change`. Isso evita placeholder improvisado e impede que o inventário pareça completo quando uma frente importante nem foi analisada.
5. Antes de editar código, peça aprovação explícita do usuário para o Gate 1. Esse gate existe para congelar riscos, migrações e otimizações antes que a limpeza se espalhe pelo repositório.
6. Na **Fase 1B**, rode `bash .agents/skills/modularizar/scripts/modularizar_guard.sh validate-plan --phase phase1 --target <file-or-module>` ou `--plan <generated-plan-path>` e execute apenas o saneamento profundo aprovado.
7. Registre no mesmo plano o que foi executado na Fase 1B, incluindo callers migrados, símbolos promovidos e validações locais já concluídas.
8. Na **Fase 2A**, proponha a modularização pós-limpeza: mapa de módulos, entrypoints públicos, símbolos internos, símbolos promovidos a públicos, migração de imports/exports/callers e sequência unitária de extração.
9. Antes de modularizar, peça aprovação explícita do usuário para o Gate 2. Esse gate existe para separar limpeza de redesign estrutural e evitar extrações prematuras com contratos ainda instáveis.
10. Na **Fase 2B**, rode `bash .agents/skills/modularizar/scripts/modularizar_guard.sh validate-plan --phase phase2 --target <file-or-module>` ou `--plan <generated-plan-path>` e execute a modularização aprovada.
11. Registre a execução em `modularizar_<target-basename>-output.md` usando `references/OUTPUT_TEMPLATE.md`. O report final deve espelhar cada `Inventory item` aprovado na Fase 1 e cada `Planned step` aprovado na Fase 2 com bloco próprio, status, evidência e rollback. Depois valide via `lint-and-validate` e finalize com `bash .agents/skills/modularizar/scripts/modularizar_guard.sh validate-report --target <file-or-module>` ou `--report <generated-report-path>`.
12. Se o escopo mudar materialmente durante qualquer fase, revise o plano e peça nova aprovação antes de continuar. O objetivo é manter o workflow auditável, não “ganhar velocidade” escondendo mudança nova dentro do diff.

## Exemplos

### Caso positivo

**Entrada:** "Quebra esse componente enorme, remove duplicação, reaproveita os helpers já existentes e deixa os nomes profissionais."
**Saída esperada:** Abrir `modularizar`, criar o plano faseado, listar o inventário completo da Fase 1, pedir aprovação, executar a limpeza, propor a modularização e só então extrair os módulos.

### Caso positivo

**Entrada:** "Esse service está virando um god file; se precisar mexer nos callers e promover utilitários públicos, pode fazer, mas me mostra tudo por fase."
**Saída esperada:** Abrir `modularizar`, registrar impactos em callers/imports/exports no plano, tratar deduplicação compartilhada e modularizar somente após o Gate 2.

### Caso negativo

**Entrada:** "Desenha a arquitetura nova do backend para suportar múltiplos bounded contexts."
**Por quê não:** Isso é arquitetura ou planning amplo; use `architecture`, `planner` ou `openspec-workflow`.

### Caso negativo

**Entrada:** "Mede o gargalo desse fluxo antes de qualquer mudança."
**Por quê não:** Isso é profiling puro; use `performance-profiling`.

## Evals de trigger

Deve acionar:

- "quebra esse arquivo gigante em módulos"
- "limpa completamente esse código confuso e remove duplicação"
- "extrai utilitários compartilhados desse bloco monolítico"
- "modulariza esse god component sem esconder os impactos nos callers"
- "saneia esse módulo enorme e me mostra o plano faseado"
- "modularisa esse arquivozao e reaproveita os utils que ja existem"

Não deve acionar:

- "define a arquitetura dessa feature nova"
- "mede o gargalo dessa query"
- "investiga esse bug intermitente sem causa raiz"
- "redesenha esse endpoint REST"
- "só organiza esse arquivo grande por legibilidade; não precisa mexer em callers, contratos ou gates"
- "preciso de um refactor amplo multi-time sem alvo claro"

## Evals de workflow

### Cenário 1: limpeza profunda com deduplicação compartilhada

**Entrada:** "Esse service virou um god file. Remove duplicação, reutiliza utilitários existentes, melhora o algoritmo e me mostra tudo por fase."

- [ ] cria `modularizar_<target-basename>.md`
- [ ] o plano inclui pelo menos uma entrada para `P1-INT`, `P1-SHARED`, `P1-BIGO`, `P1-COMMENT`, `P1-NAME` e `P1-CALLER`
- [ ] pede Gate 1 antes de editar código
- [ ] registra a execução da Fase 1B no mesmo plano antes de propor a Fase 2

### Cenário 2: modularização após limpeza aprovada

**Entrada:** "Depois da limpeza, extrai os módulos, ajusta os callers e promove só o que virar reutilizável."

- [ ] valida `phase2` antes de extrair módulos
- [ ] descreve entrypoints públicos, símbolos internos e sequência unitária de extração
- [ ] gera `modularizar_<target-basename>-output.md`
- [ ] o report final lista símbolos públicos promovidos, migrações de import/export e migrações de callers

## Scripts

- `.agents/skills/modularizar/scripts/modularizar_guard.sh`: inicializa o plano, valida cada gate de fase e confere o relatório final do workflow.

## Referências

Leia apenas o arquivo relevante para a etapa atual:

| Situação | Arquivo |
|---|---|
| Preencher o plano faseado e o inventário obrigatório | `references/PLAN_TEMPLATE.md` |
| Entender a sequência operacional e os gates | `references/PHASES.md` |
| Montar o relatório final com evidência das execuções | `references/OUTPUT_TEMPLATE.md` |
| Ver exemplos de Fase 1 e Fase 2 com migração de callers | `references/EXAMPLES.md` |
