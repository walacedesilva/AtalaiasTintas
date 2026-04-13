# Fiscal Compliance Checklist - Inventory & Fiscal Integration

**Purpose**: Ensure Brazilian NFe regulations compliance and SEFAZ integration accuracy
**Created**: 2026-04-12  
**Feature**: [Inventory & Fiscal Integration](../spec.md)

## NFe Layout Compliance (4.00)

### Document Structure
- [ ] NFe XML follows layout version 4.00 schema
- [ ] All mandatory fields present in XML generation
- [ ] Optional fields only included when applicable
- [ ] QR Code generated with correct parameters  
- [ ] Digital signature follows ICP-Brasil standards
- [ ] UTF-8 encoding maintained throughout XML

### Product Identification
- [ ] NCM (Nomenclatura Comum do Mercosul) correctly assigned
- [ ] Product codes comply with 60-character limit
- [ ] Product descriptions follow fiscal requirements
- [ ] Unit measurements use SEFAZ-approved codes
- [ ] GTIN/EAN codes included when available
- [ ] CEST codes applied for relevant products

### Tax Calculations
- [ ] ICMS calculation follows state-specific rules
- [ ] PIS/COFINS rates applied correctly per product type
- [ ] Tax base calculations accurate for paint products
- [ ] Substitution tax (ICMS-ST) handled for applicable items
- [ ] Tax regime (Simples Nacional vs Normal) respected
- [ ] Zero-rated items properly identified

## SEFAZ WebService Integration

### Connection Management
- [ ] Correct SEFAZ URLs for production/homologation by state
- [ ] SSL/TLS certificate validation enforced
- [ ] Connection timeout configured (30s max)
- [ ] Read timeout configured (60s max)
- [ ] Rate limiting respect (1 request per 2 seconds per CNPJ)
- [ ] Proper SOAP envelope structure

### Authentication & Authorization
- [ ] Digital certificate (A1/A3) properly loaded
- [ ] Certificate password encryption at rest
- [ ] Certificate validation before each request
- [ ] Certificate expiration monitoring (30-day alert)
- [ ] CNPJ validation in certificate matches configuration
- [ ] Environment switching (homolog/prod) validated

### Error Handling
- [ ] SEFAZ rejection codes properly parsed and handled
- [ ] Network timeout errors caught and logged
- [ ] Certificate errors result in clear user messages
- [ ] Retry logic implements exponential backoff (2s, 4s, 8s, 16s)
- [ ] Failed MNe marked for manual review after 3 attempts
- [ ] Critical errors (invalid certificate) stop processing immediately

### Status Management
- [ ] NFe status correctly tracked (Rascunho → Enviando → Autorizada)
- [ ] Authorization protocol properly stored
- [ ] Authorization date/time recorded accurately
- [ ] Rejection reasons logged with full detail
- [ ] Cancellation process follows SEFAZ requirements
- [ ] Status queries implemented for pending NFe

## Business Compliance

### Customer Classification  
- [ ] B2B customers (CNPJ) automatically trigger NFe
- [ ] B2C customers (CPF) allow optional NFe generation
- [ ] Cash sales without documents properly handled
- [ ] Customer fiscal data validation (CPF/CNPJ check digits)
- [ ] Customer state determines ICMS calculation rules
- [ ] Foreign customers handled per regulation

### Document Numbering
- [ ] Sequential numbering maintained per series
- [ ] Number gaps properly justified and documented
- [ ] Series configuration per store/POS terminal
- [ ] Backup numbering for SEFAZ offline periods
- [ ] Duplicate number prevention enforced
- [ ] Number range monitoring and alerts

### Timing Requirements
- [ ] B2B NFe generated within 30 seconds of sale
- [ ] Manual B2C NFe interface accessible within 10 seconds
- [ ] NFe cancellation possible within 24 hours
- [ ] Corrections via CCe (Carta de Correção Eletrônica)
- [ ] Contingency mode activation for SEFAZ outages
- [ ] Offline sales synchronization when SEFAZ returns

## Data Retention & Audit

### XML Storage
- [ ] Original NFe XML stored permanently
- [ ] Authorization return XML archived
- [ ] Digital signatures preserved in storage  
- [ ] Backup and recovery procedures tested
- [ ] File integrity validation (checksums)
- [ ] Encrypted storage for production environment

### Audit Trail
- [ ] All NFe attempts logged with timestamps
- [ ] User identification recorded for manual operations
- [ ] Failed attempts logged with error details
- [ ] System changes tracked (who, what, when)
- [ ] Performance metrics collected (processing times)
- [ ] Compliance reporting capability

### Legal Requirements
- [ ] NFe retention period compliance (5+ years)
- [ ] SPED fiscal integration capability
- [ ] Digital archive standards followed
- [ ] Backup procedures meet legal requirements
- [ ] Disaster recovery tested and documented
- [ ] Data export capability for audits

## Multi-Unit & Paint Store Specific

### Unit Conversions
- [ ] Commercial unit matches fiscal unit requirements
- [ ] Tax unit calculations accurate for all conversions
- [ ] Liter/Milliliter conversions maintain precision
- [ ] Gallon/Quart conversions follow standards
- [ ] Paint can sizes (1L, 3.6L, 18L) properly mapped
- [ ] Density calculations for weight-based products

### Tintometry Integration
- [ ] Tinted paint formulas properly documented in NFe
- [ ] Base + colorants itemized per fiscal requirements
- [ ] Mixed product NCM classification accurate
- [ ] Custom colors receive proper product codes
- [ ] Color matching services properly classified
- [ ] Waste/spillage handling in stock vs fiscal

### Paint Industry Compliance
- [ ] Hazardous material classification (if applicable)
- [ ] Environmental tax compliance (paint disposal)
- [ ] Quality certification requirements documented
- [ ] Brand/manufacturer information accurate
- [ ] Import/export documentation for foreign paints
- [ ] Industrial vs retail classification proper