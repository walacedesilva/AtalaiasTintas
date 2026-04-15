# Tasks: Sistema de Mistura de Tintas Tintométrica

**Input**: Spec + Plan de `/specs/1-tintometric-mixing/`  
**Prerequisites**: spec.md ✅, plan.md ✅, checklists/ ✅  
**Generated**: 2026-04-14

**Tests**: Precisão de cálculo ≥ 99.5%, cobertura de testes ≥ 90%, testes de integração end-to-end para todos os user stories.

**Organization**: Tasks agrupadas por fase de implementação seguindo o roadmap do plan.md.

**⚠️ IMPORTANTE**: Após completar tasks.md, executar `/speckit.analyze` para validar consistência antes de implementar.

## Formato: `[ID] [P?] [US#] Descrição`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[US#]**: User story referenciada (US1, US2, US3, US4)
- Caminhos de arquivo baseados no plan.md

## Convenções de Caminho

- `backend/apps/tintometry/` — app principal tintométrica
- `backend/apps/tintometry/services/` — serviços de negócio
- `backend/apps/tintometry/labels/` — sub-app de etiquetas
- `backend/tintas_system/` — configurações Django
- `requirements/` — dependências Python

---

## Estado Atual (Pré-Tasks)

> Análise da base de código gerou este mapa do que já existe:

**✅ JÁ IMPLEMENTADO:**
- Todos os models definidos em `models.py` (MisturaTinta, ItemMistura, EstoquePigmento, EtiquetaMistura, etc.)
- Services: `FormulaCalculatorService`, `StockManagerService`, `MixtureService`, `ColorScienceService`
- ViewSets: `PigmentoViewSet`, `FormulaTintometricaViewSet`, `MisturaTintaViewSet` (com `calculate_mixture`, `confirm`), `EstoquePigmentoViewSet`
- Admin interfaces para todos os modelos principais
- Labels sub-app: `LabelGenerationViewSet`, `EtiquetaHistoryViewSet`
- URL routing para todos os ViewSets
- Dependências: qrcode, reportlab, numpy, scipy, Pillow em `requirements/base.txt`

**❌ PENDENTE (escopo dessas tasks):**
- Migration 0002 para MisturaTinta e modelos relacionados
- TINTOMETRY_CONFIG em settings
- Endpoint dedicado de histórico de cliente com busca por telefone
- colour-science library (para cálculos científicos de cor avançados)
- Testes unitários e de integração para os serviços
- Endpoints de relatórios (produção diária, uso de pigmentos)
- Endpoint quick-calculate para PDV
- Frontend React para o módulo tintométrico

---

## Phase 1: Infraestrutura Pendente (Semana 1)

**Objetivo**: Completar migrações e configurações base necessárias para o sistema funcionar

### Migrações

- [x] T001 [P] [US1,US2,US4] Gerar migration 0002 em `apps/tintometry/migrations/0002_mixture_system.py` para os modelos: MisturaTinta, ItemMistura, EstoquePigmento, EtiquetaMistura executando `python manage.py makemigrations tintometry`
- [x] T002 [P] [US4] Gerar migration para sub-app labels: verificar e gerar migrations em `apps/tintometry/labels/migrations/` se inexistentes para LabelTemplate, LabelPrintJob, LabelPrintQueue, PrinterConfiguration
- [x] T003 [US1,US2,US3,US4] Aplicar todas as migrations de tintometry no banco: `python manage.py migrate tintometry` (depende de T001, T002)

### Configurações

- [x] T004 [P] [US1,US2] Adicionar bloco `TINTOMETRY_CONFIG` em `backend/tintas_system/settings.py` com chaves: `DEFAULT_FORMULA_VOLUME`, `MINIMUM_MIXTURE_VOLUME` (0.1), `MAXIMUM_MIXTURE_VOLUME` (20.0), `PIGMENT_PRECISION_ML` (0.1), `AUTO_GENERATE_MIXTURE_CODE`, `ENABLE_STOCK_ALERTS`, `COLOR_TOLERANCE_DELTA_E` (3.0)
- [x] T005 [P] [US4] Instalar colour-science: adicionar `colour-science>=0.4.2` em `requirements/base.txt` e instalar no venv

**Checkpoint**: Sistema migrado e configurado — pode-se usar o admin para cadastrar dados de teste

---

## Phase 2: Histórico de Clientes e Busca (Semana 1-2)

**Objetivo**: Completar o fluxo de US3 — histórico de cores por cliente com busca por telefone

### CustomerHistory Endpoint

- [ ] T006 [P] [US3] Criar `CustomerHistoryViewSet` em `apps/tintometry/views.py` com `get_queryset` filtrando por `cliente_id` e ação extra `search_by_phone` (query param `phone`) que retorna histórico das últimas 10 misturas por telefone
- [ ] T007 [P] [US3] Criar `CustomerHistorySerializer` em `apps/tintometry/serializers.py` com campos: `codigo_mistura`, `cor`, `data_confirmacao`, `volume_produzido`, `observacoes_cliente`, `formula_id`
- [ ] T008 [US3] Registrar `CustomerHistoryViewSet` no router em `apps/tintometry/urls.py` como `r'customer-history'` (depende de T006, T007)
- [ ] T009 [P] [US3] Adicionar ação `reproduce_from_history` em `MisturaTintaViewSet` que recebe `mistura_id` e retorna o cálculo pré-preenchido com a fórmula original para nova mistura idêntica

**Checkpoint**: Funcionário consegue buscar cliente por telefone e reproduzir cor anterior

---

## Phase 3: Endpoints de Relatórios e PDV (Semana 2)

**Objetivo**: Endpoints para produção diária, uso de pigmentos e cálculo rápido para PDV

### Report Endpoints

- [ ] T010 [P] [US2] Criar view `daily_production_report` (APIView) em `apps/tintometry/views.py` com query params `date`, `loja_id` retornando total de misturas, volume produzido, custo total e ranking dos 10 pigmentos mais utilizados no dia
- [ ] T011 [P] [US2] Criar view `pigment_usage_report` (APIView) em `apps/tintometry/views.py` com query params `start_date`, `end_date`, `loja_id` retornando consumo por pigmento com totais e comparação com período anterior
- [ ] T012 [US2] Adicionar URLs dos relatórios em `apps/tintometry/urls.py`: `path('reports/daily-production/', ...)` e `path('reports/pigment-usage/', ...)` (depende de T010, T011)

### Cancelamento de Mistura com Restauração de Estoque (GAP-1)

- [x] T012a [US2] Implementar método `cancel_mixture(mistura_id, motivo)` em `apps/tintometry/services/mixture_service.py` que: muda status para CANCELADA, restaura saldo_ml de cada ItemMistura no EstoquePigmento via StockManagerService, e registra motivo_cancelamento
- [x] T012b [US2] Adicionar action `cancel` em `MisturaTintaViewSet` em `apps/tintometry/views.py` com POST body `{motivo}` que chama `MixtureService.cancel_mixture` — apenas misturas com status CALCULADA ou CONFIRMADA são canceláveis (depende de T012a)

### Testes Formula CRUD (GAP-2)

- [ ] T012c [P] [US1] Criar testes de `FormulaTintometricaViewSet` em `apps/tintometry/tests/test_views.py`: `test_create_formula_with_items`, `test_update_formula_proportions`, `test_calculate_mixture_action_on_formula`, `test_formula_inactive_excluded_from_list`

### Quick Calculate (PDV)

- [ ] T013 [P] [US1] Criar view `quick_formula_calculation` (APIView) em `apps/tintometry/views.py` com POST body `{formula_id, volume, loja_id}` que retorna cálculo sem criar MisturaTinta — endpoint otimizado para uso no PDV com resposta < 1s
- [ ] T014 [US1] Adicionar URL `path('quick-calculate/', ...)` em `apps/tintometry/urls.py` (depende de T013)

**Checkpoint**: Relatórios acessíveis e endpoint quick-calculate funcional para PDV

---

## Phase 4: Testes Unitários (Semana 2-3)

**Objetivo**: Cobrir os serviços críticos com testes antes de validar end-to-end

### Estrutura de Testes

- [ ] T015 [P] Criar estrutura de testes em `apps/tintometry/tests/` com `__init__.py`, `test_models.py`, `test_services.py`, `test_views.py`, `test_integrations.py` e diretório `fixtures/`
- [ ] T016 [P] Criar fixtures em `apps/tintometry/tests/fixtures/`: `pigments.json` (5 pigmentos padrão com custo_ml e cor_hex), `formulas.json` (2 fórmulas com itens), `colors.json` (3 cores RAL com valores Lab)

### Testes de Serviços

- [ ] T017 [P] [US1] Criar testes de `FormulaCalculatorService` em `apps/tintometry/tests/test_services.py`:
  - `test_calculate_pigment_quantities_precision` — precisão de 0.1ml
  - `test_proportional_scaling_correctness` — escalonamento proporcional
  - `test_stock_availability_check_blocks_when_insufficient` — bloqueic por estoque
  - `test_calculate_returns_stock_alerts_when_short` — alertas retornados
  - `test_cost_breakdown_accuracy` — custo total correto
- [ ] T018 [P] [US2] Criar testes de `StockManagerService` em `apps/tintometry/tests/test_services.py`:
  - `test_execute_stock_reduction_updates_saldo_ml` — baixa correta
  - `test_restock_alert_triggered_at_minimum` — alerta no mínimo
  - `test_no_negative_stock_without_override` — bloqueio de negativo
  - `test_concurrent_stock_reduction_consistency` — transação atômica
- [ ] T019 [P] [US1,US2] Criar testes de `MixtureService` em `apps/tintometry/tests/test_services.py`:
  - `test_create_mixture_generates_unique_code` — código único
  - `test_confirm_mixture_changes_status` — status CONFIRMADA
  - `test_cancel_mixture_restores_stock` — estoque restaurado
  - `test_customer_history_updated_after_completion` — histórico salvo

### Testes de Models

- [ ] T020 [P] [US1,US2] Criar testes em `apps/tintometry/tests/test_models.py`:
  - `test_mistura_codigo_uniqueness` — unicidade do código
  - `test_estoque_pigmento_unique_together` — unique_together pigmento+loja
  - `test_item_mistura_stock_before_after` — campos before/after
  - `test_mistura_status_transitions` — transições de status válidas

### Testes de Views/API

- [ ] T021 [P] [US1] Criar testes de API em `apps/tintometry/tests/test_views.py`:
  - `test_calculate_mixture_endpoint_returns_quantities` — endpoint calculate
  - `test_calculate_mixture_returns_409_when_stock_short` — conflito de estoque
  - `test_confirm_mixture_reduces_stock` — confirmação atualiza estoque
  - `test_quick_calculate_responds_under_1_second` — performance PDV
  - `test_customer_history_search_by_phone` — busca por telefone

**Checkpoint**: Cobertura de testes ≥ 90% nos serviços críticos

---

## Phase 5: Testes de Integração End-to-End (Semana 3)

**Objetivo**: Validar os 5 integration tests do spec end-to-end (IT-001 a IT-005)

- [ ] T021a [P] [US2] IT-002b: Criar teste de cancelamento — mistura CONFIRMADA → cancel com motivo → estoque restaurado ao valor anterior para todos os pigmentos (depende de T012b, T020)
- [ ] T022 [US1,US2] IT-001: Criar `tests/tintometry/test_integration_flow.py` — fluxo completo: seleção de cor → cálculo de fórmula → verificação de estoque → confirmação → baixa automática → registro no histórico (depende de T015-T021)
- [ ] T023 [US3] IT-002: Criar teste — busca de cliente com histórico → seleção de cor anterior → reproduce_from_history → nova mistura idêntica (depende de T009, T022)
- [ ] T024 [US1,US2] IT-003: Criar teste — múltiplas misturas simultâneas com `threading` → baixas paralelas → validação de consistência final de saldos (depende de T022)
- [ ] T025 [US1] IT-004: Criar teste — esgotamento de pigmento → tentativa de nova mistura → bloqueio correto com alertas no response (depende de T022)
- [ ] T026 [US2] IT-005: Criar teste — cadastro de nova fórmula via admin/API → primeira utilização → cálculo preciso → baixa correta de todos componentes (depende de T022)
- [ ] T026a [P] [US4] IT-006: Criar teste para US4 end-to-end — `complete_mixture` → verificar que EtiquetaMistura é criada com `codigo_etiqueta` único → `generate_label` retorna dados completos (codigo, data, cliente, composição, QR code) (depende de T022)
- [ ] T026b [P] [US1] Edge case: Criar teste `test_formula_not_found_for_color_returns_404` — cor sem fórmula cadastrada retorna erro apropriado ao tentar calcular
- [ ] T026c [P] [US1] Edge case: Criar teste `test_minimum_volume_validation_rejects_below_100ml` — volume < MINIMUM_MIXTURE_VOLUME deve retornar 400 com mensagem clara
- [ ] T026d [P] [US1,US2] Edge case: Criar teste `test_multistore_stock_isolation` — EstoquePigmento de loja A não é afetado por mistura da loja B usando o mesmo pigmento

**Checkpoint**: Todos os integration tests do spec passando, incluindo US4 e edge cases

---

## Phase 6: Frontend React (Semana 4)

**Objetivo**: Interface React para o módulo tintométrico no frontend existente

### Tipos e API Client

- [ ] T027 [P] [US1] Criar types em `frontend/src/types/tintometry.ts`: `Pigmento`, `FormulaTintometrica`, `MisturaTinta`, `EstoquePigmento`, `CalculationResult`, `StockAlert`, `CustomerHistoryItem`
- [ ] T028 [P] [US1] Criar API client em `frontend/src/api/tintometry.ts` com funções: `calculateFormula(formulaId, volume, lojaId)`, `quickCalculate(data)`, `confirmMixture(id)`, `getCustomerHistory(phone)`, `getLowStockAlerts(lojaId)`

### Componentes

- [ ] T029 [P] [US1] Criar `FormulaCalculator` component em `frontend/src/components/tintometry/FormulaCalculator.tsx` — seletor de cor, input de volume, botão calcular, exibição de lista de pigmentos com quantidades
- [ ] T030 [P] [US1] Criar `StockAvailabilityBadge` component em `frontend/src/components/tintometry/StockAvailabilityBadge.tsx` — badge colorido (verde/amarelo/vermelho) para disponibilidade de cada pigmento
- [ ] T031 [P] [US3] Criar `CustomerColorHistory` component em `frontend/src/components/tintometry/CustomerColorHistory.tsx` — busca por telefone, lista de cores anteriores, botão "reproduzir esta cor"
- [ ] T032 [P] [US1] Criar `MixtureConfirmation` component em `frontend/src/components/tintometry/MixtureConfirmation.tsx` — resumo da mistura, custo total, botão confirmar produção
- [ ] T033 [P] [US2] Criar `LowStockAlerts` component em `frontend/src/components/tintometry/LowStockAlerts.tsx` — lista de pigmentos abaixo do mínimo com percentual de estoque

### Páginas

- [ ] T034 [US1,US3] Criar página `TintometryPage` em `frontend/src/pages/TintometryPage.tsx` integrando os 5 componentes acima no fluxo: busca cliente → seleção fórmula → cálculo → confirmação (depende de T027-T033)
- [ ] T035 [US2] Criar página `PigmentStockPage` em `frontend/src/pages/PigmentStockPage.tsx` com gerenciamento de estoque de pigmentos, alertas e histórico de movimentações (depende de T027, T028)
- [ ] T036 [US1,US2,US3,US4] Adicionar rotas em `frontend/src/App.tsx`: `/tintometry`, `/tintometry/stock` (depende de T034, T035)

**Checkpoint**: Interface React funcional para fluxo completo de mistura de tintas

---

## Phase 7: Performance e Qualidade Final (Semana 5)

**Objetivo**: Validar critérios de performance do spec e preparar para produção

### Performance Validation

- [ ] T037 [P] [US1] Criar teste de performance para `FormulaCalculatorService.calculate_mixture_quantities` — deve responder em < 2 segundos mesmo com 50 pigmentos na fórmula
- [ ] T038 [P] [US2] Criar teste de performance para `StockManagerService.execute_stock_reduction` — deve completar em < 500ms incluindo transaction e lock
- [ ] T039 [P] [US3] Criar teste de performance para busca de histórico por telefone — deve responder em < 1 segundo com 1000+ misturas no banco
- [ ] T040 [P] [US4] Criar índices de banco de dados: adicionar `Meta.indexes` no model `MisturaTinta` para `(cliente_telefone, data_confirmacao)` e `EstoquePigmento` para `(loja_id, saldo_ml)`

### Checklist de Qualidade

- [ ] T041 [P] Validar todos os itens do checklist `specs/1-tintometric-mixing/checklists/requirements.md`
- [ ] T042 [P] [US4] Verificar que `generate_label` action existe em `MisturaTintaViewSet` ou `labels/` — se não existir, adicionar ação `generate_label` no `MisturaTintaViewSet` que delega para `LabelGenerationViewSet`
- [ ] T043 [P] Executar `python manage.py check` e resolver todos os warnings/errors de configuração

**Checkpoint**: Sistema completo, performático e pronto para `/speckit.analyze`

---

## Resumo das Fases

| Fase | Semana | Foco | Tasks |
|------|--------|------|-------|
| 1 | 1 | Migrações + Config | T001-T005 |
| 2 | 1-2 | Histórico cliente | T006-T009 |
| 3 | 2 | Relatórios + PDV | T010-T014 |
| 4 | 2-3 | Testes unitários | T015-T021 |
| 5 | 3 | Integração E2E | T022-T026 |
| 6 | 4 | Frontend React | T027-T036 |
| 7 | 5 | Performance + QA | T037-T043 |

**Total**: 50 tasks | **Dependências críticas**: T003 depende de T001,T002 | T008 depende de T006,T007 | T012b depende de T012a | T021a depende de T012b | T022-T026 dependem de T015-T021 | T026a depende de T022

---

**Próximo**: Rodar `/speckit.analyze` para validar consistência entre spec.md, plan.md e este tasks.md antes de iniciar implementação.
