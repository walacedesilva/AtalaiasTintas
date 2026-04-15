# Quality Assurance Checklists — Feature 6: Gestão de Clientes, Pedidos e PDV

## Overview

Checklists de qualidade para garantir que o módulo de vendas, PDV e gestão de crédito atenda todos os requisitos de segurança, integridade, performance e acessibilidade antes de entrar em produção.

## Domínios de Qualidade

### 🔒 [Segurança](security.md)
**48 checkpoints** — autorização de desconto, proteção de dados PF/PJ, atomicidade do PDV, auditoria.
- PIN gerencial nunca em texto claro
- CPF/CNPJ protegidos por permissão
- Transação atômica no checkout PDV
- Log de auditoria imutável

### 📊 [Lógica de Negócio](business-logic.md)
**55 checkpoints** — regras de desconto, crédito/crediário, fluxo pedido→venda, cancelamentos.
- Limites de desconto por nível de usuário
- Controle de limite de crédito pré-venda
- Baixa de estoque somente após confirmação
- NFe automática para cliente B2B (CNPJ)

### 🎯 [Integridade de Dados](data-integrity.md)
**42 checkpoints** — atomicidade do PDV, consistência de recebíveis, reversão de estoque.
- Checkout PDV como transação única
- Recebível criado apenas se venda confirmada
- Cancelamento reverte estoque e fiscal
- Saldo crédito sempre consistente

### ⚡ [Performance](performance.md)
**30 checkpoints** — tempo de resposta do PDV, busca de produto/cliente, carregamento do histórico.
- Busca de produto: < 300ms
- Checkout PDV: < 2s end-to-end
- Histórico de cliente: paginado, < 1s

### ♿ [Acessibilidade](accessibility.md)
**28 checkpoints** — teclado no PDV, contraste, ARIA, operação sem mouse.
- PDV 100% operável por teclado (F10, ESC, Tab)
- WCAG 2.1 AA para todas as páginas novas
- Leitores de tela nos modais de aprovação

## Cobertura de Testes Necessária

| Camada | Meta |
|---|---|
| Backend — services (DescontoService, CreditoService, RecebivelService) | ≥ 95% |
| Backend — APIs (PDV checkout, devolver, aprovar) | ≥ 90% |
| Frontend — PDVPage (fluxo completo) | Playwright E2E |
| Integração — PDV → Estoque → NFe flag | ≥ 1 teste por BR-00x |
