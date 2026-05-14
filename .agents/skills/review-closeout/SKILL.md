---
name: review-closeout
description: Consolida findings, gates e seguranca em um verdict canonico e exporta a view humana final do review.
---

# Review Closeout

## Use When

Use quando os itens de review, gates e status de seguranca ja estao em estado terminal e o reviewer precisa consolidar um veredito canonico.

## Do Not Use When

Nao use para iniciar review, expandir contexto de um arquivo ou rodar validacao mecanica ainda ausente.

## Required Inputs

- Findings persistidos da sessao.
- Gate report atual e status de seguranca.
- `session_dir` e artifacts canonicos necessarios para gerar o veredito final.

## Phase Machine

1. Agregar findings, gates e estados de seguranca relevantes.
2. Classificar o veredito canonico conforme blockers, cobertura e evidencias.
3. Exportar `review-verdict`, `gate-clearance-report` e a view humana final.

## Fundamentos

- **O Gate Canônico:** A decisão de um Reviewer não é uma opinião abstrata. É um *Gate* duro. Se o `lint-and-validate` falhou, o verdict Nunca pode ser Aprovação Condicional. Se testes estão ausentes em um refactor crítico, o verdict é REJEIÇÃO automática.
- **Transparência Extrema:** A "Final Human View" deve elencar claramente o que foi tocado e os potenciais débitos técnicos aceitos (ex: "Aprovado, mas O(n^2) tolerado na busca por restrição de escopo").

## Procedimento
1. **Agrupe as Falhas:**
   - Junte todos os apontamentos coletados pela skill `review-item`. Elimine nitpicks (chatices estilísticas puras que o linter resolveria) das falhas bloqueantes de arquitetura/segurança.
2. **Defina o Verdict:**
   - APPROVED: Zero falhas estruturais, lints passaram, cobertura OK.
   - CHANGES_REQUESTED: Lógica ok, mas faltam testes, documentação, ou há pequenos ofensores de Clean Code.
   - BLOCKED: Falha de segurança material (`vulnerability-scanner`), linter quebrado, ou desvio flagrante da Spec do usuário.
3. **Produza o Relatório de Fechamento (`review-verdict`):**
   - Estruture em seções curtas com GitHub Alerts: `> [!IMPORTANT] Segurança e Cobertura OK`.
   - Se rejeitado, delegue o *Handoff* de volta ao Developer Engineer com o log limpo do erro.

## Scripts

- `scripts/consolidate-verdict.py`: consolida artifacts de review em veredito canônico.
- `scripts/export-review-summary.py`: exporta uma view humana do review consolidado.

## If Step Fails

- Se gates ou findings estiverem stale, devolva o fluxo para `review-item` ou `lint-and-validate` em vez de fechar um veredito fraco.
- Se seguranca nao estiver terminal, preserve o blocker e explicite a dependencia restante.

## Exit Conditions

- O veredito canonico foi gerado a partir dos artifacts atuais.
- O status final deixa claro se o diff esta aprovado, bloqueado ou requer mudancas.
- A view humana final foi exportada ou a impossibilidade ficou registrada.

## Expected Handoff

Entregue `review-verdict`, `gate-clearance-report` e `final-human-view` consistentes, prontos para o reviewer comunicar a decisao terminal.

## Exemplos

### Caso positivo
**Entrada:** Itens de review e gate-report já existem e precisam virar veredito final.
**Saída esperada:** Consolidar findings, status de segurança, evidências e decisão terminal sem reabrir análise ampla.

### Caso negativo
**Entrada:** Usuário pede começar um review do zero.
**Por quê não:** Use `review-session`; ainda não há sessão nem plano.

## Evals de trigger

Deve acionar:
- "fecha o review com veredito"
- "consolida findings e gate-report"

Não deve acionar:
- "começa um review"
- "audita esta linha específica"
