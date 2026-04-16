# Plan: Sistema Totalmente Responsivo

**Feature**: 007-full-responsive-ui  
**Fase**: Plano Técnico  
**Data**: 2026-04-16

---

## Estratégia Geral

O sistema já usa **TailwindCSS** com breakpoints padrão:
- `sm` = 640px
- `md` = 768px
- `lg` = 1024px (sidebar já implementada)
- `xl` = 1280px

A abordagem é **mobile-first**: corrigir todos os pontos identificados na auditoria mantendo a hierarquia de breakpoints do Tailwind.

---

## Grupos de Correção

### G1 — Tabelas sem overflow horizontal (4 ocorrências)
**Padrão**: envolver `<table>` em `<div className="overflow-x-auto">` onde não existe ainda.

Arquivos:
- `EstoquePage.tsx` — LotesTab e EntradasTab
- `PedidosPage.tsx` — sub-tabela de itens do pedido + tabela do carrinho no drawer

### G2 — Formulários multi-coluna sem breakpoint mobile (13 ocorrências)
**Padrão**: `grid-cols-2` → `grid-cols-1 sm:grid-cols-2` | `grid-cols-3` → `grid-cols-1 sm:grid-cols-3`

Arquivos:
- `EstoquePage.tsx` (2×)
- `ClientesPage.tsx` (2×)
- `PedidosPage.tsx` (1×)
- `CoresPage.tsx` (4×)
- `PigmentosPage.tsx` (1×)
- `FormulasPage.tsx` (3×)
- `MisturasPage.tsx` (1×)
- `FormulaCalculator.tsx` (1×)

### G3 — Modais sem padding mobile (2 ocorrências)
**Padrão**: adicionar `p-4` no backdrop e `max-h-[95vh] overflow-y-auto` no container.

Arquivos:
- `VendasPage.tsx` — CancelModal
- `PigmentStockPage.tsx` — AddStockModal (já tem `mx-4`, falta `max-h`)

### G4 — PDV Page: layout crítico mobile (P1)
**Estratégia**: 
- Em mobile: mostrar apenas um painel por vez com toggle tabs (Produtos / Carrinho)
- Em desktop (lg+): manter layout lado a lado atual (`w-80` painel direito)
- Implementar estado `activePanel: 'products' | 'cart'` com toggle buttons no mobile

### G5 — Grid fixo em ItemRow das fórmulas
**Padrão**: `grid-cols-[2fr_1fr_1fr_auto]` → `grid-cols-1 sm:grid-cols-[2fr_1fr_1fr_auto]` com layout empilhado no mobile

### G6 — Filtro de datas em RecebiveisPage
**Padrão**: `flex` row → `flex flex-wrap` com `gap-2`

### G7 — Inputs com largura fixa (px) em contextos de formulário flexível
**Padrão**: manter `w-16/w-20/w-24` apenas em contextos onde faz sentido (campos numéricos pequenos dentro de tabelas); em formulários, substituir por `w-full` ou `max-w-xs`

---

## Arquitetura de Componentes Afetados

```
frontend/src/
├── pages/
│   ├── inventory/EstoquePage.tsx          — G1, G2
│   ├── customers/ClientesPage.tsx         — G2
│   ├── sales/
│   │   ├── PedidosPage.tsx               — G1, G2
│   │   ├── RecebiveisPage.tsx            — G6
│   │   └── VendasPage.tsx               — G3
│   ├── colors/CoresPage.tsx              — G2
│   ├── pigments/
│   │   ├── PigmentosPage.tsx             — G2
│   │   └── PigmentStockPage.tsx          — G3
│   ├── formulas/FormulasPage.tsx         — G2, G5
│   ├── mixtures/MisturasPage.tsx         — G2
│   └── pdv/PDVPage.tsx                   — G4 (crítico)
└── components/
    ├── tintometry/FormulaCalculator.tsx   — G2, G7
    ├── sales/CarrinhoTable.tsx            — (manter w-20 no input de qtd, é esperado)
    └── sales/PagamentoSplitPanel.tsx      — G7
```

---

## Dependências Técnicas

- Nenhuma nova biblioteca necessária
- TailwindCSS já instalado com breakpoints configurados
- Mudanças são apenas de classes CSS
- Nenhuma alteração de lógica de negócio

---

## Risco

| Item | Risco | Mitigação |
|------|-------|-----------|
| PDVPage refactor | Médio — mudança de estrutura JSX | Testar em 375px, 768px, 1280px |
| FormulasPage ItemRow | Baixo — só classes CSS | Layout empilhado no mobile é aceitável |
| Testes snapshot | Baixo | Apenas classes mudam, não estrutura semântica |

---

## Não Muda

- Lógica de negócio
- APIs e chamadas de dados
- Componentes de layout (Navigation, Header, RootLayout) — já corrigidos
- EtiquetasPage, FiscalPage, Dashboard, ProfilePage — sem issues
