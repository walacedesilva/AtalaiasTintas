# Plan: Página de Ajuda e Onboarding

**Feature**: 13-onboarding-help-page

---

## Arquitetura

### Componentes novos
- `frontend/src/pages/help/HelpPage.tsx` — página principal de onboarding

### Arquivos modificados
- `frontend/src/providers/RouterProvider.tsx` — adicionar rota `/help`
- `frontend/src/components/layout/Header.tsx` — botão Ajuda redireciona para `/help`

---

## Estrutura da HelpPage

### Layout
```
┌─────────────────────────────────────────┐
│  Header: "Guia do Sistema" + progresso  │
├──────────────┬──────────────────────────┤
│ Sidebar      │  Conteúdo do passo       │
│ (índice)     │  - Ícone grande          │
│ [1] Dashboard│  - Número + Título       │
│ [2] Estoque  │  - Descrição             │
│ [3] ...      │  - Ações práticas        │
│              │  - Dicas                 │
│              │  - Botão "Ir para tela"  │
├──────────────┴──────────────────────────┤
│  [← Anterior]  [Próximo →] / [Concluir] │
└─────────────────────────────────────────┘
```

### Passos do Guia
0. **Bem-vindo** — Visão geral do sistema
1. **Dashboard** — Painel de controle e métricas
2. **Estoque** — Controle de produtos e entradas
3. **Tintometria** — Misturas e fórmulas de cores
4. **Etiquetas** — Geração e impressão
5. **Fiscal / NFe** — Notas fiscais e documentos
6. **Relatórios** — Análises e exportações
7. **Configurações** — Personalização do sistema

### Dados
Definidos inline no componente (sem API). Cada passo:
```ts
interface GuideStep {
  id: number;
  icon: LucideIcon;
  title: string;
  subtitle: string;
  description: string;
  actions: { label: string; steps: string[] }[];
  tips: string[];
  route?: string; // para o botão "Ir para tela"
  routeLabel?: string;
  color: string; // tailwind color class
}
```

### Navegação
- Estado `currentStep: number` gerenciado com `useState`
- Teclado: ← → para navegar
- Sidebar: clique direto no passo
- Botões: Anterior / Próximo / Concluir (volta ao dashboard)
- Barra de progresso no topo

---

## Mudança no Header

Botão Ajuda passa a usar `useNavigate('/help')` em vez de `openHelp()`.  
O `HelpDrawer` continua funcionando para o atalho `?` via teclado (contextual).
