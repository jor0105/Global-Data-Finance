# Optimization

> Otimize com evidencia. "Acho que falta indice" e palpite; `EXPLAIN ANALYZE`,
> row counts, shape da query e workload real sao evidencia.

## Loop minimo de diagnostico

1. capture a query real, nao a lembranca dela
2. entenda o objetivo de negocio da leitura/escrita
3. rode `EXPLAIN ANALYZE` ou equivalente
4. compare estimado vs real
5. inspecione filtros, joins, ordenacao, projecao e cardinalidade
6. mude uma variavel por vez

## O que procurar no plano

- `Seq Scan` em tabela grande pode indicar indice faltando, mas as vezes e correto
  se a seletividade for baixa ou a tabela for pequena.
- estimativas muito erradas apontam para estatisticas ruins ou predicado estranho.
- muitos `Rows Removed by Filter` sugerem indice ou predicado mal alinhado.
- sort caro pode pedir indice composto, nao so memoria.
- lookup repetido aponta para N+1 ou round-trip desnecessario.

## Ordem pratica de intervencao

1. confirmar query shape e predicados
2. selecionar menos colunas e menos linhas
3. corrigir N+1 / batch / join strategy
4. alinhar tipos e predicados para serem indexaveis
5. criar ou ajustar indice certo
6. so depois considerar cache

## Criterios minimos antes de sugerir indice novo

- a query e frequente ou suficientemente cara
- o predicado e estavel
- ha seletividade ou ordenacao que o indice pode explorar
- o custo extra de escrita faz sentido
- a melhora nao deveria vir primeiro de schema, tipo de dado ou query mais enxuta

## Anti-patterns

- usar cache para esconder query estruturalmente ruim
- recomendar indice sem a query
- achar que subquery e sempre pior que join, ou vice-versa
- ignorar que tipo textual ruim pode impedir comparacao/indexacao eficaz
