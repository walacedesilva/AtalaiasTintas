# Spec: PDV/Nova Venda — Melhorias de UX e Fluxo de Dados

**Feature**: 11-pdv-ux-improvements  
**Status**: Specify  
**Data**: 2026-04-20

---

## Resumo

Operadores de caixa precisam finalizar vendas com o mínimo de cliques e máxima clareza visual. A modal/drawer de "Nova Venda" e a tela PDV apresentam fricção desnecessária no fluxo atual: campo de parcelas sempre editável (mesmo para Pix), ausência de autofoco, busca de produtos sem feedback de estoque e ausência de atalhos de teclado relevantes.

---

## Histórias de Usuário

**US-1** — Como operador, quero que o cursor já esteja no campo "Cliente" ao abrir a drawer, para não precisar clicar antes de digitar.

**US-2** — Como operador, quero que o campo "Parcelas" fique desabilitado e fixo em 1 para pagamentos que não permitem parcelamento (Dinheiro, Pix, Débito, Transferência, Cheque, Fiado), poupando cliques desnecessários.

**US-3** — Como operador, quero ver a bandeira do cartão (Visa, Mastercard, etc.) como campo extra quando o pagamento for Cartão Crédito ou Débito.

**US-4** — Como operador, quero que os campos de endereço de entrega apareçam automaticamente somente quando o tipo de entrega for "Entrega" ou "Transportadora", mantendo a interface limpa para vendas de balcão.

**US-5** — Como operador, quero que a lista de resultados de busca de produto mostre preço e estoque disponível, com alerta visual quando o estoque estiver baixo (< 5 unidades).

**US-6** — Como operador, quero um botão "+" ao lado do campo de cliente para abrir um mini-modal de cadastro rápido sem sair da tela de venda.

**US-7** — Como operador, quero usar Ctrl+Enter para finalizar a venda sem tirar as mãos do teclado, e ver os atalhos disponíveis na base da drawer.

**US-8** — Como operador, quero que a drawer de Nova Venda utilize um layout de duas colunas em telas maiores: à esquerda os campos do pedido (loja, cliente, pagamento, entrega) e à direita a busca de produtos e o carrinho com o total em destaque.

**US-9** — Como operador PDV, quero usar F2 para focar na busca de produtos e Ctrl+Enter para abrir o painel de pagamento.

---

## Requisitos Funcionais

| ID | Requisito |
|----|-----------|
| RF-01 | Autofoco no campo "Cliente" ao abrir a drawer Nova Venda |
| RF-02 | Campo "Parcelas" desabilitado (valor = 1) para DINHEIRO, PIX, CARTAO_DEBITO, TRANSFERENCIA, CHEQUE, FIADO |
| RF-03 | Campo "Bandeira" (select) exibido quando forma = CARTAO_CREDITO ou CARTAO_DEBITO |
| RF-04 | Seção de endereço de entrega exibida apenas para DELIVERY e TRANSPORTADORA |
| RF-05 | Dropdown de busca exibe preço e quantidade disponível com indicador de estoque baixo |
| RF-06 | Estoque < 3 = vermelho; 3–9 = âmbar; ≥ 10 = verde no dropdown |
| RF-07 | Botão "+" ao lado da busca de cliente abre QuickAddClienteModal |
| RF-08 | QuickAddClienteModal permite cadastrar nome + telefone + CPF/CNPJ e fecha retornando o cliente selecionado |
| RF-09 | Ctrl+Enter aciona "Finalizar Venda" na drawer Nova Venda |
| RF-10 | Barra de atalhos discretos no rodapé da drawer ("Ctrl+Enter: Finalizar · ESC: Fechar") |
| RF-11 | Layout 2 colunas na drawer para viewports ≥ 1024px (lg) |
| RF-12 | PDVPage: F2 foca campo de busca de produto |
| RF-13 | PDVPage: Ctrl+Enter equivale a F10 (abre painel de pagamento) |
| RF-14 | PDVPage: Atualizar hints de atalho para incluir F2 e Ctrl+Enter |

---

## Requisitos Não Funcionais

- Layout responsivo: coluna única em mobile, 2 colunas em desktop
- Não quebrar testes E2E existentes (pdv-flow.spec.ts, pdv-a11y.spec.ts)
- Acessibilidade: todos os novos inputs com `aria-label` ou `label` associado
- Sem chamadas de API novas além das já existentes para criar cliente

---

## Fora de Escopo

- Cálculo automático de frete por CEP
- Integração com gateway de cartão para bandeira
- Histórico de clientes na mini-modal
