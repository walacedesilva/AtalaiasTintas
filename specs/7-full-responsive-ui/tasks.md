# Tasks: Sistema Totalmente Responsivo

**Feature**: 007-full-responsive-ui  
**Gerado**: 2026-04-16

---

## Status Legend

- [ ] Não iniciado
- [x] Concluído
- [~] Em progresso

---

## P1 — MVP (deve ter)

### [T001] PDVPage — Layout mobile com painéis alternáveis [US5]
- **Arquivo**: `src/pages/pdv/PDVPage.tsx`
- **Ação**: Adicionar estado `activePanel`, toggle para mobile, esconder painel direito com `hidden lg:flex`
- **Critério**: PDV utilizável em 375px sem scroll horizontal
- [ ] Implementado

### [T002] EstoquePage — Tabelas com overflow-x-auto [US2]
- **Arquivo**: `src/pages/inventory/EstoquePage.tsx`
- **Ação**: Adicionar `<div className="overflow-x-auto">` em LotesTab e EntradasTab
- [ ] Implementado

### [T003] EstoquePage — Formulários modal responsivos [US3]
- **Arquivo**: `src/pages/inventory/EstoquePage.tsx`
- **Ação**: `grid-cols-2` → `grid-cols-1 sm:grid-cols-2` nos modais
- [ ] Implementado

### [T004] PedidosPage — Sub-tabela e carrinho com overflow-x-auto [US2]
- **Arquivo**: `src/pages/sales/PedidosPage.tsx`
- **Ação**: Adicionar wrapper `overflow-x-auto` em itens expandidos e no carrinho do drawer
- [ ] Implementado

### [T005] PedidosPage — Formulário pagamento responsivo [US3]
- **Arquivo**: `src/pages/sales/PedidosPage.tsx`
- **Ação**: `grid-cols-3` → `grid-cols-1 sm:grid-cols-3` no campo de pagamento
- [ ] Implementado

### [T006] ClientesPage — Formulário PJ e contatos responsivo [US3]
- **Arquivo**: `src/pages/customers/ClientesPage.tsx`
- **Ação**: `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`
- [ ] Implementado

### [T007] CoresPage — Formulários do modal responsivos [US3]
- **Arquivo**: `src/pages/colors/CoresPage.tsx`
- **Ação**: `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`; `grid-cols-3` → `grid-cols-1 sm:grid-cols-3`
- [ ] Implementado

---

## P2 — Importante (deveria ter)

### [T008] VendasPage — Modal cancelamento responsivo [US7]
- **Arquivo**: `src/pages/sales/VendasPage.tsx`
- **Ação**: Adicionar `p-4` no backdrop e `max-h-[90vh] overflow-y-auto` no container; ajustar `min-w-[200px]` para responsivo
- [ ] Implementado

### [T009] PigmentStockPage — AddStockModal responsivo [US7]
- **Arquivo**: `src/pages/pigments/PigmentStockPage.tsx`
- **Ação**: Adicionar `max-h-[90vh] overflow-y-auto` + `p-4` no backdrop
- [ ] Implementado

### [T010] PigmentosPage — Modal formulário responsivo [US3]
- **Arquivo**: `src/pages/pigments/PigmentosPage.tsx`
- **Ação**: `grid-cols-3` → `grid-cols-1 sm:grid-cols-3` para RGB
- [ ] Implementado

### [T011] FormulasPage — Formulário modal responsivo [US3]
- **Arquivo**: `src/pages/formulas/FormulasPage.tsx`
- **Ação**: `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`
- [ ] Implementado

### [T012] FormulasPage — ItemRow lista de pigmentos responsivo [US3] [G5]
- **Arquivo**: `src/pages/formulas/FormulasPage.tsx`
- **Ação**: `grid-cols-[2fr_1fr_1fr_auto]` → empilhar em mobile com `flex flex-col sm:grid sm:grid-cols-[2fr_1fr_1fr_auto]`
- [ ] Implementado

### [T013] MisturasPage — Formulário modal responsivo [US3]
- **Arquivo**: `src/pages/mixtures/MisturasPage.tsx`
- **Ação**: `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`
- [ ] Implementado

### [T014] RecebiveisPage — Filtro de datas responsivo [US6]
- **Arquivo**: `src/pages/sales/RecebiveisPage.tsx`
- **Ação**: `flex items-center` → `flex flex-wrap items-center`
- [ ] Implementado

### [T015] FormulaCalculator — Formulário cliente responsivo [US3]
- **Arquivo**: `src/components/tintometry/FormulaCalculator.tsx`
- **Ação**: `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`
- [ ] Implementado

### [T016] PagamentoSplitPanel — Input valor responsivo [US3]
- **Arquivo**: `src/components/sales/PagamentoSplitPanel.tsx`
- **Ação**: `w-32` → `w-full sm:w-32` no input de valor do pagamento
- [ ] Implementado

---

## P3 — Nice to have

### [T017] Executar suite completa de testes
- **Ação**: `npm test -- --run` para confirmar todos os testes passam após mudanças
- [ ] Concluído
