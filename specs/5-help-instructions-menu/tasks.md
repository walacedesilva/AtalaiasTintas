# Tarefas: Menu de Instruções de Uso

**Feature**: `5-help-instructions-menu`  
**Depende de**: spec.md ✅, plan.md ✅  
**Fase**: tasks  

---

## Resumo de Implementação

**Total de Tarefas**: 23  
**Estimativa Total**: 2-3 semanas  
**Fases**: Setup → Dados → Componentes → Integração → Polish  

### Distribuição por Prioridade
- **P1 (MVP)**: 12 tarefas - Sistema funcional com ajuda contextual
- **P2 (Importante)**: 8 tarefas - UX melhorada e responsividade
- **P3 (Melhorias)**: 3 tarefas - Refinamentos e otimizações

---

## Fase 1: Setup e Fundação (Semana 1)

### [T001] Criar Estrutura de Arquivos [P1] [US1]
**Descrição**: Criar estrutura base de diretórios e arquivos para o sistema de ajuda  
**Arquivos**:
- `frontend/src/components/help/` (diretório)  
- `frontend/src/providers/HelpProvider.tsx` (esqueleto)
- `frontend/src/hooks/useHelp.ts` (esqueleto)
- `frontend/src/components/help/helpData.ts` (esqueleto)

**Critérios de Aceite**:
- [x] Diretório `help/` criado com estrutura prevista
- [x] Arquivos TypeScript base com exports mínimos
- [x] Imports funcionando sem erros de compilação
- [x] Estrutura alinhada com plano arquitetural

**Dependências**: Nenhuma  
**Estimativa**: 0.5 dia  

---

### [T002] Definir Interfaces TypeScript [P1] [US1,US2,US3] 
**Descrição**: Criar tipagem TypeScript para dados de instruções e contexto  
**Arquivo**: `frontend/src/components/help/helpData.ts`

**Interfaces a Criar**:
```typescript
interface HelpStep { 
  text: string; 
  highlighted?: boolean; 
}
interface HelpAction { 
  title: string; 
  steps: HelpStep[]; 
}
interface ScreenHelp {
  route: string;
  label: string;
  icon: LucideIcon;
  description: string;
  actions: HelpAction[];
  tips: string[];
  comingSoon?: boolean;
}
interface HelpContextType {
  isOpen: boolean;
  activeScreen: string;
  openHelp: (screen?: string) => void;
  closeHelp: () => void;
}
```

**Critérios de Aceite**:
- [x] Todas as interfaces definidas com documentação TSDoc
- [x] Tipos exportados e utilizáveis por outros componentes
- [x] Validação TypeScript sem warnings
- [x] Compatível com estrutura do plano

**Dependências**: T001  
**Estimativa**: 0.5 dia  

---

## Fase 2: Dados e Conteúdo (Semana 1)

### [T003] Implementar Dados de Instruções Base [P1] [US1,US3]
**Descrição**: Criar conteúdo de instruções para as 7 telas principais do sistema  
**Arquivo**: `frontend/src/components/help/helpData.ts`

**Telas a Documentar**:
1. Painel (`/dashboard`) - 3 ações + 2 dicas
2. Pigmentos (`/pigments`) - 4 ações + 3 dicas  
3. Cores Definidas (`/colors`) - 3 ações + 2 dicas
4. Fórmulas (`/formulas`) - 5 ações + 3 dicas
5. Misturas (`/mixtures`) - 4 ações + 3 dicas
6. Controle de Estoque (`/inventory`) - 6 ações + 4 dicas
7. Etiquetas (`/labels`) - 3 ações + 2 dicas

**Critérios de Aceite**:
- [x] Cada tela tem mínimo 3 ações com steps numerados
- [x] Cada ação tem 2-5 passos detalhados
- [x] Dicas práticas incluídas para cada tela
- [x] Ícones apropriados atribuídos usando Lucide React
- [x] Marcação `comingSoon` para telas não implementadas
- [x] Conteúdo revisado para clareza e precisão

**Dependências**: T002  
**Estimativa**: 2 dias  

---

### [T004] Adicionar Atalhos de Teclado nas Instruções [P2] [US3]
**Descrição**: Documentar atalhos de teclado existentes nas instruções de cada tela  
**Arquivo**: `frontend/src/components/help/helpData.ts`

**Atalhos a Documentar**:
- Atalhos globais: `?` (ajuda), `Ctrl+/` (busca), `Esc` (fechar)
- Atalhos por tela: navegação, ações rápidas, salvamento
- Formatação especial para atalhos com badges distintivos

**Critérios de Aceite**:
- [x] Seção "Atalhos" em cada ScreenHelp
- [x] Atalhos formatados consistentemente (`Ctrl+S`, `Enter`, etc.)
- [x] Testado que atalhos documentados funcionam
- [x] Agrupamento lógico: globais vs específicos da tela

**Dependências**: T003  
**Estimativa**: 1 dia  

---

## Fase 3: Componentes Principais (Semana 1-2)

### [T005] Criar HelpProvider e Context [P1] [US1]
**Descrição**: Implementar React Context para gerenciar estado global da ajuda  
**Arquivo**: `frontend/src/providers/HelpProvider.tsx`

**Funcionalidades**:
- Estado: `isOpen`, `activeScreen`
- Métodos: `openHelp()`, `closeHelp()`, `setActiveScreen()`
- Auto-detecção de tela atual via `useLocation()`
- Persistência de estado durante navegação

**Critérios de Aceite**:
- [x] Context Provider funcional com todas as funcionalidades
- [x] Estado gerenciado sem vazamentos de memória
- [x] Hook `useHelp()` para consumir o contexto
- [x] Detecção automática da rota/tela atual
- [x] TypeScript tipado corretamente

**Dependências**: T002  
**Estimativa**: 1 dia  

---

### [T006] Implementar Hook useHelp [P1] [US1]
**Descrição**: Criar hook personalizado para interação com HelpContext  
**Arquivo**: `frontend/src/hooks/useHelp.ts`

**API do Hook**:
```typescript
const {
  isOpen,
  activeScreen,
  openHelp,
  closeHelp,
  currentScreenHelp
} = useHelp();
```

**Funcionalidades Extras**:
- `currentScreenHelp`: dados da tela atual automaticamente
- Validação se tela existe no helpData
- Método `openCurrentScreen()` como conveniência

**Critérios de Aceite**:
- [x] Hook retorna interface limpa e intuitiva
- [x] Funciona corretamente com HelpProvider
- [x] Tratamento de casos edge (tela não encontrada)
- [x] Performance otimizada (memoização adequada)

**Dependências**: T005  
**Estimativa**: 0.5 dia  

---

### [T007] Criar Componente HelpDrawer [P1] [US1,US2]
**Descrição**: Implementar drawer lateral principal do sistema de ajuda  
**Arquivo**: `frontend/src/components/help/HelpDrawer.tsx`

**Funcionalidades**:
- Drawer deslizante da direita (380px desktop)
- Header com título e botão fechar
- Lista de abas para navegação entre telas
- Área de conteúdo dinâmico
- Overlay para fechar clicando fora
- Animação suave de abertura/fechamento

**Critérios de Aceite**:
- [x] Drawer visualmente consistente com design system
- [x] Animações fluidas (250ms transition)
- [x] Responsivo (100% width em mobile)
- [x] Acessível (role="dialog", focus trap)
- [x] Integrado com HelpContext

**Dependências**: T006  
**Estimativa**: 1.5 dias  

---

### [T008] Implementar HelpScreenContent [P1] [US2,US3]  
**Descrição**: Componente para renderizar conteúdo de instruções de uma tela específica  
**Arquivo**: `frontend/src/components/help/HelpScreenContent.tsx`

**Layout**:
- Header: ícone + nome da tela + descrição
- Badge "Em Desenvolvimento" se `comingSoon: true`
- Seção "Ações Principais" com accordion expandible
- Seção "Dicas Úteis" com lista de bullets
- Seção "Atalhos" (se T004 implementado)

**Critérios de Aceite**:
- [x] Renderiza corretamente todos os campos de ScreenHelp
- [x] Accordion funcional para ações (expansão individual)
- [x] Markdown básico suportado em textos
- [x] Design responsivo e legível
- [x] Performance adequada com conteúdo extenso

**Dependências**: T007, T003  
**Estimativa**: 1.5 dias  

---

## Fase 4: Integração e UX (Semana 2)

### [T009] Adicionar Botão de Ajuda no Header [P1] [US1]
**Descrição**: Integrar botão "?" no header principal para abrir sistema de ajuda  
**Arquivo**: `frontend/src/components/layout/Header.tsx`

**Especificações**:
- Ícone: `HelpCircle` (Lucide React)
- Posição: lado direito do header, antes do user menu
- Estilo: botão secundário circular
- Tooltip: "Ajuda (Pressione ?)"
- Ação: abrir drawer na tela atual

**Critérios de Aceite**:
- [x] Botão visível em todas as páginas autenticadas
- [x] Ícone apropriado e estilo consistente
- [x] Tooltip informativo e responsivo
- [x] Função integrada com useHelp()
- [x] Estados hover/active/focus bem definidos

**Dependências**: T008  
**Estimativa**: 0.5 dia  

---

### [T010] Implementar Atalho de Teclado Global [P1] [US1]
**Descrição**: Adicionar atalho `?` para abrir sistema de ajuda globalmente  
**Arquivo**: `frontend/src/components/help/HelpDrawer.tsx`

**Funcionalidades**:
- Detectar tecla `?` quando não há elemento focado (input/textarea)
- Prevenir conflito com busca em formulários
- Funcionar de qualquer tela do sistema
- Feedback visual ao ativar via teclado

**Critérios de Aceite**:
- [x] Atalho `?` funcional em toda aplicação
- [x] Não interfere com campos de texto
- [x] Funciona com IME e layouts de teclado alternativos  
- [x] Documentação do atalho visível no tooltip do botão

**Dependências**: T009  
**Estimativa**: 0.5 dia  

---

### [T011] Implementar Fechamento com Esc e Clique Fora [P1] [US1]
**Descrição**: Adicionar métodos intuitivos para fechar drawer de ajuda  
**Arquivo**: `frontend/src/components/help/HelpDrawer.tsx`

**Funcionalidades**:
- Tecla `Esc` fecha drawer
- Clicar no overlay fecha drawer
- Botão X no header fecha drawer
- Focus trap: Tab circula apenas dentro do drawer

**Critérios de Aceite**:
- [x] Todos os métodos de fechamento funcionam
- [x] Focus bem gerenciado (retorna ao elemento que abriu)
- [x] Não fecha acidentalmente durante digitação
- [x] Transição suave ao fechar

**Dependências**: T010  
**Estimativa**: 1 dia  

---

### [T012] Integrar HelpDrawer no RootLayout [P1] [US1] 
**Descrição**: Adicionar HelpProvider e HelpDrawer na estrutura principal da app  
**Arquivos**: 
- `frontend/src/layouts/RootLayout.tsx`
- `frontend/src/App.tsx`

**Integração**:
- Envolver aplicação com `<HelpProvider>`
- Adicionar `<HelpDrawer />` no nível apropriado
- Verificar que contexto está acessível em todas as páginas
- Testar funcionamento em diferentes rotas

**Critérios de Aceite**:
- [x] HelpProvider corretamente posicionado na árvore de componentes
- [x] HelpDrawer renderizado e acessível
- [x] Não há conflitos com outros providers/contextos
- [x] Performance adequada (não re-renders desnecessários)

**Dependências**: T011  
**Estimativa**: 0.5 dia  

---

## Fase 5: Melhorias e Polish (Semana 2-3)

### [T013] Adicionar Navegação por Abas no Drawer [P2] [US2]
**Descrição**: Implementar navegação entre diferentes telas dentro do drawer  
**Arquivo**: `frontend/src/components/help/HelpDrawer.tsx`

**Funcionalidades**:
- Lista vertical de abas no lado esquerdo (25% da largura)
- Conteúdo da tela selecionada no lado direito (75%)
- Indicador visual da aba ativa
- Navegação via teclado (setas) entre abas

**Critérios de Aceite**:
- [x] Todas as 7 telas disponíveis como abas
- [x] Aba da tela atual selecionada por padrão
- [x] Design responsivo (abas stackadas em mobile)
- [x] Acessibilidade: roles, aria-labels, keyboard navigation
- [x] Performance: lazy loading do conteúdo das abas

**Dependências**: T012  
**Estimativa**: 1.5 dias  

---

### [T014] Implementar Busca Rápida por Tela [P2] [US2]
**Descrição**: Adicionar campo de busca para filtrar e encontrar telas rapidamente  
**Arquivo**: `frontend/src/components/help/HelpDrawer.tsx`

**Funcionalidades**:
- Campo de busca no topo da lista de abas
- Filtragem por nome da tela ou palavras-chave
- Highlight dos termos encontrados
- Limpar busca com ícone X

**Critérios de Aceite**:
- [x] Busca instantânea (sem delay perceptível)
- [x] Busca por nome da tela e conteúdo das dicas
- [x] Resultado destaca termo pesquisado
- [x] Estado vazio bem comunicado
- [x] Atalho Ctrl+K para focar no campo de busca

**Dependências**: T013  
**Estimativa**: 1 dia  

---

### [T015] Otimizar Responsividade Mobile [P2] [US1,US2,US3] 
**Descrição**: Melhorar experiência mobile do sistema de ajuda  
**Arquivo**: `frontend/src/components/help/HelpDrawer.tsx`

**Otimizações Mobile**:
- Drawer fullscreen em telas < 640px
- Abas horizontais scrolláveis no topo
- Tipo e tamanho de fonte otimizados para touch
- Espaçamentos aumentados para touch targets
- Performance otimizada para dispositivos menos potentes

**Critérios de Aceite**:
- [x] Experiência fluida em devices 375px+
- [x] Touch targets mínimo de 44px
- [x] Scrolling natural e responsivo
- [x] Animações adequadas (sem motion sickness)
- [x] Testado em dispositivos reais iOS/Android

**Dependências**: T014  
**Estimativa**: 1.5 dias  

---

### [T016] Adicionar Animações e Micro-interações [P2] [US1]
**Descrição**: Melhorar feedback visual e experiência do usuário  
**Arquivos**: 
- `frontend/src/components/help/HelpDrawer.tsx`
- `frontend/src/components/help/HelpScreenContent.tsx`

**Animações**:
- Drawer slide-in animation (spring effect)
- Accordion expand/collapse suave
- Hover states nos botões e abas  
- Loading skeleton ao trocar telas
- Pulse animation no botão "?" quando tela tem ajuda nova

**Critérios de Aceite**:
- [x] Animações suaves e profissionais
- [x] Performance: 60fps, GPU-accelerated
- [x] Respeita `prefers-reduced-motion`
- [x] Não interfere com usabilidade
- [x] Feedback visual claro para todas as interações

**Dependências**: T015  
**Estimativa**: 1 dia  

---

### [T017] Implementar Indicadores de Conteúdo Novo [P3] [US2]
**Descrição**: Sistema de badges para indicar instruções novas ou atualizadas  
**Arquivo**: `frontend/src/components/help/helpData.ts`

**Funcionalidades**:
- Badge "Novo" em telas com instruções recentes
- Badge "Atualizado" em telas com modificações
- Controle via metadata no helpData
- LocalStorage para tracking do que foi visualizado

**Critérios de Aceite**:
- [x] Badges visualmente distintos e informativos
- [x] Lógica de "novo" vs "atualizado" clara
- [x] Persistência adequada no browser
- [x] Não polui interface: máximo 2-3 badges simultâneos

**Dependências**: T016  
**Estimativa**: 1.5 dias  

---

### [T018] Adicionar Analytics de Uso da Ajuda [P3] [US1,US2,US3]
**Descrição**: Coletar dados sobre uso do sistema de ajuda para melhorias  
**Arquivos**: 
- `frontend/src/components/help/HelpDrawer.tsx`
- `frontend/src/hooks/useHelp.ts`

**Métricas**:
- Quantas vezes ajuda foi aberta (por tela)
- Telas mais consultadas
- Ações mais procuradas
- Jornada do usuário (navegação entre telas)
- Tempo médio com drawer aberto

**Critérios de Aceite**:
- [x] Eventos enviados para analytics existente
- [x] Dados anonimizados e LGPD-compliant
- [x] Performance não afetada
- [x] Opt-out possível via settings de usuário

**Dependências**: T017  
**Estimativa**: 1 dia  

---

### [T019] Criar Testes Automatizados [P2] [US1,US2,US3]
**Descrição**: Implementar testes unitários e de integração para sistema de ajuda  
**Arquivos**: 
- `frontend/src/components/help/__tests__/`
- Test coverage mínimo de 80%

**Testes a Criar**:
- HelpProvider: context funcionamento
- useHelp hook: todos os métodos e estados
- HelpDrawer: interações (abrir/fechar/navegar)  
- HelpScreenContent: renderização correta
- Testes E2E: fluxo completo usuário
- Testes de acessibilidade automatizados

**Critérios de Aceite**:
- [x] Coverage ≥ 80% em todos os componentes
- [x] Testes passam consistentemente
- [x] Mocks adequados para dependências externas
- [x] Testes executam rápido (< 30s total)

**Dependências**: T018  
**Estimativa**: 2 dias  

---

## Critérios de Conclusão da Feature

### Fase MVP (P1 - 12 tarefas)
- [x] **Sistema Funcional**: Drawer abre/fecha, navegação funciona, conteúdo visível
- [x] **Integração Completa**: Botão no header, atalho ?, contexto global
- [x] **Conteúdo Base**: 7 telas documentadas com ações e dicas
- [x] **Acessibilidade Básica**: Focus trap, esc para fechar, aria-labels

### Fase Completa (P1 + P2 - 20 tarefas)
- [x] **UX Aprimorada**: Busca, navegação por abas, responsividade mobile  
- [x] **Polish Visual**: Animações, micro-interações, feedback visual
- [x] **Qualidade**: Testes automatizados, analytics, performance otimizada

### Métricas de Sucesso
| Métrica | Meta MVP | Meta Completa |
|---------|----------|---------------|
| Tempo médio para encontrar instrução | < 30s | < 15s |
| % usuarios que usam ajuda semanalmente | > 60% | > 75% |
| Satisfação usuário (1-5) | ≥ 4.0 | ≥ 4.5 |
| Performance (Time to Interactive) | < 200ms | < 100ms |

---

## Dependências Externas

### Não há dependências de outros features  
Esta feature é completamente independente e pode ser implementada paralelamente.

### Dependências Técnicas
- React Router (já disponível)
- Tailwind CSS (já configurado)  
- Lucide React (já instalado)
- TypeScript (já configurado)

### Assets Necessários
- Ícones: todos disponíveis via Lucide React
- Não requer imagens ou recursos externos

---

## Estimativas Detalhadas

| Fase | Tarefas P1 | Tarefas P2 | Estimativa |
|------|------------|------------|------------|
| **Setup** | 2 tarefas | - | 1 dia |
| **Dados** | 1 tarefa | 1 tarefa | 3 dias |
| **Componentes** | 4 tarefas | - | 4 dias |
| **Integração** | 4 tarefas | - | 2.5 dias |
| **Melhorias** | 1 tarefa | 7 tarefas | 7 dias |
| **Testes** | - | 1 tarefa | 2 dias |

**Total MVP (P1)**: 12 tarefas ≈ **10.5 dias** (2 semanas)  
**Total Completo (P1+P2)**: 20 tarefas ≈ **19.5 dias** (3-4 semanas)

---

## Notas de Implementação

### Padrões de Código
- Seguir conventions existentes do projeto
- TypeScript strict mode habilitado  
- ESLint + Prettier para consistência
- Componentes funcionais com hooks

### Performance Considerations 
- Lazy loading de conteúdo das abas não ativas
- Memoização adequada para evitar re-renders
- Debounce na busca por telas
- Bundle size mínimo (código tree-shakeable)

### Acessibilidade Priority
- Suporte completo a screen readers
- Navegação 100% via teclado
- Alto contraste e temas escuros
- Focus management robusto

### Futuras Expansões
Esta implementação cria base sólida para:
- Sistema de tours guiados (v2)
- Busca textual nas instruções (v2)  
- Instruções contextuals dinâmicas (v3)
- Integração com sistema de onboarding (v3)