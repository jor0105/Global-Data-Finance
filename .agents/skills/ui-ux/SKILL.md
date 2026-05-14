---
name: ui-ux
description: >
  Use para definir a identidade visual de um produto ou feature quando a duvida
  principal for cores, tipografia, tokens, motion, iconografia, tema, branding
  ou design system. Ative quando o usuario pedir "essa interface esta generica",
  "qual estetica combina com esse produto?", "monta um design system", "define
  uma paleta", "escolhe as fontes", "cria tokens" ou quando `frontend-design`
  ja resolveu a tela e precisa apenas do sistema visual. Nao use para layout,
  fluxo, CTA, responsividade ou review de tela.
---

# UI/UX

## Fundamentos

- **Owner de identidade visual:** esta skill decide paleta, tokens,
  tipografia, motion-base, iconografia, tema, branding e guardrails esteticos.
  Ela nao e owner de layout, fluxo, CTA, responsividade ou review de tela.
- **Sistema antes de detalhe:** transforme a direcao visual em tema, custom
  properties ou tokens semanticos antes de falar de um componente isolado.
- **Saida reutilizavel:** entregue um sistema aplicavel em varias telas, nao uma
  resposta ad hoc para um unico bloco de UI.

## Procedimento

1. Classifique o pedido em um destes modos:
   - identidade visual ou design system para produto, marca, tema ou feature
   - apoio a outra skill, normalmente `frontend-design`, que ja decidiu a tela
   - ajuste mecanico que na verdade nao pede decisao de sistema visual
2. Se o pedido for de apoio a outra skill, limite a saida a paleta, tokens,
   tipografia, motion, iconografia, efeitos e anti-patterns. Nao tome ownership
   de layout, fluxo, CTA, responsividade ou ordem dos modulos.
3. Levante o contexto minimo: tipo de produto, industria, sinais de marca,
   restricoes existentes, stack, nivel de maturidade do sistema atual e se a
   expectativa e evoluir ou substituir o visual existente.
4. Para o fluxo completo, use `scripts/visual_system_workflow.py`; ele consome
   os datasets locais em `assets/data/`, automatiza design system base,
   suplementos por dominio e stack guidance. Use `scripts/search.py` apenas
   para buscas cirurgicas ou quando voce quiser um dominio especifico.
5. Quando o sistema visual precisar durar, use `--persist` para gerar
   `design-system/MASTER.md` e overrides por pagina quando fizer sentido.
6. Traduza a direcao encontrada para tokens, familias visuais, regras de uso,
   exemplos de aplicacao, anti-patterns e limites de implementacao. Quando a
   skill estiver apoiando implementacao, explicite como isso entra em theme,
   CSS, framework config ou componentes base.
7. Se o problema real for tela, fluxo, review, CTA ou responsividade web,
   redirecione para `frontend-design`. Se for mecanico dentro de um sistema
   fechado, redirecione para a skill tecnica apropriada.

## Scripts

- `scripts/visual_system_workflow.py`: entrypoint automatico para o fluxo
  completo de identidade visual, com design system, suplementos por dominio e
  stack guidance.
- `scripts/core.py`: biblioteca de busca e dados usada pelos scripts da skill.
- `scripts/design_system.py`: gera artefatos de design system a partir dos dados locais.
- `scripts/search.py`: busca estilos, cores, tipografia, UX visual e stack guidance.

## Assets

- `assets/data/*.csv`: datasets locais de estilos, cores, produtos, tipografia,
  prompts, UX visual e padroes web usados pelos scripts para fundamentar a
  direcao visual.
- `assets/data/stacks/*.csv`: guias por stack para React, Next.js, Tailwind,
  shadcn, Vue, mobile e afins. Consulte via scripts; nao precisa ler CSV
  manualmente a menos que esteja depurando a skill.

## Referencias

Leia apenas o arquivo necessario para a decisao em maos:

| Necessidade | Ler | Extrair |
|---|---|---|
| Cor, contraste, dark mode e anti-patterns de paleta | `references/color-system.md` | familias de cor, distribuicao, contraste, emotion mapping e guardrails |
| Escala, pairing e legibilidade tipografica | `references/typography-system.md` | font pairing, escala, line-height, line-length e tokens |
| Motion base e microinteracoes | `references/animation-guide.md` | duracao, easing, loading, hover e reduced motion |
| Motion avancado e acabamento premium | `references/motion-graphics.md` | Lottie, GSAP, SVG, 3D, performance e limites |
| Gradientes, sombras, glassmorphism e efeitos | `references/visual-effects.md` | efeitos visuais, overlays, glow e anti-patterns |

## Exemplos

### Caso positivo

**Entrada:** Usuario pede "essa interface esta generica; define paleta, tipografia e tokens para esse produto".
**Saida esperada:** Selecionar direcao visual, gerar sistema reutilizavel e definir tokens, guardrails e anti-patterns.

### Caso positivo

**Entrada:** `frontend-design` esta desenhando um onboarding novo e precisa de uma paleta, tipografia e motion-base para sustentar a tela.
**Saida esperada:** Entregar apenas o sistema visual e os anti-patterns, sem tomar ownership do fluxo ou do layout.

### Caso negativo

**Entrada:** Usuario pede revisar uma tela confusa, reorganizar a hierarquia e melhorar o CTA no mobile.
**Por que nao:** O problema dominante e tela, fluxo ou review. Use `frontend-design`.

### Caso negativo

**Entrada:** Usuario pede trocar uma classe para usar um token que ja existe.
**Por que nao:** E ajuste mecanico dentro de sistema fechado, nao decisao de identidade visual.

## Evals de trigger

Deve acionar:

- "essa interface esta generica; define uma linguagem visual melhor"
- "monta um design system para esse produto"
- "escolhe paleta e tipografia para esse dashboard"
- "define uma estetica enterprise para este SaaS"
- "essa tela ja tem fluxo resolvido, mas precisa de uma identidade visual nova"

Nao deve acionar:

- "melhora essa tela para mobile e desktop sem perder o design system"
- "faz uma revisao visual desse fluxo porque o CTA esta perdido"
- "troque essa classe para usar o token que ja foi definido"
- "corrige aria-label"
- "erro SQL"

## Evals de workflow

### Caso 1 - identidade visual standalone

**Entrada:** produto novo precisa de design system, paleta, tipografia, tema e tokens.

Assertions:
- [ ] output deixa claro que o owner e de identidade visual, nao de tela
- [ ] output comeca por direcao visual e sistema de tokens
- [ ] output inclui paleta, tipografia, motion/effects quando relevantes
- [ ] output inclui guardrails, anti-patterns e limites de implementacao
- [ ] output nao tenta decidir layout, CTA ou ordem dos modulos da tela

### Caso 2 - apoio a `frontend-design`

**Entrada:** tela nova precisa de fluxo novo e tambem de paleta nova.

Assertions:
- [ ] output assume papel de apoio ao owner da tela
- [ ] output limita a resposta a paleta, tokens, tipografia, motion, efeitos e iconografia
- [ ] output nao toma ownership de layout, CTA ou responsividade
- [ ] output deixa `frontend-design` como owner explicito da tela

### Caso 3 - near-miss de tela

**Entrada:** pedido para reorganizar hierarquia, responsividade e estados de uma tela existente.

Assertions:
- [ ] output redireciona para `frontend-design`
- [ ] output nao tenta resolver a tela como se fosse apenas identidade visual
- [ ] output deixa explicita a fronteira entre tela e sistema visual
