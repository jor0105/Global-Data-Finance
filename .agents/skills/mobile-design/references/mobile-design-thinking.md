# Mobile Design Thinking

> Use este arquivo quando o risco não está em uma regra isolada, mas em escolher um padrão por hábito.
> Ele transforma defaults de training data em um protocolo curto de análise para direction e review mobile.

---

## Quick Start

- Abra este arquivo quando a solução parecer “óbvia demais” e você precisar validar se o padrão serve ao contexto real.
- Extraia daqui 3 coisas: contexto que muda a solução, diferenças relevantes entre iOS e Android e custo de interação/performance.
- Se a dúvida já for de shell de navegação, testing ou performance detalhada, pule para `mobile-navigation.md`, `mobile-testing.md` ou `mobile-performance.md`.

## Jump Map

| Se você precisa... | Vá para | Decida |
| --- | --- | --- |
| evitar cair em padrão memorizado | `## 1. Working Protocol` | quais hipóteses precisam ser questionadas |
| decompor uma tela ou fluxo | `## 2. Screen Decomposition Worksheet` | CTA, toque, estado, offline e platform fit |
| revisar uma escolha comum | `## 4. Pattern Questioning Matrix` | que alternativas comparar antes de escolher |
| avaliar gesto, lista ou performance | `## 7. Interaction Breakdown` | custo real da interação e do rendering |

## 1. Working Protocol

Antes de propor solução, responda em linguagem simples:

- qual é a tarefa principal desta tela
- qual suposição você está herdando por hábito
- o que muda entre iOS e Android neste fluxo
- que risco de toque, estado offline ou performance pode invalidar a solução

### Working Sequence

```
1. Context scan
   └── What assumptions are you inheriting from similar apps?
2. Pattern check
   └── Are you choosing this because it is common or because it fits the task?
3. Platform decomposition
   └── What should feel native on iOS and Android?
4. Interaction breakdown
   └── Where can touch, keyboard, back or offline state break the flow?
5. Performance impact
   └── Is the default solution still safe on low-end devices?
```

---

## 2. Pattern Defaults to Question

### Common anti-patterns and what to compare first

These patterns are common because they appear often in examples, not because they are automatically correct.
Before choosing one, compare it against task fit, touch cost, platform conventions and performance.

```
NAVIGATION:
├── Tab bar for every project
├── Fixed 5 tabs
├── "Home" tab on the left
└── Drawer just because there are many destinations

STATE:
├── Redux everywhere
├── Global state for everything
├── Context provider chains
└── BLoC for every Flutter project

LISTS AND FEEDS:
├── FlatList as default
├── Large render window without evidence
├── removeClippedSubviews without verification
└── ListView.builder without checking separation or caching strategy

UI PATTERNS:
├── FAB bottom-right by habit
├── Pull-to-refresh on every list
├── Swipe-to-delete without visible alternative
└── Bottom sheet for every modal
```

---

## 3. Screen Decomposition Worksheet

### Decomposition Analysis for Every Screen

Before designing any screen, perform this analysis:

```
SCREEN: [Screen Name]
├── PRIMARY ACTION: [What is the main action?]
│   └── Is it in thumb zone? [Yes/No → Why?]
│
├── TOUCH TARGETS: [All tappable elements]
│   ├── [Element 1]: [Size]pt → Sufficient?
│   ├── [Element 2]: [Size]pt → Sufficient?
│   └── Spacing: [Gap]pt → Accidental tap risk?
│
├── SCROLLABLE CONTENT:
│   ├── Is it a list? → FlatList/FlashList [Why this choice?]
│   ├── Item count: ~[N] → Performance consideration?
│   └── Fixed height? → Is getItemLayout needed?
│
├── STATE REQUIREMENTS:
│   ├── Is local state sufficient?
│   ├── Do I need to lift state?
│   └── Is global required? [Why?]
│
├── PLATFORM DIFFERENCES:
│   ├── iOS: [Anything different needed?]
│   └── Android: [Anything different needed?]
│
├── OFFLINE CONSIDERATION:
│   ├── Should this screen work offline?
│   └── Cache strategy: [Yes/No/Which one?]
│
└── PERFORMANCE IMPACT:
    ├── Any heavy components?
    ├── Is memoization needed?
    └── Animation performance?
```

---

## 4. Pattern Questioning Matrix

Ask these questions for every default pattern:

### Navigation Pattern Questioning

| Assumption         | Question                   | Alternative                          |
| ------------------ | -------------------------- | ------------------------------------ |
| "I'll use tab bar" | How many destinations?     | 3 → minimal tabs, 6+ → drawer        |
| "5 tabs"           | Are all equally important? | "More" tab? Drawer hybrid?           |
| "Bottom nav"       | iPad/tablet support?       | Navigation rail alternative          |
| "Stack navigation" | Did I consider deep links? | URL structure = navigation structure |

### State Pattern Questioning

| Assumption         | Question                     | Alternative                       |
| ------------------ | ---------------------------- | --------------------------------- |
| "I'll use Redux"   | How complex is the app?      | Simple: Zustand, Server: TanStack |
| "Global state"     | Is this state really global? | Local lift, Context selector      |
| "Context Provider" | Will re-render be an issue?  | Zustand, Jotai (atom-based)       |
| "BLoC pattern"     | Is the boilerplate worth it? | Riverpod (less code)              |

### List Pattern Questioning

| Assumption            | Question                 | Alternative              |
| --------------------- | ------------------------ | ------------------------ |
| "FlatList"            | Is performance critical? | FlashList (faster)       |
| "Standard renderItem" | Is it memoized?          | useCallback + React.memo |
| "Index key"           | Does data order change?  | Use item.id              |
| "ListView"            | Are there separators?    | ListView.separated       |

### UI Pattern Questioning

| Assumption           | Question                     | Alternative                       |
| -------------------- | ---------------------------- | --------------------------------- |
| "FAB bottom-right"   | User handedness?             | Accessibility settings            |
| "Pull-to-refresh"    | Does this list need refresh? | Only when necessary               |
| "Modal bottom sheet" | How much content?            | Full screen modal might be better |
| "Swipe actions"      | Discoverability?             | Visible button alternative        |

---

## 5. Anti-Memorization Test

### Ask Yourself Before Every Solution

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANTI-MEMORIZATION CHECKLIST                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  □ Did I pick this solution "because I always do it this way"?  │
│    → If YES: STOP. Consider alternatives.                       │
│                                                                 │
│  □ Is this a pattern I've seen frequently in training data?     │
│    → If YES: Is it REALLY suitable for THIS project?            │
│                                                                 │
│  □ Did I write this solution automatically without thinking?    │
│    → If YES: Step back, do decomposition.                       │
│                                                                 │
│  □ Did I consider an alternative approach?                      │
│    → If NO: Think of at least 2 alternatives, then decide.      │
│                                                                 │
│  □ Did I think platform-specifically?                           │
│    → If NO: Analyze iOS and Android separately.                 │
│                                                                 │
│  □ Did I consider performance impact of this solution?          │
│    → If NO: What is the memory, CPU, battery impact?            │
│                                                                 │
│  □ Is this solution suitable for THIS project's CONTEXT?        │
│    → If NO: Customize based on context.                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Context-Based Decision Protocol

### Think Differently Based on Project Type

```
DETERMINE PROJECT TYPE:
        │
        ├── E-Commerce App
        │   ├── Navigation: Tab (Home, Search, Cart, Account)
        │   ├── Lists: Product grids (memoized, image optimized)
        │   ├── Performance: Image caching CRITICAL
        │   ├── Offline: Cart persistence, product cache
        │   └── Special: Checkout flow, payment security
        │
        ├── Social/Content App
        │   ├── Navigation: Tab (Feed, Search, Create, Notify, Profile)
        │   ├── Lists: Infinite scroll, complex items
        │   ├── Performance: Feed rendering CRITICAL
        │   ├── Offline: Feed cache, draft posts
        │   └── Special: Real-time updates, media handling
        │
        ├── Productivity/SaaS App
        │   ├── Navigation: Drawer or adaptive (mobile tab, tablet rail)
        │   ├── Lists: Data tables, forms
        │   ├── Performance: Data sync
        │   ├── Offline: Full offline editing
        │   └── Special: Conflict resolution, background sync
        │
        ├── Utility App
        │   ├── Navigation: Minimal (stack-only possible)
        │   ├── Lists: Probably minimal
        │   ├── Performance: Fast startup
        │   ├── Offline: Core feature offline
        │   └── Special: Widget, shortcuts
        │
        └── Media/Streaming App
            ├── Navigation: Tab (Home, Search, Library, Profile)
            ├── Lists: Horizontal carousels, vertical feeds
            ├── Performance: Preloading, buffering
            ├── Offline: Download management
            └── Special: Background playback, casting
```

---

## 7. Interaction Breakdown

### Analysis for Every Gesture

Before adding any gesture:

```
GESTURE: [Gesture Type]
├── DISCOVERABILITY:
│   └── How will users discover this gesture?
│       ├── Is there a visual hint?
│       ├── Will it be shown in onboarding?
│       └── Is there a visible alternative when the gesture is missed?
│
├── PLATFORM CONVENTION:
│   ├── What does this gesture mean on iOS?
│   ├── What does this gesture mean on Android?
│   └── Am I deviating from platform convention?
│
├── ACCESSIBILITY:
│   ├── Can motor-impaired users perform this gesture?
│   ├── Is there a VoiceOver/TalkBack alternative?
│   └── Does it work with switch control?
│
├── CONFLICT CHECK:
│   ├── Does it conflict with system gestures?
│   │   ├── iOS: Edge swipe back
│   │   ├── Android: Back gesture
│   │   └── Home indicator swipe
│   └── Is it consistent with other app gestures?
│
└── FEEDBACK:
    ├── Is haptic feedback defined?
    ├── Is visual feedback sufficient?
    └── Is audio feedback needed?
```

---

## 8. Spirit Over Checklist

### Passing the Checklist is Not Enough!

| ❌ Self-Deception                                       | ✅ Honest Assessment                            |
| ------------------------------------------------------- | ----------------------------------------------- |
| "Touch target is 44px" (but on edge, unreachable)       | "Can user reach it one-handed?"                 |
| "I used FlatList" (but didn't memoize)                  | "Is scroll smooth?"                             |
| "Platform-specific nav" (but only icons differ)         | "Does iOS feel like iOS, Android like Android?" |
| "Offline support exists" (but error message is generic) | "What can user actually do offline?"            |
| "Loading state exists" (but just a spinner)             | "Does user know how long to wait?"              |

> 🔴 **Passing the checklist is NOT the goal. Creating great mobile UX IS the goal.**

---

## 9. Mobile Design Commitment

### Fill This at the Start of Every Mobile Project

```
📱 MOBILE DESIGN COMMITMENT

Project: _______________
Platform: iOS / Android / Both

1. Default pattern I will NOT use in this project:
   └── _______________

2. Context-specific focus for this project:
   └── _______________

3. Platform-specific differences I will implement:
   └── iOS: _______________
   └── Android: _______________

4. Area I will specifically optimize for performance:
   └── _______________

5. Unique challenge of this project:
   └── _______________

If I can't fill this commitment, I still do not understand the project well enough.
   → Go back, understand context better, ask the user.
```

---

## 10. Before Every Mobile Work

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRE-WORK VALIDATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  □ Did I complete Component Decomposition?                      │
│  □ Did I fill the Pattern Questioning Matrix?                   │
│  □ Did I pass the Anti-Memorization Test?                       │
│  □ Did I make context-based decisions?                          │
│  □ Did I analyze Interaction Breakdown?                         │
│  □ Did I fill the Mobile Design Commitment?                     │
│                                                                 │
│  ⚠️ Do not write code without completing these!                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

> **Remember:** If you chose a solution "because that's how it's always done," you chose WITHOUT THINKING. Every project is unique. Every context is different. Every user behavior is specific. **THINK, then code.**
