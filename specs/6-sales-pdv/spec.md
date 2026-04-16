# Feature 6: Gestão de Clientes, Pedidos e PDV (Frente de Caixa)

**Status:** ✅ Specify  
**Priority:** P1 (MVP)  
**Estimated Complexity:** High  
**Business Impact:** Critical — Desbloqueia operação comercial completa da loja

---

## Clarification Questions & Answers

### Q1: Identificação e Diferenciação PF vs PJ
**Question:** Um cliente sem CPF/CNPJ pode ser atendido? Qual o comportamento mínimo para venda balcão sem cliente cadastrado?

**Business Impact:** Define fluxo do PDV para vendas rápidas e requisitos mínimos de cadastro.

**Answer:** Três modos de atendimento coexistem:
- **Cliente cadastrado (PF/PJ):** Busca por nome, CPF, CNPJ ou telefone; associado ao pedido
- **Consumidor Identificado:** CPF informado no ato mas sem cadastro completo — válido para NFC-e fiscal
- **Balcão anônimo:** Sem identificação — apenas recibo interno, sem NFe; permitido para compras de baixo valor
- Vendedor pode optar por cadastrar cliente rapidamente no início do atendimento ("cadastro rápido")

### Q2: Regras de Desconto e Autorização
**Question:** Qualquer vendedor pode aplicar desconto? Existe limite máximo? O desconto pode ser aplicado por item ou só no total?

**Business Impact:** Afeta controle de margem, auditoria e fluxo de aprovação.

**Answer:** Sistema de desconto por níveis de permissão:
- **Vendedor:** Até 5% no total do pedido sem aprovação
- **Gerente de Vendas:** Até 20% por item ou no total
- **Diretor / Admin:** Sem limite
- Desconto pode ser aplicado por item (produto específico) ou no total do pedido
- Descontos acima do limite exibem modal de solicitação de aprovação com código de autorização do gerente
- Log de desconto com motivo + aprovador é obrigatório para auditoria

### Q3: Formas de Pagamento e Parcelamento
**Question:** PIX exige confirmação manual ou automática? Crediário tem controle de parcelas e vencimentos? Limite de crédito bloqueia a venda?

**Business Impact:** Define fluxo de caixa, gestão de recebíveis e integração com limite de crédito.

**Answer:** Cada forma de pagamento tem regras específicas:
- **Dinheiro:** Operador informa valor recebido; sistema calcula troco automaticamente
- **PIX:** Qr Code exibido no caixa; confirmação manual pelo operador após verificar extrato
- **Cartão Débito/Crédito:** Operador confirma manualmente após aprovação na máquina física
- **Crediário (fiado):** Requer cliente cadastrado com limite de crédito suficiente; cria lançamento de recebível; bloqueia se saldo de crédito for insuficiente (salvo override gerencial)
- **Parcelamento cartão crédito:** Operador informa número de parcelas; sistema registra mas não controla financeiramente as parcelas individuais (integração financeira futura)
- **Múltiplas formas:** Uma venda pode usar combinação de pagamentos (ex: parte PIX + parte crediário)

### Q4: Ciclo de Vida Pedido → Venda e Integração Tintometria
**Question:** Toda venda precisa passar pela etapa de Pedido? PDV pode criar venda direta? Como vincular a tinta produzida no tintômetro ao item do pedido?

**Business Impact:** Define arquitetura dos fluxos de trabalho e integração entre módulos.

**Answer:** Dois fluxos coexistem:
- **Fluxo PDV (venda rápida):** Cria pedido + finaliza venda em uma única operação atômica; não há etapa intermediária visível ao usuário
- **Fluxo Balcão (pedido completo):** Orçamento → aprovação gerencial opcional → produção (tintometria) → pronto → entrega → fechamento financeiro
- **Integração tintometria:** Quando item é tinta personalizada, operador pode vincular `ProducaoTinta` criada no Tintômetro ao item do pedido; baixa de estoque usa a produção como referência
- **Venda sem pedido:** Não permitida — PDV sempre cria pedido internamente para garantir rastreabilidade fiscal

### Q5: Devoluções e Cancelamentos
**Question:** Uma venda finalizada pode ser cancelada? Estoque é estornado automaticamente? Existe prazo para cancelamento?

**Business Impact:** Afeta integridade do estoque, crédito do cliente e obrigações fiscais.

**Answer:** Política de cancelamento por situação:
- **Pedido em Orçamento ou Aprovado:** Cancelamento livre, estoque reservado é liberado automaticamente
- **Venda Finalizada (mesmo dia):** Cancelamento permitido com motivo obrigatório; estoque é estornado; NFe é cancelada na SEFAZ se emitida
- **Venda Finalizada (após D+0):** Requer devolução formal; cria movimentação de entrada no estoque; NF-e de devolução pode ser necessária
- **Crediário cancelado:** Lançamento financeiro é removido ou estornado conforme situação

---

## Context & Business Need

A loja de tintas opera com dois perfis de atendimento: varejo balcão (consumidor final compra de forma simples e rápida) e B2B (construtoras, pintores profissionais fazem pedidos com condições negociadas). Hoje não existe um sistema integrado que cubra desde o cadastro do cliente até o fechamento da venda com controle de estoque e registro fiscal, forçando o uso de planilhas paralelas, registros manuais e reconciliações frequentes.

**Pain Points Atuais:**
- Sem API REST de clientes, cada módulo que precisa de cliente (vendas, tintometria, fiscal) não tem como operar de forma integrada
- Pedidos de orçamento feitos verbalmente ou em papel, sem rastreabilidade
- PDV inexistente — qualquer venda é registrada manualmente fora do sistema
- Limite de crédito de clientes não é verificado no momento da venda
- Histórico de compras desconectado do histórico de tintometria
- Descontos aplicados sem controle ou registro de quem autorizou

**Objetivo:** Ter um sistema onde o vendedor abre o PDV, localiza o cliente, adiciona produtos/tintas personalizadas, aplica desconto com autorização adequada, recebe o pagamento em qualquer forma, finaliza a venda com baixa automática de estoque e registro fiscal integrado — tudo em uma interface única e fluída.

---

## User Stories

### US001: Cadastro e Busca de Clientes
**Como** vendedor da loja  
**Eu quero** cadastrar e localizar clientes de forma rápida  
**Para que** eu possa associar o cliente à venda e acessar seu histórico

**Acceptance Scenarios:**

1. **Given** operador está no PDV ou na tela de clientes, **When** digita CPF ou CNPJ, **Then** sistema localiza cliente existente em menos de 1 segundo ou exibe formulário de cadastro pré-preenchido com os dados digitados
2. **Given** busca por nome retorna múltiplos resultados, **When** operador vê a lista, **Then** resultados mostram nome, tipo (PF/PJ), telefone e data da última compra para identificação rápida
3. **Given** novo cliente sem nenhum dado anterior, **When** operador acessa "cadastro rápido", **Then** pode criar cliente com apenas nome + telefone em menos de 30 segundos e continuar a venda
4. **Given** cliente tem bloqueio de crédito, **When** vendedor tenta criar pedido com crediário, **Then** sistema exibe aviso mas permite concluir com outra forma de pagamento
5. **Given** cliente PJ, **When** dados são exibidos, **Then** sistema mostra razão social, CNPJ, IE, limite de crédito disponível e saldo devedor atual

---

### US002: Registro de Orçamento e Pedido de Venda
**Como** vendedor da loja  
**Eu quero** registrar orçamentos e pedidos com todos os detalhes comerciais  
**Para que** eu possa gerenciar o ciclo completo do pedido sem perdas de informação

**Acceptance Scenarios:**

1. **Given** cliente selecionado, **When** vendedor adiciona produtos ao pedido, **Then** sistema exibe SKU, descrição, estoque disponível e preço unitário em tempo real; produto sem estoque é destacado com aviso
2. **Given** item adicionado ao pedido, **When** vendedor informa desconto por item (até 5%), **Then** sistema recalcula preço do item e total do pedido instantaneamente
3. **Given** desconto solicitado ultrapassa o limite do vendedor, **When** sistema solicita código gerencial, **Then** gerente informa PIN e o desconto é aplicado com log registrado (usuário aprovador + horário + motivo)
4. **Given** pedido tem produto de tinta personalizada, **When** vendedor vincula produção do tintômetro, **Then** item exibe cor, fórmula e referência da produção; baixa de estoque vai deduzir os pigmentos corretos
5. **Given** pedido em situação "ORÇAMENTO", **When** cliente aprova valor, **Then** gerente ou vendedor com permissão muda situação para "APROVADO" e sistema reserva o estoque dos itens
6. **Given** pedido em produção de tintometria, **When** tinta é produzida, **Then** situação muda para "PRONTO" e sistema notifica vendedor responsável
7. **Given** pedido está "PRONTO", **When** produto é entregue ao cliente, **Then** vendedor finaliza a entrega, sistema converte pedido em venda, baixa o estoque definitivamente e dispara fluxo fiscal conforme tipo de cliente

---

### US003: PDV — Venda Rápida no Balcão
**Como** operador de caixa  
**Eu quero** realizar uma venda rápida sem precisar navegar por múltiplas telas  
**Para que** o atendimento seja ágil e clientes não fiquem esperando

**Acceptance Scenarios:**

1. **Given** operador abre o PDV, **When** a tela carrega, **Then** cursor está automaticamente no campo de busca de produto; operador pode escanear código de barras ou digitar nome sem clicks adicionais
2. **Given** produto é localizado (por código ou nome), **When** adicionado ao carrinho, **Then** aparece com quantidade 1 editável, preço, e total parcial atualizado instantaneamente
3. **Given** carrinho com produtos, **When** operador aciona "Finalizar Venda" (F10 ou botão), **Then** tela de pagamento abre com total devido em destaque
4. **Given** tela de pagamento aberta, **When** operador seleciona "Dinheiro" e informa valor recebido, **Then** sistema calcula e exibe troco em destaque antes de confirmar
5. **Given** tela de pagamento, **When** operador divide o pagamento (50% PIX + 50% dinheiro), **Then** ambas as formas são registradas e o total confere com o valor da venda
6. **Given** venda finalizada, **When** sistema processa o fechamento, **Then** estoque é baixado atomicamente (se baixa falhar, venda não é confirmada), número da venda é gerado e recibo pode ser impresso
7. **Given** cliente identificado como B2B (CNPJ), **When** venda é finalizada, **Then** flag de emissão NFe automática é ativada e processo fiscal é iniciado em background
8. **Given** venda em progresso, **When** operador pressiona "Cancelar" (ESC), **Then** sistema pede confirmação e, se confirmado, libera todos os itens reservados sem registrar nada

---

### US004: Gestão de Descontos com Controle de Autorização
**Como** gerente de vendas  
**Eu quero** controlar quais descontos são aplicados e por quem  
**Para que** a margem da loja seja protegida sem travar o atendimento

**Acceptance Scenarios:**

1. **Given** vendedor aplica desconto de 3% no total, **When** confirma, **Then** desconto é registrado automaticamente com ID do vendedor, data e hora — sem necessidade de aprovação adicional
2. **Given** vendedor tenta aplicar 15% de desconto, **When** sistema detecta que ultrapassa o limite, **Then** exibe modal pedindo código de autorização de gerente com campo visible/mascarável
3. **Given** gerente informa PIN correto no modal, **When** desconto é aprovado, **Then** log de auditoria registra: ID do pedido, valor original, valor com desconto, percentual, ID do vendedor que solicitou, ID do gerente que aprovou, timestamp
4. **Given** relatório de descontos é acessado por admin, **When** filtra por período, **Then** lista todos os descontos com colunas: pedido, cliente, vendedor, valor antes, valor depois, percentual, aprovador, motivo

---

### US005: Controle de Crédito e Crediário
**Como** gerente financeiro  
**Eu quero** controlar o crédito dos clientes no momento da venda  
**Para que** inadimplência seja controlada antes de virar problema

**Acceptance Scenarios:**

1. **Given** cliente tem limite de crédito de R$ 500 e já deve R$ 300, **When** vendedor tenta finalizar venda de R$ 250 no crediário, **Then** sistema exibe aviso de limite insuficiente (disponível: R$ 200, necessário: R$ 250) e bloqueia a finalização
2. **Given** limite excedido, **When** gerente valida override com PIN, **Then** venda é permitida e uma flag "crédito excedido com autorização" é registrada no pedido
3. **Given** venda no crediário é finalizada com sucesso, **When** sistema confirma, **Then** cria automaticamente um registro de recebível com: cliente, valor, data de vencimento calculada, referência ao pedido/venda
4. **Given** cliente paga parcela do crediário, **When** operador registra baixa do recebível, **Then** limite de crédito do cliente é automaticamente restaurado pelo valor pago
5. **Given** relatório de clientes inadimplentes, **When** admin acessa, **Then** lista clientes com saldo devedor vencido, dias em atraso e valor total em aberto

---

### US006: Histórico de Compras e Cores do Cliente
**Como** vendedor  
**Eu quero** ver o histórico de compras e tintas anteriores de um cliente  
**Para que** eu possa sugerir o produto correto em um retoque

**Acceptance Scenarios:**

1. **Given** cliente selecionado no PDV ou tela de clientes, **When** acessa aba "Histórico", **Then** lista todas as compras com data, produtos, forma de pagamento e valor total — ordenado do mais recente ao mais antigo
2. **Given** compra anterior continha tinta personalizada, **When** vendedor clica no item, **Then** exibe cor, fórmula usada, quantidade, data de produção e referência da mistura para facilitar reordem
3. **Given** vendedor está criando novo pedido e cliente tem histórico, **When** acessa "Reordenar última compra", **Then** sistema pré-carrega os mesmos itens com quantidades e preços atualizados para confirmação

---

### US007: Cancelamento e Devolução de Venda
**Como** gerente  
**Eu quero** cancelar ou processar devoluções de vendas  
**Para que** o cliente seja atendido e o estoque e financeiro fiquem corretos

**Acceptance Scenarios:**

1. **Given** venda finalizada no mesmo dia, **When** gerente acessa a venda e aciona "Cancelar", **Then** sistema exige motivo obrigatório, confirmação de PIN, e processa: estorno do estoque, cancelamento de NFe na SEFAZ (se emitida), cancelamento do recebível de crediário (se aplicável)
2. **Given** venda de dia anterior sendo devolvida, **When** operador cria "Devolução", **Then** sistema gera movimentação de entrada de estoque, cria recebível negativo (crédito para o cliente) e marca venda original como "com devolução"
3. **Given** tentativa de cancelamento de venda com NFe já autorizada, **When** sistema processa, **Then** envia cancelamento para SEFAZ automaticamente se dentro do prazo legal (24h); fora do prazo, exibe aviso e instrução para emitir NF-e de devolução

---

## Scope Boundaries

### In Scope (Spec 6)
- Cadastro completo de clientes PF e PJ com busca inteligente
- API REST de clientes (CRUD + busca + histórico)
- Pedidos de venda: orçamento, aprovação, produção, entrega
- PDV: interface de caixa, múltiplas formas de pagamento, troco
- Controle de desconto com níveis de autorização
- Controle de limite de crédito e crediário (recebíveis básicos)
- Histórico de compras integrado ao histórico de tintometria
- Cancelamento (mesmo dia) e devolução básica
- Integração com baixa automática de estoque (via Spec 4)
- Flag e disparo de fluxo NFe por tipo de cliente (execução via Spec 4 Phase 3)

### Out of Scope (spec separada)
- Emissão técnica de NFe para SEFAZ (Spec 4, Phase 3)
- Conciliação bancária e integração com TEF
- Financeiro completo (contas a pagar, fluxo de caixa, DRE) → Spec 7
- Fornecedores CRUD → Spec 7
- Relatórios BI / Curva ABC → Spec 7
- Entrega com logística / rastreamento → Spec 8

---

## Business Rules Summary

| Regra | Detalhe |
|---|---|
| BR-001 | Venda sem cliente é permitida (balcão anônimo), mas sem NFe e sem crediário |
| BR-002 | Toda venda finalizada gera um `PedidoVenda` + `Venda` atomicamente |
| BR-003 | Estoque é reservado ao aprovar pedido; baixado definitivamente ao finalizar venda |
| BR-004 | Se baixa de estoque falhar, a venda NÃO é confirmada (transação atômica) |
| BR-005 | Desconto ≤ 5%: livre para vendedor; 5–20%: necessita PIN gerencial; > 20%: necessita PIN diretor |
| BR-006 | Cliente PJ com CNPJ válido → flag NFe automática ativa ao finalizar venda |
| BR-007 | Crediário exige cliente cadastrado com limite de crédito definido |
| BR-008 | Cancelamento no mesmo dia: estoque revertido + NFe cancelada na SEFAZ |
| BR-009 | Devolução pós D+0: cria nova movimentação de entrada, não cancela original |
| BR-010 | Log de auditoria é obrigatório para: descontos, overrides de crédito, cancelamentos |
