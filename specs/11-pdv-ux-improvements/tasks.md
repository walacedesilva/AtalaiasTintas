# Tasks: PDV/Nova Venda — Melhorias de UX

**Feature**: 11-pdv-ux-improvements  
**Status**: Tasks → Implement  
**Data**: 2026-04-20

---

## Dependency Order

```
T1 (ProductSearch) → T3 (Drawer layout depends on enhanced ProductSearch)
T2 (QuickAddClienteModal) → T3 (Drawer uses QuickAddClienteModal)
T3 (Drawer refactor) — depende de T1 e T2
T4 (PDVPage) — independente
```

---

## Tasks

### [T1] [P1] Melhorar ProductSearch com indicador de estoque [US-5, US-6]
**Arquivo:** `frontend/src/pages/sales/PedidosPage.tsx`  
**Seção:** `function ProductSearch`

- Adicionar state `activeIndex` para navegação por teclado
- Adicionar `onKeyDown` no input para ArrowDown/Up/Enter
- Adicionar função `stockColor(qty: number)` e ícone de alerta quando qty < 3
- Mostrar preço em destaque e estoque com cor dinâmica no dropdown

Status: [x] completed

---

### [T2] [P1] Criar QuickAddClienteModal [US-6, RF-07, RF-08]
**Arquivo:** `frontend/src/pages/sales/PedidosPage.tsx`  
**Posição:** antes de `NovaPedidoDrawer`

- Mini-modal com campos: nome (required), telefone, cpf_cnpj
- Usa `salesAPI.clientes.create()`
- Props: `onClose`, `onCreated(c: Cliente)`
- Spinner de loading durante mutação

Status: [x] completed

---

### [T3] [P1] Refatorar NovaPedidoDrawer — layout + campos inteligentes [US-1,2,3,4,7,8]
**Arquivo:** `frontend/src/pages/sales/PedidosPage.tsx`  
**Seção:** `function NovaPedidoDrawer`

- Expandir drawer para `max-w-4xl`
- Body: `lg:grid lg:grid-cols-[380px_1fr]`
- AutoFocus no campo cliente ao abrir
- Smart parcelas (disabled quando não parcelável)
- Campo bandeira (condicional para cartão)
- Campos endereço (condicional para entrega/transportadora)
- Botão "+" para abrir QuickAddClienteModal ao lado do campo cliente
- Ctrl+Enter aciona finalizarMutation
- Rodapé com hint de atalhos
- Total card em destaque na coluna direita

Status: [x] completed

---

### [T4] [P1] PDVPage — atalhos F2 e Ctrl+Enter [US-9, RF-12,13,14]
**Arquivo:** `frontend/src/pages/pdv/PDVPage.tsx`

- Adicionar `F2` ao handler de teclado → `searchRef.current?.focus()`
- Adicionar `Ctrl+Enter` → `if (cart.length) setShowPagamento(true)`
- Atualizar texto de hints

Status: [x] completed

---

## Checklist de Qualidade

- [ ] Todos os inputs novos têm `label` ou `aria-label`
- [ ] Testar navegação por teclado no ProductSearch dropdown
- [ ] Verificar que Ctrl+Enter não aciona quando cart vazio
- [ ] Verificar que parcelas = '1' é enviado corretamente para API quando desabilitado
- [ ] Layout 2 colunas não quebra em 768-1023px (drawer deve ter scroll horizontal oculto)
- [ ] QuickAddClienteModal fecha com ESC
