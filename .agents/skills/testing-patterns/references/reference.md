# reference.md

## Heuristicas

- Escolha o menor teste que prova o comportamento mudado.
- Use mocks para isolamento de dependencias externas, nao para esconder logica ruim.
- Cobertura boa reduz regressao sem criar ruido ou flakiness.
- Para seguranca, comece pelo teste negativo que reproduz o vetor original.
- Prefira provar o controle no limite correto: middleware para auth, repository/RLS para tenant, serializer para erro/log.
- Um teste de fix deve falhar antes da remediacao e passar depois; se isso nao for possivel, declare o gate manual.

## Testes negativos de seguranca

| Vetor             | Caso minimo                                                                          |
| ----------------- | ------------------------------------------------------------------------------------ |
| Usuario errado    | User B tenta acessar recurso, sessao, conversa ou trace de user A.                   |
| Tenant errado     | Workspace B tenta ler ou mutar dado de workspace A.                                  |
| Sessao expirada   | Token expirado ou logout invalida bootstrap, stream e chamada subsequente.           |
| Token ausente     | Rota protegida rejeita antes de buscar dados ou chamar provider/backend.             |
| API key invalida  | `X-API-Key` invalida/revogada/wrong-scope retorna erro sanitizado.                   |
| Log sem segredo   | Erro com token, API key ou provider payload nao aparece em log/audit/error response. |
| Fix sem regressao | O bypass original e uma variante adjacente continuam bloqueados.                     |

## Criterios de validacao

- Nomeie o comportamento protegido no teste, nao apenas a funcao.
- Use fixtures pequenas com dois usuarios/tenants quando o risco for isolamento.
- Verifique ausencia de payload sensivel em resposta, log ou audit artifact quando o vetor envolver segredo.
- Evite snapshots amplos para seguranca; asserts explicitos sao mais resistentes.

## Limites

- Nao e skill de execucao de gates.
- Nao deve ser carregada quando o comportamento ja esta coberto adequadamente.
