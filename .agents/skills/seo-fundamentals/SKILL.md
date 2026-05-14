---
name: seo-fundamentals
description: >
  Use para SEO clássico em Google e buscadores: on-page, headings, metadados, sitemap,
  robots, E-E-A-T, indexação e Core Web Vitals. Ative quando o usuário pedir "melhora
  SEO", "audita ranking", "meta title", "schema.org" ou "por que não indexa?".
---

# SEO Fundamentals



## On-Page SEO Essentials

```html
<!-- Title — único por página, 50-60 chars -->
<title>Análise de Dados | Meu Produto</title>

<!-- Meta description — único por página, 150-160 chars -->
<meta name="description" content="Analise ações e empresas com IA em tempo real. Dados CVM, histórico e chat inteligente num só lugar.">

<!-- Canonical — evita conteúdo duplicado -->
<link rel="canonical" href="https://exemplo.com/pagina">

<!-- Open Graph — para compartilhamento social -->
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:image" content="https://...">
```

---

## Estrutura Semântica

```html
<!-- Uma única h1 por página -->
<h1>Análise de Ações com Inteligência Artificial</h1>

<!-- Hierarquia correta: h1 → h2 → h3 -->
<h2>Como funciona</h2>
  <h3>Análise de dados de mercado</h3>
  <h3>Chat com contexto financeiro</h3>

<!-- Nunca pular níveis (h1 → h3) -->
<!-- Nunca usar headings para estilo — usar CSS -->
```

**Regra de ouro:** Uma pessoa consegue entender a estrutura da página só pelos headings? Se não, o outline está errado.

---

## E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)

Fatores que o Google avalia para ranqueamento de conteúdo:

| Sinal | Como implementar |
|---|---|
| **Experience** | Exemplos reais, dados próprios, casos de uso concretos |
| **Expertise** | Autor identificado, credenciais visíveis, profundidade técnica |
| **Authoritativeness** | Links de sites autoritativos, citações, referências a fontes |
| **Trustworthiness** | HTTPS obrigatório, política de privacidade, dados de contato |

---

## Core Web Vitals como Sinal de SEO

> Para análise de performance pura (backend, profiling, Lighthouse detalhado) use `performance-profiling`.

CWV são métricas de UX que o Google usa como fator de ranqueamento:

| Métrica | O que mede | Meta |
|---|---|---|
| **LCP** (Largest Contentful Paint) | Quanto o maior elemento leva para renderizar | < 2.5s |
| **INP** (Interaction to Next Paint) | Responsividade a interações do usuário | < 200ms |
| **CLS** (Cumulative Layout Shift) | Estabilidade visual durante carregamento | < 0.1 |

**Causas comuns de falha:**
- LCP alto: imagens sem `loading="lazy"`, fontes sem `font-display: swap`, servidor lento
- CLS alto: imagens sem dimensões declaradas, ads/embeds que empurram conteúdo

---

## Indexação e Rastreamento

```
# robots.txt — controla o que o crawler acessa
User-agent: *
Disallow: /admin/
Disallow: /api/
Allow: /

# Sitemap — lista todas as URLs indexáveis
Sitemap: https://exemplo.com/sitemap.xml
```

**Regras:**
- Nunca bloquear CSS ou JS no robots.txt — o Google precisa renderizar a página
- Conteúdo atrás de login não é indexado — é esperado para SaaS

---

## Checklist de Decisão

- [ ] Cada página tem title e meta description únicos?
- [ ] Existe uma única `<h1>` por página?
- [ ] O canonical está declarado?
- [ ] HTTPS está ativo?
- [ ] LCP < 2.5s, CLS < 0.1, INP < 200ms?
- [ ] O robots.txt não bloqueia CSS/JS?
- [ ] Sitemap XML existe e está atualizado?


## Procedimento

1. Identifique a intenção de busca e a falha dominante: indexação, metadado, arquitetura de headings, conteúdo, linking interno ou Core Web Vitals.
2. Audite primeiro a capacidade de crawl e renderização; sem isso, ajustes de copy ou schema têm pouco efeito.
3. Priorize correções mensuráveis e reversíveis: title, description, canonical, heading hierarchy, sitemap, robots, schema e CWV.
4. Feche com uma verificação do HTML gerado ou do fluxo de build para garantir que os sinais de SEO realmente chegam ao documento final.

## Scripts

- `scripts/seo_checker.py`: audita sinais básicos de SEO em páginas e metadados.

## Exemplos

### Caso positivo
**Entrada:** Usuário quer melhorar indexação Google, metadados, headings e Core Web Vitals.
**Saída esperada:** Auditar on-page SEO, E-E-A-T, crawl/index e recomendações mensuráveis.

### Caso negativo
**Entrada:** Usuário quer otimizar para respostas de LLMs.
**Por quê não:** Use `geo-fundamentals`; o motor alvo é outro.

## Evals de trigger

Deve acionar:
- "melhora SEO on-page"
- "audita Core Web Vitals para ranking"

Não deve acionar:
- "otimiza para Perplexity"
- "cria servidor MCP"
