# Next App Router Boundaries

## Quando ler

- Use esta referência apenas para projetos Next com App Router, Server Components, `"use client"` ou `next/dynamic`.
- Ignore esta referência em React genérico, Vite, CRA, Remix ou quando o problema não depender de boundary client/server.

## Sinais fortes

- Uma rota inteira virou client component por causa de uma pequena interação.
- Muitos módulos pesados entram no browser porque a boundary está alta demais.
- Fetch e suspense poderiam começar no servidor, mas o trabalho foi puxado para o cliente.

## Checklist de revisão

1. Trate Server Components como default. Só mantenha `"use client"` onde houver interatividade real, browser APIs ou hooks client-only.
2. Empurre `"use client"` para folhas pequenas e serializáveis. Passe dados prontos, não estruturas pesadas nem lógica inteira.
3. Inicie fetch o mais cedo possível no servidor quando a necessidade de dados já for conhecida na rota.
4. Use `next/dynamic` para folhas pesadas e client-only, não para esconder boundary ampla demais.
5. Revise suspense e streaming perto do subtree lento, não como wrapper global da página.

## Recomendações que costumam funcionar

- Manter layout, shell, dados estáveis e formatação pesada no servidor.
- Deixar no cliente apenas o que realmente precisa de evento, input, animação ou browser API.
- Isolar chart, editor, mapa ou painel avançado como folha dinâmica em vez de puxar a rota inteira para o cliente.
- Revisar cache e `revalidate` com base na semântica dos dados, não como chute para performance.

## Anti-patterns

- Subir `"use client"` para resolver um único botão, popover ou campo controlado.
- Puxar todo o fetch para o cliente porque uma parte da tela é interativa.
- Tratar `dynamic` como substituto de boundary mal escolhida.
- Misturar preocupação de performance com preocupação de auth ou segurança; isso pertence a outras skills.

## Evidência esperada

- Menor JS entregue ao browser.
- Menos hidratação desnecessária.
- Boundary interativa menor e mais local.
- Conteúdo útil aparecendo mais cedo com streaming ou trabalho iniciado no servidor.
