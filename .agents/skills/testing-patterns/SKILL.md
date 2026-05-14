---
name: testing-patterns
description: >
  Use para desenhar testes unitários, integração, mocks, fixtures, regressão e negativos
  de segurança. Ative quando o usuário perguntar "qual teste escrever?", "mocko isso
  como?", "cobre auth expirada", "teste errado tenant" ou revisar assertions.
---

# Testing Patterns



## Fundamentos

- **O Anti-Pattern do Mock Total:** O maior erro em testes é mockar a própria lógica sob teste ou o próprio banco de dados, resultando em testes que apenas atestam que "a ferramenta de mock funciona". Mocke APENAS boundaries de rede difíceis (ex: chamadas reais à OpenAI ou APIs externas).
- **Fixtures vs Factories:** Use Factories e Fixtures controladas. Testes que criam usuários hardcoded frequentemente quebram uns aos outros por violação de restrições de unicidade no banco.
- **Testes Negativos e Segurança:** É fácil testar que o administrador acessa. O teste que salva o repositório é o *Negative Test*: O Tenant A não pode listar os dados do Tenant B. Credenciais inválidas devem retornar `401/403`. Logs de erro não podem conter payloads com senhas de clientes.

## Procedimento
1. **Defina a Estratégia de Cobertura:** Antes de criar arquivos, use a técnica AAA (Arrange, Act, Assert).
2. **Setup Isolado:** Crie um ambiente estéril no bloco `beforeEach`. Nunca confie no estado deixado por um teste anterior.
3. **Escrita (Act & Assert):**
   - Não use assertions genéricas como `expect(res).toBeTruthy()`. Use `expect(res.status).toBe(200)` e verifique contratos de interface.
   - Escreva blocos `it("should fail when...")` abordando todas as exceções documentadas do contrato.
4. **Validar Localmente:** Rode os testes recém-criados localmente e garanta que falham quando a implementação é removida (garantia contra tautologia).

## Exemplos

### Caso positivo
**Entrada:** Usuário quer desenhar unit/integration/security negative tests para comportamento específico.
**Saída esperada:** Escolher nível de teste, fixtures, mocks e assertions que pegam regressão real.

### Caso negativo
**Entrada:** Usuário quer coordenar uma campanha E2E inteira.
**Por quê não:** Use `coordinator`; o escopo exige orquestracao multi-owner.

## Evals de trigger

Deve acionar:
- "qual teste cobre essa regressão?"
- "cria negative tests de auth"

Não deve acionar:
- "coordena suíte inteira"
- "audita UX visual"

## Scripts

- `scripts/test_runner.py`: resolve e executa comandos de teste proporcionais ao escopo.

## Referências

Leia apenas o arquivo relevante para o teste que precisa ser desenhado:

| Problema | Arquivo |
|---|---|
| Ver exemplos de testes e edge cases | `references/examples.md` |
| Confirmar heurísticas de mocks, fixtures e assertions | `references/reference.md` |
