# Business Logic Checklist - Inventory & Fiscal Integration

**Purpose**: Validate inventory policies, NFe automation rules, and paint store workflows
**Created**: 2026-04-12
**Feature**: [Inventory & Fiscal Integration](../spec.md)

## NFe Automation Rules (B2B vs B2C)

### Customer Type Detection
- [ ] CNPJ customers automatically classified as B2B
- [ ] CPF customers automatically classified as B2C  
- [ ] Mixed document customers (CNPJ + CPF) handled per business rule
- [ ] Cash sales without documents properly categorized
- [ ] Customer reclassification (B2C→B2B) triggers rule change
- [ ] Government/public entity customers handled appropriately

### B2B Automatic NFe Generation
- [ ] B2B sales trigger NFe generation within 30 seconds of completion
- [ ] B2B NFe includes all required commercial information
- [ ] B2B failures queue for manual retry with manager notification
- [ ] B2B NFe includes purchase order references when available
- [ ] B2B volume discounts reflected accurately in NFe
- [ ] B2B payment terms documented per fiscal requirements

### B2C Manual NFe Processing
- [ ] B2C NFe interface accessible within 10 seconds of sale
- [ ] B2C customer can request NFe up to 24 hours after purchase
- [ ] B2C NFe optional selection clearly presented
- [ ] B2C cash sales default to receipt-only (no NFe)
- [ ] B2C NFe includes customer CPF when provided
- [ ] B2C small value sales (under R$100) handle NFe appropriately

### Customer Classification Edge Cases
- [ ] New customers default to appropriate classification
- [ ] Foreign customers (without CPF/CNPJ) handled correctly
- [ ] Customers with invalid CPF/CNPJ are flagged appropriately
- [ ] Customer type changes retroactively affect pending NFe
- [ ] Bulk sales to individual consumers handled per regulation
- [ ] Government purchases follow specific fiscal rules

## Multi-Unit Product Configuration

### Unit Definition & Relationships
- [ ] Each product has exactly one base unit for stock tracking
- [ ] Commercial units (sold to customer) properly configured
- [ ] Fiscal units (for tax calculation) mapped correctly
- [ ] Unit conversion factors are mathematically accurate
- [ ] Paint-specific units (L, mL, gal, qt) properly supported
- [ ] Unit activation/deactivation preserves existing sales data

### Configurable Conversions
- [ ] Manager can configure conversion factors per product
- [ ] Conversion factor changes require manager approval
- [ ] Historical conversions preserved for audit trail
- [ ] Conversion accuracy validated before activation
- [ ] Unit price differentiation supported (bulk discounts)
- [ ] Tintometry products support paint + colorant conversions

### Paint Industry Specific Units
- [ ] Standard paint can sizes (1L, 3.6L, 18L) preconfigured
- [ ] Gallon to liter conversions accurate (1 gal = 3.78541 L)
- [ ] Quart to liter conversions accurate (1 qt = 0.946353 L)
- [ ] Pint to liter conversions supported (1 pt = 0.473176 L)
- [ ] Custom container sizes configurable per product
- [ ] Density-based conversions for weight-sold products

### Unit Validation Rules
- [ ] Negative conversion factors rejected
- [ ] Zero conversion factors prevented
- [ ] Circular conversion dependencies detected and prevented
- [ ] Unit code uniqueness enforced
- [ ] Unit abbreviations standardized (L, mL, gal, kg, g)
- [ ] Fiscal unit compatibility validated with SEFAZ requirements

## Inventory Validation Policies

### Insufficient Stock Handling
- [ ] Sales blocked when requested quantity exceeds available stock
- [ ] Clear error message explains insufficient stock situation
- [ ] Alternative quantities suggested when partial stock available
- [ ] Stock check includes reserved quantities in calculation
- [ ] Multi-unit products check stock in base unit equivalent
- [ ] Reservation system prevents overselling during checkout

### Manager Override Capability
- [ ] Manager can override insufficient stock blocks
- [ ] Override requires manager authentication (login/PIN)
- [ ] Override reason mandatory and recorded in audit log
- [ ] Override creates negative stock with clear tracking
- [ ] Override triggers automatic reorder alerts
- [ ] Override authority limited to specific user roles

### Stock Reservation Logic
- [ ] Stock reserved during checkout process (30-minute window)
- [ ] Reservation prevents other sales of same stock
- [ ] Reservation expires automatically if sale not completed
- [ ] Expired reservations release stock immediately
- [ ] Multiple reservations by same user handled appropriately
- [ ] Reservation conflicts resolved with clear user messaging

### Stock Adjustment Policies
- [ ] Physical inventory adjustments require manager approval
- [ ] Adjustment reasons categorized and mandatory
- [ ] Large adjustments (>10% or >R$1000) require dual approval
- [ ] Adjustment audit trail includes before/after quantities
- [ ] Adjustment impact on valuation properly calculated
- [ ] Seasonal/cyclical adjustments tracked and analyzed

## Tintometry Integration Points

### Paint Formula Management
- [ ] Base paint + colorants treated as single product for stock
- [ ] Colorant usage automatically deducted from inventory
- [ ] Formula modifications update stock calculations automatically
- [ ] Waste factor incorporated into stock deductions
- [ ] Custom colors assigned unique product codes
- [ ] Color matching history tracked per customer

### Tintometry Stock Interactions
- [ ] Base paint availability checked before color mixing
- [ ] Colorant availability validated for requested formula
- [ ] Mixed paint quantities properly recorded in inventory
- [ ] Tinting machine integration updates stock in real-time
- [ ] Error/waste during mixing properly accounted
- [ ] Cleanup/maintenance materials deducted from stock

### Custom Color Special Cases
- [ ] Custom colors receive appropriate NFe classification
- [ ] Color formula proprietary information protected
- [ ] Customer color requests tracked for repeat orders
- [ ] Special order colors handled with extended lead times
- [ ] Color matching services properly priced and documented
- [ ] Color accuracy guarantees handled per store policy

## Paint Store Business Rules

### Product Lifecycle Management
- [ ] Seasonal products handled with appropriate stock policies
- [ ] Discontinued products prevent new sales but allow stock depletion
- [ ] Product substitutions properly documented and tracked
- [ ] Manufacturer product changes reflected in inventory
- [ ] Product recalls handled with full traceability
- [ ] Expired products automatically flagged and quarantined

### Pricing & Discount Logic
- [ ] Volume discounts automatically applied per business rules
- [ ] Contractor pricing tiers properly implemented  
- [ ] Promotional pricing reflected accurately in NFe
- [ ] Price changes effective date properly handled
- [ ] Currency fluctuations handled for imported products
- [ ] Tax-inclusive vs tax-exclusive pricing properly calculated

### Customer-Specific Business Logic
- [ ] Credit limits enforced before sale completion
- [ ] Customer payment terms reflected in NFe
- [ ] Loyal customer discounts automatically applied
- [ ] Customer delivery preferences recorded and followed
- [ ] Customer paint preferences remembered for future sales
- [ ] Corporate account billing procedures followed

### Store Operations Integration
- [ ] Store hours affect transaction timing and NFe emission
- [ ] Multi-store inventory transfers properly documented
- [ ] Store-specific tax rates applied correctly
- [ ] Store manager permissions properly scoped
- [ ] Store closing procedures include inventory reconciliation
- [ ] Store opening procedures validate system readiness

## Regulatory Compliance Validation

### Brazilian Fiscal Requirements
- [ ] NCM codes properly assigned to all paint products
- [ ] ICMS calculations follow state-specific rules
- [ ] Environmental taxes included for applicable products
- [ ] Import duties calculated for foreign products
- [ ] Tax substitution rules applied correctly
- [ ] Fiscal year boundaries respected for reporting

### Paint Industry Regulations
- [ ] VOC (Volatile Organic Compound) content tracked
- [ ] Hazardous material classifications documented
- [ ] Environmental disposal regulations followed
- [ ] Quality certifications maintained and tracked
- [ ] Safety data sheets accessible for all products
- [ ] Industry-specific labeling requirements met

### Audit & Reporting Requirements
- [ ] Stock movement reports support fiscal audits
- [ ] NFe history searchable by inspector requirements
- [ ] Inventory valuation methods documented and consistent
- [ ] Physical inventory procedures documented
- [ ] Variance explanations readily available
- [ ] Management reports support business decision-making