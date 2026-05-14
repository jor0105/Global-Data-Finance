# Loading, Waterfalls And Cache

## Quando ler

- Use esta referência para waterfall de requests, loading que começa tarde, refetch duplicado ou suspense/cache mal distribuídos.
- Ignore esta referência se o problema principal for re-render local sem impacto de rede ou uma boundary específica de App Router.

## Sinais fortes

- Requests independentes esperam umas pelas outras.
- Dados só começam a ser buscados depois do primeiro paint sem necessidade.
- A mesma tela refaz fetch ao montar múltiplos componentes equivalentes.
- O usuário vê vários loadings curtos em vez de um fluxo coordenado.

## Checklist de revisão

1. Procure `await` sequencial entre operações independentes. Se não houver dependência real, inicie tudo cedo e aguarde junto.
2. Valide se o trabalho pode começar antes: loader, server render, cache compartilhado, suspense-friendly fetcher ou bootstrap do framework.
3. Descubra se a tela duplica fetch por ownership errado ou falta de cache compartilhado.
4. Revise boundaries de loading: o conteúdo útil principal deve aparecer cedo, e os slow paths devem ficar isolados.
5. Em paginação e buscas, cheque se o trabalho novo invalida demais o trabalho já pronto.

## Recomendações que costumam funcionar

- `Promise.all` para requests independentes.
- Início de fetch no topo da rota, loader ou boundary que já conhece a necessidade de dados.
- Cache explícito com uma única fonte de verdade quando múltiplos componentes consomem o mesmo recurso.
- Suspense ou placeholders isolados quando a stack já oferece suporte maduro.
- `startTransition` para atualizações não urgentes que disparam busca ou recomputação.

## Anti-patterns

- Buscar no `useEffect` por reflexo quando o framework já permite iniciar o trabalho antes.
- Encadear requests apenas porque o código foi escrito em ordem top-down.
- Usar cache sem política clara de invalidação ou deduplicação.
- Colocar um spinner global onde uma boundary local resolveria com menos bloqueio perceptível.

## Evidência esperada

- Cascata de rede menor ou inexistente no painel de network.
- Menor tempo até conteúdo útil.
- Menos refetch redundante ao navegar, filtrar ou abrir painéis relacionados.
- Loading mais previsível, com menos troca de estados intermediários.
