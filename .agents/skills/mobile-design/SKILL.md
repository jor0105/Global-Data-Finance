---
name: mobile-design
description: >
  Use para decisoes de UX mobile nativo ou cross-platform em iOS, Android,
  React Native, Expo, Flutter, SwiftUI ou Jetpack Compose. Ative quando o
  usuario pedir "reve essa tela React Native", "safe area quebrada",
  "keyboard avoidance", "gesture", "bottom sheet", "push notification",
  "app lifecycle", "permissoes mobile" ou "melhora esse fluxo mobile nativo".
  Nao use para CSS, Tailwind, layout responsivo de SaaS web, viewport estreita
  ou React web; nesses casos prefira `frontend-design`.
---

# Mobile Design

## Procedimento

1. Antes de propor a solucao, decida qual destes casos descreve melhor o pedido:
   - desenho de fluxo ou tela mobile nova
   - revisao de implementacao existente com problema observavel
   - ajuste localizado preservando convencoes nativas e sistema existente
2. Abra a resposta explicando em prosa simples qual caso domina, por que ele manda na decisao e o que ficou fora.
3. Levante o contexto minimo: plataforma alvo, framework, fluxo principal, shell de navegacao, estado atual, device dominante, restricoes de produto e se ha design system ou biblioteca mobile consolidada.
4. Diferencie cedo o que e compartilhado do que precisa ser especifico de iOS ou Android. Nao force uma solucao unica quando isso empobrecer gesto, navegacao, feedback ou acessibilidade da plataforma.
5. Se o pedido for desenho de fluxo ou tela nova, entregue direcao concreta antes de codigo: jornada principal, CTA por tela, navegacao, gesto ou alternativa visivel, comportamento do back, safe area, teclado, estados assincronos e recuperacao apos interrupcao.
6. Se o pedido for revisao de implementacao existente, entregue findings primeiro, ordenados por impacto, cobrindo safe area, teclado virtual, toque, navegacao, lifecycle, fidelidade de plataforma e performance percebida quando relevante.
7. Se o pedido for ajuste localizado em app consolidado, proponha a menor mudanca capaz de resolver o problema sem abrir redesign arbitrario nem importar padroes web por reflexo.
8. Modele estados reais de uso movel: `loading`, `empty`, `error`, `offline`, `permission denied`, `backgrounded`, `resumed` e retorno apos o app ser encerrado pelo sistema quando isso afetar o fluxo.
9. Preserve padroes nativos quando eles carregam expectativa do usuario. Quando optar por componente neutro ou cross-platform, explicite o porquê e o custo da escolha.
10. Se houver codigo existente e a resposta se beneficiar de evidencia, use `scripts/mobile_audit.py` para codigo React Native ou Flutter antes de concluir.
11. Se o problema na verdade for web responsiva, CSS ou dashboard SaaS em viewport estreita, nao force a skill. Redirecione para `frontend-design`.

## Heuristicas

- Safe areas e barras do sistema nao sao detalhe cosmetico. Conteudo, CTA fixo, bottom sheet e gesto de fechar nao podem disputar espaco com notch, island, status bar ou home indicator.
- Teclado virtual faz parte do layout. Inputs criticos precisam permanecer visiveis com margem adequada, scroll previsivel, dismiss claro e tipo de teclado coerente com o dado.
- Toque e impreciso. Use area interativa minima de 44x44 pt no iOS ou 48x48 dp no Android, com pelo menos 8 pt entre alvos concorrentes.
- Thumb zone importa mais que simetria. Acoes frequentes e decisivas devem ficar acessiveis com uma mao; menus distantes do polegar pedem motivo forte.
- Navegacao mobile e comportamento, nao apenas estrutura. Stack, tabs, modal, sheet, swipe back e hardware back precisam formar um fluxo coerente e reversivel.
- Sempre ofereca alternativa visivel para gesto importante. Swipe sem affordance, sheet sem handle claro ou back implicito demais aumenta erro e reduz acessibilidade motora.
- Offline e latencia precisam de estado explicito. Mostre conexao ausente, retry, cache local quando existir e o que o usuario pode ou nao fazer naquele momento.
- Interrupcao e parte do uso normal. Considere background, retorno por push, troca de app, perda de foco, permissao negada e restauracao parcial de contexto.
- Fidelidade a iOS e Android vale mais que copiar web. Feedback tatil, ripple, tipografia, densidade, navegacao e linguagem de componentes devem respeitar a plataforma.
- Motion em mobile precisa caber no orcamento de performance. Prefira feedback curto, claro e leve; evite animacoes que disputem CPU, bateria ou scroll fluido.

## Contrato de saida

### Quando o pedido for desenho de fluxo ou tela mobile nova

Entregue um brief curto e implementavel contendo:

- qual parte da experiencia mobile ainda precisa ser decidida e por que esse e o eixo dominante
- arquitetura de tela e navegacao principal
- CTA principal por tarefa e por viewport movel
- estados `default`, `focus`, `loading`, `empty`, `error`, `offline`, `permission denied`, `backgrounded` e `resumed` quando relevantes
- diferencas de comportamento entre iOS e Android
- restricoes de implementacao, preservacao de componentes existentes e riscos de UX ou performance

### Quando o pedido for revisao de implementacao existente

Entregue findings primeiro, ordenados por impacto. Depois traga:

- por que o caso e de revisao e nao de desenho novo
- correcoes recomendadas
- riscos de UX, acessibilidade, lifecycle ou performance percebida
- o que deve ser preservado para nao quebrar consistencia de plataforma ou design system

### Quando o pedido for ajuste localizado preservando convencoes nativas

Entregue mudancas minimas e especificas:

- qual problema real sera corrigido
- o que ajustar
- o que preservar
- quais padroes nativos, componentes ou tokens existentes devem continuar mandando

Nao abra redesign completo nesse caso.

## Uso de scripts

- Use `python3 .agents/skills/mobile-design/scripts/mobile_audit.py <path>` para revisar codigo React Native ou Flutter com evidencia estatica.
- Use `python3 .agents/skills/mobile-design/scripts/mobile_audit.py <path> --json` quando o volume de achados pedir estrutura para resumir melhor.
- O script atual e focado em React Native e Flutter. Para SwiftUI ou Jetpack Compose, faca revisao manual guiada pelas referencias da skill.
- Nao rode o script para CSS, Tailwind, viewport estreita em web ou responsividade de SaaS; nesses casos a skill correta e `frontend-design`.

## Exemplos

### Caso positivo

**Entrada:** Usuario pede para desenhar o fluxo principal de onboarding em React Native com permissao de notificacao, recuperacao apos interrupcao e navegacao por tabs.
**Saida esperada:** Explicar que o pedido exige desenho de fluxo mobile, depois entregar arquitetura do fluxo, CTA principal, estados de permissao e diferencas entre iOS e Android.

### Caso positivo

**Entrada:** Usuario pede revisao de uma tela Flutter que parece apertada, corta conteudo no notch e fica ruim quando o teclado abre.
**Saida esperada:** Explicar que o pedido e uma revisao de implementacao existente, listar findings primeiro e usar o script apenas se houver codigo Flutter util para sustentar a resposta.

### Caso negativo

**Entrada:** Usuario pede para arrumar um layout no celular com Tailwind, viewport de 390px e CTA desalinhado.
**Por que nao:** Isso e UI web responsiva. Use `frontend-design`; o eixo dominante nao e app mobile nativo.

## Evals de trigger

Deve acionar:

- "projeta essa tela em React Native com bottom sheet e swipe back"
- "safe area e keyboardAvoidingView quebrados no iOS"
- "reve esse fluxo Flutter porque o back e o offline estao estranhos"
- "decide entre tabs, stack e modal para esse app Expo"
- "quero melhorar permissoes, push notification e lifecycle desse app Android"

Nao deve acionar:

- "arruma esse layout no celular com Tailwind"
- "essa tela React web esta ruim em 390px"
- "ajusta o CSS responsivo desse dashboard SaaS"
- "erro de import no backend"

## Evals de workflow

### Caso 1 - desenho de fluxo ou tela mobile nova

**Entrada:** novo fluxo React Native com tabs, permissao de camera, estado offline e retomada apos background.

Assertions:
- [ ] output deixa claro que o pedido exige desenho da experiencia mobile antes de codigo
- [ ] output explica por que nao e apenas revisao de implementacao ou ajuste localizado
- [ ] output inclui arquitetura de tela e navegacao
- [ ] output inclui CTA principal por tela ou tarefa
- [ ] output inclui estados `offline` e `resumed`
- [ ] output explicita diferencas entre iOS e Android quando elas mudam a solucao
- [ ] output evita importar convencoes web como default

### Caso 2 - revisao de implementacao existente

**Entrada:** tela Flutter pronta corta conteudo no notch, perde contexto ao voltar do background e esconde input atras do teclado.

Assertions:
- [ ] findings aparecem antes das recomendacoes
- [ ] output explica por que o caso e de revisao e nao de desenho novo
- [ ] output cobre safe area, teclado virtual ou lifecycle
- [ ] output recomenda script apenas se houver codigo existente util
- [ ] output inclui risco de UX, acessibilidade ou performance percebida

### Caso 3 - ajuste localizado preservando convencoes nativas

**Entrada:** owner quer justificar redesign amplo de uma tela iOS que ja segue bem o padrao nativo, quando o problema real e so o CTA secundario competir com o primario.

Assertions:
- [ ] output limita a mudanca ao problema real
- [ ] output preserva padroes nativos e componentes existentes
- [ ] output nao abre redesign arbitrario

## Referencias

Leia apenas o arquivo necessario para a decisao em maos:

| Necessidade | Ler | Extrair |
|---|---|---|
| Escolher fluxo, plataforma e abordagem mobile | `references/decision-trees.md`, `references/mobile-design-thinking.md` | framing do problema, trade-offs de plataforma e fronteira entre fluxo novo e preservacao |
| Navegacao, back behavior, tabs, modais e sheets | `references/mobile-navigation.md` | arquitetura de navegacao, gesto de retorno e padroes de shell |
| Tipografia, cor e toque | `references/mobile-typography.md`, `references/mobile-color-system.md`, `references/touch-psychology.md` | escala, contraste, feedback tatil ou visual e ergonomia de toque |
| Performance percebida, backend e debugging | `references/mobile-performance.md`, `references/mobile-backend.md`, `references/mobile-debugging.md` | budgets de animacao, estados offline, caching e investigacao de falhas |
| Testes e validacao | `references/mobile-testing.md` | estrategia de teste, device matrix e limites de simulacao |
| Particularidades de iOS e Android | `references/platform-ios.md`, `references/platform-android.md` | convencoes nativas, componentes esperados e diferencas de comportamento |
