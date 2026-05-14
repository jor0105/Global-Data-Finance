---
name: frontend-design
description: >
  Use para decisoes de tela, fluxo, hierarquia, CTA, estados, responsividade e
  revisao de UI web dentro de um sistema visual ja definido ou preservado. Ative
  quando o usuario pedir "melhora essa tela", "faz uma revisao visual", "essa
  interface esta confusa", "cria o fluxo da tela" ou "redesenha isso sem perder
  o design system". Nao use para criar paleta, tokens, tipografia, iconografia,
  tema, branding ou design system novo; nesses casos prefira `ui-ux`.
---

# Frontend Design

## Procedimento

1. Antes de propor qualquer solucao, classifique o pedido em um destes casos:
   - tela nova, fluxo novo ou redesign aberto dentro de sistema visual preservado
   - revisao de uma tela existente com problemas observaveis
   - ajuste localizado em uma UI ja governada por design system
2. Abra a resposta explicando em prosa simples qual caso domina a decisao, o que
   esta sendo preservado e o que ficou fora.
3. Levante o contexto minimo: objetivo principal da tela, conteudo dominante,
   estado atual, viewport principal, restricoes de produto e se o sistema visual
   esta definido ou precisa apenas ser respeitado.
4. Se o pedido for tela nova, fluxo novo ou redesign aberto, entregue direcao de
   tela antes de codigo: hierarquia, layout, CTA principal por tarefa e viewport,
   estados interativos, responsividade, acessibilidade e interacao.
5. Se o pedido for revisao de tela existente, entregue findings primeiro,
   ordenados por impacto, com correcoes objetivas e riscos de UX, acessibilidade
   ou consistencia.
6. Se o pedido for ajuste localizado em sistema consolidado, proponha a menor
   mudanca capaz de resolver o problema sem abrir redesign arbitrario.
7. Preserve o sistema visual consolidado. Trate tokens, componentes, tema e
   regras existentes como padrao, nao como sugestao.
8. Se o trabalho de tela revelar necessidade de nova paleta, novos tokens,
   tipografia, motion-base, iconografia ou estilo-base, mantenha ownership da
   tela aqui e consulte `../ui-ux/SKILL.md` para o sistema visual.
9. Se nao houver decisao real de UX web, layout, fluxo, hierarquia ou review,
   saia da skill e redirecione para a skill correta.

## Heuristicas

- Priorize clareza de tarefa, leitura e fluxo antes de detalhe cosmetico.
- Faca o CTA principal ficar obvio para a tarefa atual e para o viewport atual.
- Toda interface clicavel precisa de feedback visivel. Toda acao assincrona
  precisa de estado explicito.
- Preserve densidade, componentes e convencoes do produto antes de introduzir
  novidade visual.
- Use estilo forte apenas quando ele for suportado pelo contexto da tela; se a
  mudanca pedida for de linguagem visual, abra hand-off para `ui-ux`.
- Quando revisar codigo, diferencie defeito de fluxo e defeito de sistema visual.
  O primeiro e desta skill; o segundo deve ser deferido ao owner visual.

## Padroes de sizing e CSS

- Nao congele layout, espacamento ou componentes em valores fixos arbitrarios.
  Trate sizing como sistema fluido e adaptativo por viewport e container.
- Prefira medidas relativas e fluidas para implementacao: `%`, `fr`, `rem`,
  `em`, `vw`, `vh`, `clamp()` e limites responsivos por breakpoint ou container.
- Evite largura, altura, `gap`, `padding` e `margin` como numeros soltos quando
  eles puderem vir de escala existente.
- Se alguma restricao tecnica exigir minimo estavel, esconda isso atras de token
  semantico em vez de espalhar numero cru.
- Consuma tokens existentes para cores, tipografia, raios, sombras e motion. Se
  o token certo ainda nao existir, consulte `ui-ux` em vez de inventar
  sistema novo dentro da tela.

## Contrato de saida

### Quando o pedido for tela nova, fluxo novo ou redesign aberto

Entregue um brief curto e implementavel contendo:

- qual aspecto da tela ainda precisa ser decidido e por que esse e o eixo dominante
- hierarquia visual e estrutura da tela
- comportamento mobile e desktop
- estados `default`, `hover`, `focus`, `loading`, `empty` e `error`
- restricoes de implementacao e o que precisa ser preservado do sistema existente
- dependencias visuais que precisam ser mantidas ou consultadas em `ui-ux`

### Quando o pedido for revisao de tela existente

Entregue findings primeiro, ordenados por impacto. Depois traga:

- por que o caso e de revisao e nao de redesign aberto
- correcoes recomendadas
- riscos de UX ou acessibilidade
- o que deve ser preservado para nao piorar a consistencia do sistema
- se algum problema na verdade exige hand-off de sistema visual para `ui-ux`

### Quando o pedido for ajuste localizado em sistema consolidado

Entregue mudancas minimas e especificas:

- qual problema real sera corrigido
- o que ajustar
- o que preservar
- quais tokens, componentes ou padroes existentes devem continuar mandando

Nao abra redesign completo nesse caso.

## Uso de scripts

- Use `scripts/ux_audit.py <path>` para revisar heuristicas de UX/UI em codigo existente.
- Use `scripts/ux_audit.py <path> --json` quando o volume de achados pedir estrutura.
- Use `scripts/accessibility_checker.py <project_path>` para uma varredura rapida de acessibilidade.
- Nao rode scripts em pedidos puramente conceituais, sem codigo, ou quando a analise manual ja for suficiente.

## Exemplos

### Caso positivo

**Entrada:** Usuario pede para redesenhar um dashboard confuso, melhorar a hierarquia e decidir como o CTA principal aparece no mobile sem perder o design system atual.
**Saida esperada:** Explicar que o pedido e de tela/fluxo dentro de sistema preservado, depois entregar direcao de layout, prioridade de CTA, estados, responsividade e restricoes de implementacao.

### Caso positivo

**Entrada:** Usuario pede novo fluxo de onboarding e descobre no meio que a tela tambem precisa de uma paleta nova.
**Saida esperada:** Manter ownership da tela em `frontend-design`, definir estrutura e fluxo, e consultar `ui-ux` apenas para o sistema visual.

### Caso negativo

**Entrada:** Usuario pede gerar design system, paleta, tipografia e tokens para um produto novo.
**Por que nao:** O problema dominante e sistema visual. Use `ui-ux`.

### Caso negativo

**Entrada:** Usuario pede apenas para corrigir um erro de TypeScript em um componente sem mudar a UI.
**Por que nao:** E manutencao tecnica. A skill nao deve ser carregada quando nao ha decisao real de UX, layout ou review de tela.

## Evals de trigger

Deve acionar:

- "melhora essa tela para mobile e desktop sem perder o design system"
- "faz uma revisao visual desse fluxo porque ele parece confuso"
- "cria o fluxo principal dessa interface e decide a hierarquia"
- "redesenha essa tela, mas preserve o visual atual"

Nao deve acionar:

- "gera paleta, tipografia e tokens para esse dashboard"
- "cria um design system brutalist para o produto"
- "troque essa classe para usar o token que ja existe"
- "corrige esse import quebrado"
- "otimiza essa query SQL"

## Evals de workflow

### Caso 1 - tela nova dentro de sistema existente

**Entrada:** redesign de tela com problema de hierarquia visual, estado vazio fraco e CTA pouco claro, preservando o sistema atual.

Assertions:
- [ ] output deixa claro que o pedido precisa de direcao de tela antes de codigo
- [ ] output explica o que esta sendo preservado do sistema existente
- [ ] output inclui hierarquia visual e estrutura da tela
- [ ] output inclui estados `default`, `hover`, `focus`, `loading`, `empty` e `error`
- [ ] output inclui comportamento mobile e desktop
- [ ] output evita reinventar paleta, tipografia ou motion-base

### Caso 2 - revisao de tela existente

**Entrada:** tela pronta parece generica, densa e inconsistente no mobile.

Assertions:
- [ ] findings aparecem antes das recomendacoes
- [ ] output explica por que o caso e de revisao e nao de redesign aberto
- [ ] output inclui riscos de UX ou acessibilidade
- [ ] output recomenda script apenas se houver codigo existente e evidencia util
- [ ] output separa defeitos de fluxo de defeitos de sistema visual

### Caso 3 - pedido misto

**Entrada:** tela nova exige fluxo novo e tambem uma paleta nova.

Assertions:
- [ ] output mantem `frontend-design` como owner da tela
- [ ] output abre hand-off explicito para `ui-ux` no sistema visual
- [ ] output nao tenta fechar layout e design system como se fossem a mesma decisao

## Referencias

Leia apenas o arquivo necessario para a decisao em maos:

| Necessidade | Ler | Extrair |
|---|---|---|
| Estrutura de tela, layout e caminhos de decisao | `references/decision-trees.md`, `references/reference.md` | organizacao de tela, direcao de layout e fronteira entre redesign e preservacao |
| Psicologia de UX, priorizacao e confianca | `references/ux-psychology.md` | custo de decisao, feedback, densidade, confianca e riscos cognitivos |
| Sistema de cor e contraste | `../ui-ux/references/color-system.md` | familia de cor, distribuicao, contraste e anti-patterns visuais |
| Sistema tipografico | `../ui-ux/references/typography-system.md` | escala, pairing, line-height, line-length e tokens de tipografia |
| Motion e microinteracoes | `../ui-ux/references/animation-guide.md`, `../ui-ux/references/motion-graphics.md` | motion-base, limites de efeitos e quando abrir hand-off visual |
| Efeitos visuais e acabamento | `../ui-ux/references/visual-effects.md` | gradientes, sombras, overlays e guardrails de efeitos |
| Exemplos rapidos de acionamento | `references/examples.md` | comparacao entre caso de tela e caso mecanico |
