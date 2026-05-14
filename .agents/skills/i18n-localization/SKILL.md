---
name: i18n-localization
description: >
  Use para internacionalizacao e localizacao de produto: remover strings
  hardcoded, estruturar locale files, pluralizacao, datas, numeros, moedas,
  fallback e RTL. Ative quando o usuario pedir "prepara para pt/en", "adiciona
  i18n", "remove textos hardcoded", "formata moeda por pais", "revisa readiness
  de traducao" ou quando a interface precisa suportar multiplos idiomas sem
  quebrar UX, acessibilidade ou consistencia.
---

# I18n Localization

## Procedimento

1. Antes de propor qualquer solucao, decida qual destes casos descreve melhor o pedido:
   - estruturar a base de i18n para multiplos idiomas e locales
   - migrar codigo e interface existentes para remover strings hardcoded
   - revisar readiness, consistencia e riscos de traducao
2. Abra a resposta explicando em prosa simples qual desses casos domina, por que ele manda na decisao e o que ficou fora.
3. Levante o contexto minimo: idiomas alvo, superficies afetadas, estrategia atual de i18n, estrutura de locale files, requisitos de data, moeda e numero e necessidade de RTL.
4. Defina a menor estrategia viavel antes de mover strings; evite churn em massa sem fechar namespace, fallback e regras de formatacao.
5. Se o pedido for estruturar a base de i18n, entregue primeiro inventario, estrutura de chaves, fallback, pluralizacao e ordem de rollout.
6. Se o pedido for migrar codigo existente, priorize o que mais vaza manutencao ou quebra UX: textos visiveis, atributos acessiveis, mensagens de erro, fluxos criticos e valores locale-sensitive.
7. Se o pedido for revisao de readiness, entregue findings primeiro, ordenados por impacto, cobrindo pluralizacao, expansao de texto, fallback, consistencia entre locale files e direcao da interface quando houver idioma RTL.
8. Valide a solucao contra pluralizacao, expansao de texto, fallback e direcao da interface quando houver idioma RTL.
9. Se o pedido for apenas traduzir uma frase isolada ou revisar layout sem decisao real de i18n, saia da skill e redirecione para o caminho correto.

## Heuristicas

- Externalize texto visivel ao usuario: labels, titulos, mensagens, placeholders, tooltips e notificacoes.
- Externalize tambem atributos acessiveis voltados ao usuario, como `aria-label`, `alt` e `title`.
- Nao externalize logs de sistema, enums internos e chaves de configuracao que nao fazem parte da experiencia do usuario.
- Use `Intl` para data, hora, numero e moeda; nao formate isso manualmente.
- Evite concatenacao manual para pluralizacao. Use o sistema plural da biblioteca de i18n adotada.
- Estruture chaves e namespaces de forma estavel para reduzir churn e colisoes semanticas.
- Considere que traducoes podem crescer 30-40% e quebrar layout, truncamento e hierarquia.
- Quando houver idioma RTL, prefira `dir` e propriedades logicas em vez de depender de `left` e `right`.

## Anti-patterns

- Tratar i18n como "trocar string por `t()`" sem pensar em namespace, fallback e manutencao.
- Traduzir so texto visivel e esquecer `aria-label`, `alt` ou mensagens de erro.
- Concatenar plurais e frases manualmente.
- Formatar datas, moedas e numeros no braco.
- Copiar locale files sem estrategia de consistencia de chaves.
- Assumir que a UI suporta traducao longa ou RTL sem revisar layout.

## Contrato de saida

### Quando o pedido for estruturar a base de i18n

Entregue um brief curto e implementavel contendo:

- qual parte do produto ainda nao tem base estavel de internacionalizacao
- inventario do que precisa ser internacionalizado
- estrutura sugerida de namespaces e locale files
- estrategia minima de fallback
- regras de pluralizacao e uso de `Intl`
- ordem de rollout por superficies ou criticidade

### Quando o pedido for migrar strings e interface existentes

Entregue um plano de migracao contendo:

- por que o caso e de migracao e nao de arquitetura do zero
- tipos de strings e atributos a mover primeiro
- padroes proibidos que precisam sair do codigo
- sequencia de refactor para reduzir churn
- validacoes de consistencia entre locale files e interface

### Quando o pedido for revisar readiness e consistencia

Entregue findings primeiro, ordenados por impacto. Depois traga:

- por que o caso e de revisao e nao de migracao estrutural
- correcoes recomendadas
- riscos de expansao de texto, fallback e RTL
- lacunas de consistencia entre idiomas, chaves e formatacao

## Exemplos

### Caso positivo

**Entrada:** Usuario quer preparar o app para portugues e ingles, incluindo datas e moedas por locale.
**Saida esperada:** Explicar que o pedido exige estruturar a base de i18n e devolver inventario, estrutura de locale files, fallback, regras de pluralizacao e sequencia de rollout.

### Caso positivo

**Entrada:** Usuario quer remover textos hardcoded de uma UI existente e corrigir atributos acessiveis nao traduzidos.
**Saida esperada:** Explicar que o pedido e de migracao de strings existentes e devolver sequencia de migracao, prioridades e padroes que devem sair do codigo.

### Caso positivo

**Entrada:** Usuario quer revisar se a interface aguenta traducao longa, pluralizacao e idioma RTL sem quebrar.
**Saida esperada:** Explicar que o pedido e uma revisao de readiness, listar findings primeiro e apontar riscos concretos de layout, fallback e consistencia.

### Caso negativo

**Entrada:** Usuario pede so para traduzir uma frase isolada.
**Por que nao:** Nao ha arquitetura, migracao nem revisao real de i18n. E traducao pontual, nao internacionalizacao de produto.

## Evals de trigger

Deve acionar:
- "prepara o app para pt-BR e en-US"
- "remove hardcoded strings e cria locales"
- "formata datas e moedas por pais"
- "revisa readiness de traducao e RTL"

Nao deve acionar:
- "traduz essa frase"
- "muda cor do botao"
- "ajusta esse layout para mobile"
- "corrige esse import"

## Evals de workflow

### Caso 1 - estruturar a base de i18n

**Entrada:** produto vai suportar pt-BR e en-US e ainda nao tem estrutura estavel de locales.

Assertions:
- [ ] output deixa claro que o pedido exige base estrutural antes de mover strings em massa
- [ ] output explica por que nao e apenas migracao localizada ou revisao de readiness
- [ ] output inclui inventario das superficies a internacionalizar
- [ ] output inclui estrutura de namespaces ou locale files
- [ ] output inclui fallback minimo
- [ ] output inclui regras para pluralizacao e `Intl`
- [ ] output inclui ordem de rollout ou priorizacao

### Caso 2 - migrar strings e interface existentes

**Entrada:** fluxo existente contem textos hardcoded, `aria-label` fixo e concatenacao manual de plural.

Assertions:
- [ ] output prioriza textos visiveis, atributos acessiveis e mensagens criticas
- [ ] output explica por que o caso e de migracao e nao de arquitetura do zero
- [ ] output proibe concatenacao manual e formatacao manual de locale-sensitive values
- [ ] output inclui sequencia de migracao para reduzir churn
- [ ] output inclui checagem de consistencia entre chaves e locale files

### Caso 3 - revisar readiness e consistencia

**Entrada:** UI parece pronta, mas ha risco de quebra com traducoes longas, fallback inconsistente e idioma RTL.

Assertions:
- [ ] findings aparecem antes das recomendacoes
- [ ] output explica por que o caso e de revisao e nao de migracao estrutural
- [ ] output inclui riscos de expansao de texto, fallback ou RTL
- [ ] output inclui lacunas de consistencia entre idiomas ou chaves
- [ ] output aponta impactos concretos em UX e acessibilidade
