# Plan: PDV/Nova Venda — Melhorias de UX

**Feature**: 11-pdv-ux-improvements  
**Status**: Plan  
**Data**: 2026-04-20

---

## Arquitetura Geral

Todas as mudanças ficam dentro do frontend React/TypeScript. Não há alterações de backend ou banco de dados.

**Arquivos afetados:**
- `frontend/src/pages/sales/PedidosPage.tsx` — mudanças principais
- `frontend/src/pages/pdv/PDVPage.tsx` — atalhos adicionais

---

## Componentes e Mudanças

### 1. `ProductSearch` (inline em PedidosPage.tsx)

**Situação atual:** Dropdown simples sem indicador de estoque.  
**Mudança:** Adicionar cor de estoque nos itens do dropdown.

```
stockColor(qty):
  qty < 3  → "text-red-600"  + ícone AlertTriangle
  qty < 10 → "text-amber-600"
  else     → "text-emerald-600"
```

Adicionar navegação por teclado (ArrowDown/Up/Enter) com `activeIndex` state.

---

### 2. `QuickAddClienteModal` (novo componente inline em PedidosPage.tsx)

Mini-modal com formulário mínimo:
- Nome (obrigatório)
- Telefone
- CPF/CNPJ (opcional)
- tipo_cliente = 'PF' (padrão)

Chama `salesAPI.clientes.create()`. Ao sucesso, fecha o modal e preenche o cliente selecionado na drawer.

**Props:**
```typescript
{ onClose: () => void; onCreated: (c: Cliente) => void }
```

---

### 3. `NovaPedidoDrawer` — refactor estrutural

**Width:** `max-w-4xl` (era `max-w-2xl`)

**Body layout:**
```
lg:grid lg:grid-cols-[380px_1fr] overflow-hidden
  LEFT col (overflow-y-auto, p-6, border-r):
    - Loja selector
    - Cliente + botão QuickAdd
    - Pagamento + Bandeira (condicional)
    - Parcelas (desabilitado se não parcelável)
    - Tipo Entrega + Endereço (condicional)
    - Observações
  RIGHT col (flex flex-col, p-6):
    - ProductSearch (enhanced)
    - Cart table (flex-1 overflow-y-auto)
    - Total card (sticky)
```

**Smart Parcelas:**
```typescript
const PARCELAVEL = ['CARTAO_CREDITO', 'CREDIARIO'];
const parcelasDisabled = !PARCELAVEL.includes(forma);
// quando parcelasDisabled: valor fixo = '1', campo desabilitado
```

**Bandeira condicional:**
```typescript
const CARD_FORMAS = ['CARTAO_CREDITO', 'CARTAO_DEBITO'];
// quando incluso: renderiza <select> com opções Visa/Mastercard/Elo/Amex/Hipercard/Outro
```

**Endereço condicional:**
```typescript
const ENTREGA_FORMAS = ['DELIVERY', 'TRANSPORTADORA'];
// quando incluso: renderiza campos enderecoEntrega + cidadeEntrega + cepEntrega
// armazenados em state local; adicionados ao campo observacoes ao finalizar
```

**AutoFocus:**  
`useEffect` com ref para cliente search input → `.focus()` no mount

**Ctrl+Enter:**  
`useEffect` com `keydown` handler:
```typescript
if (e.ctrlKey && e.key === 'Enter') → finalizarMutation.mutate()
```

**Rodapé de atalhos:**
```
<p class="text-xs text-slate-400">Ctrl+Enter: Finalizar · ESC: Fechar</p>
```

---

### 4. `PDVPage.tsx` — atalhos extras

Adicionar ao handler de teclado existente:
- `e.key === 'F2'` → `searchRef.current?.focus()`
- `e.ctrlKey && e.key === 'Enter'` → `if (cart.length) setShowPagamento(true)`

Atualizar o texto de hints de `F10 = Pagar · ESC = Limpar` para:
`F2 = Buscar · F10 / Ctrl+Enter = Pagar · ESC = Limpar`

---

## Dependências

- Sem novas dependências de pacotes
- `salesAPI.clientes.create` já existe
- `ClientePayload` já definido em `api/sales.ts`

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Refactor estrutural do drawer pode quebrar testes E2E | Manter os mesmos `role`, `aria-label` e placeholder nos campos |
| Drawer muito larga em tablet (768-1023px) | `max-w-4xl` com `overflow-x-hidden` no backdrop |
| Endereço armazenado em observacoes pode ser inadequado | Tratar como campo visual por ora; API pode ser estendida futuramente |
