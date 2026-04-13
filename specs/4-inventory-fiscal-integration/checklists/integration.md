# Integration Checklist - Inventory & Fiscal Integration

**Purpose**: Ensure robust SEFAZ API integration and Django app coordination
**Created**: 2026-04-12  
**Feature**: [Inventory & Fiscal Integration](../spec.md)

## SEFAZ WebService Integration

### Connection Reliability
- [ ] SEFAZ service status checked before NFe submission
- [ ] Multiple SEFAZ endpoints configured per state (primary/backup)
- [ ] Automatic failover to backup endpoints on primary failure
- [ ] Network connectivity issues handled gracefully
- [ ] SSL/TLS certificate validation for SEFAZ endpoints
- [ ] Connection pooling configured for optimal performance

### Rate Limiting Compliance
- [ ] 1 request per 2 seconds per CNPJ enforced at application level
- [ ] Rate limiting queue prevents SEFAZ rejection
- [ ] Multi-store/CNPJ rate limiting handled separately
- [ ] Rate limit violations logged and monitored
- [ ] Queue management for high-volume periods
- [ ] Emergency bypass for critical NFe (with approval)

### Error Handling & Retry Logic
- [ ] Exponential backoff implemented (2s, 4s, 8s, 16s intervals)
- [ ] Transient errors (timeout, network) retried automatically
- [ ] Permanent errors (invalid certificate) fail immediately
- [ ] Retry attempts logged with timestamp and reason
- [ ] Manual retry queue for failed automatic attempts
- [ ] Maximum retry limit prevents infinite loops

### SOAP/XML Processing
- [ ] SOAP envelope correctly formatted for SEFAZ layout 4.00
- [ ] XML schema validation before submission
- [ ] Digital signature applied correctly to XML
- [ ] XML parsing handles all SEFAZ response formats
- [ ] Encoding (UTF-8) preserved throughout processing
- [ ] Large XML documents handled efficiently

### Status Tracking
- [ ] NFe status synchronization with SEFAZ
- [ ] Periodic status queries for pending NFe
- [ ] Authorization protocol properly parsed and stored
- [ ] Rejection codes mapped to user-friendly messages
- [ ] Status change notifications to relevant users
- [ ] Historical status tracking maintained

## Django App Coordination

### Cross-App Data Flow
- [ ] Sales app triggers inventory reservation correctly
- [ ] Inventory confirmation triggers fiscal processing
- [ ] NFe completion updates sales status appropriately
- [ ] Failed operations rollback changes in all affected apps
- [ ] App dependencies clearly defined and documented
- [ ] Inter-app communication maintains transaction boundaries

### Shared Model Consistency
- [ ] Cliente model changes synchronized between sales/fiscal
- [ ] Produto model updates reflected in all dependent apps
- [ ] ConfiguracaoFiscal changes applied immediately
- [ ] Company/Loja data consistent across all operations
- [ ] User permissions validated across all apps
- [ ] Migration scripts maintain cross-app referential integrity

### Event Handling
- [ ] Django signals fire correctly for all state changes
- [ ] Signal handlers maintain transactional integrity  
- [ ] Signal processing errors don't break main operations
- [ ] Event ordering preserved for dependent operations
- [ ] Signal handler performance doesn't impact user experience
- [ ] Event replay capability for failed processing

### Service Layer Integration
- [ ] EstoqueService integrates cleanly with sales workflow
- [ ] NFEService coordinates with inventory stock movements
- [ ] ConversaoService provides consistent results across apps
- [ ] SefazClient handles all fiscal integrations uniformly
- [ ] Service interfaces clearly defined and stable
- [ ] Service error handling propagates appropriately

## Event-Driven Architecture

### Django Signals Implementation
- [ ] post_save signals trigger NFe processing correctly
- [ ] pre_delete signals clean up reservations appropriately
- [ ] Signal handlers are idempotent (safe to retry)
- [ ] Signal processing maintains database consistency
- [ ] Circular signal dependencies prevented
- [ ] Signal handler exceptions logged and monitored

### Celery Task Processing
- [ ] Async tasks queued correctly from signal handlers
- [ ] Task failures don't corrupt system state
- [ ] Task retry logic preserves data integrity
- [ ] Task progress monitoring implemented
- [ ] Dead letter queue handling for failed tasks
- [ ] Task prioritization working correctly (urgent NFe first)

### Message Queue Reliability
- [ ] Redis message persistence configured correctly
- [ ] Message delivery guarantees appropriate for operations
- [ ] Queue monitoring and alerting implemented
- [ ] Queue backup and recovery procedures tested
- [ ] Message serialization handles all data types
- [ ] Queue performance adequate for peak loads

### Workflow Orchestration
- [ ] Sale → Reservation → Stock → NFe workflow reliable
- [ ] Compensation logic handles partial failures
- [ ] Workflow state tracking accurate and queryable
- [ ] Long-running workflows monitored for completion
- [ ] Workflow timeouts prevent indefinite processing
- [ ] Manual intervention points clearly defined

## External API Integration

### HTTP Client Configuration
- [ ] Connection timeout appropriate for SEFAZ (30s)
- [ ] Read timeout balances reliability/performance (60s)
- [ ] HTTP connection keep-alive configured properly
- [ ] User agent properly identifies application to SEFAZ
- [ ] Request/response logging excludes sensitive data
- [ ] HTTP status codes handled appropriately

### Authentication Management
- [ ] Digital certificate authentication working correctly
- [ ] Certificate renewal handled without service interruption
- [ ] Multi-certificate support for different stores/CNPJs
- [ ] Certificate validation errors handled gracefully
- [ ] Certificate expiration monitoring and alerting
- [ ] Backup authentication methods configured

### Data Transformation
- [ ] Internal data model maps correctly to SEFAZ XML format
- [ ] Tax calculations match SEFAZ requirements exactly
- [ ] Product codes translated appropriately for fiscal use
- [ ] Customer data formatted per SEFAZ specifications
- [ ] Date/time formatting matches SEFAZ requirements
- [ ] Decimal precision preserved through transformations

### Response Processing
- [ ] SEFAZ authorization responses parsed correctly
- [ ] Error responses mapped to appropriate actions
- [ ] Status change notifications processed accurately
- [ ] Response validation ensures data integrity
- [ ] Unexpected response formats handled gracefully
- [ ] Response caching implemented where appropriate

## Integration Testing

### End-to-End Workflows
- [ ] Complete sale-to-NFe workflow tested end-to-end
- [ ] B2B automatic NFe generation tested thoroughly
- [ ] B2C manual NFe option tested and validated
- [ ] Stock reservation expiration tested completely
- [ ] Manager override workflow tested with permissions
- [ ] Multi-unit product sales tested across all conversion scenarios

### Error Scenario Testing
- [ ] SEFAZ service outage handling tested
- [ ] Network timeout scenarios validated
- [ ] Certificate expiration/invalid scenarios tested
- [ ] Database transaction failure recovery tested
- [ ] Concurrent access conflicts resolved correctly
- [ ] Partial system failure recovery validated

### Performance Integration Testing
- [ ] High-volume concurrent operations tested
- [ ] Peak load scenarios validated (Black Friday, etc.)
- [ ] Memory usage under sustained load monitored
- [ ] Database performance under integration load tested
- [ ] External service degradation impact assessed
- [ ] Recovery time from failures measured and acceptable

### Mock Testing Strategy
- [ ] SEFAZ integration tested with VCR.py recorded responses
- [ ] Mock SEFAZ responses cover all success scenarios
- [ ] Mock SEFAZ responses include all error conditions
- [ ] Integration tests run without external dependencies
- [ ] Mock data represents realistic production scenarios
- [ ] Mock testing maintains accuracy with real SEFAZ behavior