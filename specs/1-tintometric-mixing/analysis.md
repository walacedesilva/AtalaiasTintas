# Analysis: Sistema de Mistura de Tintas Tintométrica

**Phase**: `/speckit.analyze`  
**Date**: 2026-04-14  
**Status**: ⚠️ GAPS RESOLVIDOS — Pronto para `/speckit.implement`

## Resumo Executivo

| Artefato | Status |
|----------|--------|
| spec.md | ✅ Completo |
| plan.md | ✅ Completo |
| checklists/ | ✅ Aprovado |
| tasks.md | ✅ Atualizado com 50 tasks |
| Consistência spec→tasks | ✅ Todos os FR cobertos |
| Consistência plan→tasks | ✅ Todos os componentes do plan referenciados |
| Integration Tests | ✅ IT-001 a IT-005 + 4 adicionais |

## Gaps Encontrados e Resolvidos

### 🔴 GAP-1 (Crítico — RESOLVIDO): Cancel action ausente

**Problema**: Spec US2 requer que cancelamento restaure estoque. O código tinha status `CANCELADA` definido no model mas sem endpoint nem lógica de restauração.

**Resolução**: Adicionadas tasks T012a (método `cancel_mixture` em `MixtureService`) e T012b (action `cancel` em `MisturaTintaViewSet`). Task T021a cobre o teste de regressão.

### 🟡 GAP-2 (Importante — RESOLVIDO): FR-008 sem testes

**Problema**: `FormulaTintometricaViewSet` (ModelViewSet completo) existia mas não havia tasks de teste para CRUD de fórmulas.

**Resolução**: Adicionada task T012c com 4 testes cobrindo create, update, calculate action e filtragem de fórmulas inativas.

### 🟡 GAP-3 (Importante — RESOLVIDO): US4 (Etiquetas) sem IT

**Problema**: US4 (Gerar Etiquetas) não tinha integration test end-to-end. Labels sub-app existia mas o fluxo `complete → gerar etiqueta → dados completos` não era validado.

**Resolução**: Adicionada task T026a cobrindo o fluxo completo de US4.

### 🔵 GAP-4 (Menor — RESOLVIDO): 3 edge cases do spec sem cobertura

**Problema**: Spec lista 4 edge cases; apenas "pigmento indisponível" estava coberto.

**Resolução**: Adicionadas tasks T026b (fórmula não registrada), T026c (volume mínimo) e T026d (isolamento multi-loja).

### 🔵 GAP-5 (Informativo — NÃO AUTOMATABLE): SC-004

**SC-004**: "Redução de 70% no tempo de preparação" — métrica de negócio que requer observação em produção. Nenhuma task automática pode validar isso. Deve ser medido via cronometragem após implantação e comparado com baseline manual.

## Mapeamento Final FR → Tasks de Validação

| FR | Task(s) de Teste |
|----|-----------------|
| FR-001 Calcular pigmentos | T017, T021 |
| FR-002 Validar estoque | T017, T025 |
| FR-003 Baixa automática | T018, T022, T021a |
| FR-004 Histórico por cliente | T006–T009, T019 |
| FR-005 Busca por dados | T021, T023 |
| FR-006 Calcular custo | T017 |
| FR-007 Alertas mínimo | T018, T033 |
| FR-008 Cadastro fórmulas | T012c |
| FR-009 Código único | T019 |

## Mapeamento IT → Tasks

| IT Spec | Task | Edge Cases |
|---------|------|-----------|
| IT-001 Fim-a-fim | T022 | — |
| IT-002 Histórico→reprodução | T023 | T021a (cancel) |
| IT-003 Simultâneas | T024 | T026d (multi-loja) |
| IT-004 Esgotamento | T025 | T026b (fórmula inexistente) |
| IT-005 Nova fórmula | T026 | T026c (volume mínimo) |
| IT-006 US4 Etiquetas | T026a | — |

## Decisão

**✅ APROVADO para `/speckit.implement`**

Iniciar pela Phase 1 (T001–T005): migrações e configurações são pré-requisito para todas as demais tasks.

**Ordem recomendada para primeira sessão de implementação:**
1. T001 → `makemigrations tintometry`
2. T002 → migrations da sub-app labels
3. T003 → `migrate`
4. T004 → `TINTOMETRY_CONFIG` em settings.py
5. T012a → `cancel_mixture` em MixtureService
6. T012b → action `cancel` em views.py
