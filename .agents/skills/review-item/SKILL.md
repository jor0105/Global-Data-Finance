---
name: review-item
description: Executa itens do review, expande contexto minimo, persiste findings e decide ou registra escalonamento de seguranca.
---

# Review Item

## Use When

Use quando o reviewer ja tem um item do plano para auditar e precisa expandir contexto, registrar finding estruturado ou abrir um handoff de seguranca material.

## Do Not Use When

Nao use para iniciar a sessao de review nem para consolidar o veredito final; nesses casos use `review-session` ou `review-closeout`.

## Required Inputs

- Item atual do `review-plan` ou arquivo/risco equivalente.
- `session_dir` e artifacts canonicos para persistir findings.
- Contexto minimo do diff e dos callers quando a mudanca altera contratos.

## Phase Machine

1. Expandir o contexto minimo do item com leitura vertical e callers relevantes.
2. Auditar logica, risco de regressao, complexidade e sinais de seguranca.
3. Persistir `file-findings` e `security-flags`, ou marcar o item como limpo.

## Fundamentos

- **O Limite do Nitpick:** Comentários como "use aspas simples em vez de duplas" são Nitpicks inúteis (o Prettier resolve). Foque o Review Item em: Lógica Quebrada, Complexidade Ciclomática Alta (Muitos `if/else` aninhados), Vazamento de Memória, Nomes Ambíguos, e Boundary Escapes.
- **Leitura Vertical Completa:** Não leia o diff isolado. Se a função mudou a assinatura, exija evidências empíricas (pesquisa no repositório inteiro com `grep_search`) de que todos os arquivos que chamam essa função (`callers`) também foram atualizados, senão o projeto não compilará.

## Procedimento
1. **Expansão de Contexto:** Use as ferramentas `view_file` para ler não apenas as linhas editadas, mas o arquivo completo ao redor para entender o side-effect.
2. **Análise de Lógica de Negócio:** Avalie inline se o código ficou legível, com nomes claros, concerns bem separados, sem abstração prematura, sem surpresa semântica e com contratos/callers preservados.
3. **Escalonamento Local:** Se você encontrar injeções diretas de strings em SQL (`"SELECT * FROM " + var`), bloqueie imediatamente e grave um `security-flag`.
4. **Acumulação de Findings:** Registre suas descobertas temporárias (ex: "Arquivo X: Requer tratamento do erro do Fetch") e prepare-se para o próximo arquivo, repetindo o loop até o término.

## Scripts

- `scripts/append-finding.py`: adiciona finding estruturado ao artifact de review.
- `scripts/create-security-handoff.py`: cria handoff de segurança a partir de finding material.
- `scripts/detect-security-touch.py`: detecta se um item toca superfície de segurança.
- `scripts/expand-review-item-context.py`: expande contexto mínimo para auditar item de review.
- `scripts/mark-review-item-done.py`: marca item de review como concluído.

## If Step Fails

- Se o contexto continuar insuficiente depois da expansao minima, devolva a incerteza explicitamente em vez de especular.
- Se aparecer risco material de seguranca, grave `security-flag` e prepare handoff para `security-engineer`.

## Exit Conditions

- O item foi marcado como limpo ou gerou finding verificavel.
- Todo finding persistido tem evidencia acionavel suficiente.
- O reviewer sabe se deve seguir para o proximo item, abrir seguranca ou devolver remediacao.

## Expected Handoff

Entregue `file-findings` e `security-flags` atualizados, com status do item e proximo passo claro para o reviewer.

## Exemplos

### Caso positivo
**Entrada:** Plano de review aponta um arquivo/risco específico para auditar.
**Saída esperada:** Expandir contexto, registrar finding verificável ou marcar item como limpo, escalando segurança quando preciso.

### Caso negativo
**Entrada:** Usuário pede resumo executivo do review inteiro.
**Por quê não:** Use `review-closeout`; item-level não é a saída final.

## Evals de trigger

Deve acionar:
- "audita este item do plano de review"
- "expande contexto deste arquivo modificado"

Não deve acionar:
- "resumo final do review"
- "cria sessão de review"
