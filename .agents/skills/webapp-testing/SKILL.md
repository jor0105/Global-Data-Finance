---
name: webapp-testing
description: >
  Use para testes browser-facing de web app: Playwright, smoke checks, jornadas críticas,
  auth/session, acessibilidade, regressão visual e evidência por screenshot. Ative quando
  o usuário pedir "testa no navegador", "E2E", "Playwright", "fluxo de login" ou validar
  UI real.
---

# Webapp Testing



## Fundamentos

- **Testes Resilientes:** Nunca selecione elementos usando classes CSS frágeis (`.text-blue-500`). Use atributos de teste unívocos como `data-testid` ou seletores acessíveis (`getByRole('button', { name: 'Submit' })`).
- **Estado de Sessão:** Evite fazer login pelo UI em todos os testes E2E. Use a funcionalidade de injeção de Cookie/Token do Playwright (Session State) para acelerar a suíte.
- **Flakiness (Intermitência):** Se um teste de interface falha aleatoriamente, geralmente é por falta de espera de animações, carregamentos de rede pendentes (network idle) ou timeouts. Não adicione `sleep` manual; use `waitFor`.

## Procedimento

1. Use `python3 scripts/playwright_runner.py` como ponto de entrada para smoke checks e jornadas E2E do navegador.
2. Se houver falha, analise trace, screenshot, console e network antes de editar seletores; a causa costuma estar no fluxo ou no estado da página.
3. Ao criar um novo teste, cubra a jornada crítica ligada à mudança e reutilize fixtures de auth/session sempre que possível.
4. Feche com resultado por jornada: o que passou, o que falhou, qual evidência foi coletada e em que tela o fluxo quebrou.

## Exemplos

### Caso positivo
**Entrada:** Usuário quer smoke/E2E Playwright para fluxo browser, auth ou regressão UI.
**Saída esperada:** Definir jornada crítica, browser real/simulado, asserts de estado, acessibilidade e evidência visual quando útil.

### Caso negativo
**Entrada:** Usuário quer teste unitário de função pura.
**Por quê não:** Use `testing-patterns`; browser não adiciona valor.

## Evals de trigger

Deve acionar:
- "cria Playwright para login"
- "smoke test browser do dashboard"

Não deve acionar:
- "unit test função pura"
- "schema de banco"
