---
name: review-session
description: Inicializa, retoma e prepara a sessao canonica de review, incluindo o plano ordenado por risco quando necessario.
---

# Review Session

## Use When

Use quando o reviewer precisa abrir a sessao canonica, retomar uma sessao stale ou reconstruir o plano de leitura por risco antes de julgar findings.

## Do Not Use When

Nao use para corrigir codigo, fechar veredito final ou auditar um item isolado do plano; nesses casos use o owner correto ou a skill seguinte do fluxo.

## Required Inputs

- `changed_files` ou diff equivalente para montar a ordem de leitura.
- `change_type`, `changed_by` e `security_touch` para calibrar risco.
- `session_dir` quando a sessao ja existe ou precisa ser retomada.

## Phase Machine

1. Mapear arquivos alterados e ordenar por risco arquitetural: infra, dados, contratos, logica, UI, testes.
2. Inicializar ou retomar os artifacts canonicos da sessao usando os scripts da pasta `scripts/`.
3. Produzir um `review-plan` proporcional e preparar o proximo item para `review-item`.

## Fundamentos

- **Leitura Direcionada a Riscos (Risk-Ordered Reading):** Nunca revise os arquivos na ordem alfabética. Revisar CSS antes de revisar a Modelagem do Banco é perda de tempo (se o banco estiver errado, o CSS será jogado fora). A ordem absoluta de revisão arquitetural é: 1. Infra/Configurações, 2. Banco de Dados/Models, 3. Contratos de API/Interfaces, 4. Lógica de Negócio (Services), 5. UI/Components, 6. Testes.
- **Isolamento de Escopo Mínimo:** Se a mudança tocar fora do escopo aprovado no OpenSpec inicial, classifique como "Leak de Escopo" na sessão.

## Procedimento
1. **Defina o Plano de Leitura:**
   - Extraia a lista de arquivos alterados (usando o diff ou a mensagem recebida).
   - Ordene-os conforme a heurística de Riscos (Infra -> Models -> Interfaces -> Logic -> UI -> Tests).
2. **Setup do Review:**
   - Crie o `review-plan` (mentalmente ou em um arquivo no `/scratch`).
   - Se o diff for minúsculo (1-2 arquivos), pule a ordenação e siga direto para a revisão lógica.
3. **Passe o Bastão:** Invoque iterativamente a habilidade `review-item` para avaliar o primeiro conjunto crítico de arquivos.

## Scripts

- `scripts/build-review-plan.py`: gera plano de review ordenado por risco.
- `scripts/init-review-session.py`: inicializa sessão canônica de review.

## If Step Fails

- Se faltar diff, `session_dir` ou contexto minimo, devolva blocker explicito para o reviewer em vez de inventar sessao.
- Se os artifacts estiverem stale ou corrompidos, reinitialize a sessao e registre essa decisao no handoff.

## Exit Conditions

- A sessao canonica existe e esta coerente com o diff atual.
- O `review-plan` foi produzido ou atualizado com ordem de leitura verificavel.
- O proximo item para `review-item` ficou claro.

## Expected Handoff

Entregue `review-plan`, `risk-ordered-files` e o estado da sessao com contexto suficiente para o reviewer seguir para `review-item` sem reabrir planejamento do zero.

## Exemplos

### Caso positivo
**Entrada:** Usuário pede review e ainda não existe sessão/ordem de leitura.
**Saída esperada:** Inicializar sessão, mapear risco, montar plano ordenado e preparar artifacts canônicos.

### Caso negativo
**Entrada:** Usuário pede corrigir diretamente um bug conhecido.
**Por quê não:** Não é review; encaminhe para implementação ou debugging.

## Evals de trigger

Deve acionar:
- "faz review deste PR"
- "monta plano de leitura por risco"

Não deve acionar:
- "fecha findings existentes"
- "corrige esse bug"
