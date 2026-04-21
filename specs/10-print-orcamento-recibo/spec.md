# Feature 10: Impressão de Orçamento e Recibo de Venda

**Status:** ✅ Specify  
**Priority:** P1 (MVP)  
**Estimated Complexity:** Medium  
**Business Impact:** Alto — Habilita entrega formal de documentos ao cliente no balcão e no PDV

---

## Context & Business Need

A loja precisa entregar ao cliente um documento impresso em dois momentos distintos:

1. **Orçamento:** Durante o atendimento balcão, antes da decisão de compra. O cliente precisa levar uma proposta formal com produtos, quantidades, preços unitários, desconto e total.
2. **Recibo de Venda:** Após a conclusão do pagamento. Confirma o que foi comprado, quanto foi pago, qual forma de pagamento e serve como comprovante interno (nos casos em que não há NF-e).

Hoje os vendedores anotam à mão ou usam planilhas para gerar esses documentos, causando erros, falta de padronização e perda de tempo no atendimento.

**Pain Points Atuais:**
- Nenhum documento impresso disponível no sistema atual
- Informação divergente entre o que é anotado e o que o cliente recebe
- Sem registro visual do desconto aplicado e da forma de pagamento
- Atendimento B2B exige orçamento formal com CNPJ da loja e do cliente

---

## User Stories

### US1 — Impressão de Orçamento
**Como** vendedor,  
**Quero** imprimir um orçamento formatado para o cliente,  
**Para que** ele tenha uma proposta formal com todos os itens, preços e total antes de decidir a compra.

**Critérios de Aceitação:**
- O orçamento pode ser gerado a partir de um pedido em situação `ORCAMENTO` ou `APROVADO`
- O documento exibe: dados da loja (nome, CNPJ, endereço, telefone), data e número do pedido, dados do cliente (nome, CPF/CNPJ se disponível), lista de itens (produto, unidade, quantidade, preço unitário, desconto por item, subtotal), desconto geral, valor total, validade do orçamento (configurável, padrão 3 dias), campo para assinatura do cliente
- O usuário pode escolher entre imprimir diretamente ou salvar como PDF
- Orçamento anônimo (balcão sem cliente) é permitido, exibindo "Consumidor Final" no campo do cliente

### US2 — Impressão de Recibo de Venda
**Como** vendedor,  
**Quero** imprimir um recibo após finalizar a venda,  
**Para que** o cliente tenha um comprovante de pagamento com detalhes do que foi comprado e como pagou.

**Critérios de Aceitação:**
- O recibo só pode ser gerado para vendas em situação `FINALIZADA`
- O documento exibe: dados da loja, data/hora da venda, número da venda, dados do cliente (ou "Consumidor Final"), lista de itens comprados, forma(s) de pagamento utilizada(s) com valores, total pago, troco se aplicável, campo de observações
- Se a venda possui NF-e emitida, o recibo exibe a chave de acesso da NF-e e texto "Este recibo não substitui a Nota Fiscal"
- O sistema oferece opção de imprimir automaticamente o recibo ao finalizar a venda (configurável por loja)
- O usuário pode reimprimir o recibo de uma venda já finalizada acessando o histórico

### US3 — Pré-visualização antes de Imprimir
**Como** vendedor,  
**Quero** visualizar o documento antes de imprimir,  
**Para que** possa confirmar que os dados estão corretos e evitar desperdício de papel.

**Critérios de Aceitação:**
- Tanto o orçamento quanto o recibo oferecem pré-visualização em modal ou nova aba antes de acionar a impressão
- A pré-visualização usa o mesmo layout do documento impresso
- O usuário pode cancelar sem imprimir

### US4 — Configuração da Logo e Dados da Loja
**Como** administrador,  
**Quero** configurar os dados e logo da loja que aparecem nos documentos impressos,  
**Para que** os documentos tenham identidade visual consistente com a marca.

**Critérios de Aceitação:**
- Administrador pode fazer upload de uma logo da loja (PNG/JPG, max 500KB)
- Dados configuráveis: nome fantasia, razão social, CNPJ, endereço, telefone, e-mail, site (opcional)
- Configurações ficam visíveis e editáveis no painel de configurações da loja
- Mudanças se refletem imediatamente nos próximos documentos gerados

---

## Out of Scope

- Envio do orçamento/recibo por e-mail ou WhatsApp (feature separada)
- Impressão de NF-e / DANFE (gerenciado pelo módulo fiscal)
- Impressão térmica (bobina 58mm/80mm) — considerada em fase futura
- Assinatura digital do cliente

---

## Constraints

- O documento deve ser compatível com impressoras comuns (A4/carta) e impressoras de recibo A5
- O layout deve ser responsivo para diferentes tamanhos de papel (A4 e A5)
- Geração deve ocorrer no lado do cliente (browser `window.print()`) para não requerer infraestrutura de PDF no servidor
- Dados sensíveis do cliente (CPF/CNPJ) devem respeitar as permissões de visualização já existentes no sistema
