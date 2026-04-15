# Tasks: Gestão de Clientes, Pedidos e PDV (Spec 6)

**Input**: Design documents from `specs/6-sales-pdv/`  
**Prerequisites**: spec.md ✅, plan.md ✅, checklists/ ✅ (5 arquivos, 203 checkpoints)

**Tests**: Cobertura mínima ≥95% em services, ≥90% em APIs, E2E para PDVPage (ver checklists/README.md)

**Organization**: Tasks organizadas em 7 fases de acordo com grafo de dependências do plan.md. Fases 4 e 7 podem rodar em paralelo com as fases anteriores conforme indicado.

**⚠️ IMPORTANTE**: Após criar tasks.md, SEMPRE executar `/speckit.analyze` para validar consistência entre spec, plan e tasks antes de iniciar implementação.

## Formato: `[ID] [P?] [US#] Descrição`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[US#]**: User story de referência do spec.md
- Caminhos de arquivo exatos conforme plan.md
- Status: `[ ]` = pendente, `[x]` = concluído

## Path Conventions (plan.md §2)

- `backend/apps/sales/` — models, services, APIs, admin do sales
- `backend/apps/inventory/` — EstoqueService (já existente)
- `frontend/src/pages/pdv/` — PDVPage
- `frontend/src/pages/sales/` — RecebiveisPage, extensões de ClientesPage/PedidosPage
- `frontend/src/components/sales/` — novos componentes compartilhados
- `frontend/src/types/index.ts` — tipos TypeScript
- `frontend/src/api/sales.ts` — API client

---

## Phase 1: Models & Migration (bloqueante para todo o resto)

**Propósito**: Novos modelos de dados e alterações no `PedidoVenda` — tudo antes de qualquer service ou API.  
**Checkpoint**: `python manage.py migrate` roda sem erros; novos models visíveis no Django Admin.

### Alterações em `PedidoVenda`

- [ ] T001 [US2,US4] Adicionar campos `desconto_aprovador` (FK User nullable), `desconto_motivo` (CharField 500), `desconto_aprovado_em` (DateTimeField nullable) em `backend/apps/sales/models.py` no model `PedidoVenda`

- [ ] T002 [US1,US3,US7] Alterar em `backend/apps/sales/models.py`:
  - `PedidoVenda.cliente`: `PROTECT NOT NULL` → `SET_NULL, null=True, blank=True` (BR-001 — balcão anônimo)
  - `Venda`: adicionar `tem_devolucao = BooleanField(default=False)` — necessário para T025 (sem este campo, T025 causa `AttributeError` em runtime)

### Novos Models

- [ ] T003 [P] [US3,US5] Criar model `PagamentoVenda` em `backend/apps/sales/models.py`:
  - FK `venda` (Venda, CASCADE, related_name='pagamentos')
  - `forma` CharField choices=`PedidoVenda.FORMAS_PAGAMENTO`
  - `valor` DecimalField(12,2) — constraint: > 0
  - `valor_recebido` DecimalField(12,2) nullable (só DINHEIRO)
  - `troco` DecimalField(12,2) default=0
  - `referencia_externa` CharField(100) nullable
  - `observacoes` CharField(300) nullable

- [ ] T004 [P] [US5] Criar model `Recebivel` em `backend/apps/sales/models.py`:
  - FK `cliente` (Cliente, PROTECT, related_name='recebiveis')
  - FK `venda` (Venda, PROTECT, related_name='recebiveis', nullable)
  - FK `loja` (Loja, PROTECT)
  - `valor_original`, `valor_pago` (default=0), `valor_saldo` DecimalField(12,2) — `valor_saldo` computado no `save()`
  - `data_vencimento` DateField
  - `situacao` CharField choices ABERTO/PAGO/PARCIAL/VENCIDO/CANCELADO, default='ABERTO'
  - `observacoes` TextField nullable
  - `cancelado_por` FK User nullable SET_NULL
  - `data_cancelamento` DateTimeField nullable
  - `motivo_cancelamento` CharField(500) nullable
  - `criado_com_override` BooleanField default=False — indica override gerencial de limite (US005 AC2)
  - `aprovador_override` FK User nullable SET_NULL related_name='overrides_credito' — aprovador do override
  - `class Meta`: constraint `valor_saldo >= 0`

- [ ] T005 [P] [US4] Criar model `DescontoAuditLog` em `backend/apps/sales/models.py`:
  - FK `pedido` (PedidoVenda, PROTECT, related_name='logs_desconto')
  - FK `solicitante` (User, PROTECT, related_name='descontos_solicitados')
  - FK `aprovador` (User, nullable SET_NULL, related_name='descontos_aprovados_log')
  - `tipo_desconto` CharField choices: ITEM / TOTAL
  - FK `item` (ItemPedidoVenda, nullable SET_NULL) — usado só se tipo_desconto='ITEM'
  - `valor_antes`, `valor_depois`, `percentual` DecimalField(12,2), DecimalField(12,2), DecimalField(5,2)
  - `motivo` CharField(500) nullable
  - `aprovado_com_pin` BooleanField default=False
  - Sem delete endpoint (imutável por design — cheklist SEC-4)

### Migrations

- [ ] T006 [US1,US2,US3,US4,US5] Criar arquivo de migration em `backend/apps/sales/migrations/` cobrindo:
  - T001: novos campos em `PedidoVenda`
  - T002: `cliente` nullable em `PedidoVenda`
  - T003: novo model `PagamentoVenda`
  - T004: novo model `Recebivel` com constraints
  - T005: novo model `DescontoAuditLog`
  - Executar `python manage.py makemigrations sales` e validar SQL gerado

### Indexes (performance) — separar em migration própria

- [ ] T007 [P] [US3,US5] Criar migration de indexes em `backend/apps/sales/migrations/` com:
  - `Recebivel(cliente, situacao)`
  - `Recebivel(loja, data_vencimento, situacao)`
  - `PedidoVenda(loja, situacao, created_at)` (se ainda não existir)
  - (ver checklists/performance.md §PERF-3)

### Admin Registration

- [ ] T008 [P] [US1,US2,US3,US4,US5] Registrar novos models no `backend/apps/sales/admin.py`:
  - `PagamentoVenda` como inline de `VendaAdmin`
  - `RecebivelAdmin` com list_display (cliente, venda, valor_saldo, situacao, data_vencimento) e list_filter (situacao, loja)
  - `DescontoAuditLogAdmin` como readonly (sem add/change/delete no Admin — SEC-4)

**Checkpoint**: `python manage.py migrate` sem erros; models em admin; 208 testes existentes ainda passam.

---

## Phase 2: Service Layer (depende Phase 1)

**Propósito**: Lógica de negócio em services.py — sem acoplamento com HTTP.  
**Checkpoint**: Todos unit tests de services passam; `python -m pytest backend/tests/sales/` verde.

### DescontoService

- [ ] T009 [US4] Implementar `DescontoService.validar_desconto(pedido, percentual, solicitante)` em `backend/apps/sales/services.py`:
  - ≤ 5%: aplica diretamente, cria `DescontoAuditLog`, retorna `{'aprovado': True, 'requer_pin': False}`
  - > 5% e ≤ 20%: retorna `{'aprovado': False, 'requer_pin': True, 'nivel': 'gerente'}`
  - > 20%: retorna `{'aprovado': False, 'requer_pin': True, 'nivel': 'diretor'}`

- [ ] T010 [US4] Implementar `DescontoService.aprovar_com_pin(pedido, percentual, motivo, pin, aprovador)` em `backend/apps/sales/services.py`:
  - Verifica permissão do aprovador pelo `nivel` retornado em T009
  - PIN verificado via `aprovador.check_password(pin)` — NUNCA armazenar PIN (SEC-1)
  - Máximo 3 tentativas de PIN (SEC-1); 4ª tentativa → raise exceção com cooldown
  - Aplica desconto em `pedido.valor_desconto`, salva `desconto_aprovador`, `desconto_motivo`, `desconto_aprovado_em`
  - Cria `DescontoAuditLog` na mesma operação (transação da camada superior)
  - Retorna pedido atualizado

- [ ] T011 [US4] Implementar `DescontoService.aplicar_desconto_item(item, percentual_ou_valor, solicitante, aprovador=None)` em `backend/apps/sales/services.py`:
  - Mesmas regras de nível do validar_desconto
  - Recalcula totais do pedido após aplicar desconto no item
  - Cria `DescontoAuditLog` com `tipo_desconto='ITEM'` e FK `item`

### CreditoService

- [ ] T012 [US5] Implementar `CreditoService.verificar_disponivel(cliente, valor_novo)` em `backend/apps/sales/services.py`:
  - `SELECT FOR UPDATE` (ou aggregate sem lock — decidir por safety)
  - `saldo_devedor = sum(Recebivel.valor_saldo) where situacao in ('ABERTO','PARCIAL','VENCIDO')`
  - `disponivel = cliente.limite_credito - saldo_devedor`
  - Retorna `{'disponivel': Decimal, 'saldo_devedor': Decimal, 'limite': Decimal, 'ok': bool}`

- [ ] T013 [US5] Implementar `CreditoService.bloquear_para_venda(cliente, valor, venda)` em `backend/apps/sales/services.py`:
  - Chama `verificar_disponivel` — raise `CreditoInsuficienteError` se não ok
  - Cria `Recebivel` com `data_vencimento = hoje + 30 dias` (configurável via settings)
  - Retorna `Recebivel` criado

- [ ] T013a [US5] Implementar `CreditoService.override_com_pin(cliente, valor, venda, pin, aprovador)` em `backend/apps/sales/services.py`:
  - Requer permissão `sales.override_credit` no aprovador (raise `PermissionDenied` se ausente)
  - Verifica PIN do aprovador via `aprovador.check_password(pin)` — NUNCA armazenar PIN
  - Cria `Recebivel` com `criado_com_override=True`, `aprovador_override=aprovador`
  - Registra auditoria: usuário, timestamp, `valor_limite`, `valor_solicitado`, motivo (BR-010, SEC-3.2)
  - Retorna `Recebivel` criado

- [ ] T014 [US5] Implementar `CreditoService.registrar_pagamento(recebivel, valor_pago)` em `backend/apps/sales/services.py`:
  - `select_for_update()` no recebivel (DI-2 — conc. safety)
  - Atualiza `valor_pago` e `valor_saldo`
  - Atualiza `situacao`: PAGO se `valor_saldo == 0`, PARCIAL caso contrário
  - Retorna recebivel atualizado

### RecebivelService

- [ ] T015 [US5] Implementar `RecebivelService.criar(cliente, venda, valor, data_vencimento, loja)` em `backend/apps/sales/services.py`:
  - Cria Recebivel com `valor_saldo = valor` (computado no save)
  - Retorna instância

- [ ] T016 [US5] Implementar `RecebivelService.baixar(recebivel, valor_pago, usuario)` em `backend/apps/sales/services.py`:
  - `@transaction.atomic`
  - `select_for_update()` no recebivel
  - Delega para `CreditoService.registrar_pagamento`
  - Registra auditoria (parceiro de log se houver sistema AuditLog; senão comentário)
  - Retorna recebivel atualizado

- [ ] T017 [US7] Implementar `RecebivelService.cancelar(recebivel, motivo, usuario)` em `backend/apps/sales/services.py`:
  - Marca `situacao='CANCELADO'`, `cancelado_por`, `data_cancelamento`, `motivo_cancelamento`
  - Restaura crédito ao cliente (saldo_devedor diminui pelo cancelamento)
  - Retorna recebivel

### Unit Tests — Services

- [ ] T018 [P] [US4] Criar `backend/tests/sales/test_desconto_service.py`:
  - Caso: desconto ≤5% aprovado automaticamente, log criado
  - Caso: 5%–20% exige PIN de gerente
  - Caso: >20% exige PIN de diretor
  - Caso: PIN correto → aprovação, log aprovado_com_pin=True
  - Caso: PIN incorreto → exceção, tentativa contada
  - Caso: 3 tentativas erradas → cooldown
  - Caso: `aplicar_desconto_item` recalcula totais

- [ ] T019 [P] [US5] Criar `backend/tests/sales/test_credito_service.py`:
  - Caso: cliente com crédito disponível — ok=True
  - Caso: saldo_devedor cobre o limite — ok=False
  - Caso: `bloquear_para_venda` cria Recebivel corretamente
  - Caso: `registrar_pagamento` parcial → PARCIAL; total → PAGO
  - Caso: concorrência — dois pagamentos simultâneos (select_for_update)
  - Caso: crédito "travado" por paralelo — stale credit scenario
  - Caso: `override_com_pin` com PIN correto + permissão → Recebivel com `criado_com_override=True`
  - Caso: `override_com_pin` sem permissão `sales.override_credit` → PermissionDenied
  - Caso: `override_com_pin` com PIN errado → CreditoOverrideError

- [ ] T020 [P] [US5] Criar `backend/tests/sales/test_recebivel_service.py`:
  - Caso: `criar` gera `valor_saldo = valor_original`
  - Caso: `baixar` atomic — simular erro → rollback
  - Caso: `cancelar` restaura crédito; novo `verificar_disponivel` reflete cancelamento

**Checkpoint**: `python -m pytest backend/tests/sales/ -v` — todos passam, sem warnings.

---

## Phase 3: Backend APIs (depende Phase 2)

**Propósito**: DRF ViewSets e actions — expor services via REST.  
**Checkpoint**: Todos testes de API passam; `python -m pytest backend/tests/sales/ -k api` verde.

### PedidoVendaViewSet — novas actions

- [ ] T021 [US2] Implementar `aprovar()` action em `backend/apps/sales/apis.py` (PedidoVendaViewSet):
  - `POST /sales/pedidos/{id}/aprovar/`
  - Body: `{ data_entrega_prevista? }`
  - Transição: ORCAMENTO → APROVADO
  - Chama `EstoqueService.reservar()` para todos itens
  - Retorna: pedido serializado

- [ ] T022 [US4] Implementar `aprovar_desconto()` action em `backend/apps/sales/apis.py`:
  - `POST /sales/pedidos/{id}/aprovar-desconto/`
  - Body: `{ percentual, motivo, pin, aprovador_id, tipo: 'TOTAL'|'ITEM', item_id? }`
  - Chama `DescontoService.aprovar_com_pin()`
  - Retorna: pedido serializado com novo total

- [ ] T023 [US2] Implementar `finalizar_entrega()` action em `backend/apps/sales/apis.py`:
  - `POST /sales/pedidos/{id}/finalizar-entrega/`
  - Transição: PRONTO → ENTREGUE
  - Chama `VendaService.finalizar_venda()` atomicamente
  - Retorna: `{ pedido, venda }`

- [ ] T024 [US7] Implementar `cancelar()` action em `backend/apps/sales/apis.py` (PedidoVendaViewSet):
  - `POST /sales/pedidos/{id}/cancelar/`
  - Body: `{ motivo }`
  - Libera reservas de estoque via `EstoqueService`
  - Transição: qualquer estado válido → CANCELADO

### VendaViewSet — novas actions

- [ ] T025 [US7] Implementar `devolver()` action em `backend/apps/sales/apis.py` (VendaViewSet):
  - `POST /sales/vendas/{id}/devolver/`
  - Body: `{ motivo, itens: [{item_id, quantidade}]? }`
  - Cria `MovimentacaoEstoque` de entrada para cada item devolvido
  - Cria `Recebivel` negativo (crédito) se a venda original usou crediário
  - Marca `venda.tem_devolucao = True` (campo adicionado em T002)
  - Retorna: `{ venda, movimentacoes_entrada }`

- [ ] T025a [US7] Implementar `cancelar()` action em `backend/apps/sales/apis.py` (VendaViewSet):
  - `POST /sales/vendas/{id}/cancelar/`
  - Body: `{ motivo, pin }` — PIN obrigatório por US007 AC1 e checklist business-logic §6.1
  - Verifica que `venda.data_venda.date() == hoje` (D+0); caso contrário → 400 com instrução para usar devolução
  - Verifica PIN do usuário autenticado via `request.user.check_password(pin)` (ou permissão de gerência)
  - Chama `VendaService.cancelar_venda()` dentro de `@transaction.atomic`:
    1. Estoque revertido via `EstoqueService` (movimentação de entrada)
    2. Recebível de crediário cancelado via `RecebivelService.cancelar()` (se existir)
    3. Se NFe situacao `AUTORIZADA` → dispara sinal de cancelamento SEFAZ (Spec 4 §3) — sem bloquear response
    4. Se NFe situacao `PENDENTE` → muda para `CANCELADA` sem chamar SEFAZ (BR-008)
  - Auditoria: registra motivo, usuário, timestamp, `nfe_situacao_antes` (BR-010, SEC-3.2)
  - Segundo cancelamento do mesmo registro → 400 (idempotência)
  - Retorna: venda atualizada com `situacao='CANCELADA'`

### ClienteViewSet — nova action

- [ ] T026 [US6] Implementar `historico()` action em `backend/apps/sales/apis.py` (ClienteViewSet):
  - `GET /sales/clientes/{id}/historico/`
  - Query params: `?page=1&page_size=10`
  - `select_related` + `prefetch_related` para evitar N+1
  - Retorna: lista paginada de `PedidoVenda` com itens (incluindo `producao_tinta` e cor se existir)
  - Ordenado por `data_pedido DESC`

### Novo RecebivelViewSet

- [ ] T027 [US5] Criar `RecebivelViewSet` em `backend/apps/sales/apis.py`:
  - CRUD padrão DRF
  - `GET /sales/recebiveis/` com filtros: `cliente`, `situacao`, `loja`, `data_vencimento__lte/__gte`
  - Permissão: loja-scoped (apenas recebiveis da loja do usuário)
  - `select_related('cliente', 'venda', 'loja')`

- [ ] T028 [US5] Adicionar action `baixar()` em `RecebivelViewSet`:
  - `POST /sales/recebiveis/{id}/baixar/`
  - Body: `{ valor_pago, forma_pagamento?, observacoes? }`
  - Chama `RecebivelService.baixar()`

- [ ] T029 [US5] Adicionar action `cancelar()` em `RecebivelViewSet`:
  - `POST /sales/recebiveis/{id}/cancelar/`
  - Body: `{ motivo }`
  - Chama `RecebivelService.cancelar()`

### Novo PDVCheckoutAPIView

- [ ] T030 [US3] Criar `PDVCheckoutAPIView` em `backend/apps/sales/apis.py`:
  - `POST /sales/pdv/checkout/`
  - `@transaction.atomic` — tudo ou nada:
    1. Valida estoque para todos itens (raise `EstoqueInsuficienteError` → rollback)
    2. Cria `PedidoVenda` com `situacao='ENTREGUE'`
    3. Cria `ItemPedidoVenda` para cada item
    4. Baixa estoque via `EstoqueService.baixar()`
    5. Cria `Venda`
    6. Cria `PagamentoVenda` para cada pagamento
    7. Se forma inclui CREDIARIO: `CreditoService.bloquear_para_venda()`
    8. Signal `venda_post_save` dispara NFe se B2B
  - Retorna: `{ pedido, venda, numero_venda, recebiveis?, troco? }`
  - Rate limiting (T031)
  - Valida `loja_id` contra lojas do usuário autenticado (SEC-3)
  - Se forma inclui CREDIARIO + `verificar_disponivel` retorna `ok=False`:
    - Sem `override_credito` no body → 402 com `{disponivel, saldo_devedor, limite}`
    - Com `override_credito: { pin, aprovador_id }` → chama `CreditoService.override_com_pin()` em vez de `bloquear_para_venda()` (US005 AC2)

- [ ] T031 [US3] Adicionar rate limiting na `PDVCheckoutAPIView` e `aprovar-desconto`:
  - `PDVCheckoutAPIView`: 60 req/min por user (throttle DRF)
  - `aprovar-desconto`: 10 req/min por user

### URL Routing

- [ ] T032 [US1,US2,US3,US4,US5,US6,US7] Registrar novos endpoints em `backend/apps/sales/urls.py`:
  - `RecebivelViewSet` → router.register
  - `PDVCheckoutAPIView` → `path('pdv/checkout/', ...)`
  - Novas actions já registradas automaticamente via DRF router para ViewSets existentes

### API Tests

- [ ] T033 [P] [US3] Criar `backend/tests/sales/test_pdv_checkout.py`:
  - Happy path: carrinho com 2 itens, pagamento misto (dinheiro + PIX)
  - Falha de estoque no item 2 → rollback completo (PedidoVenda não criado)
  - Cliente anônimo (cliente_id=None) → OK (BR-001)
  - Crediário: valida criação de Recebivel
  - Limite de crédito excedido → 400
  - Estoque exato disponível → OK; estoque -1 → 400
  - Concorrência: dois checkouts simultâneos do mesmo produto (race condition)

- [ ] T034 [P] [US4] Criar `backend/tests/sales/test_desconto_api.py`:
  - `aprovar-desconto` com PIN correto → 200, log criado
  - `aprovar-desconto` com PIN errado → 403, tentativa registrada
  - `aprovar-desconto` com percentual acima do nível → 403

- [ ] T035 [P] [US7] Criar `backend/tests/sales/test_cancelamento_devolucao.py`:
  - Cancelamento de Venda (D+0): PIN correto → estoque revertido, situacao=CANCELADA
  - Cancelamento de Venda (D+0): PIN errado → 403, venda intacta
  - Cancelamento de Venda (D+0): tentativa após D+0 → 400
  - Cancelamento com NFe PENDENTE → muda para CANCELADA sem chamar SEFAZ
  - Cancelamento com NFe AUTORIZADA → sinal de cancelamento SEFAZ disparado
  - Cancelamento de venda crediário → Recebivel cancelado, crédito restaurado
  - Segundo cancelamento do mesmo registro → 400 (idempotência)
  - Devolução (pós-D+0): estoque restaurado via movimentação de entrada, `tem_devolucao=True`
  - Devolução de venda no crediário: cria Recebivel negativo (crédito para cliente)

- [ ] T036 [P] [US2,US5,US6] Criar `backend/tests/sales/test_pedido_actions.py`:
  - `aprovar()`: transição ORCAMENTO→APROVADO, reserva de estoque criada
  - `finalizar-entrega()`: PRONTO→ENTREGUE, Venda criada
  - `cancelar()`: reservas liberadas
  - `historico()`: retorna pedidos paginados, sem N+1 (assertNumQueries ≤ 5)

- [ ] T037 [P] [US3,US5] Criar `backend/tests/sales/test_integration_pdv_flow.py`:
  - Fluxo completo: produto criado → PDV checkout → estoque baixado → NFe flag definido
  - Crediário: checkout → Recebivel criado → baixar → PAGO
  - `assertNumQueries` máximo 15 para o checkout completo (PERF-5)

**Checkpoint**: `python -m pytest backend/tests/sales/ -v` — todos passam. 208 testes existentes ainda passam.

---

## Phase 4: Frontend Types & API Client (paralelo com Phase 3)

**Propósito**: Tipos TypeScript e métodos de API — pode ser feito antes das páginas, enquanto backend Phase 3 ainda está em andamento.  
**Checkpoint**: `cd frontend && npm run build` compila sem erros de tipo.

- [ ] T038 [P] [US1,US3,US5] Adicionar tipos em `frontend/src/types/index.ts`:
  ```typescript
  PagamentoVenda { id, forma, valor, valor_recebido, troco }
  Recebivel extends BaseModel { cliente, cliente_nome, venda, valor_original, valor_pago, valor_saldo, data_vencimento, situacao }
  PDVCartItem { produto_variacao_id, sku, nome, quantidade, unidade_id, preco_unitario, desconto_valor, preco_total, estoque_disponivel }
  PDVCheckoutPayload { loja_id, cliente_id?, itens[], pagamentos[], desconto_total?, observacoes?, override_credito?: { pin: string; aprovador_id: number } }
  FormaPagamento (enum/union: 'DINHEIRO'|'PIX'|'CARTAO_CREDITO'|'CARTAO_DEBITO'|'CREDIARIO'|'TRANSFERENCIA')
  ```

- [ ] T039 [P] [US1,US2,US3,US4,US5,US6,US7] Adicionar métodos em `frontend/src/api/sales.ts`:
  ```typescript
  pdv.checkout(payload: PDVCheckoutPayload)
  recebiveis.list(filters)
  recebiveis.baixar(id, valor_pago, forma_pagamento?, observacoes?)
  recebiveis.cancelar(id, motivo)
  pedidos.aprovar(id, data_entrega_prevista?)
  pedidos.aprovarDesconto(id, payload)
  pedidos.finalizarEntrega(id)
  pedidos.cancelar(id, motivo)
  vendas.devolver(id, payload)
  clientes.historico(id, params)
  ```

**Checkpoint**: TypeScript compilado; nenhum `any` implícito nos novos tipos.

---

## Phase 5: Frontend Pages & Components (depende Phase 3 + Phase 4)

**Propósito**: UI completa do PDV, recebíveis e extensões de páginas existentes.  
**Checkpoint**: Dev server roda sem erros; funcionalidades críticas do PDV operacionais.

### Componentes Compartilhados

- [ ] T040 [US3] Criar `frontend/src/components/sales/CarrinhoTable.tsx`:
  - Tabela de itens do PDV com campos: SKU, nome, qtde (editável inline), unitário, total
  - Botão remover item (Delete key quando linha focada — ACC-1)
  - Props: `items: PDVCartItem[]`, `onUpdate(id, qty)`, `onRemove(id)`

- [ ] T041 [US1,US3] Criar `frontend/src/components/sales/ClienteQuickSearch.tsx`:
  - Input com dropdown de resultados
  - Debounce 300ms → `GET /sales/clientes/?search=...`
  - `AbortController` para cancelar requests antigos (PERF-4)
  - Suporte a busca por nome, CPF (mascarado), CNPJ
  - Props: `onSelect(cliente)`, `placeholder`, `autoFocus?`

- [ ] T042 [US4] Criar `frontend/src/components/sales/DescontoAprovacaoModal.tsx`:
  - `role="dialog"` + `aria-modal="true"` + focus trap (ACC-3)
  - Campo PIN mascarado (`type="password"`)
  - Campo motivo (obrigatório)
  - Select de aprovador (gerente/diretor conforme nível exigido)
  - Contador de tentativas (máx 3) — desabilita botão após 3
  - ESC fecha modal sem submeter

- [ ] T043 [US3,US5] Criar `frontend/src/components/sales/PagamentoSplitPanel.tsx`:
  - Lista dinâmica de formas de pagamento (adicionar/remover)
  - Calculadora de troco automática quando forma = DINHEIRO
  - Valida: soma dos pagamentos deve igualar `valor_liquido` antes de habilitar finalizar
  - `aria-live="polite"` no troco (ACC-7)

### PDV Page

- [ ] T044 [US3,US4] Criar `frontend/src/pages/pdv/PDVPage.tsx`:
  - Estado gerenciado com `useReducer` — cart como `PDVCartItem[]` (sem round-trips para cálculos)
  - Layout: coluna esquerda (busca produto + CarrinhoTable) + coluna direita (totais + PagamentoSplitPanel)
  - `autoFocus` no campo de busca de produto ao montar página
  - Teclas: `F10` = abrir pagamento, `ESC` = cancelar/limpar carrinho, `Enter` no search = adicionar item, `↑↓` nos resultados
  - `ClienteQuickSearch` acima do carrinho (cliente opcional — BR-001)
  - Busca de produto: debounce 300ms + AbortController
  - Desconto: se > 5%, abre `DescontoAprovacaoModal`
  - Submissão: chama `salesAPI.pdv.checkout()` → feedback de sucesso/erro
  - Número da venda exibido após sucesso

### Recebíveis Page

- [ ] T045 [US5] Criar `frontend/src/pages/sales/RecebiveisPage.tsx`:
  - Tabela de recebíveis com filtros: situação, loja, data_vencimento (range)
  - Indicadores visuais (nunca só cor — ACC-6): vencido (vermelho + texto "VENCIDO"), hoje (âmbar + "VENCE HOJE"), futuro (verde + "EM DIA")
  - Action "Registrar Pagamento": modal com valor + forma de pagamento → `salesAPI.recebiveis.baixar()`
  - Action "Cancelar": confirmar com motivo → `salesAPI.recebiveis.cancelar()`

### Extensões de Páginas Existentes

- [ ] T046 [US6] Estender `ClientesPage.tsx` em `frontend/src/pages/sales/ClientesPage.tsx`:
  - Adicionar tab "Histórico de Compras" ao painel de detalhe do cliente
  - Lista de pedidos com data, total, situação, preview de itens
  - Para itens com `producao_tinta`: badge de cor + nome da cor
  - Botão "Reordenar" → navega para `/pdv` com itens pré-carregados (via state/query param)

- [ ] T047 [US2,US4] Estender `PedidosPage.tsx` em `frontend/src/pages/sales/PedidosPage.tsx`:
  - Desconto no **total** do pedido: input + se > 5%, abre `DescontoAprovacaoModal` com `tipo='TOTAL'`
  - Desconto **por item**: cada linha da tabela de itens tem campo de percentual de desconto; se > 5%, abre `DescontoAprovacaoModal` com `tipo='ITEM'` e `item_id` do item selecionado (Q2/US002 AC2)
  - Botão "Aprovar Pedido" → `salesAPI.pedidos.aprovar(id)` → atualiza list
  - Botão "Finalizar Entrega" para pedidos em status PRONTO → `salesAPI.pedidos.finalizarEntrega(id)`
  - Botão "Cancelar" com dialog de confirmação + motivo (cancela pedido pré-finalizado via T024)

### Routing & Navigation

- [ ] T048 [US3,US5] Adicionar rotas `/pdv` e `/recebiveis` no `RouterProvider` em `frontend/src/App.tsx` (ou arquivo de rotas equivalente):
  ```typescript
  { path: '/pdv', element: <PDVPage /> }
  { path: '/recebiveis', element: <RecebiveisPage /> }
  ```

- [ ] T049 [US3,US5] Adicionar links "PDV" e "Recebíveis" na sidebar de navegação:
  - Ícone de caixa registradora para PDV
  - Ícone de lista/recibo para Recebíveis
  - Highlight no item ativo

**Checkpoint**: `npm run build` sem erros; npm dev server roda; PDVPage funcional em browser.

---

## Phase 6: Frontend Tests (paralelo com Phase 5+)

**Propósito**: Testes unitários de componentes e E2E do fluxo PDV.  
**Checkpoint**: `npm run test` verde; E2E PDV passa; zero violations axe-core.

- [ ] T050 [P] [US4] Criar testes unitários para `DescontoAprovacaoModal.tsx`:
  - Renderiza com campos corretos
  - ESC fecha sem submeter
  - 3 tentativas erradas desabilita botão
  - Focus trap ativo (ACC-3)

- [ ] T051 [P] [US3,US5] Criar testes unitários para `PagamentoSplitPanel.tsx`:
  - Troco calculado corretamente para DINHEIRO
  - Botão finalizar desabilitado quando soma ≠ total
  - Adição/remoção de formas de pagamento

- [ ] T052 [P] [US1,US3] Criar testes unitários para `ClienteQuickSearch.tsx`:
  - Debounce 300ms (jest fake timers)
  - AbortController cancela request antigo
  - Teclas ↑↓ navegam nos resultados

- [ ] T053 [P] [US3] Criar testes de `useReducer` do carrinho em `PDVPage`:
  - Adicionar item → total correto
  - Remover item → total atualizado
  - Alterar quantidade → total recalculado
  - Limpar carrinho → estado zerado

- [ ] T054 [US3] Criar test E2E em `frontend/tests/e2e/pdv-flow.spec.ts` (Playwright):
  - Login → navegar para /pdv
  - Buscar produto → adicionar ao carrinho
  - Definir cliente (opcional)
  - Aplicar desconto ≤5% → sem modal
  - Aplicar desconto >5% → modal de aprovação abre
  - Selecionar forma pagamento → finalizar
  - Número da venda exibido no sucesso
  - Verificar estoque diminuiu

- [ ] T055 [P] [US1,US5,US3] Executar `axe-core` nas páginas PDVPage, RecebiveisPage, DescontoAprovacaoModal:
  - Zero critical violations (ACC-8)
  - Documentar resultado em `frontend/tests/a11y/pdv-a11y-report.md`

**Checkpoint**: `npm run test` verde; `npm run test:e2e` PDV flow verde; zero axe-core critical.

---

## Phase 7: Backend Tests Adicionais (paralelo com Phase 5+)

**Propósito**: Cenários de edge-case e regressão — pode rodar enquanto frontend avança.  
**Checkpoint**: `python -m pytest backend/ -v` 100% passando; cobertura ≥95% nos services.

- [ ] T056 [P] [US3] Ampliar `test_pdv_checkout.py` com cenários de concorrência:
  - ThreadPoolExecutor com 2 threads comprando o último item em estoque
  - Apenas 1 deve ter sucesso; outro recebe 409 ou 400

- [ ] T057 [P] [US5] Ampliar `test_credito_service.py` com cenário de crédito "travado":
  - Cliente com limite exato; dois checkouts simultâneos de crediário
  - Apenas 1 deve criar Recebivel; outro deve falhar

- [ ] T058 [P] [US4] Verificar que `DescontoAuditLog` é criado na mesma transação do desconto:
  - Simular falha do save de PedidoVenda após criação do log
  - Log deve ser revertido (DI-3)

- [ ] T059 [P] [US1,US2,US3,US4,US5,US6,US7] Cheklist de regressão — após todas as implementações:
  - Executar suíte completa: `python -m pytest backend/ -v --tb=short`
  - 208 testes existentes + novos testes todos passando
  - Cobertura: `python -m pytest --cov=apps.sales backend/tests/sales/ --cov-report=term-missing`
  - Meta: ≥95% cobertura em `apps/sales/services.py`, ≥90% em `apps/sales/apis.py`

**Checkpoint final**: Todos os testes passando. Servidor Django sobe sem erros. Frontend builda sem erros.

---

## Resumo de Dependências

```
Phase 1 (T001–T008)    — bloqueante
    ↓
Phase 2 (T009–T020)    — depende Phase 1
    ↓
Phase 3 (T021–T037)    — depende Phase 2
    ↓                          ↘
Phase 5 (T040–T049)    ←  Phase 4 (T038–T039) [paralelo com Phase 3]
    ↓ (paralelo)
Phase 6 (T050–T055)    — pode começar assim que componentes estiverem criados em Phase 5
Phase 7 (T056–T059)    — pode começar assim que APIs Phase 3 estiverem prontas
```

## Contagem por Fase

| Fase | Tasks | Status |
|---|---|---|
| Phase 1 — Models & Migration | T001–T008 (8 tasks) | [ ] |
| Phase 2 — Service Layer | T009–T020 + T013a (13 tasks) | [ ] |
| Phase 3 — Backend APIs | T021–T037 + T025a (18 tasks) | [ ] |
| Phase 4 — Frontend Types & API | T038–T039 (2 tasks) | [ ] |
| Phase 5 — Frontend Pages | T040–T049 (10 tasks) | [ ] |
| Phase 6 — Frontend Tests | T050–T055 (6 tasks) | [ ] |
| Phase 7 — Backend Tests Extras | T056–T059 (4 tasks) | [ ] |
| **Total** | **62 tasks** | **0/62** |

## Estimativa de Esforço (plan.md §7)

| Fase | Esforço estimado |
|---|---|
| Phase 1 | ~0.5 dia |
| Phase 2 | ~1.5 dias |
| Phase 3 | ~2.0 dias |
| Phase 4 | ~0.5 dia |
| Phase 5 | ~2.0 dias |
| Phase 6 | ~0.75 dia |
| **Total** | **~7.25 dias** |

---

> **Próximo passo**: `/speckit.analyze` — validar consistência entre spec.md, plan.md, checklists/ e este tasks.md antes de iniciar implementação.
