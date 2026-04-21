# Spec 14 — Dashboard com Dados Reais + Produtos Mais Vendidos

## Problema
Todas as métricas do dashboard (Vendas Totais, Pedidos, Ticket Médio, Taxa de Conversão,
Resumo de Vendas, Status Fiscal) estão usando dados mock com `Math.random()`. O usuário
vê números diferentes a cada atualização, sem relação com os dados reais do banco.

## Requisitos

### US1 — Métricas reais do negócio
Como gerente, quero ver métricas reais do dia para tomar decisões corretas.
- Vendas Totais = soma de `valor_liquido` das vendas não canceladas do dia
- Pedidos = contagem de vendas não canceladas do dia
- Ticket Médio = média de `valor_liquido` das vendas do dia
- Taxa de Conversão = (vendas concluídas / pedidos criados) × 100
- Comparação com dia anterior (% de variação)

### US2 — Resumo de vendas real
- Vendas de Hoje = contagem de vendas do dia
- Faturamento Hoje = soma de valor_liquido do dia
- Meta do Dia = % relativo à média dos últimos 7 dias

### US3 — Status Fiscal real
- NFe Emitidas = Venda com `nfe_situacao = AUTORIZADA`
- NFe Pendentes = Venda com `nfe_situacao IN (PENDENTE, PROCESSANDO)`
- NFe com Erro = Venda com `nfe_situacao IN (ERRO_TECNICO, REJEITADA, AGUARDANDO_RETRY)`

### US4 — Produtos Mais Vendidos
Como gerente, quero ver os 5 produtos com maior receita do dia no dashboard.
- Nome do produto (produto_base.nome)
- Quantidade vendida
- Receita gerada
- Barra de progresso relativa ao maior produto

## Critérios de Aceite
- AC1: Ao recarregar o dashboard, os números não mudam aleatoriamente
- AC2: Os números do Status Fiscal coincidem com os dados reais de NFe
- AC3: Produtos Mais Vendidos mostra produtos reais, ordenados por receita
- AC4: Se não há vendas no dia, mostra "Nenhuma venda hoje" gracefully
