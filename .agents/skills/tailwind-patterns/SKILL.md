---
name: tailwind-patterns
description: >
  Use para Tailwind CSS, especialmente v4: configuração CSS-first, @theme, tokens, dark
  mode, container queries e padrões responsivos. Ative quando o usuário pedir "configura
  Tailwind", "classe não aplica", "tokens Tailwind", "migra v3 para v4" ou revisar
  utilitários.
---

# Tailwind Patterns



## Tailwind v4 — Breaking Changes vs v3

| v3 | v4 |
|---|---|
| `tailwind.config.js` | Configuração via CSS (`@theme`) |
| `theme.extend` | `@theme { --color-*: ... }` |
| `purge/content` | Automático via CSS cascade |
| `darkMode: 'class'` | `@variant dark (.dark &)` |
| `@layer components` | `@layer components` (mantido) |
| Plugins JS | `@plugin` em CSS |

**Regra crítica:** No v4, não usar `tailwind.config.js` para tokens — tudo via `@theme` no CSS principal.

---

## Design Tokens com `@theme`

O `@theme` é o mecanismo. Os **valores** (cores, fontes, espaçamentos) são definidos pelo design system do projeto — não por esta skill.

```css
@import "tailwindcss";

@theme {
  /* Cores — valores definidos pelo design system do projeto */
  --color-brand: <valor-do-design-system>;
  --color-brand-hover: <valor-do-design-system>;

  /* Tipografia */
  --font-sans: <fonte-do-projeto>, system-ui, sans-serif;

  /* Formas e sombras */
  --radius-card: 0.75rem;
  --shadow-card: 0 4px 24px rgb(0 0 0 / 0.4);
}
```

Após definir, usar como classes: `bg-brand`, `text-brand`, `rounded-card`.

---

## Container Queries

```html
<!-- Wrapper com @container -->
<div class="@container">
  <!-- Responsivo pelo tamanho do container, não da viewport -->
  <div class="grid grid-cols-1 @md:grid-cols-2 @xl:grid-cols-3">
    ...
  </div>
</div>
```

**Quando usar container queries vs breakpoints:**
- Container query → componente que aparece em contextos diferentes (sidebar, modal, full-width)
- Breakpoint → layout de página inteira com base na viewport

---

## Dark Mode

```css
/* Definir variante dark baseada em classe no HTML */
@variant dark (&:where(.dark, .dark *));
```

```html
<!-- Uso em componentes -->
<div class="bg-white dark:bg-surface text-gray-900 dark:text-gray-100">
```

**Decisão:** Controlar dark mode via classe no `<html>` permite que o usuário decida, independente de `prefers-color-scheme`. Use `prefers-color-scheme` apenas se o modo deve seguir o sistema sem override do usuário.

---

## Anti-patterns

```css
/* ERRADO — @apply em excesso */
@layer components {
  .card {
    @apply bg-white rounded-lg shadow p-4 flex flex-col gap-2;
  }
}
```

```jsx
{/* CORRETO — classes inline em componentes JSX */}
<div className="bg-surface rounded-card shadow-card p-4 flex flex-col gap-2">
```

**Regra:** `@apply` é aceitável apenas para:
- Reset de elementos HTML (`a`, `button`, `input`) onde não há JSX
- Contextos sem componentes (e-mail templates, MDX estático)

Em componentes React/JSX, sempre classes inline.

---

## Checklist de Decisão

- [ ] Token repetido em >3 lugares? → extrair para `@theme`
- [ ] Componente aparece em múltiplos contextos de largura? → `@container`
- [ ] Dark mode necessário? → `@variant dark` com classe no HTML
- [ ] `@apply` em componente React? → converter para classes inline
- [ ] Classe customizada necessária? → `@layer utilities` em vez de CSS solto


## Procedimento

1. Identifique se o problema está em configuração, tokens, utilitários, responsividade, dark mode ou migração de versão.
2. Reuse o sistema de design existente antes de criar classes novas; em Tailwind, escala e consistência costumam valer mais do que criatividade local.
3. Mantenha a decisão no nível certo: config/Tokens para regra global, utilities/componentes para exceção local.
4. Valide em estados e breakpoints reais para garantir que a solução não depende de uma combinação frágil de classes.

## Exemplos

### Caso positivo
**Entrada:** Usuário pede configurar Tailwind v4, tokens, dark mode ou classes responsivas.
**Saída esperada:** Aplicar CSS-first config, tokens, container queries e evitar classes frágeis.

### Caso negativo
**Entrada:** Usuário pede design visual sem Tailwind específico.
**Por quê não:** Use `frontend-design`; framework CSS não é a decisão.

## Evals de trigger

Deve acionar:
- "configura Tailwind v4 @theme"
- "dark mode com tokens Tailwind"

Não deve acionar:
- "design sem código CSS"
- "query lenta"
