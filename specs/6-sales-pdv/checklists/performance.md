# Checklist de Performance — Feature 6: PDV / Vendas / Clientes

**Feature**: [Spec 6 — Gestão de Clientes, Pedidos e PDV](../spec.md)  
**Domínio**: Tempo de resposta, queries N+1, paginação, experiência no caixa

---

## 1. Targets de Performance (SLOs)

| Operação | Target P95 | Crítico |
|---|---|---|
| Busca de produto no PDV (campo de busca) | < 200ms | Sim — fluidez do caixa |
| Busca de cliente por nome/CPF | < 300ms | Sim |
| PDV Checkout (atomic) | < 2.000ms | Sim — não pode travar o caixa |
| Criar/Atualizar pedido | < 500ms | Sim |
| Listar pedidos com filtros | < 800ms | Médio |
| Histórico de cliente (página 1) | < 600ms | Médio |
| Listar recebíveis com filtros | < 600ms | Médio |
| Aprovação de desconto | < 400ms | Sim — não interrompe atendimento |
| Cancelamento de venda | < 1.500ms (inclui reversão estoque) | Sim |

---

## 2. Queries de Banco — Evitar N+1

### 2.1 PDVCheckoutAPIView
- [ ] Validação de estoque para múltiplos itens: uma query com `__in` — não loop com queries individuais
- [ ] `select_related('loja', 'cliente')` no `PedidoVenda` de saída

### 2.2 PedidoVendaViewSet
- [ ] `get_queryset()` usa `select_related('loja', 'cliente', 'vendedor')` + `prefetch_related('itens')`
- [ ] `prefetch_related('itens__produto_variacao', 'itens__producao_tinta__cor_personalizada')` para detalhes do pedido
- [ ] Listagem de pedidos: campos de itens só incluídos no detail, não na list (usar serializer diferente)

### 2.3 ClienteViewSet
- [ ] `GET /clientes/{id}/historico/` usa `prefetch_related('pedidos__itens__producao_tinta')` — não lazy loading
- [ ] Listagem de clientes não inclui campos calculados pesados (`saldo_devedor`) — usar endpoint separado
- [ ] Saldo devedor do cliente (`CreditoService.verificar_disponivel`) usa `aggregate(Sum)` — uma query

### 2.4 RecebivelViewSet
- [ ] `list` usa `select_related('cliente', 'venda', 'loja')`
- [ ] Filtro por `vencimento_ate` + `situacao='ABERTO'` indexado no banco

---

## 3. Índices de Banco de Dados

### 3.1 Novos models — índices necessários
- [ ] `Recebivel`: índice em `(cliente, situacao)` para `CreditoService.verificar_disponivel`
- [ ] `Recebivel`: índice em `(loja, data_vencimento, situacao)` para listagem de vencimentos
- [ ] `Recebivel`: índice em `(venda)` para lookup por venda
- [ ] `PagamentoVenda`: índice em `(venda)` para lookup por venda
- [ ] `DescontoAuditLog`: índice em `(pedido)` para lookup por pedido
- [ ] `DescontoAuditLog`: índice em `(created_at)` para relatório de descontos por período

### 3.2 Modelos existentes — índices adicionais
- [ ] `PedidoVenda`: índice em `(loja, situacao, created_at)` — busca por fila de pedidos por loja
- [ ] `Venda`: índice em `(loja, data_venda)` — relatório diário de vendas
- [ ] `Cliente`: índice em `(cpf)` e `(cnpj)` já existem via `unique=True` — confirmar

---

## 4. Frontend — PDV Performance

### 4.1 Responsividade do Campo de Busca
- [ ] Debounce de 300ms no campo de busca de produto (não dispara query a cada keystroke)
- [ ] Debounce de 300ms no campo de busca de cliente
- [ ] Mínimo de 2 caracteres antes de disparar busca
- [ ] Loading spinner visível durante busca (não congela UI)
- [ ] Resultado de busca cancela request anterior se usuário continua digitando (AbortController)

### 4.2 Estado Local do Carrinho
- [ ] Carrinho do PDV gerenciado com `useReducer` (state local) — sem round-trip ao servidor para adicionar/remover itens
- [ ] Total do pedido calculado client-side em tempo real — nenhuma chamada de API necessária para recalcular
- [ ] Formulário de quantidade: input do tipo `number` com `step=0.01` — sem lag

### 4.3 Carregamento Inicial do PDV
- [ ] Página do PDV carrega lista de lojas ativas em `useEffect` uma vez (não a cada render)
- [ ] Dados de loja/usuário vêm do contexto de autenticação — não nova requisição

---

## 5. Paginação de Listagens

- [ ] `ClientesPage` — listagem paginada com `page_size=20` (configurável via query param)
- [ ] `PedidosPage` — listagem paginada com `page_size=15`
- [ ] `VendasPage` — listagem paginada com `page_size=15`
- [ ] `RecebiveisPage` — listagem paginada com `page_size=20`
- [ ] Histórico do cliente — paginado com `page_size=10`
- [ ] Todas as listas têm `next`/`previous` links (DRF `PageNumberPagination`)
- [ ] Frontend usa `useInfiniteQuery` ou paginação via botões — não carrega tudo de uma vez

---

## 6. Caching

- [ ] Busca de produto no PDV: `cache_page(30)` (30 segundos) para queries idênticas — aceitável para o caixa
- [ ] Histórico de cliente: `cache_page(60)` — dados não mudam em tempo real
- [ ] Lista de formas de pagamento disponíveis (estática): `cache_page(3600)`
- [ ] Checkout e cancelamento: **sem cache** — `Cache-Control: no-store`

---

## 7. Testes de Performance

- [ ] Teste de carga: 10 checkouts simultâneos em < 3s (usando pytest-benchmark ou locust simples)
- [ ] Teste: Busca de produto com `search='tinta'` em catálogo de 1000 produtos: < 200ms
- [ ] Teste: Histórico de cliente com 100 pedidos: < 600ms (paginado)
- [ ] Verificar contagem de queries no checkout com `django.test.utils.assertNumQueries` — máx 15 queries
