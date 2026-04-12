# Fase 6: Sistema Fiscal

## Objetivos da Branch
- Emissão de notas fiscais eletrônicas
- Integração completa com SEFAZ
- Certificação digital A1/A3
- Sistema de contingência
- Compliance tributário completo

## Tarefas Principais
- [ ] Engine de emissão NFe/NFCe
- [ ] Integração SEFAZ todos os estados
- [ ] Sistema de certificação digital
- [ ] Cálculos tributários automatizados
- [ ] Sistema de contingência offline
- [ ] Backup e auditoria fiscal
- [ ] Dashboard fiscal
- [ ] Relatórios SPED/REINF

## Arquivos a Desenvolver
- fiscal/nfe/engine.py
- fiscal/nfe/sefaz_client.py
- fiscal/nfe/certificate_manager.py
- fiscal/nfce/emitter.py
- fiscal/taxes/calculator.py
- fiscal/contingency/offline_system.py
- fiscal/sped/generator.py
- fiscal/audit/trail.py

## Funcionalidades Fiscais
### NFe (Nota Fiscal Eletrônica)
- Emissão, cancelamento, inutilização
- Carta de Correção Eletrônica
- Consulta de situação no SEFAZ
- Manifesto do Destinatário
- Download de XMLs automático

### NFCe (Nota Fiscal de Consumidor)
- Emissão para vendas no PDV
- Sistema de contingência offline
- QR Code para validação
- SAT-CF-e como backup

### Cálculos Tributários
- ICMS, PIS, COFINS automáticos
- Substituição tributária
- Diferencial de alíquota
- Simples Nacional
- Regime tributário por produto

## Certificação Digital
- Suporte A1 (arquivo) e A3 (token/smart card)
- Renovação automática de certificados
- Gestão multi-empresa
- Backup seguro de certificados

## Sistema de Contingência
- Modo offline para NFCe
- FS-IA (Impressão Auxiliar)
- EPEC (Evento Prévio)
- Sincronização automática

## Integrações Obrigatórias
- SEFAZ de todos os estados brasileiros
- Receita Federal (consultas CNPJ/CPF)
- Banco Central (cotações)
- IBGE (tabelas de códigos)

## Auditoria Fiscal
- Log completo de operações
- Trilha de auditoria imutável
- Relatórios de não conformidades
- Backup automático de XMLs
- Sistema de alertas fiscais

## Relatórios SPED
- SPED Fiscal (EFD ICMS/IPI)
- SPED Contribuições (EFD PIS/COFINS)
- SPED ECD (Escrituração Digital)
- REINF (Retenções)

## Critérios de Entrega
- NFe/NFCe sendo emitidas corretamente
- Integração SEFAZ funcionando
- Certificados digitais configurados
- Sistema de contingência operacional
- Auditoria e conformidade ativos

## Status: 📋 AGUARDANDO MARKETPLACES