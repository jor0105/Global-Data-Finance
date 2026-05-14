# Bundle And Browser JS

## Quando ler

- Use esta referência para bundle inicial pesado, hidratação cara, CPU alta no browser ou dependências grandes carregadas cedo demais.
- Ignore esta referência se o gargalo principal estiver em query remota, boundary específica de Next ou render local sem impacto de JS entregue.

## Sinais fortes

- Charts, editores, markdown, motion complexa ou visualizações 3D entram no chunk inicial sem serem críticos.
- O browser faz parsing e execução demais antes de a tela ficar útil.
- Componentes leves importam dependências grandes só para um estado raro ou aba secundária.

## Checklist de revisão

1. Liste as dependências mais pesadas da rota ou fluxo.
2. Pergunte se cada dependência precisa existir no primeiro carregamento ou pode entrar por rota, aba, modal ou interação.
3. Em React genérico, considere `React.lazy` ou code splitting do bundler. Em Next, use `next/dynamic` apenas para a folha pesada e interativa.
4. Reveja transforms caros, parsing e formatação feitos no browser que poderiam nascer prontos do servidor.
5. Se a UI depende de listas grandes, confira virtualização antes de atacar apenas o bundle.

## Recomendações que costumam funcionar

- Split por rota, modal, chart, editor ou painel colapsado.
- Import direto de módulos necessários, em vez de pontos de entrada genéricos demais.
- Mover parsing, agregação e formatação pesados para o servidor quando a stack permitir.
- Carregar bibliotecas visuais só quando a interação realmente acontecer.

## Anti-patterns

- Tratar lazy loading como solução para qualquer lentidão sem saber se o custo real está em rede, CPU ou render.
- Empurrar dependência pesada para o bootstrap só para evitar um estado de loading localizado.
- Usar `dynamic` ou `lazy` em componente crítico de first paint que o usuário sempre vê.

## Evidência esperada

- Chunks iniciais menores.
- Menos tempo de parse e execução no browser.
- Melhor LCP, TBT ou INP quando a causa for JS excessivo.
- Menor custo de hidratação ou inicialização.
