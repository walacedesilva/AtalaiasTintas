# Feature 4: Sistema Integrado de Controle de Estoque e Emissão de Nota Fiscal Eletrônica

**Status:** ❓ Clarify  
**Priority:** P1 (MVP)  
**Estimated Complexity:** High  
**Business Impact:** Critical

## Clarification Questions & Answers

### Q1: NFe Emission Timing & Automation
**Question:** Should NFe emission be automatic when finalizing a sale, or a separate manual step performed by fiscal operator after sale completion?

**Business Impact:** Defines system architecture, user workflow, and compliance timing.

**Answer:** Semi-automatic approach with business rule flexibility:
- **B2B sales (CNPJ customers):** NFe MUST be emitted automatically when sale is finalized
- **B2C sales (CPF customers):** NFe emission is optional/manual, triggered by fiscal operator when needed  
- **Cash sales without customer data:** No NFe required, only internal receipt
- **System MUST validate:** Customer data completeness before allowing automatic NFe emission
- **Fallback:** If automatic NFe fails, sale is completed but flagged for manual NFe retry

### Q2: Multi-Unit Conversion Rules & Configuration
**Question:** How should the system handle conversions between different units of measure (liters, cans, gallons)? Are conversion rates fixed or configurable per product?

**Business Impact:** Affects inventory accuracy, pricing flexibility, and operational complexity.

**Answer:** Flexible per-product conversion system:
- **Base Unit:** All products have a primary unit (usually liters for liquids)
- **Conversion Ratios:** Configurable per product variant (e.g., 1 can = 3.6L, 1 gallon = 3.785L)
- **Price Independence:** Each unit can have independent pricing (bulk vs. retail)
- **Stock Consolidation:** System maintains inventory in base unit but displays/sells in any configured unit
- **Automatic Conversion:** Sales in any unit automatically convert to base unit for inventory deduction
- **Configuration UI:** Admin can set conversion ratios and enable/disable units per product

### Q3: Insufficient Inventory Behavior & Business Rules  
**Question:** What should happen when a sale attempts to use more inventory than available? Block sale, allow negative inventory, or partial fulfillment?

**Business Impact:** Defines business continuity vs. inventory accuracy priority.

**Answer:** Configurable inventory policy with safety controls:
- **Default Behavior:** Block sale when insufficient inventory with clear error message
- **Override Permission:** Managers can override and allow negative inventory for urgent sales
- **Partial Sales:** System offers partial quantity available and asks user to confirm
- **Reservation System:** Products are reserved during sale composition, released if sale is cancelled  
- **Negative Inventory Alerts:** If negative allowed, daily alerts sent to inventory managers
- **Automatic Reorders:** When inventory hits minimum threshold, system generates purchase suggestions  

## Context & Business Need

Uma loja de tintas necessita de controle rigoroso de estoque integrado com emissão de nota fiscal eletrônica para atender à legislação brasileira e otimizar operações comerciais. O sistema deve automatizar baixas de estoque no momento da venda, garantir conformidade fiscal e fornecer rastreabilidade completa de produtos.

**Pain Points Atuais:**
- Baixa manual de estoque gera inconsistências e atrasos  
- Emissão de NFe desconectada do sistema principal causa retrabalho
- Falta de rastreabilidade entre vendas, estoque e documentos fiscais
- Dificuldade para controlar produtos com diferentes unidades de medida (litros, latas, galões)
- Ausência de alertas automáticos para estoque baixo impacta vendas

## User Stories

### US001: Controle Automático de Estoque na Venda
**Como** vendedor da loja de tintas  
**Eu quero** que o estoque seja baixado automaticamente quando finalizo uma venda  
**Para que** eu não precise fazer baixas manuais e evite inconsistências de estoque

**Scenario:** Venda de tinta com baixa automática
- Vendedor registra venda de 5L de tinta branca  
- Sistema **reserva** 5L durante composição do pedido
- Ao finalizar venda, sistema reduz definitivamente 5L do estoque disponível
- Estoque atualizado fica visível imediatamente para todos os usuários
- Se estoque for insuficiente, sistema **bloqueia** a venda com mensagem clara
- Gerente pode fazer override para permitir venda com estoque negativo  
- Se estoque ficar abaixo do mínimo, sistema gera alerta automático

### US002: Emissão de NFe Integrada com Venda
**Como** operador fiscal  
**Eu quero** emitir NFe diretamente a partir dos dados da venda  
**Para que** eu garanta conformidade fiscal sem retrabalho de digitação

**Scenario:** Emissão de NFe baseada no tipo de cliente
- **Venda B2B (CNPJ):** Sistema automaticamente inicia emissão de NFe ao finalizar venda
- **Venda B2C (CPF):** Operador fiscal pode optar por emitir NFe posteriormente
- **Venda balcão s/doc:** Apenas recibo interno é gerado, sem NFe
- Sistema pré-preenche NFe com dados corretos (produtos, valores, cliente)
- Se emissão automática falhar, venda continua com flag para retry manual
- NFe transmitida para SEFAZ retorna com número oficial  
- PDF da NFe é gerado automaticamente para impressão/envio

### US003: Entrada de Produtos no Estoque  
**Como** operador de estoque  
**Eu quero** registrar entradas de produtos com nota fiscal do fornecedor  
**Para que** eu mantenha controle preciso do que entra no estoque

**Scenario:** Recebimento de mercadorias
- Operador registra chegada de produtos baseado na NF do fornecedor
- Sistema permite entrada por diferentes unidades (litros, latas, galões)
- Produtos são adicionados ao estoque disponível
- Histórico de movimentações é mantido para auditoria

### US004: Controle de Estoque Multi-Unidade
**Como** gerente da loja  
**Eu quero** controlar produtos em diferentes unidades de medida  
**Para que** eu possa vender tanto a granel quanto em embalagens fechadas

**Scenario:** Tinta vendida em diferentes formatos
- Mesmo produto disponível em litros (granel) e latas de 3.6L
- Sistema converte automaticamente entre unidades na baixa
- Relatórios mostram estoque total em unidade base
- Preços podem ser diferentes por unidade de medida

### US005: Rastreabilidade Fiscal-Comercial
**Como** contador da empresa  
**Eu quero** rastrear completamente o ciclo produto → venda → NFe  
**Para que** eu tenha dados precisos para declarações fiscais e auditoria

**Scenario:** Auditoria de movimentação
- Contador consulta produto específico no sistema
- Visualiza histórico completo: entrada → estoque → venda → NFe emitida
- Relatórios fiscais são gerados automaticamente
- Documentos comprobatórios são acessíveis digitalmente

## Functional Requirements

### FR-001: Gestão de Estoque Multi-Unidade Configurável
Sistema MUST manter estoque centralizado com:
- Produtos categorizados por tipo (tintas, vernizes, solventes, pigmentos)
- **Unidade base** configurável por produto (ex: litros para líquidos)
- **Conversões flexíveis** configuráveis por administrador (1 lata = 3.6L configurável)
- **Preços independentes** por unidade (granel vs. embalagem fechada)
- **Consolidação automática** do estoque na unidade base
- **Vendas em qualquer unidade** com conversão automática para baixa
- Controle de lotes e validades para produtos perecíveis  
- Estoque mínimo configurável com alertas automáticos e sugestões de reposição
- Sistema de reservas durante checkout com expiração em 30 minutos
- Histórico completo de movimentações (entrada, saída, ajustes, conversões)

### FR-002: Baixa Automática na Venda com Reservas
Sistema MUST realizar baixa automática quando:
- Produtos são reservados durante composição do pedido (checkout em andamento)
- Venda é finalizada no PDV ou sistema web (baixa definitiva do estoque)  
- Cancelamentos de venda restauram estoque automaticamente
- Devoluções aumentam estoque com status específico
- Sistema bloqueia vendas com estoque insuficiente (configurável por produto)
- Gerentes podem override para permitir estoque negativo em casos excepcionais
- Reservas expiram em 30 minutos se venda não for finalizada

### FR-003: Emissão de NFe Semi-Automática
Sistema MUST permitir emissão de NFe com:
- **B2B (CNPJ):** Emissão automática obrigatória no fechamento da venda
- **B2C (CPF):** Emissão manual opcional pelo operador fiscal
- **Vendas balcão s/documento:** Apenas recibo interno, sem NFe
- Pré-preenchimento automático baseado em dados da venda validados
- Validação de dados obrigatórios antes da transmissão
- Integração com WebService da SEFAZ para envio/consulta  
- Geração de PDF oficial da NFe para impressão
- Fallback: Se emissão automática falhar, venda continua com flag para retry manual
- Armazenamento de XML recebido da SEFAZ

### FR-004: Controle de Entrada de Mercadorias
Sistema MUST permitir registro de entradas com:
- Associação à nota fiscal do fornecedor (chave de acesso)
- Produtos cadastrados ou criação de novos durante entrada
- Diferentes formas de entrada (compra, transferência, ajuste)  
- Validação de quantidades e valores contra NF fornecedor
- Cálculo automático de custos médios ponderados

### FR-005: Relatórios Fiscais e Gerenciais
Sistema MUST gerar relatórios de:
- Livro de Inventário com posição atual do estoque
- Livro de Movimentação com todas as transações
- Relatório de NFe emitidas por período  
- Análise ABC de produtos mais vendidos
- Previsões de reposição baseadas em histórico

### FR-006: Conformidade Fiscal NFe
Sistema MUST garantir conformidade com:
- Layout NFe versão 4.00 ou superior
- Códigos NCM corretos para produtos de tinta
- Cálculos de impostos (ICMS, IPI, PIS, COFINS)
- Contingência offline quando SEFAZ indisponível
- Manifestação do Destinatário para NFe recebidas

## Non-Functional Requirements  

### NFR-001: Performance de Consultas
- Consultas de estoque MUST responder em < 2 segundos
- Emissão de NFe MUST completar em < 30 segundos
- Relatórios de até 1000 registros MUST gerar em < 10 segundos

### NFR-002: Disponibilidade do Sistema
- Sistema MUST ter uptime ≥ 99% durante horário comercial
- Backup automático diário dos dados fiscais e estoque
- Recuperação de desastres em < 4 horas  

### NFR-003: Segurança e Auditoria
- Todas as operações MUST ser logadas com usuário e timestamp
- Certificado A1 ou A3 para assinatura digital das NFe
- Criptografia de dados fiscais sensíveis
- Controle de acesso por perfis (vendedor, estoque, fiscal, gerência)

### NFR-004: Integração e Interoperabilidade  
- API REST para integração com PDV externo
- Importação de NFe fornecedores via XML
- Exportação para sistemas contábeis (formato SPED)
- Sincronização com marketplaces (B2W, Mercado Livre)

### NFR-005: Usabilidade Fiscal
- Interface intuitiva para operadores com pouco conhecimento fiscal
- Validações em tempo real durante preenchimento de NFe  
- Mensagens de erro compreensíveis em português
- Wizard para configuração inicial de parâmetros fiscais

## Acceptance Criteria

### AC-001: Baixa Automática com Controle de Estoque
✅ Venda finalizada reduz estoque imediatamente na unidade base
✅ Produtos são reservados durante checkout e liberados se cancelado  
✅ Sistema **bloqueia venda** quando estoque insuficiente (padrão)
✅ Gerentes podem **override** para permitir estoque negativo excepcionalmente
✅ Cancelamento de venda restaura estoque e remove reservas corretamente  
✅ Alertas diários são enviados quando existir estoque negativo
✅ Histórico mostra todas as movimentações com detalhes de conversão

### AC-002: NFe Semi-Automática por Tipo de Cliente  
✅ **B2B (CNPJ):** NFe é emitida automaticamente no fechamento da venda
✅ **B2C (CPF):** Emissão manual opcional disponível para operador fiscal
✅ **Balcão s/doc:** Apenas recibo interno, sem NFe obrigatória
✅ XML é validado ANTES do envio para SEFAZ  
✅ Se emissão automática falhar, venda continua com flag para retry manual
✅ Numero oficial da NFe é recebido e armazenado  
✅ PDF é gerado e pode ser impresso/enviado por email
✅ Status da NFe é consultável (enviada, autorizada, cancelada)

### AC-003: Controle Multi-Unidade Configurável e Preciso
✅ Administrador pode configurar conversões por produto (1 lata = X litros)
✅ Mesmo produto aceita vendas em diferentes unidades cadastradas
✅ Conversões para unidade base são automáticas e precisas na baixa
✅ Preços são independentes por unidade (granel ≠ lata fechada)  
✅ Relatórios consolidam estoque total na unidade base
✅ Interface administrativa permite habilitar/desabilitar unidades por produto

### AC-004: Rastreabilidade e Configuração Flexível
✅ Qualquer produto pode ser rastreado desde entrada até NFe emitida
✅ Políticas de estoque são configuráveis (bloquear vs. permitir negativo)
✅ Sistema gera sugestões de compra quando atinge estoque mínimo
✅ Relatórios fiscais confirmam conformidade com legislação  
✅ Auditores conseguem validar movimentações e conversões facilmente
✅ Documentos digitais são acessíveis e organizados por período
✅ Histórico é preservado mesmo após exclusões com log de auditoria

## Out of Scope  

❌ **Gestão financeira/contas a receber:** Foco apenas no fiscal e estoque  
❌ **E-commerce próprio:** Integração sim, desenvolvimento não  
❌ **NFCe (cupom fiscal):** Apenas NFe modelo 55  
❌ **Controle de produção:** Sistema para revenda, não manufatura  
❌ **CRM avançado:** Apenas dados básicos de clientes para NFe  
❌ **Múltiplas filiais:** Versão inicial para loja única  

## Success Metrics

### Eficiência Operacional  
- ⏱️ **Tempo de fechamento de venda:** Redução de 40% (de 5 min → 3 min)
- 📊 **Precisão de estoque:** Acurácia ≥ 98% (vs. contagem física)
- 🔄 **Retrabalho fiscal:** Redução de 70% em correções de NFe

### Conformidade Fiscal
- ✅ **NFe aprovadas 1ª transmissão:** ≥ 95% das emissões  
- 📅 **Prazo de emissão NFe:** 100% dentro de 24h da venda
- 🔍 **Auditorias sem pendências:** Zero apontamentos fiscais

### Satisfação do Usuário  
- 😊 **NPS operadores:** Score ≥ 8/10 em usabilidade
- 📚 **Tempo de treinamento:** ≤ 4 horas para novo funcionário  
- 🆘 **Chamados de suporte:** Redução de 50% vs. sistema anterior

### Impacto nos Negócios
- 💰 **Redução de perdas:** Diminuição de 30% em divergências de estoque
- ⚡ **Velocidade de atendimento:** Aumento de 25% em vendas/hora  
- 📈 **Otimização de compras:** Redução de 15% em capital de giro
- 🎯 **Conformidade fiscal:** 100% NFe B2B emitidas automaticamente
- 🔄 **Flexibilidade operacional:** Suporte a múltiplas unidades com conversão automática

---

**Next Phase:** 🏗️ Plan → Definir arquitetura técnica e estrutura de implementação