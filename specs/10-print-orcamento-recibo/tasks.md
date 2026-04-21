# Tasks: Impressão de Orçamento e Recibo de Venda

**Feature:** 10-print-orcamento-recibo  
**Plan:** specs/10-print-orcamento-recibo/plan.md  
**Status:** 🔲 Not Started

---

## Task List

### T001 — Expor `endereco` e `telefone` no LojaSerializer [P1]
**File:** `backend/apps/companies/apis.py`  
**User Story:** US1, US2  
**Description:** Adicionar `endereco` e `telefone` ao `fields` do `LojaSerializer` para que os dados da loja sejam acessíveis nos documentos impressos.

```python
# De:
fields = ['id', 'nome', 'uf', 'cidade', 'ativa']
# Para:
fields = ['id', 'nome', 'uf', 'cidade', 'ativa', 'endereco', 'telefone']
```

**Tests:** Verificar que `GET /api/v1/companies/lojas/` retorna `endereco` e `telefone`.

- [ ] Status: 🔲 Not Started

---

### T002 — Criar tipo TypeScript `LojaDetalhada` [P1] [P]
**File:** `frontend/src/types/index.ts`  
**User Story:** US1, US2  
**Depends on:** T001  
**Description:** Estender ou criar interface `Loja` com os novos campos.

```typescript
export interface Loja {
  id: number;
  nome: string;
  uf: string | null;
  cidade: string | null;
  ativa: boolean;
  endereco: string | null;   // novo
  telefone: string | null;   // novo
}
```

- [ ] Status: 🔲 Not Started

---

### T003 — Criar `print.css` com estilos de impressão [P1] [P]
**File:** `frontend/src/components/print/print.css`  
**User Story:** US1, US2, US3  
**Description:** CSS com `@media print` para isolar o componente de impressão e ocultar o restante da UI.

```css
@media print {
  body > #root > * { display: none !important; }
  .print-document { display: block !important; }
  @page { margin: 15mm; size: A4; }
}
.print-document { display: none; }
```

- [ ] Status: 🔲 Not Started

---

### T004 — Criar hook `usePrint` [P1] [P]
**File:** `frontend/src/hooks/usePrint.ts`  
**User Story:** US1, US2  
**Description:** Hook que injeta o conteúdo em um container isolado e invoca `window.print()`.

```typescript
export function usePrint() {
  const print = (elementId: string) => {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.classList.add('print-document');
    window.print();
    el.classList.remove('print-document');
  };
  return { print };
}
```

- [ ] Status: 🔲 Not Started

---

### T005 — Criar `OrcamentoPrintLayout` [P1]
**File:** `frontend/src/components/print/OrcamentoPrintLayout.tsx`  
**User Story:** US1, US3  
**Depends on:** T002, T003  
**Description:** Componente presentacional que renderiza o layout do orçamento. Recebe `pedido: PedidoVenda`, `loja: Loja`, `empresa: Empresa` como props. Sem chamadas de API.

Conteúdo:
- Cabeçalho: nome fantasia da empresa, CNPJ formatado, endereço, telefone
- Título: "ORÇAMENTO Nº {numero_pedido}" + data
- Dados do cliente (ou "Consumidor Final" se ausente)
- Tabela de itens: produto, unidade, quantidade, preço unitário, desconto item, subtotal
- Rodapé de totais: desconto geral, valor total
- Campo de validade (data pedido + 3 dias) + campo de assinatura
- Texto: "Este orçamento não constitui nota fiscal"

- [ ] Status: 🔲 Not Started

---

### T006 — Criar `ReciboPrintLayout` [P1]
**File:** `frontend/src/components/print/ReciboPrintLayout.tsx`  
**User Story:** US2, US3  
**Depends on:** T002, T003  
**Description:** Componente presentacional para o recibo. Recebe `venda: Venda`, `loja: Loja`, `empresa: Empresa` como props.

Conteúdo:
- Cabeçalho: mesmos dados da empresa
- Título: "RECIBO DE VENDA Nº {id_venda}" + data/hora
- Dados do cliente (ou "Consumidor Final")
- Tabela de itens do pedido de origem
- Seção de pagamentos: lista `PagamentoVenda` com forma + valor
- Troco (se pagamento em dinheiro com valor > total)
- Total pago em destaque
- Bloco condicional: chave NF-e + disclaimer se `nfe_chave_acesso` presente
- Texto: "Guarde este recibo para sua garantia"

- [ ] Status: 🔲 Not Started

---

### T007 — Criar `PrintPreviewModal` [P1]
**File:** `frontend/src/components/print/PrintPreviewModal.tsx`  
**User Story:** US3  
**Depends on:** T004, T005, T006  
**Description:** Modal genérico de pré-visualização que recebe o conteúdo a imprimir como children. Botões: "Imprimir" e "Fechar".

```typescript
interface Props {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode; // OrcamentoPrintLayout ou ReciboPrintLayout
}
```

- [ ] Status: 🔲 Not Started

---

### T008 — Integrar impressão de orçamento em `PedidosPage` [P1]
**File:** `frontend/src/pages/sales/PedidosPage.tsx`  
**User Story:** US1  
**Depends on:** T007  
**Description:** Adicionar botão "Imprimir" nos pedidos com situação `ORCAMENTO` ou `APROVADO`. Ao clicar, abre `PrintPreviewModal` com `OrcamentoPrintLayout`.

- Botão com ícone `Printer` da Lucide React
- Visível apenas em pedidos com `situacao` ∈ `['ORCAMENTO', 'APROVADO', 'PRONTO', 'ENTREGUE']`
- Buscar dados da loja via `companiesAPI.lojas.list()` (já disponível em cache no contexto)

- [ ] Status: 🔲 Not Started

---

### T009 — Integrar impressão de recibo em `VendasPage` [P1]
**File:** `frontend/src/pages/sales/VendasPage.tsx`  
**User Story:** US2  
**Depends on:** T007  
**Description:** Adicionar botão "Imprimir Recibo" nas vendas finalizadas (não canceladas). Ao clicar, abre `PrintPreviewModal` com `ReciboPrintLayout`.

- Verificar que `Venda` inclui `pagamentos` na resposta da API; se não, ajustar serializer ou fazer fetch separado
- Botão com ícone `Printer` da Lucide React

- [ ] Status: 🔲 Not Started

---

### T010 — Verificar campos de `Venda` e `PedidoVenda` nos serializers [P1] [P]
**File:** `backend/apps/sales/apis.py`  
**User Story:** US2  
**Description:** Confirmar que:
- `VendaSerializer` expõe `pagamentos` (lista de `PagamentoVenda` com `forma` e `valor`)
- `VendaSerializer` expõe `nfe_chave_acesso` (se existir link com `NotaFiscal`)
- `PedidoVendaSerializer` expõe itens com `nome_produto`, `unidade`, `quantidade`, `preco_unitario`, `desconto_valor`, `preco_total`

Ajustar campos expostos se necessário (sem alterar lógica de negócio).

- [ ] Status: 🔲 Not Started

---

## Dependency Order

```
T001 (backend: LojaSerializer)
T010 (backend: verificar Venda/Pedido serializers)
  ↓
T002 (types: Loja)
T003 (CSS de impressão)        ← paralelo com T002
T004 (hook usePrint)           ← paralelo com T002
  ↓
T005 (OrcamentoPrintLayout)
T006 (ReciboPrintLayout)       ← paralelo com T005
  ↓
T007 (PrintPreviewModal)
  ↓
T008 (PedidosPage integração)
T009 (VendasPage integração)   ← paralelo com T008
```

---

## Acceptance Criteria Summary

| Task | Critério de Done |
|---|---|
| T001 | `GET /api/v1/companies/lojas/` retorna `endereco` e `telefone` |
| T002 | TypeScript compila sem erros com novos campos |
| T003 | Print preview oculta UI; exibe apenas documento |
| T004 | `usePrint()` invoca `window.print()` sem erros |
| T005 | Orçamento renderiza todos os campos especificados (US1) |
| T006 | Recibo renderiza todos os campos especificados (US2) |
| T007 | Modal abre/fecha corretamente; preview fiel ao impresso |
| T008 | Botão visível no pedido; modal abre com dados corretos |
| T009 | Botão visível na venda; modal abre com dados corretos |
| T010 | Serializers expõem todos os campos necessários |
