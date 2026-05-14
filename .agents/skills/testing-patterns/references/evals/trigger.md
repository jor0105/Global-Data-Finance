# trigger.md

## Deve acionar

### Caso 1

Pedido: "Essa feature precisa de unit, integration ou e2e?"
Esperado: acionar `testing-patterns` para escolher o menor tipo de teste confiavel.

### Caso 2

Pedido: "Quais mocks sao aceitaveis para cobrir este servico externo?"
Esperado: acionar `testing-patterns` por envolver isolamento e estrategia de suite.

### Caso 3

Pedido: "Preciso ampliar cobertura sem deixar a suite ruidosa."
Esperado: acionar `testing-patterns` para orientar cobertura proporcional ao risco.

## Nao deve acionar

### Caso 1

Pedido: "Rode o ai:verify e testes."
Esperado: nao acionar `testing-patterns`; usar `lint-and-validate`.

### Caso 2

Pedido: "Modele o schema do banco desta feature."
Esperado: nao acionar `testing-patterns`; usar `database-design` para schema, tipos, constraints, migrations e ownership.

### Caso 3

Pedido: "O fluxo ja esta coberto e so preciso reexecutar a suite."
Esperado: nao acionar `testing-patterns`; a tarefa e operacional.
