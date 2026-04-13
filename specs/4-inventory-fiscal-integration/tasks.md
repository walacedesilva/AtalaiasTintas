# Tasks: Sistema Integrado de Controle de Estoque e NFe

**Input**: Design documents from `/specs/4-inventory-fiscal-integration/`
**Prerequisites**: plan.md ✅, spec.md ✅, checklists/ ✅

**Tests**: Comprehensive testing required per checklist requirements - 95% code coverage, integration tests, SEFAZ mock testing

**Organization**: Tasks are grouped by implementation phases to enable systematic build-out of inventory and fiscal integration system.

**⚠️ IMPORTANT**: After generating tasks.md, ALWAYS run `/speckit.analyze` to validate consistency between spec, plan, and tasks before implementation begins.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions per plan.md

## Path Conventions

Based on plan.md structure: 
- `apps/inventory/` - Multi-unit inventory management
- `apps/fiscal/` - NFe processing and SEFAZ integration
- `apps/sales/` - Enhanced sales with inventory integration
- `apps/core/` - Event handling and shared services
- `static/js/` - Frontend JavaScript components
- `templates/` - HTML templates
- `requirements/` - New package dependencies

---

## Phase 1: Infrastructure Setup (Weeks 1-2)

**Purpose**: Database models, migrations, and core services foundation

### Database Models & Migrations

- [x] T001 [P] [US4] Create UnidadeMedida model in apps/inventory/models.py with codigo, nome, sigla, tipo fields
- [x] T002 [P] [US4] Create ProdutoUnidade model in apps/inventory/models.py with produto, unidade, unidade_base, fator_conversao fields  
- [x] T003 [P] [US1] Create EstoqueReserva model in apps/inventory/models.py with produto, quantidade, sessao_checkout, expira_em fields
- [x] T004 [P] [US1,US3] Create MovimentacaoEstoque model in apps/inventory/models.py with complete audit trail fields
- [x] T005 [P] [US2] Enhance NotaFiscalEletronica model in apps/fiscal/models.py with automation fields (tipo_emissao, status, tentativas_envio)
- [x] T006 [P] [US2] Create ItemNotaFiscalEletronica model in apps/fiscal/models.py with multi-unit support fields
- [x] T007 [US1,US2,US4] Create migration file 0003_lote_validade_entrada.py for inventory models (depends on T001-T004) — includes LoteProduto, EntradaMercadoria, EntradaMercadoriaItem
- [x] T008 [US2] Fiscal models with automation fields already included in 0002_initial.py
- [ ] T009 [US1,US2] Create migration file for sales model extensions (Phase 4)

### Core Service Layer

- [x] T010 [P] [US1,US4] Create EstoqueService class in apps/inventory/services.py with stock management methods
- [x] T011 [P] [US4] Create ConversaoService class in apps/inventory/services.py with multi-unit conversion logic
- [x] T012 [P] [US2] Create NFEService skeleton in apps/fiscal/services.py (stub — full impl Phase 3)
- [x] T013 [P] [US2] Create SefazClient stub in apps/fiscal/services.py (full impl Phase 3)
- [x] T014 [P] [US1,US2] Create event signal handlers in apps/core/signals.py for sale → inventory → NFe workflow

### Basic Configuration

- [x] T015 [P] xmltodict already in requirements/base.txt; celery[redis] in base.txt
- [x] T016 [P] Celery configuration already in tintas_system/settings/base.py
- [ ] T017 [P] Create NFe environment variables template in .env.example
- [x] T018 [P] [US1,US2] Redis already configured in base.py (django-redis)

**Checkpoint**: Foundation models and services ready - can begin feature implementation

---

## Phase 2: Inventory System (Weeks 3-4)

**Purpose**: Multi-unit inventory management with reservation system

### Multi-Unit Conversion System

- [x] T019 [US4] Implement calcular_disponibilidade method in EstoqueService (depends on T010)
- [x] T020 [US4] Implement converter_quantidade method in ConversaoService (depends on T011)
- [x] T021 [US4] Implement obter_unidade_base method in ConversaoService (depends on T011)
- [x] T022 [P] [US4] Create unit conversion admin interface in apps/inventory/admin.py (ProdutoUnidadeAdmin + ProdutoVariacaoAdmin with inline)
- [ ] T023 [P] [US4] Create multi-unit calculator JavaScript component in static/js/inventory/multi-unit-calculator.js
- [x] T024 [US4] Create ConversaoUnidadeViewSet in apps/inventory/apis.py for unit conversion API (depends on T020-T021)

### Stock Reservation System

- [x] T025 [US1] Implement criar_reserva method in EstoqueService (depends on T019)
- [x] T026 [US1] Implement confirmar_reservas method in EstoqueService (depends on T025)
- [x] T027 [US1] Create EstoqueReservaViewSet in apps/inventory/apis.py for reservation management (depends on T025-T026)
- [ ] T028 [P] [US1] Create stock reservation JavaScript component in static/js/inventory/stock-reservation.js
- [ ] T029 [P] [US1] Create stock availability template in templates/inventory/stock-availability.html
- [x] T030 [US1] Create Celery task limpar_reservas_expiradas_v2 in apps/inventory/tasks.py (depends on T010)

### Stock Movement Management

- [x] T031 [US1,US3] Implement processar_baixa_venda method in EstoqueService (depends on T026)
- [x] T032 [P] [US3] Create EstoqueConsultaAPIView in apps/inventory/apis.py for real-time stock queries
- [x] T033 [P] [US1,US3] Create MovimentacaoEstoque admin interface in apps/inventory/admin.py
- [x] T034 [US3] Implement entrada de produtos workflow in EstoqueService.processar_entrada + EntradaMercadoriaService (depends on T031)

### Lotes & Validade Control (NEW — FR-001)

- [x] T034a [P] Create LoteProduto model in apps/inventory/models.py with numero_lote, data_validade, quantidade_atual, status fields
- [x] T034b [P] Create LoteService in apps/inventory/services.py with FIFO/FEFO, proximos_vencimento, marcar_vencidos methods
- [x] T034c [P] Create LoteViewSet in apps/inventory/apis.py with proximos-vencimento and marcar-vencidos actions
- [x] T034d [P] Create LoteProdutoAdmin in apps/inventory/admin.py with validade status display
- [x] T034e [P] Create marcar_lotes_vencidos Celery task in apps/inventory/tasks.py
- [ ] T034f Create unit tests for LoteService in tests/inventory/test_lote_service.py

### XML NF-e Importer (NEW — FR-004 expansion)

- [x] T034g [P] Create XmlNFeParser in apps/fiscal/services.py — parses layout NF-e 4.00 XML
- [x] T034h [P] Create EntradaMercadoria + EntradaMercadoriaItem models in apps/inventory/models.py
- [x] T034i [P] Create EntradaMercadoriaService.importar_xml in apps/fiscal/services.py (idempotent by chave_acesso)
- [x] T034j [P] Create EntradaMercadoriaService.confirmar_entrada — updates stock via EstoqueService
- [x] T034k [P] Create EntradaMercadoriaViewSet with importar-xml, confirmar, vincular-item actions
- [x] T034l [P] Create EntradaMercadoriaAdmin with inline items and XML viewer
- [ ] T034m Create unit tests for XmlNFeParser in tests/fiscal/test_xml_nfe_parser.py

**Checkpoint**: Multi-unit inventory system, lotes/validade control and XML NF-e importer fully functional

---

## Phase 3: NFe Integration (Weeks 5-7)

**Purpose**: SEFAZ integration and automatic NFe processing

### SEFAZ Client Implementation

- [ ] T035 [US2] Implement autorizar_nfe method in SefazClient (depends on T013)
- [ ] T036 [US2] Implement consultar_situacao method in SefazClient (depends on T035)
- [ ] T037 [US2] Implement cancelar_nfe method in SefazClient (depends on T036)
- [ ] T038 [P] [US2] Create SEFAZ exception classes in apps/fiscal/sefaz/exceptions.py
- [ ] T039 [P] [US2] Create SEFAZ validators in apps/fiscal/sefaz/validators.py
- [ ] T040 [US2] Create SefazIntegracaoAPIView in apps/fiscal/apis.py for status checks (depends on T035-T037)

### NFe Business Logic

- [ ] T041 [US2] Implement deve_emitir_nfe_automatica method in NFEService (depends on T012)
- [ ] T042 [US2] Implement processar_nfe_venda method in NFEService (depends on T041)
- [ ] T043 [US2] Implement gerar_xml_nfe method in NFEService (depends on T042)
- [ ] T044 [US2] Implement enviar_sefaz method in NFEService (depends on T043,T035)
- [ ] T045 [P] [US2] Create NFe XML generation templates in apps/fiscal/xml_templates/
- [ ] T046 [US2] Create NFEAutomacaoViewSet in apps/fiscal/apis.py (depends on T041-T044)

### Async NFe Processing

- [ ] T047 [US2] Create processar_nfe_async Celery task in apps/fiscal/tasks.py (depends on T042)
- [ ] T048 [US2] Create retry_nfe_falhadas Celery task in apps/fiscal/tasks.py (depends on T047)
- [ ] T049 [P] [US2] Create NFe automation JavaScript in static/js/fiscal/nfe-automation.js
- [ ] T050 [P] [US2] Create SEFAZ status JavaScript in static/js/fiscal/sefaz-status.js
- [ ] T051 [US2] Update sales post_save signal to trigger NFe processing (depends on T047)

### NFe Management Interface  

- [ ] T052 [P] [US2] Create NFe automation dashboard template in templates/fiscal/nfe-automation-dashboard.html
- [ ] T053 [P] [US2] Create manual retry queue template in templates/fiscal/manual-retry-queue.html
- [ ] T054 [P] [US2] Enhanced NFe admin interface in apps/fiscal/admin.py
- [ ] T055 [US2] Create NFe manual retry workflow (depends on T048)

**Checkpoint**: SEFAZ integration complete - NFe generation and processing working

---

## Phase 4: Sales Integration (Week 8)

**Purpose**: Complete sales workflow with inventory and fiscal integration

### Enhanced Sales Workflow

- [ ] T056 [US1,US2] Update Venda model with NFe automation fields in apps/sales/models.py
- [ ] T057 [US1,US2] Update ItemVenda model with multi-unit fields in apps/sales/models.py  
- [ ] T058 [US1] Update sales checkout to use reservation system (depends on T027)
- [ ] T059 [US2] Integrate NFe automation into sales completion (depends on T051)
- [ ] T060 [US1] Update sales cancellation to release reservations (depends on T058)

### Sales API Updates

- [ ] T061 [US1,US2] Update sales APIs to handle reservations and NFe triggers (depends on T058-T059)
- [ ] T062 [P] [US1] Update checkout frontend to show stock availability in real-time
- [ ] T063 [P] [US2] Add NFe status display to sales interface
- [ ] T064 [US1] Add manager override interface for insufficient stock (depends on T061)

### Business Rule Implementation

- [ ] T065 [US2] Implement B2B vs B2C NFe differentiation logic (depends on T041)
- [ ] T066 [P] [US1] Add inventory validation policies to sales workflow  
- [ ] T067 [P] [US4] Add multi-unit price calculation to sales
- [ ] T068 [US5] Create complete rastreabilidade query interface (depends on all previous)

**Checkpoint**: Complete sales workflow with inventory and fiscal integration working end-to-end

---

## Phase 5: Testing & Quality Assurance (Week 9)

**Purpose**: Comprehensive testing and deployment preparation

### Unit Testing

- [ ] T069 [P] Create EstoqueService unit tests in tests/inventory/test_services.py
- [ ] T070 [P] Create ConversaoService unit tests in tests/inventory/test_conversao.py  
- [ ] T071 [P] Create NFEService unit tests in tests/fiscal/test_nfe_service.py
- [ ] T072 [P] Create SefazClient unit tests with mocks in tests/fiscal/test_sefaz_integration.py
- [ ] T073 [P] Create reservation system tests in tests/inventory/test_reservations.py

### Integration Testing

- [ ] T074 Create complete sale workflow integration test in tests/integration/test_inventory_fiscal_flow.py (depends on T068)
- [ ] T075 Create B2B automatic NFe integration test (depends on T074)
- [ ] T076 Create B2C manual NFe integration test (depends on T075)  
- [ ] T077 Create multi-unit conversion integration test (depends on T074)
- [ ] T078 Create manager override integration test (depends on T074)

### SEFAZ Mock Testing

- [ ] T079 [P] Create VCR cassettes for SEFAZ responses in tests/fiscal/cassettes/
- [ ] T080 Create SEFAZ authorization success test with VCR (depends on T079)
- [ ] T081 Create SEFAZ rejection handling test with VCR (depends on T079)
- [ ] T082 Create SEFAZ timeout/error handling test (depends on T079)

### Performance Testing

- [ ] T083 [P] Create stock query performance tests (target < 1s)
- [ ] T084 [P] Create NFe processing performance tests (target < 30s)  
- [ ] T085 [P] Create reservation cleanup performance tests (target < 5min)
- [ ] T086 Create concurrent access performance tests (depends on T083-T085)

### Security & Compliance Testing

- [ ] T087 [P] Validate fiscal compliance checklist requirements
- [ ] T088 [P] Validate security checklist requirements  
- [ ] T089 [P] Validate data integrity checklist requirements
- [ ] T090 Create certificate management security test (depends on T087-T089)

### Deployment Preparation

- [ ] T091 [P] Create feature flag configuration for gradual rollout
- [ ] T092 [P] Create database migration rollback procedures
- [ ] T093 [P] Create deployment monitoring and alerting
- [ ] T094 [P] Create operational runbook for production support
- [ ] T095 Create production deployment checklist (depends on T091-T094)

**Checkpoint**: All testing complete, system ready for production deployment

---

## Development Phases Summary

**Phase 1 (Weeks 1-2)**: Infrastructure - Models, migrations, basic services  
**Dependencies**: T001-T018 must complete before Phase 2

**Phase 2 (Weeks 3-4)**: Inventory System - Multi-unit, reservations, stock management  
**Dependencies**: T019-T034 must complete before Phase 3

**Phase 3 (Weeks 5-7)**: NFe Integration - SEFAZ client, automation logic, XML generation  
**Dependencies**: T035-T055 must complete before Phase 4

**Phase 4 (Week 8)**: Sales Integration - Complete workflow integration  
**Dependencies**: T056-T068 must complete before Phase 5

**Phase 5 (Week 9)**: Testing & Deployment - Quality assurance and production readiness  
**Dependencies**: T069-T095 complete the implementation

## Critical Success Metrics

- [ ] Stock queries respond in < 1 second (Performance checklist)
- [ ] NFe emission completes in < 30 seconds (Performance checklist)  
- [ ] 95% unit test coverage achieved (Testing requirements)
- [ ] All fiscal compliance checkpoints validated (Compliance checklist)
- [ ] All security checkpoints validated (Security checklist)
- [ ] Integration tests pass for all user stories (Integration checklist)
- [ ] SEFAZ integration tested with full error scenario coverage (Integration checklist)

## Risk Mitigation

**SEFAZ Integration Risk**: Tasks T079-T082 provide comprehensive mock testing to reduce production integration issues

**Performance Risk**: Tasks T083-T086 validate performance requirements before production deployment  

**Data Integrity Risk**: Tasks T087-T089 ensure multi-unit conversions and atomic transactions work correctly

**Security Risk**: Task T090 validates certificate management and fiscal data protection

**Deployment Risk**: Tasks T091-T095 provide safe rollout procedures with rollback capability

---

**Next Phase**: 📊 **Analysis** - Run `/speckit.analyze` to validate spec → plan → tasks consistency before implementation