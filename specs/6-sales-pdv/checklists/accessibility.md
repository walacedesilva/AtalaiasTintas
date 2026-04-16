# Checklist de Acessibilidade — Feature 6: PDV / Vendas / Clientes

**Feature**: [Spec 6 — Gestão de Clientes, Pedidos e PDV](../spec.md)  
**Padrão**: WCAG 2.1 AA  
**Domínio**: Operação por teclado no PDV, leitores de tela, contraste, modais

---

## 1. PDVPage — Operação Inteiramente por Teclado (US003)

### 1.1 Atalhos de Teclado Obrigatórios
- [ ] `F10` abre tela de pagamento (quando carrinho não está vazio)
- [ ] `ESC` no PDV: cancela operação atual ou limpa carrinho (com confirmação)
- [ ] `Enter` no campo de busca de produto: adiciona o primeiro resultado ao carrinho
- [ ] `Tab` navega: campo busca produto → campo quantidade → botão adicionar → campo busca cliente
- [ ] `↑`/`↓` nas setas: navega resultados do dropdown de busca de produto
- [ ] `Delete` ou `Backspace` na linha de item selecionado no carrinho: remove o item

### 1.2 Foco Automático
- [ ] Ao abrir PDVPage: foco automático no campo de busca de produto (`autoFocus`)
- [ ] Após adicionar produto: foco retorna ao campo de busca (pronto para próximo produto)
- [ ] Após abrir modal de pagamento: foco vai para primeiro campo do modal
- [ ] Após fechar modal: foco retorna ao elemento que abriu o modal

### 1.3 Confirmações via Teclado
- [ ] Modal de confirmação de cancelamento (`ESC`): `Enter` confirma, `ESC` fecha sem ação
- [ ] Modal de aprovação de desconto (PIN): `Enter` no campo PIN submete, `ESC` fecha
- [ ] Todos os botões de ação são focáveis e ativados por `Enter` e `Space`

---

## 2. Modais e Dialogs (ARIA)

- [ ] `DescontoAprovacaoModal` usa `role="dialog"` + `aria-modal="true"` + `aria-labelledby`
- [ ] `aria-labelledby` aponta para o título do modal (ex: "Aprovação de Desconto Gerencial")
- [ ] Foco aprisionado dentro do modal enquanto aberto (`focus-trap`)
- [ ] `ESC` fecha o modal e devolve foco ao elemento de origem
- [ ] Overlay do modal não intercepta leitura do conteúdo subjacente (correto com `aria-modal`)
- [ ] Modal de cancelamento de venda: título `aria-labelledby` descreve a ação destrutiva

---

## 3. Campos de Formulário (Clientes, Pedidos)

- [ ] Todos os `<input>` têm `<label>` associado via `htmlFor` ou `aria-label`
- [ ] Erros de validação exibidos com `role="alert"` ou `aria-describedby` apontando ao campo
- [ ] Campos obrigatórios têm `required` + indicador visual `*` com texto `aria-hidden`
- [ ] CPF/CNPJ: `inputmode="numeric"` para teclado numérico em mobile
- [ ] Campo de busca de cliente: `aria-autocomplete="list"` + `aria-activedescendant` para resultados
- [ ] PIN no modal: `type="password"` + botão de toggle com `aria-label="Mostrar/ocultar PIN"`

---

## 4. Tabelas e Listagens

- [ ] Tabela de clientes: `<table>` semântico com `<thead>`, `<tbody>`, `<th scope="col">`
- [ ] Tabela de pedidos: cabeçalhos com `scope="col"`, ações na linha com `aria-label` descritivo
- [ ] Tabela de recebíveis: coluna "Situação" com cores + texto (não só cor) para indicar estado
- [ ] Carrinho do PDV: `<table>` semântico com `aria-label="Carrinho de compras"`
- [ ] Botões de "Remover item" na tabela: `aria-label="Remover [nome do produto]"` (não só ícone)
- [ ] Linha expandível de pedido (accordion): `aria-expanded="true/false"` no botão de toggle

---

## 5. Contraste e Elementos Visuais

- [ ] Todos os textos com razão de contraste ≥ 4.5:1 (texto normal) ou ≥ 3:1 (texto grande ≥ 18px)
- [ ] Badges de situação (ORCAMENTO, APROVADO etc): contraste verificado entre texto e background
- [ ] Cor vermelha de "vencido" em recebíveis não é o único indicador — acompanhada por ícone ou texto
- [ ] Cor verde de "pago" não é o único indicador — acompanhada por checkmark ou texto
- [ ] Indicador de produto sem estoque: badge de texto "Sem Estoque" (não só cor)
- [ ] Total do carrinho em destaque: tamanho de fonte ≥ 24px no campo de total

---

## 6. Notificações e Feedback

- [ ] Toast de sucesso ("Venda finalizada!") tem `role="status"` ou `aria-live="polite"`
- [ ] Toast de erro (falha no checkout) tem `role="alert"` (lido imediatamente)
- [ ] Loading spinner durante checkout tem `aria-label="Processando venda..."` + `role="status"`
- [ ] Aviso de estoque insuficiente no PDV: `aria-live="assertive"` para anunciar imediatamente
- [ ] Cálculo de troco atualizado em tempo real: `aria-live="polite"` na área de troco
- [ ] Mensagem de "limite de crédito insuficiente" lida pelo leitor (`aria-live="assertive"`)

---

## 7. Responsividade e Mobile

- [ ] PDVPage utilizável em tablet (mínimo 768px) — layout flexível, não apenas desktop
- [ ] Campos de payment no mobile: botões grandes (mín 44×44px) para seleção de forma de pagamento
- [ ] Scanner de código de barras: campo de busca aceita input via hardware scanner (envia `\n` no final)
- [ ] Viewport configurado: `<meta name="viewport" content="width=device-width, initial-scale=1">`

---

## 8. Testes de Acessibilidade

- [ ] `axe-core` ou `@axe-core/react` sem violações críticas ou sérias em PDVPage
- [ ] `axe-core` sem violações em `ClientesPage`, `PedidosPage`, `RecebiveisPage`
- [ ] Teste manual: navegar PDV completo (busca → adicionar → pagamento → finalizar) apenas com teclado
- [ ] Teste com leitor de tela (NVDA/VoiceOver): modal de aprovação de desconto lido corretamente
