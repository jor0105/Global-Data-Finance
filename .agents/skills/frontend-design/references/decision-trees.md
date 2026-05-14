# Decision Trees & Context Templates

## Uso rapido

Leia quando:
- voce precisa sair do "deixa bonito" e transformar a decisao em estrutura,
  prioridades, CTA e trade-offs de tela
- o problema principal e layout, hierarquia, fluxo, ordem de leitura,
  responsividade ou preservacao de sistema existente

Extraia:
- a categoria da interface e a pressao principal da tela
- a combinacao de layout e navegacao que reduz mais friccao
- o viewport dominante e as restricoes reais de conteudo
- o que precisa ser preservado para nao abrir redesign arbitrario
- quando a decisao deixou de ser de tela e virou hand-off de sistema visual

> Use este arquivo para decidir estrutura e comportamento.
> Para paleta, tipografia, motion-base e efeitos, leia `../../ui-ux/references/`.

## 1. Master Decision Tree

```
WHAT ARE YOU BUILDING?
        │
        ├── E-commerce
        │   ├── Goal: Trust + action
        │   └── Pressure: comparison, checkout, objection handling
        │
        ├── SaaS / App
        │   ├── Goal: Clarity + efficiency
        │   └── Pressure: density, orientation, next action
        │
        └── Content / Landing / Portfolio
            ├── Goal: Story + conversion
            └── Pressure: narrative, proof, memorability
```

Pergunte apenas o que muda materialmente a estrutura. Se a duvida for de cor,
tipografia ou estilo-base, abra hand-off para `ui-ux`.

## 2. Audience Decision Tree

Priorize nesta ordem: job-to-be-done, letramento de dominio, device, ambiente de
uso e necessidade de confianca. Faixa etaria so entra quando nao houver sinal
mais forte.

```
TARGET USER
    │
    ├── B2B / Enterprise
    │   ├── Needs: densidade controlada, previsibilidade, ROI
    │   └── Layout bias: grid claro, filtros visiveis, navegação previsível
    │
    ├── Consumer / Casual
    │   ├── Needs: clareza imediata, onboarding leve, convencimento rapido
    │   └── Layout bias: leitura linear, CTAs evidentes, menos opcoes simultaneas
    │
    ├── Expert / Analyst
    │   ├── Needs: comparacao, scan rapido, historico, shortcuts
    │   └── Layout bias: dashboards, tabelas, atalhos, estado persistido
    │
    └── Low-confidence / High-trust
        ├── Needs: prova, explicacao, feedback e seguranca
        └── Layout bias: fluxo linear, help text, confirmacoes explicitas
```

## 3. Visual System Hand-off

Se a duvida principal virar qualquer um destes itens, pare de decidir localmente
e consulte `ui-ux`:

- paleta nova, contraste, tema claro/escuro ou tokens de cor
- pairing, escala, familias tipograficas ou densidade tipografica
- motion-base, estilo de efeitos, iconografia ou linguagem estetica
- branding, estilo "premium/brutalist/playful/enterprise" ou design system novo

Este arquivo continua owner de:

- estrutura da pagina
- hierarquia de informacao
- ordem de modulos
- CTA principal e secundario
- comportamento mobile e desktop
- estados e feedback da tela

## 4. E-commerce Guidelines

### Key Principles

- Trust first
- Action-oriented
- Scannable comparison

### Layout Principles

```
HEADER
  brand + search + cart + suporte essencial

TRUST ZONE
  shipping, returns, security, guarantees

HERO OR CATEGORY ENTRY
  foco unico e CTA claro

PRODUCT DISCOVERY
  filtros, ordenacao, comparacao e preco visiveis

SOCIAL PROOF
  reviews, testimonials, ratings

FOOTER
  politicas, contato, detalhes
```

### Psychology to Apply

- Hick's Law: limite opcoes simultaneas
- Fitts' Law: CTA de compra grande e proxima
- Social proof: prova perto de objecoes
- Scarcity: use apenas quando real

## 5. SaaS Dashboard Guidelines

### Key Principles

- Functional first
- Calm UI
- Consistent patterns

### Layout Principles

Considere estes padroes, sem tratá-los como mandatorio:

```
OPTION A: Sidebar + Content
  melhor para navegacao estrutural e muitos modulos

OPTION B: Top nav + Content
  melhor quando o conteudo horizontal importa mais

OPTION C: Collapsed + Expandable
  melhor quando a densidade compete com a navegacao
```

### Psychology to Apply

- Hick's Law: agrupe navegacao e filtros
- Miller's Law: chunk de metricas e tabelas
- Cognitive Load: consistencia, whitespace e defaults seguros

## 6. Landing Page Guidelines

### Key Principles

- Hero-centric
- Single focus
- Emotional before operational

### Structure Principles

```
NAVIGATION
  minima, CTA visivel

HERO
  hook + valor + CTA

PROBLEM
  dor principal

SOLUTION
  como resolve

PROOF
  testimonials, logos, stats

HOW / FAQ / PRICING
  objecoes e clarificacao

FINAL CTA
  repetir a acao principal
```

### Psychology to Apply

- Serial Position: key info no topo e no fim
- Social Proof: prova antes do CTA final
- Emotional Design: impressao inicial a servico da conversao

## 7. Portfolio Guidelines

### Key Principles

- Personality
- Work-focused
- Memorable but readable

### Structure Principles

```
INTRO
  quem e, o que faz, por que lembrar

WORK
  projetos destacados e facil exploracao

ABOUT
  historia e posicionamento

CONTACT
  caminho curto para a proxima conversa
```

### Psychology to Apply

- Von Restorff: diferencie o que deve ser lembrado
- Reflective: historia pessoal cria conexao
- Emotional: personalidade nao pode matar legibilidade

## 8. Pre-Design Checklists

### Before Starting Any Screen Work

- [ ] objetivo principal definido?
- [ ] CTA principal identificado?
- [ ] viewport dominante conhecido?
- [ ] restricoes de conteudo e implementacao conhecidas?
- [ ] sistema visual existente mapeado?
- [ ] alguma decisao na verdade exige `ui-ux`?

### Before Finalizing Layout

- [ ] hierarquia clara?
- [ ] primary CTA obvio?
- [ ] mobile considerado?
- [ ] feedback e estados previstos?
- [ ] conteudo cabe na estrutura sem inflar a tela?

### Before Delivery

- [ ] resolve a tarefa mais rapido?
- [ ] preserva o sistema existente?
- [ ] evita genericidade sem abrir redesign desnecessario?

## 9. Complexity Estimation

### Quick Projects

```
single component
small form
simple landing section
localized dashboard adjustment
```

→ abordagem: menor mudanca suficiente

### Medium Projects

```
multi-step flow
dashboard com modulos
multi-section landing
complex responsive adaptation
```

→ abordagem: estrutura clara, estados explicitos, possivel consulta a `ui-ux`

### Large Projects

```
full SaaS surface
large workflow redesign
cross-page navigation rethink
product-level IA of task flows
```

→ abordagem: owner de tela aqui + sistema visual tratado em `ui-ux` quando necessario
