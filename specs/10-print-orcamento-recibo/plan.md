# Plan: Impressão de Orçamento e Recibo de Venda

**Feature:** 10-print-orcamento-recibo  
**Spec:** specs/10-print-orcamento-recibo/spec.md  
**Status:** ✅ Plan

---

## Architecture Overview

A impressão usa a API nativa do browser (`window.print()`) com CSS de mídia `@media print` para gerar layouts limpos sem necessidade de infraestrutura PDF no servidor. Os dados já existem nas APIs de Pedidos e Vendas.

```
Frontend Only
├── OrcamentoPrintLayout  (componente React puro, sem lógica)
├── ReciboPrintLayout     (componente React puro, sem lógica)
├── PrintPreviewModal     (wrapper com preview + botão imprimir)
└── usePrint hook         (window.print + CSS injection)

Dados existentes (nenhuma API nova necessária para MVP)
├── GET /api/v1/sales/pedidos/{id}/        → dados do orçamento
├── GET /api/v1/sales/vendas/{id}/         → dados do recibo
├── GET /api/v1/companies/lojas/{id}/      → dados da loja
└── GET /api/v1/companies/empresas/        → CNPJ e dados da empresa
```

---

## Technical Decisions

### TD1: window.print() com iframe oculto
- Renderiza o layout em um `<div>` com classe `print-only` fora do fluxo principal
- CSS global injeta `@media print { body > * { display: none } .print-only { display: block } }`
- Preserva o estado da página atual (não recarrega)
- Alternativa (descartada): biblioteca jsPDF — complexidade desnecessária, sem fidelidade CSS

### TD2: Componentes de layout puramente presentacionais
- `OrcamentoPrintLayout` e `ReciboPrintLayout` recebem dados via props, sem chamadas de API
- Facilita testes unitários e reutilização
- A lógica de busca de dados fica nos hooks/pages que invocam a impressão

### TD3: Dados da Empresa no contexto global
- A API `/api/v1/companies/empresas/` retorna `razao_social`, `nome_fantasia`, `cnpj`, `endereco`, `telefone`
- O `AuthContext` ou um `CompanyContext` carrega esses dados uma vez no login
- Os componentes de impressão leem do contexto — sem re-fetch a cada impressão

### TD4: Logo da loja
- A model `Loja` não possui campo `logo` atualmente
- MVP: usar texto formatado (nome fantasia em destaque) no lugar da logo
- Fase 2: adicionar campo `ImageField` na model `Loja` + serializer + upload

---

## File Structure

```
frontend/src/
  components/
    print/
      OrcamentoPrintLayout.tsx      ← layout A4/A5 do orçamento
      ReciboPrintLayout.tsx         ← layout A4/A5 do recibo
      PrintPreviewModal.tsx         ← modal com iframe preview + botão imprimir
      print.css                     ← estilos @media print
  hooks/
    usePrint.ts                     ← abstração window.print()
  pages/
    sales/
      PedidosPage.tsx               ← adicionar botão "Imprimir Orçamento"
      VendasPage.tsx                ← adicionar botão "Imprimir Recibo"
```

---

## Data Flow

### Impressão de Orçamento (PedidosPage)
```
1. Usuário clica em "Imprimir Orçamento" no pedido
2. PedidosPage busca pedido completo (já tem dados em cache via React Query)
3. Abre PrintPreviewModal com <OrcamentoPrintLayout pedido={pedido} loja={loja} empresa={empresa} />
4. Modal renderiza preview em div isolado
5. Usuário clica "Imprimir" → usePrint() invoca window.print()
6. CSS @media print oculta o restante, exibe apenas o layout
```

### Impressão de Recibo (VendasPage)
```
1. Usuário clica "Imprimir Recibo" na venda finalizada
2. VendasPage busca venda completa (com itens e pagamentos)
3. Abre PrintPreviewModal com <ReciboPrintLayout venda={venda} loja={loja} empresa={empresa} />
4. Mesmo fluxo de impressão
```

---

## Layout Specs

### Orçamento (A4)
```
┌─────────────────────────────────────┐
│  [Nome Fantasia]    CNPJ: XX.XXX... │
│  Endereço | Tel | Email             │
├─────────────────────────────────────┤
│  ORÇAMENTO Nº 0001    Data: dd/mm   │
│  Cliente: Nome | CPF/CNPJ           │
│  Validade: dd/mm/yyyy               │
├─ Itens ─────────────────────────────┤
│  Produto  | Qtd | Un | P.Unit | Sub │
│  ...                                │
├─────────────────────────────────────┤
│  Desconto: R$ XX,XX                 │
│  TOTAL: R$ XXX,XX                   │
├─────────────────────────────────────┤
│  Assinatura: ___________________    │
│  "Válido por 3 dias"                │
└─────────────────────────────────────┘
```

### Recibo (A5 ou A4)
```
┌─────────────────────────────────────┐
│  [Nome Fantasia]    CNPJ: XX.XXX... │
├─────────────────────────────────────┤
│  RECIBO DE VENDA Nº 0001            │
│  Data/Hora: dd/mm/yyyy HH:MM        │
│  Cliente: Nome ou "Consumidor Final"│
├─ Itens ─────────────────────────────┤
│  Produto | Qtd | P.Unit | Total     │
├─ Pagamento ─────────────────────────┤
│  Dinheiro: R$ XX,XX                 │
│  PIX: R$ XX,XX                      │
│  Troco: R$ X,XX                     │
│  TOTAL PAGO: R$ XXX,XX              │
├─────────────────────────────────────┤
│  Chave NF-e: (se existir)           │
│  "Este recibo não substitui a NF-e" │
└─────────────────────────────────────┘
```

---

## APIs Necessárias

Nenhuma API nova para MVP. Os endpoints existentes são suficientes:

| Endpoint | Uso |
|---|---|
| `GET /api/v1/sales/pedidos/{id}/` | Dados completos do pedido + itens |
| `GET /api/v1/sales/vendas/{id}/` | Dados da venda + pagamentos |
| `GET /api/v1/companies/lojas/` | Dados da loja (nome, endereço, tel) |
| `GET /api/v1/companies/empresas/` | CNPJ, razão social |

**Nota:** Verificar se `LojaSerializer` expõe `endereco` e `telefone`. Se não, adicionar ao serializer (mudança mínima no backend).

---

## Dependencies

- React 18 (já presente)
- Tailwind CSS (já presente) — classes `print:hidden` e `print:block`
- `@tanstack/react-query` (já presente) — dados já em cache
- Nenhuma lib nova necessária

---

## Risks

| Risco | Mitigação |
|---|---|
| `window.print()` abre diálogo do OS (não controlável) | Instrução na UI: "Selecione a impressora ou salve como PDF" |
| Dados da empresa ausentes (empresa não cadastrada) | Fallback: exibir "Dados da loja não configurados" |
| Layout quebrado em diferentes impressoras | Testar com A4 e A5; usar `mm` para margens no CSS de impressão |
