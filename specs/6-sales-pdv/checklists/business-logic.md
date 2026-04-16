# Checklist de Lógica de Negócio — Feature 6: PDV / Vendas / Clientes

**Feature**: [Spec 6 — Gestão de Clientes, Pedidos e PDV](../spec.md)  
**Domínio**: Regras de venda, desconto, crédito, cancelamento, fluxo pedido→venda

---

## 1. Cadastro de Clientes (US001)

### 1.1 Diferenciação PF / PJ
- [ ] Cliente PF: CPF obrigatório para documentos fiscais (validado no serializer)
- [ ] Cliente PJ: CNPJ obrigatório + razão_social obrigatória
- [ ] CPF com 11 dígitos e CNPJ com 14 dígitos validados (algoritmo de dígito verificador)
- [ ] CPF/CNPJ únicos por banco — duplicate retorna `400` com mensagem clara
- [ ] `tipo_cliente='PF'` não permite CNPJ; `tipo_cliente='PJ'` não permite CPF
- [ ] `codigo_cliente` gerado automaticamente no create — nunca aceito no body (read-only)
- [ ] Campo `ativo=False` não impede edição do cadastro, apenas bloqueia novas vendas

### 1.2 Busca e Lookup
- [ ] Busca por CPF: normaliza input (remove `.`, `-`) antes de comparar
- [ ] Busca por CNPJ: normaliza input (remove `.`, `/`, `-`) antes de comparar
- [ ] Busca por telefone: normaliza input (remove espaços, `(`, `)`) antes de comparar
- [ ] Busca returna resultados paginados (padrão `page_size=20`)
- [ ] Campo `nome_completo` (property) exibe `nome_fantasia` para PJ ou `nome` para PF (confirmado)
- [ ] Cadastro rápido (`nome` + `telefone_principal`) salva cliente e retorna para o fluxo de venda sem sair da tela

### 1.3 Histórico de Compras (US006)
- [ ] `GET /clientes/{id}/historico/` retorna pedidos com itens, incluindo `producao_tinta` e `cor_personalizada`
- [ ] Itens com `producao_tinta` vinculada exibem: nomeCor, fórmula_resumo, quantidade_produzida
- [ ] Histórico paginado: padrão 10 pedidos por página
- [ ] Histórico ordenado por `data_pedido DESC` (pedido mais recente primeiro)
- [ ] "Reordenar" pré-carrega itens com `preco_unitario` atual (não o preço histórico salvo)

---

## 2. Pedidos e Orçamentos (US002)

### 2.1 Ciclo de Vida do Pedido
- [ ] Criação inicia em `situacao='ORCAMENTO'`
- [ ] `ORCAMENTO → APROVADO` : reserva estoque de todos os itens via `EstoqueService.reservar()`
- [ ] `APROVADO → PRODUCAO` : somente para pedidos com tintometria vinculada
- [ ] `APROVADO|PRODUCAO → PRONTO` : indica disponibilidade para entrega
- [ ] `PRONTO → ENTREGUE` : chama `VendaService.finalizar_venda()` → cria `Venda`
- [ ] `ORCAMENTO|APROVADO → CANCELADO` : libera reservas de estoque
- [ ] Transições inválidas (ex: `ORCAMENTO → ENTREGUE` diretamente) retornam `400`

### 2.2 Itens do Pedido
- [ ] Adicionar item a pedido `ENTREGUE` ou `CANCELADO` retorna `400`
- [ ] Quantidade zero ou negativa é rejeitada (min: 0.01)
- [ ] `preco_total` de cada item é recalculado automaticamente ao salvar (`qty × preco_unitario − desconto_valor`)
- [ ] Totais do pedido recalculados após qualquer mudança de item (`_recalcular_totais_pedido`)
- [ ] Produto sem estoque suficiente deve exibir aviso visual na listagem de itens (badge "Sem Estoque")
- [ ] Vinculação de `producao_tinta` ao item: validação que `producao_tinta.produto_cor` é compatível com `produto_variacao`

---

## 3. Desconto e Autorização (US004 — BR-005)

### 3.1 Limites por Nível
- [ ] Vendedor: desconto ≤ 5% aplicado automaticamente sem PIN
- [ ] Entre 5% e 20%: exige PIN de usuário com permissão `is_gerente`
- [ ] Acima de 20%: exige PIN de usuário com permissão `is_diretor` ou `is_superuser`
- [ ] Desconto por item segue as mesmas regras que desconto no total
- [ ] Combinação de descontos por item + total: percentual efetivo total não deve ultrapassar limite do operador sem aprovação

### 3.2 Aplicação e Auditoria
- [ ] `DescontoAuditLog` criado para TODA aplicação de desconto (inclusive os ≤ 5%)
- [ ] Log inclui: `aprovado_com_pin`, `aprovador_id` (nulo se desconto livre), `motivo`, `valor_antes`, `valor_depois`
- [ ] Desconto não pode ser aplicado retroativamente a vendas já finalizadas (`situacao='ENTREGUE'`)
- [ ] Reverter desconto (voltar para 0%) também cria entrada no log
- [ ] `percentual_desconto` no `PedidoVenda` reflete o desconto global (não soma de itens)

---

## 4. Formas de Pagamento (Q3 — BR-002)

### 4.1 Validação Geral
- [ ] Soma de `pagamentos[].valor` deve ser igual a `venda.valor_liquido` (tolerância: R$ 0,01 por arredondamento)
- [ ] Venda sem nenhum pagamento registrado não pode ser finalizada
- [ ] Forma `CREDIARIO` ou `FIADO` exige `cliente_id` não-nulo (BR-001)
- [ ] `PIX` e `CARTAO_*`: `valor_recebido` deve ser igual a `valor` (campo confirmação manual, sem troco)

### 4.2 Dinheiro e Troco
- [ ] `valor_recebido >= valor` — se menor, retorna `400` com mensagem "Valor recebido insuficiente"
- [ ] `troco = valor_recebido - valor` calculado no backend (não confiar no valor enviado pelo frontend)
- [ ] Troco exibido com destaque na confirmação do PDV

### 4.3 Crediário (US005 — BR-007)
- [ ] `CreditoService.verificar_disponivel()` chamado ANTES de finalizar venda crediário
- [ ] Limite insuficiente -> resposta `402` com: `disponivel`, `saldo_devedor`, `limite` no body
- [ ] Override com PIN gerencial registra aprovador no `Recebivel.criado_com_override=True`
- [ ] `Recebivel` criado com `data_vencimento = data_venda + 30 dias` (configurável por loja)
- [ ] Cliente bloqueado (`bloqueado_credito=True`) não pode usar crediário (sem override)
- [ ] Múltiplos crediários permitidos mesmo se houver vencido (mas exibe aviso de inadimplência)

---

## 5. PDV — Venda Rápida (US003 — BR-002, BR-003, BR-004)

### 5.1 Fluxo Obrigatório
- [ ] `PDVCheckoutAPIView` cria `PedidoVenda` + `Venda` em uma única transação atômica
- [ ] `PedidoVenda.situacao` começa e termina como `'ENTREGUE'` (não passa por ORCAMENTO visível ao usuário)
- [ ] Falha na baixa de estoque (qualquer item) → rollback completo → nenhuma venda criada (BR-004)
- [ ] Falha na criação da `Venda` → rollback → estoque não é baixado (BR-004)
- [ ] Venda anônima (sem `cliente_id`) aceita apenas formas `DINHEIRO`, `PIX`, `CARTAO_*` — não `CREDIARIO` (BR-001)

### 5.2 Número de Venda
- [ ] `numero_venda` gerado no backend com formato `VND-YYYYMMDD-XXXXXXXX` (único por loja)
- [ ] `numero_venda` não pode ser editado após criação

### 5.3 Recibo e NFe
- [ ] Venda com `cliente.cnpj` válido → `nfe_tipo_emissao = 'AUTOMATICA_B2B'` (BR-006)
- [ ] Venda com `cliente.cpf` → `nfe_tipo_emissao = 'MANUAL_B2C'`
- [ ] Venda anônima → `nfe_tipo_emissao = 'NAO_EMITIR'`
- [ ] Signal `venda_post_save` dispara apenas para `AUTOMATICA_B2B` (não bloqueia response PDV)

---

## 6. Cancelamento e Devolução (US007 — BR-008, BR-009)

### 6.1 Cancelamento (mesmo dia — BR-008)
- [ ] `cancelada` flag só pode ser `True` se venda foi criada no mesmo dia (D+0) — verificado por data_venda.date() == hoje
- [ ] Motivo obrigatório (mín 10 caracteres) para cancelamento
- [ ] Cancelamento: estoque revertido via movimentação de entrada + `EstoqueReserva` liberada
- [ ] Cancelamento: `Recebivel` associado cancelado automaticamente (se crediário)
- [ ] Cancelamento: NFe com situação `AUTORIZADA` → inicia cancelamento SEFAZ (Spec 4 Phase 3)
- [ ] Cancelamento: NFe com situação `PENDENTE` → muda para `CANCELADA` sem chamar SEFAZ
- [ ] Segundo cancelamento do mesmo registro retorna `400` (idempotência)

### 6.2 Devolução (pós D+0 — BR-009)
- [ ] `POST /vendas/{id}/devolver/` cria `MovimentacaoEstoque` de entrada para cada item devolvido
- [ ] Devolução parcial: campo `itens` com quantidade inferior à original é aceito
- [ ] Devolução cria crédito de recebível negativo para cliente (se venda foi crediário)
- [ ] Venda original recebe flag `tem_devolucao=True` (novo campo necessário)
- [ ] Devolução não cancela NFe original — exibe aviso de obrigação de NF-e de devolução
- [ ] Devolução não permitida em venda já cancelada (`400`)

---

## 7. Integração com Módulos Externos

### 7.1 Estoque (Spec 4)
- [ ] Ao aprovar pedido: `EstoqueService.reservar()` chamado para cada item
- [ ] Ao finalizar entrega: `EstoqueService.baixar()` chamado atomicamente
- [ ] Ao cancelar: `EstoqueService.liberar_reserva()` chamado
- [ ] Produto de tintometria: baixa deduz pigmentos da `ProducaoTinta` vinculada

### 7.2 Tintometria
- [ ] Item com `producao_tinta_id` exige que a ProducaoTinta pertença à mesma loja
- [ ] ProducaoTinta com status `'CANCELADA'` não pode ser vinculada a um item de pedido
- [ ] Ao finalizar venda: `ProducaoTinta.situacao` deve ser atualizado para `'ENTREGUE'`

### 7.3 Fiscal (Spec 4 Phase 3 — futuro)
- [ ] Interface do PDV exibe `nfe_situacao` da venda após finalização
- [ ] Falha no signal de NFe não reverte a venda (NFe é processo assíncrono)
- [ ] `nfe_requer_retry_manual` exibido como aviso na tela de vendas
