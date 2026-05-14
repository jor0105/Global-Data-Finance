# Client Runtime Costs

## Quando ler

- Use esta referência para re-render excessivo, digitação travando, listas lentas, trabalho demais por interação ou derived state redundante.
- Ignore esta referência se o problema dominante for waterfall de rede, bundle inicial ou boundary específica de Next.

## Sinais fortes

- Cada input atualiza árvore grande demais.
- Filtros, ordenação ou agregações são refeitos a cada render sem necessidade.
- Listas grandes re-renderizam por mudanças locais.
- `useEffect` replica em state algo que já pode ser derivado de props ou state atual.

## Checklist de revisão

1. Descubra quem realmente precisa possuir o estado. Se uma única folha usa o valor, o estado deve ficar perto dela.
2. Remova derived state persistido sem necessidade. Se o valor pode ser calculado durante render, prefira isso.
3. Procure trabalho caro em render: `map`, `filter`, `sort`, serialização, parsing ou formatação sobre coleções grandes.
4. Em listas extensas, valide keys estáveis, virtualização e isolamento de itens antes de discutir memoização fina.
5. Só recomende `memo`, `useMemo` ou `useCallback` quando existir custo mensurável e dependência realmente estável.

## Recomendações que costumam funcionar

- Colocar estado transitório de input, hover, expansão ou edição perto do componente interativo.
- Passar dados já reduzidos para filhos pesados, em vez de fazer o filho decidir tudo.
- Trocar `useEffect` que seta derived state por cálculo direto ou reset por `key`.
- Separar componentes pesados em folhas para reduzir invalidacão da árvore.
- Usar `startTransition` ou `useDeferredValue` quando a UX permitir distinguir trabalho urgente de não urgente.

## Anti-patterns

- Memoizar tudo para esconder ownership de estado ruim.
- Guardar em state um valor que só espelha props atuais.
- Recriar arrays, objetos e callbacks complexos apenas para compensar um componente grande demais.
- Fazer otimização fina em lista sem antes medir se o gargalo está no volume de itens.

## Evidência esperada

- Menos renders por interação no React DevTools Profiler.
- Menor commit duration ou menor tempo total por digitação.
- Menos CPU no browser durante scroll, filtro ou edição.
- Menos nós de lista atualizados por evento local.
