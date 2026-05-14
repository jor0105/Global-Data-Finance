# Migrations

> Migration segura e uma sequencia de rollout, nao so um arquivo SQL. A pergunta
> correta nao e "funciona local?", e "como entra em producao sem quebrar caller,
> lockar tabela critica ou perder rollback?".

## Sequencias seguras mais comuns

### Adicionar coluna obrigatoria

1. adicionar como nullable ou com default controlado
2. backfill em lotes se necessario
3. atualizar aplicacao para preencher a coluna
4. validar consistencia
5. so entao aplicar `NOT NULL`

### Renomear coluna

1. adicionar coluna nova
2. copiar/backfill
3. app le e escreve no lugar certo
4. remover leitura antiga
5. apagar coluna antiga em deploy posterior

### Remover coluna ou tabela

1. parar de usar no codigo
2. observar uso residual
3. remover em janela posterior

## Operacoes que exigem alerta explicito

- `DROP COLUMN`
- `DROP TABLE`
- `ALTER COLUMN ... SET NOT NULL`
- rename em passo unico
- `ALTER TYPE` com impacto amplo
- criacao de indice bloqueante em tabela quente
- backfill unico e gigante sem loteamento/observabilidade

## Roll-forward, nao so rollback

Em bancos reais, rollback nem sempre e barato ou seguro. Prefira respostas que
deixem claro:

- qual deploy prepara o schema
- qual deploy troca o caller
- qual deploy remove legado

Se a mudanca nao puder ser revertida facilmente, diga isso em voz alta.

## Heuristicas operacionais

- `CREATE INDEX CONCURRENTLY` ou estrategia equivalente quando o banco e quente
  e o engine suporta isso.
- `NOT NULL` em dado legado sem evidencia de backfill e risco, nao detalhe.
- backfill pesado precisa pensar em lote, lock e observabilidade.
- "greenfield" e excecao; quando o usuario nao disser, assuma compatibilidade com
  producao como preocupacao real.

## Anti-patterns

- tratar migration destrutiva como deploy unico por conveniencia
- confiar em rename atomico sem avaliar caller antigo
- enfiar backfill gigante no mesmo passo do schema sem medir impacto
- supor que serverless elimina lock ou risco de migration
