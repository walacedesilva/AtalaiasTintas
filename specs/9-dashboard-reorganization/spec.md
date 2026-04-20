# Feature Specification: Dashboard Interface Reorganization for Business Operations Focus

**Feature Branch**: `9-dashboard-reorganization`  
**Created**: 2026-04-19  
**Status**: Specification Complete - READY FOR CLARIFICATION  
**Input**: User requirement to reorganize dashboard from tintometry-focused to business operations-focused interface

## Problem Statement

O dashboard atual do sistema Atalaia Tintas está focado exclusivamente em operações tintométricas (Nova mistura, Gerar Etiqueta, Catálogo de cores), não refletindo as necessidades operacionais do negócio como um todo. Esta abordagem resulta em:

- **Falta de visibilidade do negócio**: Usuários não têm acesso rápido a informações críticas como vendas, pedidos, situação fiscal e relatórios gerenciais no ponto central do sistema
- **Desalinhamento entre usuários e funcionalidades**: Vendedores, gestores e operadores fiscais precisam navegar por menus secundários para acessar suas funções principais
- **Redução da produtividade**: Tempo perdido navegando para encontrar funcionalidades essenciais que deveriam estar na tela principal
- **Interface specialist vs. generalista**: Dashboard atual atende apenas mixadores/técnicos tintométricos, ignorando outros perfis de usuário do sistema
- **Baixo aproveitamento do espaço premium**: A área mais visível e acessível do sistema (dashboard) não está sendo utilizada para as funcionalidades de maior impacto no negócio

## Business Value

- **Eficiência operacional**: Acesso imediato às funções mais utilizadas (vendas, pedidos, fiscal) reduz tempo de navegação e aumenta produtividade
- **Visibilidade gerencial**: Dashboard focado em métricas de negócio (vendas, situação fiscal, relatórios) permite tomada de decisão mais rápida
- **Experiência do usuário melhorada**: Interface alinhada com o papel de cada usuário aumenta satisfação e reduz curva de aprendizado
- **Controle operacional centralizado**: Monitoramento de processos críticos (status fiscal, pedidos pendentes, performance de vendas) em local de fácil acesso
- **Redução de erros**: Acesso direto às funcionalidades principais reduz navegação desnecessária que pode levar a erros de processo
- **Flexibilidade de perfis**: Sistema atende melhor diferentes tipos de usuário (vendedores, gestores, operadores fiscais) sem prejudicar especialistas tintométricos

## User Scenarios & Testing

### User Story 1 - Acesso Rápido a Vendas e Pedidos (Priority: P1)

Como vendedor ou gestor de vendas, preciso acessar rapidamente as funcionalidades de vendas e gerenciamento de pedidos a partir da tela principal do sistema.

**Why this priority**: Vendas são a atividade principal do negócio e devem ter acesso prioritário no dashboard.

**Independent Test**: Pode ser testado verificando se os links de Vendas e Pedidos estão visíveis e funcionais na tela principal após login.

**Acceptance Scenarios**:
1. **Given** usuário com perfil de vendedor logado no sistema, **When** acessa o dashboard, **Then** visualiza ação rápida "Vendas" com acesso direto ao módulo de vendas
2. **Given** gestor de vendas no dashboard, **When** clica na ação "Pedidos", **Then** é direcionado para a tela de gerenciamento de pedidos
3. **Given** usuário no dashboard, **When** visualiza métricas de vendas/pedidos, **Then** pode clicar e ser direcionado para detalhamento completo
4. **Given** vendedor precisando registrar nova venda, **When** acessa dashboard, **Then** pode iniciar processo de venda sem navegar por menus secundários

### User Story 2 - Controle Fiscal e Compliance (Priority: P1)

Como operador fiscal ou gestor administrativo, preciso acessar rapidamente as funcionalidades fiscais/NFe e ter visibilidade do status de compliance fiscal.

**Why this priority**: Questões fiscais são críticas para operação legal do negócio e requerem monitoramento constante.

**Independent Test**: Pode ser testado verificando acesso ao módulo fiscal e exibição de métricas fiscais no dashboard.

**Acceptance Scenarios**:
1. **Given** operador fiscal no dashboard, **When** precisa emitir ou consultar NFe, **Then** tem acesso direto via ação rápida "Fiscal/NFe"
2. **Given** gestor no dashboard, **When** visualiza métricas fiscais, **Then** pode identificar rapidamente pendências ou problemas de compliance
3. **Given** usuário autorizado no dashboard, **When** clica em ação fiscal, **Then** é direcionado para interface de controle fiscal sem etapas intermediárias
4. **Given** dashboard exibindo status fiscal, **When** há alertas ou pendências, **Then** são destacados visualmente com ações corretivas sugeridas

### User Story 3 - Relatórios e Monitoramento Executivo (Priority: P2)

Como gestor ou administrador, preciso acessar relatórios gerenciais e funcionalidades de monitoramento diretamente do dashboard para acompanhar performance do negócio.

**Why this priority**: Informações gerenciais são essenciais para tomada de decisão, mas podem ser prioridade secundária após operações críticas.

**Independent Test**: Pode ser testado verificando presença e funcionalidade dos links de Relatórios e Monitoramento no dashboard.

**Acceptance Scenarios**:
1. **Given** gestor no dashboard, **When** precisa de relatórios gerenciais, **Then** tem acesso direto via ação rápida "Relatórios"
2. **Given** administrador no dashboard, **When** acessa "Monitoramento", **Then** é direcionado para dashboard de sistema com métricas técnicas
3. **Given** usuário visualizando métricas no dashboard, **When** clica em gráficos ou números, **Then** pode acessar relatórios detalhados
4. **Given** dashboard com dados de performance, **When** há anomalias ou alertas, **Then** são destacados com links para análise detalhada

### User Story 4 - Preservação de Acesso ao Controle de Estoque (Priority: P1)

Como mixador, técnico ou gestor de estoque, preciso manter o acesso rápido ao controle de estoque que já existe no dashboard atual.

**Why this priority**: Controle de estoque é funcionalidade crítica já estabelecida que deve ser preservada na reorganização.

**Independent Test**: Pode ser testado verificando que a ação "Controle de Estoque" permanece acessível e funcional no novo layout.

**Acceptance Scenarios**:
1. **Given** usuário técnico no dashboard reorganizado, **When** precisa acessar controle de estoque, **Then** a funcionalidade permanece disponível como ação rápida
2. **Given** dashboard com nova organização, **When** usuário clica em "Controle de Estoque", **Then** mantém o mesmo comportamento e destino da versão atual
3. **Given** alertas de estoque baixo no dashboard, **When** usuário clica nos alertas, **Then** é direcionado para controle de estoque como atualmente
4. **Given** métricas de estoque no dashboard, **When** usuário interage com os dados, **Then** tem acesso às mesmas funcionalidades de gestão de estoque

### User Story 5 - Remoção de Funcionalidades Tintométricas Específicas (Priority: P2)

Como usuário geral do sistema, não devo ver funcionalidades altamente especializadas (Nova Mistura, Gerar Etiqueta, Catálogo de Cores) como ações principais do dashboard, pois são específicas para perfis técnicos.

**Why this priority**: Limpeza da interface para melhor UX, mas não impacta funcionalidades críticas de negócio.

**Independent Test**: Pode ser testado verificando que as ações removidas não aparecem mais no dashboard, mas continuam acessíveis via navegação secundária.

**Acceptance Scenarios**:
1. **Given** dashboard reorganizado, **When** usuário visualiza ações rápidas, **Then** não vê mais "Nova Mistura", "Gerar Etiqueta", "Catálogo de Cores"
2. **Given** usuário técnico que precisa dessas funcionalidades, **When** navega pelo menu principal, **Then** ainda consegue acessar as funcionalidades removidas do dashboard
3. **Given** dashboard mais limpo, **When** novos usuários acessam o sistema, **Then** foco está em funcionalidades de negócio, não em operações técnicas específicas
4. **Given** métricas do dashboard, **When** exibidas, **Then** priorizam dados de vendas, fiscal e operacionais em vez de estatísticas puramente tintométricas

## Detailed Requirements

### Dashboard Quick Actions - New Structure

**Actions to ADD:**
- **Vendas** (Sales) - Direct access to sales module with sales interface/POS
- **Pedidos** (Orders) - Order management and tracking interface  
- **Fiscal/NFe** (Tax/Invoice) - Tax document emission and fiscal compliance tools
- **Relatórios** (Reports) - Business intelligence and management reports
- **Monitoramento** (Monitoring) - System and business process monitoring dashboard

**Actions to KEEP:**
- **Controle de Estoque** (Inventory Control) - Maintains current pigment/inventory management functionality

**Actions to REMOVE:**
- **Nova Mistura** (New Mixture) - Move to secondary navigation (still accessible via menu)
- **Gerar Etiqueta** (Generate Label) - Move to secondary navigation (still accessible via menu)
- **Catálogo de Cores** (Color Catalog) - Move to secondary navigation (still accessible via menu)

### Dashboard Metrics - Enhanced Business Focus

**Current metrics to ENHANCE:**
- Maintain inventory alerts but add business context (impact on sales, fiscal implications)
- Keep low stock warnings but integrate with sales forecasting

**New metrics to ADD:**
- Daily/monthly sales performance and trends
- Pending orders count and aging analysis  
- Fiscal compliance status (NFe pending, tax obligations)
- System performance indicators (uptime, response times)
- Business KPIs relevant to operations team

### User Experience Requirements

**Progressive Disclosure:**
- Dashboard shows overview and quick access to main business functions
- Specialized functions (tintometry) accessible via navigation but not prominent on main screen
- Context-sensitive help for new dashboard organization

**Performance Requirements:**
- Dashboard load time must remain under 2 seconds on 3G connection
- All quick action links must respond within 1 second
- Metrics refresh automatically every 30 seconds without full page reload

**Accessibility Requirements:**
- All new dashboard elements must meet WCAG 2.1 AA standards
- Quick actions must be keyboard navigable
- Screen reader compatible labels for all new interface elements

**Responsive Design:**
- Dashboard reorganization must work on mobile devices (responsive grid)
- Quick actions must be touch-friendly on tablets
- Maintain visual hierarchy on different screen sizes

This reorganization transforms the dashboard from a tintometry-specialist interface to a business-operations-focused interface while preserving access to technical functions through secondary navigation. The change improves workflow for the majority of users while maintaining full functionality for specialists.