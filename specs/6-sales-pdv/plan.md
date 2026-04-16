# Technical Implementation Plan — Feature 6: Gestão de Clientes, Pedidos e PDV

**Status:** ✅ Plan  
**Depends on:** Spec 4 Phase 1+2 (EstoqueService, reservas, baixas) ✅  
**Blocks:** Spec 4 Phase 3 (NFe SEFAZ needs Venda finalizada)

---

## 1. Current State Assessment

### Already Implemented (não recriar)

| Camada | Artefato | Status |
|---|---|---|
| Model | `Cliente` (20+ campos PF/PJ, limite_credito) | ✅ |
| Model | `PedidoVenda` + `ItemPedidoVenda` (multi-unit T057) | ✅ |
| Model | `Venda` (com campos NFe automation T056) | ✅ |
| Backend API | `ClienteViewSet` (CRUD + busca + toggle_ativo) | ✅ |
| Backend API | `PedidoVendaViewSet` (CRUD + create com auto-numero) | ✅ |
| Backend API | `VendaViewSet` (stub + NFe status) | ✅ |
| Backend Service | `VendaService.iniciar_checkout()` (T058) | ✅ |
| Backend Service | `VendaService.finalizar_venda()` (T059) | ✅ |
| Backend Service | `VendaService.cancelar_venda()` (T060) | ✅ |
| Backend Signal | `venda_post_save` → NFe trigger (T051) | ✅ |
| Backend URLs | `/sales/clientes/`, `/sales/pedidos/`, `/sales/vendas/` | ✅ |
| Frontend | `ClientesPage.tsx` (CRUD completo + modal) | ✅ |
| Frontend | `PedidosPage.tsx` (lista + criar + finalizar) | ✅ |
| Frontend | `VendasPage.tsx` (lista + cancelar + NFe badge) | ✅ |
| Frontend API | `salesAPI` (`sales.ts` com clientes, pedidos, vendas) | ✅ |

### Missing (escopo deste plano)

| Gap | Módulo |
|---|---|
| Modelo `PagamentoVenda` (múltiplas formas por venda) | Backend Model |
| Modelo `Recebivel` (crediário e fiado) | Backend Model |
| Modelo `DescontoAuditLog` (auditoria de descontos) | Backend Model |
| Campo `desconto_aprovador` + `desconto_motivo` em `PedidoVenda` | Backend Model |
| `DescontoService` — validação por limite + aprovação por PIN | Backend Service |
| `CreditoService` — verificar limite, deduzir, restaurar | Backend Service |
| `RecebivelService` — criar recebível no crediário, baixar | Backend Service |
| Endpoint `POST /pedidos/{id}/aprovar-desconto/` | Backend API |
| Endpoint `POST /pedidos/{id}/aprovar/` (situação APROVADO) | Backend API |
| Endpoint `POST /pedidos/{id}/finalizar-entrega/` | Backend API |
| Endpoint `POST /vendas/{id}/devolver/` | Backend API |
| Endpoint `GET /clientes/{id}/historico/` | Backend API |
| `RecebivelViewSet` (CRUD + baixar) | Backend API |
| `PDVCheckoutAPIView` — atomic PDV flow endpoint | Backend API |
| `PDVPage.tsx` — interface de caixa completa | Frontend Page |
| Aba "Histórico" em `ClientesPage.tsx` | Frontend Feature |
| Modal de aprovação de desconto em `PedidosPage.tsx` | Frontend Feature |
| `RecebiveisPage.tsx` — gestão de crediário | Frontend Page |
| Tipos TypeScript: `PagamentoVenda`, `Recebivel`, `PDVCartItem` | Frontend Types |
| Rota `/pdv` e `/recebíveis` no React Router | Frontend Routes |
| Testes backend: desconto, crédito, PDV flow, devolução | Tests |

---

## 2. Architecture Overview

```
Frontend (React + TypeScript)
  ├── PDVPage              — tela de caixa, carrinho, teclado
  ├── PedidosPage (estender) — modal de desconto, aprovação gerencial
  ├── ClientesPage (estender) — aba histórico de compras + cores
  └── RecebiveisPage       — listagem e baixa de recebíveis

         ↕ REST API (DRF)

Backend (Django + DRF)
  ├── ClienteViewSet       — [EXISTENTE] + action historico
  ├── PedidoVendaViewSet   — [EXISTENTE] + aprovar-desconto, aprovar, finalizar-entrega
  ├── VendaViewSet         — [EXISTENTE] + devolver
  ├── PDVCheckoutAPIView   — novo: cria pedido + finaliza venda atomicamente
  └── RecebivelViewSet     — novo: CRUD + baixar

         ↕ Service Layer

  ├── VendaService         — [EXISTENTE] checkout, finalizar, cancelar
  ├── DescontoService      — novo: validar limite, gerar PIN, aprovar, auditar
  ├── CreditoService       — novo: verificar limite, deduzir, restaurar
  └── RecebivelService     — novo: criar, baixar, consultar saldo

         ↕ Models

  ├── Cliente              — [EXISTENTE]
  ├── PedidoVenda          — [EXISTENTE] + campos desconto_aprovador/motivo
  ├── Venda                — [EXISTENTE]
  ├── PagamentoVenda       — novo
  ├── Recebivel            — novo
  └── DescontoAuditLog     — novo
```

---

## 3. Data Model Changes

### 3.1 `PedidoVenda` — campos adicionais (migration)
```python
# Desconto audit fields
desconto_aprovador = ForeignKey(User, null=True, blank=True, related_name='descontos_aprovados')
desconto_motivo    = CharField(max_length=500, null=True, blank=True)
desconto_aprovado_em = DateTimeField(null=True, blank=True)

# Balcão anônimo (cliente opcional — BR-001)
# Já está como PROTECT; mudar para SET_NULL + null=True, blank=True
# NOTA: Isso requer que VendaService trate cliente=None
```

### 3.2 Novo model `PagamentoVenda`
```python
class PagamentoVenda(TimeStampedModel):
    """Pagamentos de uma venda (split payment — múltiplos por venda)."""
    venda  = ForeignKey(Venda, on_delete=CASCADE, related_name='pagamentos')
    forma  = CharField(max_length=20, choices=PedidoVenda.FORMAS_PAGAMENTO)
    valor  = DecimalField(max_digits=12, decimal_places=2)
    # Troco (só para DINHEIRO)
    valor_recebido = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    troco          = DecimalField(max_digits=12, decimal_places=2, default=0)
    # Referência externa (ex: ID da transação PIX futura)
    referencia_externa = CharField(max_length=100, null=True, blank=True)
    observacoes        = CharField(max_length=300, null=True, blank=True)
```

### 3.3 Novo model `Recebivel`
```python
class Recebivel(TimeStampedModel):
    """Recebíveis gerados por vendas no crediário/fiado."""
    SITUACOES = [
        ('ABERTO', 'Em Aberto'),
        ('PAGO', 'Pago'),
        ('PARCIAL', 'Parcialmente Pago'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]
    cliente       = ForeignKey(Cliente, on_delete=PROTECT, related_name='recebiveis')
    venda         = ForeignKey(Venda, on_delete=PROTECT, related_name='recebiveis', null=True, blank=True)
    loja          = ForeignKey(Loja, on_delete=PROTECT)
    valor_original = DecimalField(max_digits=12, decimal_places=2)
    valor_pago     = DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_saldo    = DecimalField(max_digits=12, decimal_places=2)  # computed
    data_vencimento = DateField()
    situacao       = CharField(max_length=10, choices=SITUACOES, default='ABERTO')
    observacoes    = TextField(null=True, blank=True)
    # Cancelamento
    cancelado_por  = ForeignKey(User, null=True, blank=True, on_delete=SET_NULL)
    data_cancelamento = DateTimeField(null=True, blank=True)
    motivo_cancelamento = CharField(max_length=500, null=True, blank=True)
```

### 3.4 Novo model `DescontoAuditLog`
```python
class DescontoAuditLog(TimeStampedModel):
    """Log imutável de todos os descontos aplicados em pedidos."""
    pedido          = ForeignKey(PedidoVenda, on_delete=PROTECT, related_name='logs_desconto')
    solicitante     = ForeignKey(User, on_delete=PROTECT, related_name='descontos_solicitados')
    aprovador       = ForeignKey(User, null=True, blank=True, on_delete=SET_NULL, related_name='descontos_aprovados_log')
    tipo_desconto   = CharField(max_length=10, choices=[('ITEM','Por Item'),('TOTAL','No Total')])
    # item só presente se tipo_desconto == 'ITEM'
    item            = ForeignKey(ItemPedidoVenda, null=True, blank=True, on_delete=SET_NULL)
    valor_antes     = DecimalField(max_digits=12, decimal_places=2)
    valor_depois    = DecimalField(max_digits=12, decimal_places=2)
    percentual      = DecimalField(max_digits=5, decimal_places=2)
    motivo          = CharField(max_length=500, null=True, blank=True)
    aprovado_com_pin = BooleanField(default=False)
```

---

## 4. Backend Service Layer

### 4.1 `DescontoService` — `apps/sales/services.py`

```
DescontoService.validar_desconto(pedido, percentual, solicitante)
  → Se ≤ 5%: aplica direto, registra log, retorna {'aprovado': True, 'requer_pin': False}
  → Se > 5% e ≤ 20%: retorna {'aprovado': False, 'requer_pin': True, 'nivel': 'gerente'}
  → Se > 20%: retorna {'aprovado': False, 'requer_pin': True, 'nivel': 'diretor'}

DescontoService.aprovar_com_pin(pedido, percentual, motivo, pin, aprovador)
  → Verifica PIN do aprovador (senha do usuário)
  → Valida nível de permissão do aprovador
  → Aplica desconto em pedido.valor_desconto
  → Cria DescontoAuditLog
  → Retorna pedido atualizado

DescontoService.aplicar_desconto_item(item, percentual_ou_valor, solicitante, aprovador=None)
  → Regras idênticas aplicadas ao ItemPedidoVenda
  → Chama _recalcular_totais_pedido após
```

**Segurança**: PIN é verificado com `user.check_password(pin)`. Nunca armazenar PIN em texto claro.

### 4.2 `CreditoService` — `apps/sales/services.py`

```
CreditoService.verificar_disponivel(cliente, valor_novo)
  → Calcula saldo_devedor = sum(Recebivel.valor_saldo where situacao in ABERTO, PARCIAL, VENCIDO)
  → disponivel = cliente.limite_credito - saldo_devedor
  → Retorna {'disponivel': Decimal, 'saldo_devedor': Decimal, 'limite': Decimal, 'ok': bool}

CreditoService.bloquear_para_venda(cliente, valor, venda)
  → Cria Recebivel com data_vencimento = hoje + 30 dias (padrão configurável)
  → Retorna Recebivel criado

CreditoService.registrar_pagamento(recebivel, valor_pago)
  → Atualiza valor_pago e valor_saldo no Recebivel
  → Muda situacao: 'PAGO' se valor_saldo == 0, 'PARCIAL' caso contrário
```

### 4.3 `RecebivelService` — `apps/sales/services.py`

```
RecebivelService.criar(cliente, venda, valor, data_vencimento, loja)
  → Cria Recebivel, retorna instância

RecebivelService.baixar(recebivel, valor_pago, usuario)
  → @transaction.atomic
  → Atualiza valor_pago, recalcula valor_saldo
  → Muda situacao
  → Registra log de auditoria (via AuditLog se existir)

RecebivelService.cancelar(recebivel, motivo, usuario)
  → Marca cancelado, restaura crédito ao cliente
```

---

## 5. Backend API Extensions

### 5.1 `PedidoVendaViewSet` — novas actions

```
POST /sales/pedidos/{id}/aprovar-desconto/
Body: { percentual, motivo, pin, aprovador_id, tipo: 'TOTAL'|'ITEM', item_id? }
→ DescontoService.aprovar_com_pin(...)
→ Returns: pedido serializado com novo total

POST /sales/pedidos/{id}/aprovar/
Body: { data_entrega_prevista? }
→ Muda situacao: ORCAMENTO → APROVADO
→ Chama EstoqueService.reservar() para todos itens
→ Returns: pedido serializado

POST /sales/pedidos/{id}/finalizar-entrega/
Body: {}
→ Muda situacao: PRONTO → ENTREGUE
→ Chama VendaService.finalizar_venda() atomicamente
→ Returns: { pedido, venda }

POST /sales/pedidos/{id}/cancelar/
Body: { motivo }
→ Libera reservas de estoque
→ Muda situacao: CANCELADO
```

### 5.2 `VendaViewSet` — novas actions

```
POST /sales/vendas/{id}/devolver/
Body: { motivo, itens: [{item_id, quantidade}]? }
→ Cria movimentação de entrada no estoque para cada item
→ Cria Recebivel negativo (crédito para o cliente) se crediário
→ Marca venda.tem_devolucao = True
→ Returns: { venda, movimentacoes_entrada }
```

### 5.3 `ClienteViewSet` — nova action

```
GET /sales/clientes/{id}/historico/
Query params: ?page=1&page_size=10
→ Retorna PedidoVenda lista com itens (incluindo producao_tinta + cor)
→ Ordenado por data_pedido DESC
```

### 5.4 Novo `RecebivelViewSet`

```
GET    /sales/recebiveis/                    — lista com filtros (cliente, situacao, vencimento)
GET    /sales/recebiveis/{id}/               — detalhe
POST   /sales/recebiveis/{id}/baixar/        — registrar pagamento
POST   /sales/recebiveis/{id}/cancelar/      — cancelar com motivo
```

### 5.5 Novo `PDVCheckoutAPIView`

```
POST /sales/pdv/checkout/
Body: {
  loja_id,
  cliente_id?,              # null = balcão anônimo
  itens: [{produto_variacao_id, quantidade, unidade_id?, preco_unitario}],
  pagamentos: [{forma, valor, valor_recebido?}],
  desconto_total?,
  observacoes?
}
→ @transaction.atomic
→ 1. Valida estoque para todos itens
→ 2. Cria PedidoVenda (situacao='ENTREGUE' diretamente)
→ 3. Cria ItemPedidoVenda para cada item
→ 4. Baixa estoque via EstoqueService.baixar()
→ 5. Cria Venda
→ 6. Cria PagamentoVenda para cada pagamento
→ 7. Se crediário/fiado: CreditoService.bloquear_para_venda()
→ 8. Dispara signal → NFe se B2B
→ Returns: { pedido, venda, numero_venda, recebiveis?, troco? }
```

---

## 6. Frontend Architecture

### 6.1 Novas páginas

#### `frontend/src/pages/pdv/PDVPage.tsx`
Interface de caixa única (not split into sub-components no início):
- Coluna esquerda: busca de produto (foco automático), lista de itens no carrinho
- Coluna direita: painel de totais, forma de pagamento, troco
- Estado local gerenciado com `useReducer` (carrinho = array de `PDVCartItem`)
- Atalhos: `F10` = finalizar, `ESC` = cancelar/limpar, `Enter` no campo de busca = adicionar
- Busca de produto: debounce 300ms → `GET /inventory/produtos/?search=...`
- Seleção de cliente: campo separado com busca por nome/CPF
- Modal de confirmação de desconto gerencial (reutiliza componente)
- Integra `PDVCheckoutAPIView` para submissão

#### `frontend/src/pages/sales/RecebiveisPage.tsx`
- Tabela de recebíveis com filtros: situação, vencimento, cliente
- Action "Registrar Pagamento" com modal de valor + forma
- Indicador visual: vencido (vermelho), hoje (âmbar), futuro (verde)
- Rota: `/recebiveis`

### 6.2 Extensões de páginas existentes

#### `ClientesPage.tsx` — aba Histórico
- Tabs: "Dados Cadastrais" (existente) + "Histórico de Compras"
- Histórico: lista de pedidos com data, valor, situação, itens
- Para itens com `producao_tinta`: exibir badge de cor + nome da cor
- Botão "Reordenar" carrega itens no PDV ou novo pedido

#### `PedidosPage.tsx` — modal de desconto
- Após input de desconto > 5%, exibir `DescontoAprovacaoModal`
- Modal: campo PIN mascarado, campo motivo, select de aprovador
- Chama `POST /sales/pedidos/{id}/aprovar-desconto/`
- Botão "Aprovar Pedido" → `POST /sales/pedidos/{id}/aprovar/`

### 6.3 Novos componentes compartilhados

```
frontend/src/components/sales/
  DescontoAprovacaoModal.tsx    — PIN modal reusável (PDV + Pedidos)
  PagamentoSplitPanel.tsx       — seletor de múltiplas formas pagamento + troco
  ClienteQuickSearch.tsx        — campo de busca de cliente com dropdown
  CarrinhoTable.tsx             — tabela de itens do PDV com quantidade editável
```

### 6.4 Novos tipos TypeScript

```typescript
// frontend/src/types/index.ts (extending)

export interface PagamentoVenda {
  id: number;
  forma: FormaPagamento;
  valor: string;
  valor_recebido: string | null;
  troco: string;
}

export interface Recebivel extends BaseModel {
  cliente: number;
  cliente_nome: string;
  venda: string | null; // UUID
  valor_original: string;
  valor_pago: string;
  valor_saldo: string;
  data_vencimento: string;
  situacao: 'ABERTO' | 'PAGO' | 'PARCIAL' | 'VENCIDO' | 'CANCELADO';
}

export interface PDVCartItem {
  produto_variacao_id: number;
  sku: string;
  nome: string;
  quantidade: number;
  unidade_id: number | null;
  preco_unitario: number;
  desconto_valor: number;
  preco_total: number;
  estoque_disponivel: number;
}

export interface PDVCheckoutPayload {
  loja_id: number;
  cliente_id?: number | null;
  itens: Array<{
    produto_variacao_id: number;
    quantidade: number;
    unidade_id?: number | null;
    preco_unitario: number;
  }>;
  pagamentos: Array<{
    forma: FormaPagamento;
    valor: number;
    valor_recebido?: number | null;
  }>;
  desconto_total?: number;
  observacoes?: string;
}
```

### 6.5 API client — `sales.ts` additions

```typescript
pdv: {
  checkout: (payload: PDVCheckoutPayload) => POST /sales/pdv/checkout/
},
recebiveis: {
  list: (filters) => GET /sales/recebiveis/
  baixar: (id, valor) => POST /sales/recebiveis/{id}/baixar/
  cancelar: (id, motivo) => POST /sales/recebiveis/{id}/cancelar/
},
pedidos: {
  // existing + ...
  aprovar: (id) => POST /sales/pedidos/{id}/aprovar/
  aprovarDesconto: (id, payload) => POST /sales/pedidos/{id}/aprovar-desconto/
  finalizarEntrega: (id) => POST /sales/pedidos/{id}/finalizar-entrega/
},
vendas: {
  // existing + ...
  devolver: (id, payload) => POST /sales/vendas/{id}/devolver/
},
clientes: {
  // existing + ...
  historico: (id, params) => GET /sales/clientes/{id}/historico/
}
```

---

## 7. Security Considerations

| Risco | Mitigação |
|---|---|
| PIN gerencial em texto claro no log | Usar `user.check_password(pin)` — nunca armazenar PIN |
| Override de estoque / crédito sem autorização | `DescontoService` e `CreditoService` verificam `user.has_perm()` |
| PDV atomicidade (estoque baixado mas venda não criada) | Tudo em `@transaction.atomic` no `PDVCheckoutAPIView` |
| Injeção via campo de busca de produto/cliente | Filtros via ORM Django (Q objects) — sem SQL raw |
| Audit log removido | `DescontoAuditLog` sem delete endpoint; apenas admin Django pode remover |
| Recebível inflado (cliente com limite negativo) | `CreditoService.bloquear_para_venda` valida antes de criar |

---

## 8. Dependency Graph

```
Phase 1 — Models + Migrations (bloqueante para tudo)
  ├── PagamentoVenda model
  ├── Recebivel model
  ├── DescontoAuditLog model
  └── PedidoVenda migration (add desconto_aprovador, desconto_motivo)

Phase 2 — Backend Services (depende Phase 1)
  ├── DescontoService
  ├── CreditoService
  └── RecebivelService

Phase 3 — Backend APIs (depende Phase 2)
  ├── PedidoVendaViewSet — novas actions
  ├── VendaViewSet — devolver action
  ├── ClienteViewSet — historico action
  ├── RecebivelViewSet (novo)
  └── PDVCheckoutAPIView (novo)

Phase 4 — Frontend Types + API client (paralelo ao Phase 3)
  ├── Novos tipos TypeScript
  └── sales.ts API additions

Phase 5 — Frontend Pages (depende Phase 3 + 4)
  ├── PDVPage.tsx (novo)
  ├── RecebiveisPage.tsx (novo)
  ├── ClientesPage.tsx — aba histórico
  └── PedidosPage.tsx — modal desconto + botão aprovar

Phase 6 — Routing (depende Phase 5)
  └── RouterProvider — rotas /pdv e /recebiveis

Phase 7 — Testes (paralelo ao Phase 3+)
  ├── Backend: test_desconto_service.py
  ├── Backend: test_credito_service.py
  ├── Backend: test_pdv_checkout.py
  └── Backend: test_devolucao.py
```

---

## 9. Files to Create (new)

```
backend/
  apps/sales/
    migrations/000X_sales_pdv_models.py     ← PagamentoVenda, Recebivel, DescontoAuditLog + PedidoVenda fields

frontend/src/
  pages/pdv/
    PDVPage.tsx
  pages/sales/
    RecebiveisPage.tsx
  components/sales/
    DescontoAprovacaoModal.tsx
    PagamentoSplitPanel.tsx
    ClienteQuickSearch.tsx
    CarrinhoTable.tsx
```

## 10. Files to Modify (existing)

```
backend/
  apps/sales/
    models.py              ← PedidoVenda: desconto_aprovador, desconto_motivo; cliente optional
    services.py            ← + DescontoService, CreditoService, RecebivelService
    apis.py                ← + actions em PedidoVendaViewSet e VendaViewSet; + RecebivelViewSet; + PDVCheckoutAPIView
    urls.py                ← + pdv/checkout/, recebiveis/ router, clientes/historico/

frontend/src/
  types/index.ts            ← + PagamentoVenda, Recebivel, PDVCartItem, PDVCheckoutPayload
  api/sales.ts              ← + pdv, recebiveis, pedidos.aprovar, vendas.devolver, clientes.historico
  pages/customers/ClientesPage.tsx  ← + aba Histórico
  pages/sales/PedidosPage.tsx       ← + modal desconto, botão aprovar
  providers/RouterProvider.tsx      ← + /pdv, /recebiveis rotas

tests/
  backend/
    test_desconto_service.py
    test_credito_service.py
    test_pdv_checkout.py
    test_devolucao.py
```

---

## 11. Estimated Effort

| Phase | Effort | Parallelizable |
|---|---|---|
| Phase 1 — Models | 0.5 dia | Não |
| Phase 2 — Services | 1 dia | Não |
| Phase 3 — APIs | 1.5 dias | Parcial (RecebivelViewSet paralelo ao PDVCheckout) |
| Phase 4 — Frontend Types/API | 0.5 dia | Sim (com Phase 3) |
| Phase 5 — Frontend Pages | 2 dias | Parcial (PDVPage + RecebiveisPage paralelos) |
| Phase 6 — Routing | 0.25 dia | Após Phase 5 |
| Phase 7 — Testes | 1 dia | Sim (com Phase 5) |
| **Total** | **~6.75 dias** | |
