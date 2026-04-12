# Feature Specification: Sistema de Mistura de Tintas Tintométrica

**Feature Branch**: `1-tintometric-mixing`
**Created**: 2026-04-11
**Status**: Draft
**Input**: User description: "Sistema de mistura de tintas tintométrica para cálculo de fórmulas e dispensação automática de pigmentos"

## Problem Statement *(mandatory)*

Atualmente, lojas de tintas enfrentam desafios significativos na preparação de tintas customizadas:
- Cálculos manuais de fórmulas resultam em inconsistências e desperdício de até 20% dos pigmentos
- Tempo excessivo na preparação (15-30 minutos por mistura) impacta produtividade e experiência do cliente
- Falta de controle preciso do estoque de pigmentos causa rupturas não detectadas
- Histórico de cores personalizadas se perde, dificultando retoques posteriores
- Margem de lucro reduzida devido a imprecisão na dosagem e custos não controlados

## Business Value *(mandatory)*

- **Precisão financeira**: Controle exato de custos por mistura com rastreamento automático de insumos consumidos
- **Eficiência operacional**: Redução de 70% no tempo de preparação de tintas customizadas
- **Satisfação do cliente**: Reprodução exata de cores em retoques futuros através de histórico preservado
- **Otimização do estoque**: Prevenção de rupturas com alertas automáticos baseados no consumo real de pigmentos
- **Aumento da margem**: Eliminação de desperdícios e cobrança precisa baseada no custo real dos componentes

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Calcular Fórmula de Tinta (Priority: P1)

Um funcionário recebe um cliente que deseja 3.6L de tinta na cor "Azul Royal" e precisa calcular a quantidade exata de cada pigmento necessário.

**Why this priority**: É a funcionalidade core que viabiliza todo o processo de mistura controlada e representa 80% dos casos de uso diários.

**Independent Test**: Pode ser testado fornecendo uma cor padrão e quantidade desejada, verificando se o sistema retorna lista precisa de pigmentos com quantidades em ML.

**Acceptance Scenarios**:
1. **Given** uma cor registrada no sistema e quantidade desejada, **When** funcionário seleciona "calcular fórmula", **Then** sistema exibe lista de pigmentos necessários com quantidades exatas em ML
2. **Given** quantidade insuficiente de algum pigmento em estoque, **When** cálculo é solicitado, **Then** sistema alerta sobre disponibilidade e sugere alternativas

---

### User Story 2 - Registrar Baixa Automática de Estoque (Priority: P1) 

Após confirmar uma mistura, o sistema deve automaticamente reduzir as quantidades de pigmentos e base do estoque.

**Why this priority**: Essencial para manter controle financeiro e evitar rupturas não detectadas.

**Independent Test**: Pode ser testado registrando uma mistura e verificando se os saldos de estoque foram atualizados corretamente.

**Acceptance Scenarios**:
1. **Given** mistura confirmada, **When** sistema processa baixa, **Then** estoque de cada pigmento é reduzido pela quantidade exata usada
2. **Given** múltiplas misturas simultâneas, **When** baixas são processadas, **Then** sistema mantém consistência sem conflitos de saldo

---

### User Story 3 - Preservar Histórico de Cores por Cliente (Priority: P2)

Cliente retorna após 6 meses para retoque e funcionário precisa reproduzir exatamente a mesma cor anteriormente preparada.

**Why this priority**: Diferencial competitivo importante que gera fidelização e reduz retrabalho.

**Independent Test**: Pode ser testado criando um histórico para um cliente, depois buscando e reproduzindo a cor exata.

**Acceptance Scenarios**:
1. **Given** cliente com histórico de cores, **When** funcionário busca por nome/telefone, **Then** sistema exibe cores anteriores com data e observações
2. **Given** seleção de cor do histórico, **When** funcionário escolhe reproduzir, **Then** sistema carrega automaticamente a fórmula original

---

### User Story 4 - Gerar Etiquetas de Identificação (Priority: P3)

Para cada mistura preparada, gerar etiqueta com código da cor, data, cliente e composição para colagem no recipiente.

**Why this priority**: Importante para rastreabilidade mas não crítico para operação básica.

**Independent Test**: Pode ser testado criando uma mistura e verificando se etiqueta é gerada com informações corretas.

**Acceptance Scenarios**:
1. **Given** mistura concluída, **When** funcionário solicita etiqueta, **Then** sistema gera código único e imprime etiqueta com dados da mistura

### Edge Cases

- **Pigmento indisponível**: Como sistema se comporta quando pigmento necessário está zerado no estoque?
- **Fórmulas incompletas**: Como proceder quando não existe fórmula registrada para uma cor solicitada?
- **Quantidades mínimas**: Como sistema trata solicitações abaixo da quantidade mínima preparável (ex: menos que 100ml)?
- **Múltiplas lojas**: Como sincronizar fórmulas entre diferentes pontos de venda da mesma rede?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema MUST calcular quantidade exata de cada pigmento necessário baseado na fórmula da cor e quantidade solicitada
- **FR-002**: Sistema MUST validar disponibilidade de estoque antes de confirmar possibilidade de preparação
- **FR-003**: Sistema MUST registrar baixa automática no estoque de todos os componentes após confirmação da mistura  
- **FR-004**: Sistema MUST preservar histórico de todas as cores preparadas por cliente com data e observações
- **FR-005**: Sistema MUST permitir busca de cores anteriores por dados do cliente
- **FR-006**: Sistema MUST calcular custo exato de cada mistura incluindo base e todos os pigmentos
- **FR-007**: Sistema MUST alertar quando estoque de qualquer pigmento atingir nível mínimo configurado
- **FR-008**: Sistema MUST permitir cadastro e edição de novas fórmulas de cores
- **FR-009**: Sistema MUST gerar código único para cada mistura realizada para rastreabilidade

### Key Entities *(include if feature involves data)*

- **Fórmula**: Define proporção de pigmentos para uma cor específica, incluindo base recomendada e rendimento
- **Pigmento**: Insumo colorante com controle de estoque, custo e fornecedor
- **Mistura**: Registro de execução de uma fórmula, incluindo cliente, data, quantidades e custo final
- **Cliente**: Pessoa/empresa com histórico de cores preparadas e preferências
- **Cor**: Referência padronizada (RAL, Pantone) ou personalizada com fórmula associada

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Funcionário consegue calcular fórmula completa para qualquer cor cadastrada em menos de 30 segundos
- **SC-002**: Sistema mantém precisão de 99.5% no controle de estoque comparado com contagem física
- **SC-003**: 95% das cores anteriores podem ser reproduzidas exatamente usando o histórico preservado
- **SC-004**: Tempo médio de preparação de tintas personalizadas reduz em 70% comparado ao processo manual
- **SC-005**: Zero rupturas não detectadas de pigmentos através de alertas automáticos

## Integration Tests *(mandatory)*

- **IT-001**: End-to-end: Seleção de cor → Cálculo de fórmula → Verificação de estoque → Confirmação → Baixa automática → Registro no histórico
- **IT-002**: Busca de cliente com histórico → Seleção de cor anterior → Reprodução de fórmula → Nova mistura idêntica  
- **IT-003**: Múltiplas misturas simultâneas → Baixas paralelas de estoque → Validação de consistência final
- **IT-004**: Esgotamento de pigmento → Tentativa de nova mistura → Bloqueio adequado com sugestão de alternativas
- **IT-005**: Cadastro de nova fórmula → Primeira utilização → Cálculo preciso → Baixa correta de componentes

## Acceptance Criteria *(mandatory)*

1. **Cálculos precisos**: Todas as quantidades de pigmentos são calculadas com precisão de 0,1 ML baseado nas fórmulas cadastradas
2. **Controle de estoque**: Saldos são atualizados instantaneamente após cada mistura sem inconsistências
3. **Rastreabilidade completa**: Cada mistura pode ser rastreada desde a origem dos insumos até o cliente final
4. **Histórico confiável**: Cores reproduzidas a partir do histórico resultam em tonalidade idêntica à original
5. **Alertas funcionais**: Sistema detecta e alerta sobre indisponibilidade antes que impeça atendimento ao cliente
6. **Performance adequada**: Todas as operações de cálculo e consulta respondem em menos de 2 segundos
7. **Integração transparente**: Funcionalidade integra com módulo de estoque existente sem duplicar informações