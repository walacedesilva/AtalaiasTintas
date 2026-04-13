# Data Integrity Checklist - Inventory & Fiscal Integration

**Purpose**: Ensure accurate stock movements, atomic transactions, and data consistency
**Created**: 2026-04-12
**Feature**: [Inventory & Fiscal Integration](../spec.md)

## Multi-Unit Conversion Accuracy

### Conversion Logic
- [ ] Base unit conversion factors mathematically validated
- [ ] Decimal precision maintained throughout conversions (6 decimal places)
- [ ] Rounding errors minimized using proper algorithms
- [ ] Volume conversions (L↔mL↔gal) accurate to 0.001%
- [ ] Weight conversions (kg↔g↔lb) maintain precision
- [ ] Custom paint can sizes (1L, 3.6L, 18L) correctly mapped

### Unit Configuration Integrity
- [ ] Each product has exactly one base unit defined
- [ ] Conversion factors validated as positive non-zero values
- [ ] Circular conversion dependencies prevented
- [ ] Unit activation/deactivation preserves historical data
- [ ] Unit modifications audit-logged with timestamps
- [ ] Unit deletion restricted when transaction history exists

### Calculation Validation
- [ ] Forward/reverse conversions mathematically consistent
- [ ] Stock totals calculated identically across all units
- [ ] Price calculations maintain accuracy across unit conversions
- [ ] Tax calculations consistent regardless of unit sold
- [ ] Inventory valuation consistent across multi-unit products
- [ ] Conversion calculations tested with extreme values

## Stock Reservation Integrity

### Reservation Creation  
- [ ] Available stock verified before reservation creation
- [ ] Concurrent reservation requests properly synchronized
- [ ] Reservation quantities validated against stock levels
- [ ] Reservation expiration time properly calculated (30 minutes)
- [ ] Multiple reservations for same product handled correctly
- [ ] User session validation prevents reservation hijacking

### Reservation Management
- [ ] Expired reservations automatically cleaned up
- [ ] Reserved stock excluded from availability calculations  
- [ ] Reservation confirmation atomically updates stock
- [ ] Reservation cancellation immediately releases stock
- [ ] Reservation extension validated and logged
- [ ] Orphaned reservations prevented and cleaned up

### Concurrent Access Control
- [ ] Database-level locking prevents race conditions
- [ ] Stock checks and reservation creation are atomic
- [ ] Multiple users cannot reserve same stock simultaneously
- [ ] Inventory updates wait for reservation resolution
- [ ] Deadlock prevention in concurrent reservation scenarios
- [ ] Transaction isolation levels properly configured

## Transaction Atomicity (Sales → Inventory → NFe)

### Sale Transaction Integrity
- [ ] Sale creation, stock update, and NFe generation are atomic
- [ ] Partial failures correctly rollback all operations
- [ ] Transaction boundaries properly defined and tested
- [ ] Database constraints prevent invalid state transitions
- [ ] Failed NFe generation doesn't commit stock changes
- [ ] Concurrent sales don't create negative stock

### Error Recovery
- [ ] Failed transactions leave system in consistent state
- [ ] Compensation logic for partial NFe failures
- [ ] Stock movements reversible for cancelled sales
- [ ] NFe cancellation properly restores inventory
- [ ] System recovery procedures documented and tested
- [ ] Data consistency checks run automatically

### Cross-App Consistency
- [ ] Sales app updates synchronized with inventory changes
- [ ] Fiscal app NFe status reflects actual inventory state
- [ ] Customer balances consistent with completed sales
- [ ] Tintometry formulas align with inventory movements
- [ ] Company/store data consistent across all operations
- [ ] User permissions validated across all affected apps

## Stock Movement Audit Trail

### Movement Tracking
- [ ] Every stock change generates movement record
- [ ] Movement types correctly categorized and labeled
- [ ] Source and destination properly identified
- [ ] Quantities recorded in both original and base units
- [ ] Before/after stock levels accurately captured
- [ ] User identification mandatory for all movements

### Historical Integrity
- [ ] Movement history immutable once created
- [ ] Stock level reconstruction possible from movement history
- [ ] Historical data preserved during product modifications
- [ ] Audit trail searchable by product, date, user, type
- [ ] Movement corrections properly documented
- [ ] Data retention meets legal requirements (5+ years)

### Reconciliation Capability
- [ ] Current stock calculable from movement history
- [ ] Discrepancies between calculated and actual stock detectable
- [ ] Stock adjustment movements properly documented
- [ ] Physical inventory counts integrate with movement system
- [ ] Variance reporting accurate and auditable
- [ ] Stock valuation traceable through all movements

## Data Validation & Constraints

### Input Validation
- [ ] Negative quantities rejected except for returns/adjustments
- [ ] Decimal precision limits enforced consistently
- [ ] Product/unit combinations validated before operations
- [ ] Date/time stamps automatically generated and immutable
- [ ] Required fields enforced at database and application level
- [ ] Business rule violations detected and rejected

### Referential Integrity
- [ ] Product references validated before stock operations
- [ ] User references maintained during operations
- [ ] Customer references consistent between sales and fiscal
- [ ] Store/location references accurate in all movements
- [ ] Unit references validated against product configurations
- [ ] Foreign key constraints properly configured

### Business Rule Enforcement
- [ ] Insufficient stock sales blocked (unless manager override)
- [ ] Manager override permissions validated and logged
- [ ] Product status (active/inactive) respected in operations
- [ ] Store operating hours validated for transactions
- [ ] Unit combinations restricted to configured options only
- [ ] Price modifications validated against business rules

## Database Consistency

### Schema Integrity
- [ ] Database constraints prevent invalid data states
- [ ] Indexes optimized for performance without compromising integrity
- [ ] Triggers maintain derived data consistency
- [ ] Check constraints validate business rules at database level
- [ ] Unique constraints prevent duplicate critical data
- [ ] Null constraints properly configured for required fields

### Backup & Recovery
- [ ] Database backups tested for restoration accuracy
- [ ] Point-in-time recovery procedures validated
- [ ] Backup data integrity verified regularly
- [ ] Recovery procedures don't lose recent transactions
- [ ] Cross-database consistency maintained during recovery
- [ ] Backup encryption and security verified

### Performance vs Integrity
- [ ] Performance optimizations don't compromise data accuracy
- [ ] Caching mechanisms maintain data consistency
- [ ] Asynchronous operations maintain transactional integrity
- [ ] Bulk operations preserve individual transaction boundaries
- [ ] Index maintenance doesn't introduce data corruption
- [ ] Query optimization maintains result accuracy

## Integration Data Consistency

### Django App Integration
- [ ] Model relationships maintain referential integrity
- [ ] Signal handlers preserve transaction atomicity
- [ ] Shared models maintain consistent state across apps
- [ ] Migration scripts preserve existing data integrity
- [ ] App communication doesn't introduce race conditions
- [ ] Shared services maintain consistent behavior

### External System Integration
- [ ] SEFAZ data submission matches internal records exactly
- [ ] External API responses validated before processing
- [ ] Integration failures don't corrupt internal data
- [ ] Data synchronization maintains consistency
- [ ] External system outages don't affect data integrity
- [ ] Integration logging maintains audit trail integrity