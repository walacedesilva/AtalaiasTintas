# Spec: Sistema Totalmente Responsivo

**Feature ID**: 007  
**Status**: especificado  
**Data**: 2026-04-16

---

## Objetivo

Tornar o sistema AtalaiasTintas totalmente responsivo para que qualquer usuário possa acessá-lo e operá-lo em dispositivos móveis (smartphones, tablets) e desktops, sem degradação de usabilidade.

---

## Usuários Afetados

- **Operador de loja** — acessa o sistema pelo celular enquanto atende o balcão
- **Gerente** — consulta relatórios de estoque e vendas no tablet
- **Vendedor PDV** — registra vendas em tablet ou computador
- **Técnico tintométrico** — consulta fórmulas no celular próximo à máquina

---

## Problemas Atuais (contexto)

1. Tabelas com muitas colunas transbordam a tela em dispositivos pequenos
2. Formulários com múltiplas colunas ficam apertados em mobile
3. Botões e campos de ação ficam inacessíveis sem rolagem horizontal
4. Cards e grids de dashboard quebram o layout em telas < 768px
5. Páginas de etiquetas e fiscal não possuem layout adaptado para mobile
6. Navegação lateral já possui drawer em mobile (implementado), mas páginas internas ainda precisam de ajuste
7. Modais e dialogs não são scroll-friendly no mobile
8. Tipografia e espaçamentos não escalam para telas pequenas

---

## Requisitos Funcionais

### US1 — Navegação Mobile
- O usuário deve conseguir navegar entre todas as seções pelo menu hamburger em telas < 1024px
- Todos os itens do menu devem ser tocáveis com área mínima de 44x44px

### US2 — Tabelas Responsivas
- Todas as tabelas devem ser horizontalmente roláveis em mobile
- Tabelas críticas (Estoque, Vendas, NF, Pigmentos) podem colapsar colunas menos importantes em telas < 640px

### US3 — Formulários Responsivos
- Todos os formulários devem usar layout de coluna única em mobile (< 640px)
- Campos em grid devem empilhar em mobile

### US4 — Dashboard Responsivo
- Cards de KPI devem reorganizar de 4 colunas → 2 colunas (tablet) → 1 coluna (mobile)
- Gráficos devem redimensionar proporcionalmente

### US5 — PDV (Ponto de Venda) Responsivo
- A tela de PDV deve ser usável em tablet (landscape e portrait)
- Botões de ação devem ter tamanho adequado para toque

### US6 — Páginas de Listagem
- Páginas de estoque, vendas, clientes, cores, pigmentos devem ter layout responsivo
- Filtros e buscas devem ser colapsáveis em mobile

### US7 — Modais e Overlays
- Modais devem ocupar quase tela cheia em mobile (max 95vw/95vh)
- Devem ter scroll interno quando o conteúdo for maior que a tela

### US8 — Tipografia e Espaçamento
- Textos não devem ser menores que 14px em qualquer dispositivo
- Espaçamentos devem usar unidades relativas (rem/%)

---

## Requisitos Não-Funcionais

- Compatibilidade com Chrome Mobile, Safari iOS, Firefox Android
- Telas mínimas suportadas: 320px de largura
- Tempo de carregamento não deve aumentar por mudanças responsivas
- Manter acessibilidade: contraste, foco teclado, ARIA

---

## Fora do Escopo

- Desenvolvimento de app nativo (iOS/Android)
- PWA com funcionalidades offline
- Redesign visual completo

---

## Critérios de Aceite

- [ ] Todas as páginas renderizam sem overflow horizontal em 375px (iPhone SE)
- [ ] Todas as tabelas têm scroll horizontal em mobile
- [ ] Formulários usam coluna única em mobile
- [ ] Dashboard cards empilham corretamente
- [ ] PDV é utilizável em 768px (tablet)
- [ ] Modais não ultrapassam bordas da tela
- [ ] Nenhum botão/link com área de toque < 44px
- [ ] Testes de snapshot/componente continuam passando
