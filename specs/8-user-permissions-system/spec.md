# Feature Specification: Sistema de Permissões de Usuário para Telas Não-ERP

**Feature Branch**: `8-user-permissions-system`
**Created**: 2026-04-18  
**Status**: Analysis Complete - READY FOR IMPLEMENTATION ✅
**Input**: User description: "Validar para implementar permissões nas telas que não forem do ERP por usuário - sistema de controle de acesso granular para módulos específicos do sistema de tintas"

## Clarification Questions *(Process: Speckit Clarify)*

### Ambiguity 1: Scope Definition - "Non-ERP Screens" 📋
**Question**: Which specific modules/screens are considered "non-ERP" and should be included in this permission system?

**Context**: The system has multiple modules (tintometry, sales, inventory, fiscal, companies, marketplaces, monitoring). The term "non-ERP screens" is ambiguous - traditional ERP includes inventory, sales, and fiscal, but these are core to the paint business.

**Options for Resolution**:
- **Option A**: Exclude only standard business modules (companies, fiscal, inventory) and focus on paint-specific screens (tintometry formulas, color matching, mixing operations)  
- **Option B**: Include all customer-facing and operational screens, exclude only system administration and core HR/financial reporting
- **Option C**: Define by business risk - include any screen where unauthorized access could impact product quality or reveal strategic information

**Impact**: Defines the scope of implementation and affects security model complexity.

---

### Ambiguity 2: Integration Approach with Existing Permissions 🔗
**Question**: How should this system integrate with the existing User model permissions (`pode_vender`, `pode_gerenciar_estoque`, `pode_acessar_financeiro`, `pode_administrar`)?

**Context**: The current `User` model already has basic boolean permission fields that provide coarse-grained access control. The specification calls for more granular permissions.

**Options for Resolution**:
- **Option A**: Extend existing model - Add new granular fields while maintaining backward compatibility with existing boolean fields
- **Option B**: Hierarchical approach - Use existing booleans as "master switches" and add granular sub-permissions underneath 
- **Option C**: Replace system - Migrate to new role-based system and deprecate existing boolean fields over time
- **Option D**: Parallel system - Create entirely separate permission system for non-ERP screens only

**Impact**: Determines technical architecture, migration complexity, and system consistency.

---

### Ambiguity 3: Permission Granularity Requirements 🎯  
**Question**: What level of granularity is needed for permission control?

**Context**: The specification mentions "screen/module level" but also references specific actions (view, edit, create, delete, approve). Current system uses very coarse boolean permissions.

**Options for Resolution**:
- **Option A**: Module-level only - Permissions like "tintometry_access", "sales_access" (coarser, simpler to manage)
- **Option B**: Screen-level - Permissions for each major screen/view like "formula_management", "color_matching", "label_generation" 
- **Option C**: Action-level - Granular permissions like "formula.view", "formula.edit", "formula.approve", "discount.approve" (finest control)
- **Option D**: Hybrid approach - Module access + action restrictions for critical functions (balance complexity vs control)

**Impact**: Affects user experience, administrative overhead, and system performance.

## Resolution Assumptions *(Proceeding with best practices)*

*To proceed with planning, these assumptions will be used unless clarified otherwise:*

**Assumption 1 (Scope)**: Non-ERP screens include tintometry (formulas, mixing, color matching), label generation, and advanced sales features (discount approvals, margin reports). Standard ERP (companies, basic inventory, fiscal) remains under existing permissions.

**Assumption 2 (Integration)**: Hierarchical approach - Keep existing boolean fields as section-level controls, add granular sub-permissions for specific actions within allowed sections. Ensures backward compatibility.

**Assumption 3 (Granularity)**: Hybrid approach - Module access permissions + action-level restrictions for critical functions (formula editing, financial data access, system configuration). Balances security with usability.

## Problem Statement *(mandatory)*

O sistema atual não possui controle granular de permissões para telas e funcionalidades específicas do sistema de tintas que estão fora do escopo tradicional de ERP:
- Todos os usuários têm acesso irrestrito a funcionalidades críticas como configuração tintométrica, gestão de fórmulas e relatórios financeiros
- Não há diferenciação de níveis de acesso entre vendedores, mixadores, supervisores e administradores em funcionalidades específicas do negócio de tintas
- Falta auditoria de quem executa ações sensíveis como alteração de fórmulas, aprovação de descontos ou acesso a dados de margem
- Impossibilidade de restringir acesso a telas de configuração que podem comprometer a operação se alteradas incorretamente
- Ausência de delegação temporária de permissões para cobertura de turnos ou situações específicas
- Não há proteção contra acesso simultâneo a funcionalidades que podem gerar conflitos (ex: dois mixadores alterando a mesma fórmula)

## Business Value *(mandatory)*

- **Segurança operacional**: Controle de acesso reduz risco de alterações acidentais em configurações críticas do sistema tintométrico
- **Compliance e auditoria**: Rastreabilidade de ações por usuário atende requisitos de auditoria interna e externa
- **Produtividade**: Usuários veem apenas funcionalidades relevantes ao seu papel, reduzindo confusão e tempo de navegação
- **Controle de qualidade**: Restrição de acesso a fórmulas e configurações garante que apenas mixadores certificados façam alterações
- **Gestão de custos**: Controle de acesso a informações de margem e precificação protege dados estratégicos do negócio
- **Flexibilidade operacional**: Sistema de delegação permite cobertura eficiente de turnos e situações emergenciais

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Controle de Acesso por Função (Priority: P1)

Como administrador do sistema, preciso definir que apenas mixadores certificados possam alterar fórmulas tintométricas, enquanto vendedores só possam visualizar informações básicas de produtos.

**Why this priority**: Segurança das fórmulas é crítica para qualidade dos produtos e proteção do conhecimento técnico da empresa.

**Independent Test**: Pode ser testado criando usuários com diferentes perfis e verificando se conseguem acessar apenas as funcionalidades permitidas.

**Acceptance Scenarios**:
1. **Given** usuário com perfil "Vendedor", **When** tenta acessar tela de edição de fórmulas, **Then** sistema nega acesso e registra tentativa no log de auditoria
2. **Given** usuário com perfil "Mixador Certificado", **When** acessa tela de fórmulas, **Then** pode visualizar e editar fórmulas dentro do seu escopo de certificação
3. **Given** usuário com perfil "Supervisor", **When** acessa relatórios de margem, **Then** visualiza informações completas com dados financeiros detalhados
4. **Given** usuário sem permissão específica, **When** tenta executar ação restrita, **Then** recebe mensagem clara sobre limitação de acesso e processo para solicitar permissão

---

### User Story 2 - Auditoria e Rastreabilidade (Priority: P1)

Como supervisor de qualidade, preciso saber exatamente quem alterou uma fórmula específica, quando foi alterada e qual era o estado anterior para investigar problemas de qualidade.

**Why this priority**: Rastreabilidade é essencial para controle de qualidade e resolução de problemas técnicos.

**Independent Test**: Pode ser testado executando alterações com usuários diferentes e verificando se todas as ações ficam registradas com detalhes completos.

**Acceptance Scenarios**:
1. **Given** mixador altera fórmula de tinta, **When** supervisor consulta histórico da fórmula, **Then** visualiza timestamp, usuário responsável, alterações específicas e justificativa
2. **Given** tentativa de acesso não autorizado, **When** administrador consulta logs de segurança, **Then** encontra registro detalhado da tentativa incluindo usuário, IP e timestamp
3. **Given** alteração crítica em configuração, **When** sistema detecta mudança, **Then** envia notificação automática para supervisores responsáveis
4. **Given** necessidade de auditoria externa, **When** relatório é gerado, **Then** inclui todas as alterações com assinatura digital para verificação de integridade

---

### User Story 3 - Delegação Temporária de Permissões (Priority: P2)

Como supervisor de turno, preciso delegar temporariamente permissões de aprovação de descontos para um vendedor sênior durante minha ausência, com prazo definido e escopo limitado.

**Why this priority**: Flexibilidade operacional é importante para continuidade do negócio em situações de ausência de supervisores.

**Independent Test**: Pode ser testado criando delegações com diferentes prazos e escopos, verificando ativação, funcionamento e expiração automática.

**Acceptance Scenarios**:
1. **Given** supervisor cria delegação com prazo de 4 horas, **When** prazo expira, **Then** permissões delegadas são automaticamente removidas
2. **Given** delegação ativa para aprovação de descontos até R$ 500, **When** vendedor tenta aprovar desconto de R$ 800, **Then** sistema nega e solicita aprovação de nível superior
3. **Given** múltiplas delegações ativas, **When** supervisor consulta status, **Then** visualiza todas as delegações com prazos, escopos e uso atual
4. **Given** emergência operacional, **When** administrador precisa revogar delegação imediatamente, **Then** revogação é efetivada instantaneamente com notificação ao usuário

---

### User Story 4 - Gestão de Perfis e Grupos (Priority: P2)

Como administrador de TI, preciso criar e gerenciar grupos de usuários com permissões padronizadas para diferentes funções, permitindo fácil adição/remoção de usuários sem configurar permissões individuais.

**Why this priority**: Eficiência administrativa e padronização de acessos reduz erros e facilita gestão de usuários.

**Independent Test**: Pode ser testado criando grupos, atribuindo permissões, adicionando usuários e validando herança correta de permissões.

**Acceptance Scenarios**:
1. **Given** novo funcionário contratado para vendas, **When** é adicionado ao grupo "Vendedores", **Then** automaticamente herda todas as permissões padrão do grupo
2. **Given** mudança de função de funcionário, **When** é movido de "Vendedores" para "Mixadores", **Then** permissões são atualizadas automaticamente conforme novo grupo
3. **Given** criação de novo grupo "Estagiários", **When** são definidas permissões limitadas, **Then** usuários do grupo têm acesso restrito conforme configuração
4. **Given** alteração em permissões de grupo, **When** mudança é aplicada, **Then** todos os usuários membros são notificados sobre as alterações

---

### User Story 5 - Interface de Gestão de Permissões (Priority: P2)

Como administrador, preciso de uma interface intuitiva para visualizar, editar e auditar permissões de usuários e grupos, com busca eficiente e relatórios de acesso.

**Why this priority**: Interface clara facilita gestão correta de permissões e reduz erros administrativos.

**Independent Test**: Pode ser testado através de tarefas administrativas comuns medindo tempo de execução e taxa de erros.

**Acceptance Scenarios**:
1. **Given** necessidade de revisar permissões de usuário específico, **When** administrador busca por nome/email, **Then** visualiza resumo completo de permissões diretas e herdadas
2. **Given** auditoria de acessos mensual, **When** relatório é gerado, **Then** inclui estatísticas de uso, tentativas negadas e alterações de permissões
3. **Given** necessidade de permissão emergencial, **When** administrador concede acesso temporário, **Then** processo é completado em menos de 3 cliques
4. **Given** revisão de segurança, **When** são identificadas permissões não utilizadas, **Then** sistema sugere remoção com impacto detalhado

## Functional Requirements *(mandatory)*

### FR-001: Sistema de Autenticação e Autorização
- Sistema deve validar identidade do usuário através de login/senha ou integração existente
- Permissões devem ser verificadas a cada acesso a funcionalidade protegida
- Sessões devem expirar automaticamente após período de inatividade configurável
- Sistema deve suportar logout forçado de usuários específicos

### FR-002: Definição de Perfis e Grupos
- Administrador pode criar perfis de usuário personalizados (Vendedor, Mixador, Supervisor, etc.)
- Grupos podem herdar permissões de outros grupos (hierarquia)
- Usuários podem pertencer a múltiplos grupos com união de permissões
- Alterações em grupos devem ser aplicadas automaticamente aos membros

### FR-003: Controle Granular de Funcionalidades
- Permissões devem ser definidas por tela/módulo específico do sistema de tintas
- Controle deve incluir ações específicas: visualizar, editar, criar, excluir, aprovar
- Sistema deve proteger APIs e endpoints utilizados pelas telas
- Permissões devem ser aplicadas tanto na interface quanto no backend

### FR-004: Delegação Temporária
- Usuários autorizados podem delegar permissões temporariamente
- Delegações devem ter prazo de expiração obrigatório (máximo configurável pelo admin)
- Escopo da delegação deve ser limitável (funcionalidades específicas, valores máximos)
- Delegações podem ser revogadas a qualquer momento pelo delegante ou administrador

### FR-005: Log de Auditoria Completo
- Todas as ações devem ser registradas: acessos, alterações, tentativas negadas
- Logs devem incluir: usuário, timestamp, IP, ação executada, dados alterados
- Alterações críticas devem gerar notificações automáticas
- Logs devem ser protegidos contra alteração/exclusão por usuários não autorizados

### FR-006: Interface Administrativa
- Tela para gestão de usuários, grupos e permissões
- Busca e filtros eficientes para localizar informações
- Visualização hierárquica de permissões (diretas vs herdadas)
- Relatórios de uso e auditoria com exportação

### FR-007: Integração com Sistema Existente
- Aproveitamento da base de usuários atual quando possível
- Compatibilidade com sistema de autenticação existente
- Migração suave sem impacto nas operações atuais
- Sincronização com mudanças no sistema de RH/folha de pagamento

## Non-Functional Requirements *(mandatory)*

### NFR-001: Performance
- Verificação de permissões deve ser executada em menos de 100ms
- Interface de gestão deve carregar lista de usuários em menos de 2 segundos
- Sistema deve suportar até 200 usuários simultâneos sem degradação
- Cache de permissões deve ser atualizado em tempo real

### NFR-002: Segurança
- Senhas devem atender critérios mínimos de complexidade
- Tentativas de acesso não autorizado devem ser bloqueadas após 5 tentativas
- Comunicação deve usar HTTPS com certificação válida
- Dados sensíveis devem ser criptografados no banco de dados

### NFR-003: Disponibilidade
- Sistema de permissões deve ter 99.5% de uptime durante horário comercial
- Falhas no sistema de permissões não devem bloquear funcionalidades críticas de emergência
- Backup automático diário dos dados de permissões
- Recuperação de falhas deve ser possível em menos de 30 minutos

### NFR-004: Usabilidade
- Interface deve seguir padrões de design do sistema principal
- Processo de concessão de permissão emergencial deve ser completável em menos de 3 minutos
- Mensagens de erro devem ser claras e orientar próximos passos
- Sistema deve funcionar nos mesmos navegadores suportados pelo sistema principal

### NFR-005: Manutenibilidade
- Configurações de permissões devem ser exportáveis/importáveis
- Sistema deve permitir simulação de permissões para testes
- Documentação técnica deve ser mantida atualizada automaticamente
- Logs devem ser estruturados para facilitar análise automatizada

### NFR-006: Compliance
- Logs de auditoria devem ser preservados por no mínimo 5 anos
- Sistema deve permitir export de dados para auditoria externa
- Alterações em configurações críticas devem requerer aprovação dupla
- Acesso a dados pessoais deve seguir regulamentações de privacidade aplicáveis

## Success Criteria *(mandatory)*

### Critério 1: Segurança Operacional
- **Métrica**: 0 incidentes de segurança relacionados a acessos indevidos após implementação
- **Validação**: Auditoria mensal dos logs de acesso e relatório de tentativas bloqueadas
- **Prazo**: Avaliação após 3 meses de operação

### Critério 2: Redução de Erros Operacionais
- **Métrica**: 50% de redução em alterações não autorizadas em fórmulas e configurações críticas
- **Validação**: Comparação de incidentes registrados antes/depois da implementação
- **Prazo**: Avaliação após 6 meses de operação

### Critério 3: Eficiência Administrativa
- **Métrica**: Gestão de permissões de novos usuários deve levar menos de 10 minutos
- **Validação**: Cronometragem de processos administrativos comuns
- **Prazo**: Validação imediata após go-live

### Critério 4: Aceitação dos Usuários
- **Métrica**: 90% dos usuários consideram o sistema de permissões claro e não intrusivo
- **Validação**: Pesquisa de satisfação após 1 mês de uso
- **Prazo**: 30 dias após implementação

### Critério 5: Performance do Sistema
- **Métrica**: Impacto de menos de 10% na performance das telas protegidas
- **Validação**: Testes de performance antes/depois da implementação
- **Prazo**: Validação durante fase de testes

## Out of Scope *(optional)*

- Integração com sistemas de terceiros fora do ambiente atual
- Single Sign-On (SSO) com provedores externos (pode ser adicionado posteriormente)
- Controle de permissões em nível de campo individual dentro das telas
- Sistema de workflow aprovação multi-nível para alterações (versão futura)
- Mobile app específico para gestão de permissões (será using interface web responsiva)
- Integração com biometria ou autenticação de dois fatores (versão futura)

## Assumptions & Dependencies *(optional)*

### Assumptions
- Sistema atual de autenticação permanecerá funcional durante implementação
- Usuários atuais manterão seus logins e senhas existentes
- Estrutura organizacional da empresa permanecerá estável durante implementação
- Administradores do sistema terão disponibilidade para configurações iniciais

### Dependencies  
- Base de dados de usuários atual deve estar limpa e atualizada
- Definição clara das funções e responsabilidades por parte do RH
- Aprovação da diretoria para definições de níveis de acesso a informações financeiras
- Treinamento da equipe de TI para administração do novo sistema