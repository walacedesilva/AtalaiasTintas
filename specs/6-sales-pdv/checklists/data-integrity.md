# Checklist de Integridade de Dados — Feature 6: PDV / Vendas / Clientes

**Feature**: [Spec 6 — Gestão de Clientes, Pedidos e PDV](../spec.md)  
**Domínio**: Atomicidade, consistência de modelos, reversibilidade, constraints de banco

---

## 1. Atomicidade do PDV Checkout (BR-004)

- [ ] `PDVCheckoutAPIView` usa `@transaction.atomic` cobrindo: criar PedidoVenda + itens + baixar estoque + criar Venda + criar PagamentoVenda
- [ ] Se `EstoqueService.baixar()` lança exceção: rollback completo — nenhum record persistido
- [ ] Se criação de `Venda` falha após baixa de estoque: rollback reverte a baixa (testado com mock de falha)
- [ ] Se criação de `PagamentoVenda` falha: rollback completo (incluindo Venda e estoque)
- [ ] `Recebivel` criado dentro da mesma transaction para crediário — se falha, venda não criada
- [ ] Teste de regressão: simular falha em cada ponto da cadeia e verificar estado do DB

---

## 2. Consistência de Recebíveis e Crédito

- [ ] `Recebivel.valor_saldo = valor_original - valor_pago` sempre consistente — recalculado em `save()`
- [ ] `valor_pago` nunca pode exceder `valor_original` (constraint no model ou validação no serializer)
- [ ] `situacao` muda automaticamente: `valor_saldo == 0 → 'PAGO'`, `0 < valor_saldo < valor_original → 'PARCIAL'`
- [ ] `situacao = 'CANCELADO'` só pode ser aplicado por `RecebivelService.cancelar()` (não endpoint direto)
- [ ] Dois pagamentos simultâneos do mesmo recebível: `select_for_update()` previne condição de corrida
- [ ] Saldo devedor do cliente (`CreditoService.verificar_disponivel`) usa `select_for_update()` ao bloquear para criação de venda

---

## 3. Consistência de Descontos

- [ ] `DescontoAuditLog` criado dentro do mesmo `@transaction.atomic` do desconto — nunca log sem desconto
- [ ] `PedidoVenda.valor_desconto` é sempre igual à soma de `ItemPedidoVenda.desconto_valor` quando descontos por item
- [ ] `percentual_desconto` no PedidoVenda é calculado como `(valor_desconto / valor_subtotal) * 100` — não aceito do body
- [ ] Desconto no total coexiste com descontos por item sem double-counting

---

## 4. Integridade de Estoque na Venda

- [ ] Reservas de estoque liberadas quando pedido muda para `CANCELADO` (mesmo se reserva criada em outra sessão)
- [ ] Baixa definitiva de estoque só ocorre uma vez por venda (idempotência: segunda chamada a `baixar()` para mesma venda é bloqueada)
- [ ] `Venda.pedido_origem` sempre referencia o `PedidoVenda` que gerou a venda — NOT NULL constraint
- [ ] ItemPedidoVenda com `quantidade_base` NULL só permitida se `unidade_venda` também é NULL

---

## 5. Constraints de Banco de Dados

### 5.1 Novos models — constraints obrigatórias
- [ ] `PagamentoVenda.valor > 0` — `CheckConstraint` no model
- [ ] `PagamentoVenda.troco >= 0` — `CheckConstraint` no model
- [ ] `Recebivel.valor_original > 0` — `CheckConstraint`
- [ ] `Recebivel.valor_pago >= 0` — `CheckConstraint`
- [ ] `Recebivel.valor_saldo >= 0` — `CheckConstraint`
- [ ] `DescontoAuditLog.percentual` entre 0.00 e 100.00 — `CheckConstraint`
- [ ] `DescontoAuditLog.valor_depois <= DescontoAuditLog.valor_antes` — `CheckConstraint`

### 5.2 Campos alterados em PedidoVenda
- [ ] Migration para `cliente` de `PROTECT NOT NULL` para `SET_NULL NULL BLANK` (para balcão anônimo — BR-001)
- [ ] Migration para `desconto_aprovador`, `desconto_motivo`, `desconto_aprovado_em` adicionados (nullable)
- [ ] Todas as migrations têm `dependencies` corretas (não quebrar ordem)
- [ ] `makemigrations --check` não detecta mudanças pendentes após aplicar migrations

---

## 6. Reversibilidade de Operações

- [ ] Cancelamento de venda: todos os `EstoqueReserva` e movimentações de baixa são revertidos — verificar via `MovimentacaoEstoque` com tipo `ENTRADA` + motivo `CANCELAMENTO_VENDA`
- [ ] Cancelamento de recebível: `valor_saldo` do recebível = `valor_original` (ou situação = CANCELADO)
- [ ] Aprovação de pedido (reserva): se qualquer item falhar na reserva, nenhuma reserva é criada
- [ ] Reprovação/cancelamento de orçamento: se item estava em produção (tintometria), alerta gerado — produção não cancelada automaticamente

---

## 7. Unicidade e Sequências

- [ ] `numero_venda` único no banco — `unique=True` + `select_for_update` no gerador
- [ ] `numero_pedido` único no banco — `unique=True`
- [ ] `ItemPedidoVenda.sequencia` por pedido — `unique_together = ['pedido', 'sequencia']` (já implementado)
- [ ] `codigo_cliente` gerado é único — caso colisão de UUID hex, nova tentativa automática

---

## 8. Testes de Integridade

- [ ] Teste: PDV checkout com estoque insuficiente → 0 records criados no banco
- [ ] Teste: Dois checkouts simultâneos para o mesmo produto com estoque = 1 → apenas um sucede
- [ ] Teste: Cancelar venda → estoque retorna ao valor original (via `MovimentacaoEstoque`)
- [ ] Teste: Pagamento de crediário → `Recebivel.valor_saldo` decrementado corretamente
- [ ] Teste: Criar recebível com limite insuficiente sem override → `402` + nenhum recebível criado
- [ ] Teste: Devolução parcial → estoque incrementado apenas pela quantidade devolvida
