# Data Model: Modern Web Interface

**Date**: 2026-04-12  
**Feature**: Modern Web Interface Data Architecture  
**Scope**: Frontend state management, API contracts, and data flow patterns

## Overview

This document defines the client-side data architecture for the modern web interface, including React state management patterns, TypeScript interfaces, API contracts, and data flow for tintometric operations. The model supports the full paint store business domain with proper separation between server state and client state.

## State Management Architecture

### React Query (Server State)
Handles all server-side data with caching, synchronization, and error management:

```typescript
// Core business entities cached from Django API
- Pigments (color ingredients, density, cost)
- Formulas (color recipes, proportions, metadata) 
- Mixtures (execution records, customer, batch info)
- Inventory (stock levels, lot tracking, reservations)
- Customers (purchase history, color preferences)
- Users (authentication, roles, preferences)
```

### Zustand (Client State)  
Manages local UI state and temporary user interactions:

```typescript
// Transient interface state
- Current user session and preferences
- Form states and validation errors
- UI visibility states (modals, panels, notifications)
- Temporary mixing calculations before submission
- Navigation history and breadcrumb state
- Real-time notifications and alerts
```

## Core Business Entities

### Pigment Entity
**Purpose**: Represents individual color ingredients used in paint mixing

```typescript
interface Pigment {
  readonly id: string;
  readonly code: string;              // Manufacturer code (e.g., "TI-02", "CR-203")
  readonly name: string;              // Human readable name
  readonly color: ColorSpace;         // RGB, LAB, or other color representation
  readonly density: number;           // g/ml for accurate volume calculations
  readonly costPerUnit: Money;        // Cost in local currency
  readonly category: PigmentCategory; // Organic, Inorganic, Metallic, etc.
  readonly supplier: string;          // Supplier information
  readonly safetyInfo: SafetyInfo;    // MSDS, hazard warnings
  readonly stockLevel: StockInfo;     // Current inventory level
  readonly isActive: boolean;         // Available for new formulas
  readonly metadata: Record<string, unknown>;
}

interface ColorSpace {
  readonly rgb: RGBColor;
  readonly lab?: LABColor;            // For accurate color matching
  readonly cmyk?: CMYKColor;          // For print applications
}

interface StockInfo {
  readonly currentStock: number;      // Current quantity available
  readonly unit: MeasurementUnit;     // kg, liters, etc.
  readonly reservedStock: number;     // Quantity reserved for pending orders
  readonly reorderLevel: number;      // Minimum stock threshold
  readonly lastUpdated: Date;
}
```

### Formula Entity
**Purpose**: Defines color recipes and mixing instructions

```typescript
interface ColorFormula {
  readonly id: string;
  readonly code: string;              // Formula identifier (e.g., "RAL-9003")
  readonly name: string;              // Formula name
  readonly targetColor: ColorSpace;   // Desired final color
  readonly baseType: BaseType;        // Water-based, solvent-based, etc.
  readonly category: FormulaCategory; // Interior, exterior, primer, etc.
  readonly ingredients: readonly Ingredient[]; // Pigment proportions
  readonly instructions: MixingInstructions;
  readonly qualityControl: QualityRules;
  readonly isStandard: boolean;       // Standard vs custom formula
  readonly createdBy: UserReference;
  readonly lastModified: Date;
  readonly usageCount: number;        // How often this formula is used
  readonly metadata: Record<string, unknown>;
}

interface Ingredient {
  readonly pigmentId: string;
  readonly proportion: number;        // Percentage (0-100)
  readonly tolerance: number;         // Acceptable variance (±%)
  readonly isRequired: boolean;       // Can this ingredient be substituted?
}

interface MixingInstructions {
  readonly mixingOrder: readonly string[]; // Order to add pigments
  readonly mixingTime: number;        // Minutes to mix
  readonly temperature: TemperatureRange;
  readonly equipment: EquipmentType;  // Manual, mechanical mixer, etc.
  readonly notes: string;
}
```

### Mixture Entity  
**Purpose**: Records of actual paint mixing operations

```typescript
interface MixtureRecord {
  readonly id: string;
  readonly batchNumber: string;       // Unique batch identifier
  readonly formulaId: string;         // Reference to used formula
  readonly customerId?: string;       // Customer if not stock batch
  readonly requestedQuantity: Measurement;
  readonly actualIngredients: readonly ActualIngredient[]; 
  readonly mixingDetails: MixingExecution;
  readonly qualityCheck: QualityResult;
  readonly status: MixtureStatus;     // Pending, InProgress, Complete, Failed
  readonly createdBy: UserReference;
  readonly createdAt: Date;
  readonly completedAt?: Date;
  readonly cost: CostBreakdown;
  readonly labels: readonly LabelInfo[];
  readonly metadata: Record<string, unknown>;
}

interface ActualIngredient {
  readonly pigmentId: string;
  readonly plannedAmount: Measurement;
  readonly actualAmount: Measurement;
  readonly variance: number;          // Percentage difference from plan
  readonly batchInfo: PigmentBatch;   // Lot/batch of pigment used
}

interface QualityResult {
  readonly colorMatch: ColorMatchResult;
  readonly consistency: ConsistencyTest;
  readonly isApproved: boolean;
  readonly approvedBy?: UserReference;
  readonly notes: string;
}
```

### Customer Entity
**Purpose**: Customer information with color preference tracking

```typescript
interface Customer {
  readonly id: string;
  readonly name: string;
  readonly contactInfo: ContactInfo;
  readonly colorPreferences: readonly ColorPreference[];
  readonly purchaseHistory: readonly MixtureReference[];
  readonly loyaltyLevel: LoyaltyTier;
  readonly specialRequirements: readonly string[]; // Allergies, preferences
  readonly creditStatus: CreditInfo;
  readonly isActive: boolean;
  readonly metadata: Record<string, unknown>;
}

interface ColorPreference {
  readonly colorFamily: string;       // Blue, red, neutral, etc.
  readonly preferredFinishes: readonly FinishType[];
  readonly avoidedIngredients: readonly string[]; // Allergies/preferences
  readonly frequentFormulas: readonly string[];   // Formula IDs
}
```

## API Contract Specifications

### REST API Endpoints

#### Pigments API
```typescript
// GET /api/v1/pigments/
interface PigmentListResponse {
  readonly results: readonly Pigment[];
  readonly count: number;
  readonly next?: string;
  readonly previous?: string;
}

// GET /api/v1/pigments/{id}/
interface PigmentDetailResponse extends Pigment {}

// POST /api/v1/pigments/{id}/reserve/
interface ReservePigmentRequest {
  readonly quantity: number;
  readonly reservationId: string;
  readonly expiresAt: Date;
}
```

#### Formulas API  
```typescript
// GET /api/v1/formulas/
interface FormulaListResponse {
  readonly results: readonly ColorFormula[];
  readonly count: number;
  readonly filters: FormulaFilters;
}

// POST /api/v1/formulas/{id}/calculate/
interface CalculateMixtureRequest {
  readonly targetQuantity: Measurement;
  readonly adjustments?: Record<string, number>; // Pigment adjustments
}

interface CalculateMixtureResponse {
  readonly ingredients: readonly CalculatedIngredient[];
  readonly estimatedCost: Money;
  readonly warnings: readonly string[];
  readonly isValidBatch: boolean;
}
```

#### Mixing Operations API
```typescript
// POST /api/v1/mixtures/
interface CreateMixtureRequest {
  readonly formulaId: string;
  readonly customerId?: string;
  readonly targetQuantity: Measurement;
  readonly priority: Priority;
  readonly specialInstructions?: string;
}

// PUT /api/v1/mixtures/{id}/execute/
interface ExecuteMixtureRequest {
  readonly actualIngredients: readonly ActualIngredient[];
  readonly mixingNotes?: string;
  readonly qualityPhotos?: readonly string[]; // Base64 encoded images
}

// GET /api/v1/mixtures/{id}/status/
interface MixtureStatusResponse {
  readonly status: MixtureStatus;
  readonly progress: number;          // 0-100 percentage
  readonly currentStep: string;
  readonly estimatedCompletion?: Date;
  readonly canCancel: boolean;
}
```

## State Flow Patterns

### Tintometric Workflow State Machine

```typescript
type TintometricState = 
  | 'ColorSelection'    // User selects target color
  | 'FormulaSearch'     // System suggests matching formulas  
  | 'QuantityInput'     // User specifies desired quantity
  | 'IngredientCheck'   // System validates ingredient availability
  | 'CostEstimate'      // Display cost breakdown and confirmation
  | 'MixingExecution'   // Execute mixing with progress tracking
  | 'QualityControl'    // Color matching and quality verification
  | 'LabelGeneration'   // Generate labels and documentation
  | 'Completed';        // Final state

interface TintometricWorkflow {
  readonly currentState: TintometricState;
  readonly canAdvance: boolean;
  readonly canGoBack: boolean;
  readonly validationErrors: readonly ValidationError[];
  readonly workingData: WorkingMixtureData;
}
```

### Real-time Data Flow

```typescript
// WebSocket events for real-time updates
interface InventoryUpdateEvent {
  readonly type: 'INVENTORY_UPDATED';
  readonly pigmentId: string;
  readonly newLevel: number;
  readonly changeReason: string;
}

interface MixingProgressEvent {
  readonly type: 'MIXING_PROGRESS';  
  readonly mixtureId: string;
  readonly progress: number;
  readonly currentStep: string;
}

interface SystemAlertEvent {
  readonly type: 'SYSTEM_ALERT';
  readonly severity: 'Info' | 'Warning' | 'Error';
  readonly message: string;
  readonly affectedOperations?: readonly string[];
}
```

## Validation Rules

### Business Logic Validation

```typescript
interface ValidationRules {
  // Pigment availability validation
  readonly validatePigmentStock: (pigmentId: string, requestedAmount: number) => ValidationResult;
  
  // Formula consistency validation  
  readonly validateFormulaProportions: (ingredients: readonly Ingredient[]) => ValidationResult;
  
  // Mixing capacity validation
  readonly validateBatchSize: (quantity: Measurement, equipment: EquipmentType) => ValidationResult;
  
  // Color matching tolerance validation
  readonly validateColorMatch: (target: ColorSpace, actual: ColorSpace) => ColorMatchResult;
  
  // Cost threshold validation  
  readonly validateCostLimits: (estimatedCost: Money, userRole: UserRole) => ValidationResult;
}
```

### Form Validation Schemas

```typescript
// Zod schemas for client-side validation
const PigmentSchema = z.object({
  code: z.string().min(1).max(20).regex(/^[A-Z0-9-]+$/),
  name: z.string().min(1).max(100),
  density: z.number().min(0.1).max(5.0),
  costPerUnit: z.number().min(0).max(10000),
});

const MixtureRequestSchema = z.object({
  formulaId: z.string().uuid(),
  customerId: z.string().uuid().optional(),
  targetQuantity: z.number().min(0.1).max(1000),
  priority: z.enum(['Low', 'Normal', 'High', 'Urgent']),
});
```

## Error Handling Patterns

### API Error Types
```typescript
interface APIError {
  readonly type: 'ValidationError' | 'AuthorizationError' | 'BusinessLogicError' | 'SystemError';
  readonly message: string;
  readonly details?: Record<string, unknown>;
  readonly retryable: boolean;
  readonly userMessage: string; // Localized, user-friendly message
}

interface ValidationError extends APIError {
  readonly type: 'ValidationError';
  readonly fieldErrors: Record<string, readonly string[]>;
}

interface BusinessLogicError extends APIError {
  readonly type: 'BusinessLogicError';  
  readonly businessRule: string;
  readonly suggestedAction?: string;
}
```

### Offline Handling
```typescript
interface OfflineCapabilities {
  // Operations that work offline
  readonly supportedOfflineOperations: readonly OfflineOperation[];
  
  // Data that must be cached for offline use
  readonly criticalCacheData: readonly CacheEntry[];
  
  // Synchronization strategy when connection restored
  readonly syncStrategy: SyncStrategy;
}

interface OfflineOperation {
  readonly operationType: 'ViewFormulas' | 'CalculateMixture' | 'GenerateLabel';
  readonly requirements: readonly string[]; // Required cached data
  readonly limitations: readonly string[];  // What doesn't work offline
}
```

## Performance Considerations

### Caching Strategy
```typescript
interface CacheConfiguration {
  // Static data (rarely changes)
  readonly pigmentCatalog: { ttl: '24h', staleTime: '1h' };
  readonly standardFormulas: { ttl: '12h', staleTime: '30m' };
  
  // Dynamic data (changes frequently)  
  readonly inventoryLevels: { ttl: '5m', staleTime: '1m' };
  readonly activeMixtures: { ttl: '30s', staleTime: '10s' };
  
  // User-specific data
  readonly userPreferences: { ttl: '1h', staleTime: '15m' };
  readonly recentMixtures: { ttl: '2h', staleTime: '30m' };
}
```

### Data Pagination
```typescript
interface PaginationStrategy {
  readonly defaultPageSize: 25;
  readonly maxPageSize: 100;
  readonly virtualScrolling: boolean; // For large lists (10k+ formulas)
  readonly infiniteLoading: boolean;  // For real-time data streams
}
```

## Security Considerations

### Sensitive Data Handling
```typescript
interface SecurityPolicy {
  // Data that requires special handling
  readonly sensitiveFields: readonly SensitiveField[];
  
  // Role-based data filtering
  readonly dataAccessRules: Record<UserRole, readonly DataAccessRule[]>;
  
  // Encryption requirements
  readonly encryptionPolicy: EncryptionPolicy;
}

interface SensitiveField {
  readonly field: string;           // e.g., 'costPerUnit', 'formulaIngredients'
  readonly minimumRole: UserRole;   // Minimum role to view this field
  readonly maskingRule?: MaskingRule; // How to hide data from unauthorized users
}
```

## Testing Strategies

### Data Model Testing
```typescript
interface TestingCoverage {
  // Type safety tests
  readonly typeTests: readonly TypeTest[];
  
  // Business logic validation tests
  readonly validationTests: readonly ValidationTest[];
  
  // State management tests  
  readonly stateTests: readonly StateTest[];
  
  // Integration tests with backend
  readonly contractTests: readonly ContractTest[];
}
```

This data model provides a comprehensive foundation for the modern web interface, ensuring type safety, proper separation of concerns, and alignment with paint industry business requirements while supporting the technical constraints and performance targets defined in the specification.