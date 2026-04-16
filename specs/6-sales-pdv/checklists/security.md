# Checklist de Segurança — Feature 6: PDV / Vendas / Clientes

**Feature**: [Spec 6 — Gestão de Clientes, Pedidos e PDV](../spec.md)  
**Domínio**: Controle de acesso, proteção de dados, auditoria financeira, atomicidade

---

## 1. Autenticação e Controle de Acesso

### 1.1 Autorização de Desconto (BR-005)
- [ ] `DescontoService.aprovar_com_pin()` usa `user.check_password(pin)` — PIN nunca comparado em texto claro
- [ ] PIN nunca é logado (nem em `DEBUG`, nem em stack traces)
- [ ] PIN nunca é armazenado nem transmitido além do request HTTP
- [ ] Nível de permissão do aprovador (`is_gerente`, `is_diretor`) é verificado antes de aplicar desconto
- [ ] Tentativas com PIN incorreto são registradas no log de auditoria (máx 3 tentativas antes de bloquear temporariamente)
- [ ] Endpoint `POST /pedidos/{id}/aprovar-desconto/` requer `IsAuthenticated` + permissão de vendedor
- [ ] Resposta de PIN incorreto não revela se o usuário existe (`403` genérico)

### 1.2 Acesso a Dados de Clientes (LGPD)
- [ ] CPF é exibido parcialmente mascarado na listagem (`***.xxx.xxx-**`)
- [ ] CNPJ completo visível apenas para usuários com permissão `view_cliente_fiscal`
- [ ] Histórico de compras de um cliente só acessível ao vendedor responsável ou gerência
- [ ] `GET /clientes/{id}/historico/` verifica permissão por loja (usuário só vê clientes da sua loja)
- [ ] Dados financeiros do cliente (limite_credito, saldo_devedor) visíveis apenas para gerência/financeiro
- [ ] Busca por CPF/CNPJ retorna resultados apenas para usuários autenticados

### 1.3 Acesso ao PDV e Vendas
- [ ] `PDVCheckoutAPIView` requer `IsAuthenticated`
- [ ] `loja_id` no payload é validado contra as lojas às quais o usuário pertence (não aceitar loja arbitrária)
- [ ] Override de estoque (`override_estoque=True`) só disponível para usuários com permissão `sales.override_stock`
- [ ] Override de limite de crédito requer permissão `sales.override_credit` + registro de aprovador

### 1.4 Recebíveis e Crédito
- [ ] `RecebivelViewSet` — `list` filtra por loja do usuário (não expõe recebíveis de outras lojas)
- [ ] `POST /recebiveis/{id}/baixar/` requer permissão de caixa/financeiro
- [ ] `POST /recebiveis/{id}/cancelar/` requer permissão de gerência

---

## 2. Proteção contra Injeção e Validação de Inputs

### 2.1 Queries de Busca
- [ ] Busca de produto no PDV usa `Q` objects do ORM Django — sem SQL raw, sem `.raw()`
- [ ] Busca de cliente usa `Q` objects — CPF/CNPJ sanitizados (apenas dígitos) antes da query
- [ ] Campo `search` em todos os ViewSets tem limite de comprimento (max 200 chars) no serializer
- [ ] Parâmetro `page_size` tem limite máximo (ex: 100) para evitar DoS por paginação excessiva

### 2.2 Validação Financeira
- [ ] `valor` em `PagamentoVenda` é sempre `Decimal` — nunca `float` (evita erros de arredondamento fiscal)
- [ ] `percentual_desconto` aceita máximo de 2 casas decimais e máx 100.00
- [ ] Soma dos `pagamentos[].valor` deve ser `==` `valor_liquido` da venda (validado no serializer)
- [ ] `valor_recebido` (troco) só aceito para forma `DINHEIRO`
- [ ] Troco negativo é rejeitado (`valor_recebido < valor`)

### 2.3 Integridade de Referências
- [ ] `produto_variacao_id` no PDV checkout é validado contra produtos da loja (sem acesso cross-loja)
- [ ] `cliente_id` no checkout é validado — cliente inexistente retorna `400`, não `500`
- [ ] `item_id` no endpoint de devolução pertence à venda referenciada (proteção contra IDOR)
- [ ] UUID de venda no endpoint `devolver` pertence à loja do usuário autenticado

---

## 3. Log de Auditoria

### 3.1 Imutabilidade do DescontoAuditLog
- [ ] `DescontoAuditLog` não tem endpoint de DELETE na API pública
- [ ] Admin Django para `DescontoAuditLog` é `readonly_fields = '__all__'` — sem edição
- [ ] `DescontoAuditLog` registra: pedido_id, solicitante_id, aprovador_id, tipo, valor_antes, valor_depois, percentual, motivo, aprovado_com_pin, timestamp
- [ ] Log é criado dentro do mesmo `@transaction.atomic` do desconto (seja criado junto ou rollback junto)

### 3.2 Rastreabilidade de Cancelamentos
- [ ] Cancelamento de venda registra: motivo obrigatório, usuário que cancelou, timestamp, venda_id, nfe_situacao_antes
- [ ] Devolução registra: movimentação de estoque de entrada + referência à venda original
- [ ] Override de crédito registra: usuário aprovador, valor_limite, valor_solicitado, timestamp, motivo

### 3.3 Rastreabilidade do PDV
- [ ] `PagamentoVenda` registra forma, valor, valor_recebido, troco para auditoria de caixa
- [ ] `Venda.vendedor` sempre preenchido (FK não-nula) — identifica operador do caixa
- [ ] Venda anônima (sem cliente) é identificada por `cliente=None` + `observacoes='BALCAO_ANONIMO'`

---

## 4. Segurança na Transmissão

### 4.1 HTTPS e Headers
- [ ] PDV opera apenas via HTTPS em produção (verificado no `settings/production.py`)
- [ ] Endpoint de checkout não cacheável: `Cache-Control: no-store` no response
- [ ] Resposta do checkout não inclui dados desnecessários (ex: hash de senha do cliente, PIN)

### 4.2 Rate Limiting
- [ ] Endpoint `PDVCheckoutAPIView` tem throttling (`ScopedRateThrottle`) — ex: 60 req/min por usuário
- [ ] Endpoint `aprovar-desconto` tem throttling mais restrito — ex: 10 req/min (previne brute-force de PIN)
- [ ] Busca de cliente tem throttling — ex: 120 req/min

---

## 5. Proteção Específica contra OWASP Top 10

| Risco OWASP | Área de Risco | Verificação |
|---|---|---|
| A01 Broken Access Control | IDOR em recebíveis e vendas | [ ] UUID + validação de loja |
| A01 Broken Access Control | CrossLoja — PDV com `loja_id` arbitrário | [ ] Validado contra lojas do usuário |
| A02 Cryptographic Failures | PIN em log/plaintext | [ ] `check_password` apenas, sem armazenamento |
| A02 Cryptographic Failures | CPF/CNPJ em logs | [ ] Mascarado nos logs de aplicação |
| A03 Injection | SQL via campo `search` | [ ] ORM Django Q objects apenas |
| A04 Insecure Design | Troco calculado no cliente | [ ] Troco recalculado no backend |
| A05 Security Misconfiguration | Endpoint checkout sem auth | [ ] `IsAuthenticated` obrigatório |
| A07 Auth Failures | PIN brute-force | [ ] Throttle + lockout após 3 falhas |
| A08 Soft/Data Integrity | Venda criada sem baixa de estoque | [ ] `@transaction.atomic` no checkout |
| A09 Logging Failures | Descontos sem log | [ ] `DescontoAuditLog` na mesma transação |
