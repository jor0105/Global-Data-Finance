---
name: react-performance
description: >
  Use para revisar, diagnosticar ou melhorar performance React no cliente, no
  carregamento de dados e no custo de JavaScript no browser. Ative quando o
  usuário pedir "esse componente re-renderiza demais", "a tela demora para
  carregar", "tem waterfall de requests", "o bundle inicial está pesado",
  "quero reduzir trabalho no browser" ou quando um app React/Next precisar
  revisar boundaries de App Router, Server Components ou `"use client"`. Não
  use para revisão visual/UX, debugging sem sintoma de performance, performance
  de backend puro ou tuning de banco.
---

# React Performance

## Procedimento

1. Descubra qual caso realmente domina o pedido antes de sugerir qualquer correção:
   - se o sintoma for re-render excessivo, lista pesada, digitação travando, muito trabalho por interação ou custo alto no cliente, trate como problema de runtime React
   - se o sintoma for waterfall, fetch tardio, loading fragmentado, refetch duplicado ou cache mal distribuído, trate como problema de carregamento e fluxo de dados
   - se o sintoma depender de App Router, Server Components, `"use client"` ou boundary client/server em Next, trate como problema específico de boundary Next
   - se o gargalo principal não for performance React, não force a skill; redirecione para `frontend-design`, `systematic-debugging`, `performance-profiling`, `database-design` ou `supabase-postgres-best-practices`
2. Leia apenas a referência compatível com o sintoma dominante:
   - runtime React: `references/client-runtime-costs.md`
   - loading, waterfall e cache: `references/loading-waterfalls-and-cache.md`
   - bundle, code splitting e custo de JavaScript: `references/bundle-and-browser-js.md`
   - boundary de Next: `references/next-app-router-boundaries.md`
3. Identifique a evidência esperada antes de propor solução: menos renders, menos CPU no browser, requests paralelos, menor chunk inicial, menos hidratação ou menor tempo até conteúdo útil.
4. Prefira a menor mudança que elimina trabalho desnecessário:
   - mover estado para mais perto de quem consome
   - iniciar trabalho assíncrono mais cedo
   - dividir bundle em folhas pesadas
   - empurrar computação para o servidor quando a stack permitir
   - reduzir custo de render antes de memoizar por reflexo
5. Não recomende `useMemo`, `useCallback`, `memo`, `Suspense`, cache ou `dynamic` por hábito. Amarre cada recomendação ao sintoma dominante e à métrica que ela deve melhorar.
6. Em revisão de código existente, entregue findings primeiro. Depois proponha correções, risco residual e a evidência que confirmaria a melhora.
7. Use `scripts/react_performance_checker.py` quando houver código disponível e a triagem estática puder acelerar a investigação. Se o problema exigir medição real em navegador, combine esta skill com `performance-profiling`.

## Heurísticas

- Re-render excessivo quase sempre pede correção de ownership de estado, derived state redundante ou listas grandes antes de pedir memoização manual.
- Waterfall é problema de ordem de trabalho. Procure `await` sequencial, fetch iniciado tarde, deduplicação ausente ou boundary errada antes de discutir micro-otimização.
- Bundle grande é normalmente problema de fronteira e carregamento. Divida por rota, folha ou interação; evite empurrar dependência pesada para o bootstrap sem necessidade.
- Em React puro, prefira soluções portáveis: loaders do framework, `React.lazy`, suspense adotado pela stack, caches explícitos e redução de trabalho no cliente.
- Em Next, trate Server Components como default e `"use client"` como custo consciente. Mover a fronteira para baixo costuma valer mais do que memoizar a árvore inteira.
- Se a pergunta principal for "por que está quebrando?" e não "por que está lento?", a skill correta é `systematic-debugging`, não esta.

## Contrato de saída

### Quando o pedido for re-render, lista pesada ou trabalho demais no cliente

Entregue findings primeiro, ordenados por impacto. Depois traga:

- por que o problema foi tratado como custo de runtime React
- quais componentes ou hooks estão fazendo trabalho demais
- a mudança recomendada para ownership de estado, renderização ou isolamento
- a métrica ou evidência esperada: menos renders por interação, menor commit cost, menor trabalho por lista ou menos CPU no browser

### Quando o pedido for waterfall, carregamento tardio ou fetch duplicado

Entregue findings primeiro, ordenados por impacto. Depois traga:

- por que o problema foi tratado como carregamento e fluxo de dados
- onde o trabalho começa tarde ou em sequência
- que mudança reduz waterfall, fetch duplicado ou loading tardio
- a evidência esperada: requests em paralelo, menos tempo até conteúdo útil, menos loading intermediário ou menos refetch redundante

### Quando o pedido depender de App Router ou boundary client/server em Next

Entregue findings primeiro, ordenados por impacto. Depois traga:

- por que o problema foi tratado como boundary específica de Next
- qual boundary client/server está cara ou mal posicionada
- o que deve ficar no servidor e o que deve continuar no cliente
- a evidência esperada: menor JS enviado ao browser, menos hidratação, chunk menor ou boundary mais local

## Uso de scripts

- Use `python3 .agents/skills/react-performance/scripts/react_performance_checker.py <path> --framework auto` para triagem estática rápida.
- Use `--framework react` para projetos React genéricos e `--framework next` para varredura explícita de App Router e boundaries.
- Use `--json` quando o volume de findings pedir resumo estruturado.
- Não trate a saída do script como veredito final. Ela serve para apontar onde ler o código primeiro.

## Exemplos

### Caso positivo

**Entrada:** Usuário pede revisão de um componente React que re-renderiza demais depois de cada digitação.
**Saída esperada:** Tratar como problema de runtime React, listar findings primeiro e recomendar ajuste de ownership de estado, derived state ou isolamento antes de memoização automática.

### Caso positivo

**Entrada:** Usuário relata que a página carrega lento porque os requests começam um depois do outro.
**Saída esperada:** Tratar como problema de carregamento, apontar o waterfall, sugerir paralelização ou início mais cedo do trabalho e citar a evidência esperada no painel de rede.

### Caso positivo

**Entrada:** Usuário pede revisão de uma rota Next com muito `"use client"` e bundle inicial pesado.
**Saída esperada:** Tratar como problema específico de boundary em Next, apontar boundaries caras e recomendar mover folhas interativas para baixo ou dividir dependências pesadas.

### Caso negativo

**Entrada:** Usuário pede apenas para melhorar a hierarquia visual de uma tela.
**Por quê não:** O problema dominante é UX/UI. Use `frontend-design`.

### Caso negativo

**Entrada:** Usuário diz que a API está lenta por causa de query no banco.
**Por quê não:** O gargalo principal não é React. Use `performance-profiling`, `database-design` ou `supabase-postgres-best-practices`.

## Evals de trigger

Deve acionar:

- "esse componente React re-renderiza demais"
- "tem waterfall de requests nessa tela"
- "o bundle inicial está pesado"
- "quero reduzir o trabalho no browser"
- "essa rota Next tem client boundary demais"

Não deve acionar:

- "melhora a interface dessa tela"
- "não sei por que isso está quebrando"
- "otimiza essa query SQL"
- "meu backend está lento"
- "escolhe uma paleta visual"

## Evals de workflow

### Caso 1 - re-render, listas ou custo alto no cliente

Entrada: componente React perde fluidez porque cada digitação atualiza árvore grande e recalcula listas.

Assertions:
- [ ] output trata o pedido como problema de runtime React
- [ ] findings aparecem antes das recomendações
- [ ] output tenta corrigir ownership de estado, derived state ou trabalho de lista antes de memoização genérica
- [ ] output cita ao menos uma evidência esperada de melhora

### Caso 2 - waterfall, loading tardio ou fetch duplicado

Entrada: tela dispara três fetches em sequência e mostra múltiplos loadings curtos.

Assertions:
- [ ] output trata o pedido como problema de carregamento e fluxo de dados
- [ ] output aponta o ponto do waterfall ou do trabalho iniciado tarde
- [ ] output recomenda paralelização, cache, suspense ou boundary apenas se compatível com o sintoma
- [ ] output cita a evidência esperada na rede ou no tempo até conteúdo útil

### Caso 3 - boundary client/server em Next

Entrada: rota Next App Router está com muito `"use client"` e gráfico pesado no bundle inicial.

Assertions:
- [ ] output trata o pedido como problema específico de boundary em Next
- [ ] output diferencia o que pode continuar no servidor do que precisa ficar no cliente
- [ ] output evita tratar Next como default quando o problema não for específico de App Router
- [ ] output cita evidência esperada de redução de JS ou hidratação

## Referências

Leia apenas o arquivo necessário para a decisão em mãos:

| Necessidade | Ler | Extrair |
|---|---|---|
| Re-render, ownership de estado, listas e custo de render | `references/client-runtime-costs.md` | heurísticas de runtime React, derived state, memoização criteriosa e isolamento de trabalho |
| Waterfalls, suspense, cache e sequência de carregamento | `references/loading-waterfalls-and-cache.md` | paralelização, início antecipado do trabalho, deduplicação e loading orchestration |
| Bundle, code splitting e custo de JavaScript no browser | `references/bundle-and-browser-js.md` | lazy loading, dependências pesadas, chunking e redução de trabalho no cliente |
| App Router, Server Components e boundaries Next | `references/next-app-router-boundaries.md` | fronteiras client/server, `use client`, `next/dynamic` e streaming/suspense em Next |
