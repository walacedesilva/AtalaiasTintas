# Plano: Menu de Instruções de Uso

**Feature**: `5-help-instructions-menu`  
**Depende de**: spec.md ✅

---

## Arquitetura

### Componente Principal: `HelpDrawer`
Um drawer lateral deslizante (right-side) que:
- É controlado por contexto global (`HelpContext`)
- Persiste a aba selecionada no estado local
- Abre na tela atual por padrão via `useLocation()`

### Estrutura de Arquivos

```
frontend/src/
  components/
    help/
      HelpDrawer.tsx          # Drawer principal
      HelpScreenContent.tsx   # Conteúdo de uma tela
      helpData.ts             # Conteúdo das instruções (data-only)
  hooks/
    useHelp.ts                # Hook para abrir/fechar drawer
  providers/
    HelpProvider.tsx          # Context provider
```

### Fluxo de Dados
```
Header → botão "?" → HelpContext.open(currentPath)
useLocation() → detecta rota ativa → seleciona tab correspondente
helpData.ts → array de ScreenHelp → renderizado em HelpDrawer
```

### helpData.ts — Estrutura
```ts
interface HelpStep   { text: string }
interface HelpAction { title: string; steps: HelpStep[] }
interface ScreenHelp {
  route: string
  label: string
  icon: LucideIcon
  description: string
  actions: HelpAction[]
  tips: string[]
  comingSoon?: boolean
}
```

### Integração no RootLayout
```tsx
<HelpProvider>
  <Header />         // botão "?" aqui
  <Navigation />
  <main>…</main>
  <HelpDrawer />     // drawer global
</HelpProvider>
```

### Shortcut de Teclado
`useEffect` global em `HelpDrawer` detecta tecla `?` quando não está em input.

---

## Tecnologias
- React 18 + TypeScript
- Tailwind CSS (classes existentes: `card`, `btn-secondary`, `badge-*`)
- Lucide React (ícones já usados no projeto)
- React Router `useLocation`
- Sem dependências novas

---

## Responsividade
- Desktop: drawer de 380px fixo à direita, sobreposição com overlay
- Mobile: drawer de 100% largura

---

## Acessibilidade
- `role="dialog"` + `aria-modal` no drawer
- Focus trap ao abrir
- `aria-label` no botão e nas abas
- Fechar com `Esc`
