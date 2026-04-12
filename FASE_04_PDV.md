# Fase 4: Sistema PDV (Ponto de Venda)

## Objetivos da Branch
- Sistema completo de vendas
- Interface desktop PyQt6 
- Integração com hardware fiscal
- Sistema de caixa e fechamentos
- Gestão de clientes e crédito

## Tarefas Principais
- [ ] Interface PyQt6 para vendas
- [ ] Sistema de carrinho de compras
- [ ] Integração com impressoras térmicas
- [ ] Controle de caixa e turnos
- [ ] Sistema de desconto / promoções
- [ ] Análise de crédito automática
- [ ] Emissão de cupons não-fiscais
- [ ] Relatórios de vendas

## Arquivos a Desenvolver
- pdv/desktop/main_window.py
- pdv/desktop/sales_widget.py
- pdv/desktop/payment_widget.py
- sales/models.py
- sales/services.py
- cash_register/models.py
- credit/analyzer.py
- hardware/fiscal_printer.py

## Funcionalidades Específicas
- Interface touch screen otimizada
- Leitura de códigos de barras
- Múltiplas formas de pagamento
- Sistema de troco automático
- Impressão de cupons personalizados
- Backup local dos dados
- Modo offline funcional

## Integrações de Hardware
- Impressoras Epson, Daruma, Diebold
- Leitores de código de barras
- Gavetas de dinheiro
- Displays de cliente
- TEF (Transferência Eletrônica de Fundos)

## Análise de Crédito IA
- Integração com SPC/Serasa
- Algoritmos de ML para análise
- Histórico de compras do cliente
- Score de crédito automático
- Aprovação/rejeição inteligente

## Critérios de Entrega
- Interface PDV funcional e intuitiva
- Vendas sendo processadas corretamente
- Hardware fiscal integrado
- Sistema de caixa operacional
- Análise de crédito funcionando

## Status: 🏪 AGUARDANDO TINTOMETRIA