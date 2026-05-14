---
name: red-team-tactics
description: >
  Use para validação não destrutiva de exploitabilidade em findings HIGH/CRITICAL já
  suspeitos ou confirmados. Ative quando o usuário pedir cadeia de ataque, precondições,
  bypass, payload seguro, impacto e mitigação sem exfiltração, destruição ou abuso de
  credenciais.
---

# Red Team Tactics



## Fundamentos

- **Simulação, Não Destruição:** Sob NENHUMA hipótese execute scripts que deletam bancos de dados (ex: `DROP TABLE`), extraem chaves reais de API do servidor, ou enviam payloads maliciosos para ambientes que não sejam de mock/teste estrito. O objetivo é provar a *viabilidade teórica* ou executar *Proof of Concept (PoC)* isolada.
- **Attacker Chains:** Invasores raramente usam uma única vulnerabilidade. Eles encadeiam falhas. Avalie o impacto combinando, por exemplo, "Falta de Rate Limit" com "Enumeração de Usuários".
- **Boundaries (Fronteiras):** Identifique exatamente as bordas de confiança (onde o input do usuário se torna comando de banco, comando de SO, ou resposta HTTP).

## Procedimento
Sempre que a perspectiva de Red Team for invocada:
1. **Modele a Cadeia de Ataque:** Escreva um pequeno relatório (`exploit-chain-model`) descrevendo o ator (ex: Usuário sem login), a pré-condição, a ação e o impacto resultante.
2. **Identifique o Ponto de Fix:** Mapeie exatamente em qual camada (Middleware, RLS do Supabase, Validação Pydantic no Backend) o bypass está ocorrendo.
3. **Desenhe o Mitigation Guardrail:** Sugira a correção imediata e bloqueante. Use `run_command` para rodar os testes unitários afetados e confirmar que o comportamento malicioso agora é barrado.

## Exemplos

### Caso positivo
**Entrada:** Há finding HIGH/CRITICAL e usuário quer validar cadeia explorável sem destruição.
**Saída esperada:** Modelar precondições, payload seguro, impacto, bypass e mitigação sem exfiltrar ou abusar credenciais.

### Caso negativo
**Entrada:** Usuário pede scan genérico de segurança inicial.
**Por quê não:** Use `vulnerability-scanner`; red team entra após suspeita material.

## Evals de trigger

Deve acionar:
- "valida explorabilidade desse HIGH"
- "modela cadeia de ataque sem exfiltrar"

Não deve acionar:
- "scan inicial de segurança"
- "corrige copy da landing"
