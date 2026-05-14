# Coordinator Routing Demo

Este arquivo resume como o coordinator decide entre delegacao direta e orquestracao sem skills dedicadas.

## Cenario 1 - Delegacao direta

- objective: Pedido com dono natural unico vai direto para um subagent.
- decision_mode: direct
- selected_subagent: reviewer
- coordination_mode: n/a
- reason: A tarefa tem dono natural unico e isolado; o coordinator valida o contrato minimo e delega direto.

## Cenario 2 - Serial com handoff

- objective: Tarefa pequena com dois owners segue fluxo serial com contrato explicito.
- decision_mode: serial
- selected_subagent: n/a
- coordination_mode: serial
- reason: A tarefa exige mais de um owner, mas continua pequena e com baixo acoplamento.

## Cenario 3 - Refactor com planejamento

- objective: Refatoracao maior exige planejamento antes da implementacao.
- decision_mode: serial
- selected_subagent: planner -> developer-engineer
- coordination_mode: serial
- reason: Escopo amplo e necessidade de contratos indicam fluxo de planejamento e handoff.

## Cenario 4 - Testes dominantes

- objective: Fluxo com foco principal em testes delega para o tester como owner principal.
- decision_mode: direct
- selected_subagent: tester
- coordination_mode: n/a
- reason: A necessidade principal e estrategia/cobertura de testes.

## Cenario 5 - Contrato incompleto bloqueia handoff

- objective: Coordinator nao delega ao reviewer quando o contrato minimo esta incompleto.
- decision_mode: blocked
- selected_subagent: reviewer
- coordination_mode: n/a
- reason: missing_input
- contract_status: blocked
- missing_required: changed_files
