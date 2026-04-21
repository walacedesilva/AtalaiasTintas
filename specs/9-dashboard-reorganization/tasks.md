# Implementation Tasks: Dashboard Interface Reorganization

**Feature**: Dashboard Interface Reorganization for Business Operations Focus  
**Created**: 2026-04-19  
**Status**: Tasks Ready - READY FOR IMPLEMENTATION  
**Total Tasks**: 24  
**Estimated Duration**: 6-8 days

## Task Priority Legend
- **P1**: MVP - Must have (Critical business operations)
- **P2**: Important - Should have (Enhanced experience)
- **[P]**: Parallelizable task (can run in parallel with other [P] tasks)
- **[US#]**: References user story from specification

## Phase 1: Foundation (Days 1-2)

### [T001] Create TypeScript Type Definitions [P1] [P] [US1,US2,US3,US4,US5]
**File**: `frontend/src/types/dashboard.ts`
**Dependencies**: None
**Description**: Create comprehensive TypeScript interfaces for dashboard data structures
**Implementation**:
```typescript
// Core dashboard types
export interface BusinessMetrics {
  sales: SalesMetrics;
  orders: OrdersMetrics; 
  fiscal: FiscalMetrics;
  inventory: InventoryMetrics;
}

export interface DashboardQuickAction {
  id: string;
  label: string;
  icon: React.ComponentType<any>;
  path: string;
  permission?: string;
  priority: 'high' | 'medium' | 'low';
}
```
**Acceptance Criteria**:
- [x] All dashboard data structures typed
- [x] Quick action interface defined
- [x] API response types included
- [x] No TypeScript errors
**Testing**: TypeScript compilation passes
**Estimated Time**: 2 hours
**Status**: ✅ **COMPLETED** (2026-04-19)

### [T002] Set Up Component Directory Structure [P1] [P] [US1,US2,US3,US4]
**Directories**: 
- `frontend/src/components/dashboard/`
- `frontend/src/hooks/dashboard/`
- `frontend/src/services/dashboard/`
**Dependencies**: None
**Description**: Create organized directory structure for new dashboard components
**Implementation**:
```
frontend/src/
├── components/dashboard/
│   ├── BusinessMetrics.tsx (stub)
│   ├── SalesOverview.tsx (stub)  
│   ├── FiscalStatus.tsx (stub)
│   ├── SystemMonitoring.tsx (stub)
│   └── MetricCard.tsx (stub)
├── hooks/dashboard/
│   ├── useBusinessMetrics.ts (stub)
│   ├── useSalesOverview.ts (stub)
│   └── useFiscalStatus.ts (stub)
└── services/dashboard/
    └── dashboardAPI.ts (stub)
```
**Acceptance Criteria**:
- [x] All directories created
- [x] Stub files created with basic structure
- [x] Import/export structure works
**Testing**: All files import without errors
**Estimated Time**: 1 hour
**Status**: ✅ **COMPLETED** (2026-04-19)

### [T003] Create Dashboard API Service Structure [P1] [P] [US1,US2,US3]
**File**: `frontend/src/services/dashboard/dashboardAPI.ts`
**Dependencies**: T001, T002
**Description**: Set up API service with mock data for initial development
**Implementation**:
```typescript
import { BaseAPI } from '../api/base';
import { BusinessMetrics, SalesOverview, FiscalStatus } from '../../types/dashboard';

export class DashboardAPI extends BaseAPI {
  async getBusinessMetrics(timeRange: string): Promise<BusinessMetrics> {
    // Initial mock implementation
    return this.mockBusinessMetrics();
  }
  
  async getSalesOverview(): Promise<SalesOverview> {
    // Initial mock implementation  
    return this.mockSalesOverview();
  }
  
  private mockBusinessMetrics(): BusinessMetrics {
    // Mock data for development
  }
}
```
**Acceptance Criteria**:
- [x] API class structure created
- [x] Mock methods implemented
- [x] TypeScript interfaces used
- [x] Follows existing API patterns
**Testing**: Mock API calls return expected data structure
**Estimated Time**: 3 hours
**Status**: ✅ **COMPLETED** (2026-04-19)

## Phase 2: Backend Integration (Days 2-3)

### [T004] Extend Sales API for Dashboard [P1] [US1]
**File**: `frontend/src/services/api/sales.ts`
**Dependencies**: T001, T003
**Description**: Add dashboard-specific methods to existing Sales API
**Implementation**:
```typescript
// Add to existing SalesAPI class
async getDashboardOverview(): Promise<SalesDashboardData> {
  return this.client.get('/api/sales/dashboard/');
}

async getSalesMetrics(timeRange: string): Promise<SalesMetrics> {
  return this.client.get(`/api/sales/metrics/?range=${timeRange}`);
}
```
**Backend Requirement**: `/api/sales/dashboard/` endpoint must be implemented
**Acceptance Criteria**:
- [x] New methods added to Sales API
- [x] Mock implementation with real API structure
- [x] Error handling implemented
- [x] TypeScript types used
**Testing**: API calls return expected mock data structure
**Estimated Time**: 2 hours
**Status**: ✅ **COMPLETED** (2026-04-19) - Added dashboard methods to salesAPI with mock data

### [T005] Extend Fiscal API for Dashboard [P1] [US2]
**File**: `frontend/src/services/api/fiscal.ts`  
**Dependencies**: T001, T003
**Description**: Add fiscal status and compliance methods to existing Fiscal API
**Implementation**:
```typescript
// Add to existing FiscalAPI class  
async getDashboardStatus(): Promise<FiscalDashboardData> {
  return this.client.get('/api/fiscal/dashboard/');
}

async getComplianceAlerts(): Promise<ComplianceAlert[]> {
  return this.client.get('/api/fiscal/alerts/');
}
```
**Backend Requirement**: `/api/fiscal/dashboard/` and `/api/fiscal/alerts/` endpoints
**Acceptance Criteria**:
- [x] Fiscal dashboard methods implemented
- [x] Compliance alerts functionality
- [x] Error states handled
- [x] TypeScript types enforced
**Testing**: Fiscal API returns mock compliance data
**Estimated Time**: 2 hours
**Status**: ✅ **COMPLETED** (2026-04-19) - Added dashboard methods to fiscalAPI with comprehensive mock data

### [T006] Create System Monitoring API [P2] [P] [US3]
**File**: `frontend/src/services/api/monitoring.ts`
**Dependencies**: T001, T003
**Description**: Create new monitoring API for system health metrics
**Implementation**:
```typescript
export class MonitoringAPI extends BaseAPI {
  async getSystemHealth(): Promise<SystemHealth> {
    return this.client.get('/api/monitoring/system-health/');
  }
  
  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    return this.client.get('/api/monitoring/performance/');
  }
}
```
**Backend Requirement**: `/api/monitoring/system-health/` endpoint
**Acceptance Criteria**:
- [x] Monitoring API class created
- [x] System health methods implemented  
- [x] Performance metrics included
- [x] Follows existing API patterns
**Testing**: Monitoring API returns comprehensive system metrics
**Estimated Time**: 2 hours
**Status**: ✅ **COMPLETED** (2026-04-19) - Created new monitoringAPI with system health, performance, and service status methods

## Phase 3: Frontend Implementation (Days 3-5)

### [T007] Create React Query Hooks [P1] [US1,US2,US3,US4]
**Files**:
- `frontend/src/hooks/dashboard/useBusinessMetrics.ts`
- `frontend/src/hooks/dashboard/useSalesOverview.ts`
- `frontend/src/hooks/dashboard/useFiscalStatus.ts`
**Dependencies**: T004, T005, T006
**Description**: Implement React Query hooks for dashboard data management
**Implementation**:
```typescript
// useBusinessMetrics.ts
export const useBusinessMetrics = (timeRange: TimeRange) => {
  return useQuery({
    queryKey: ['business-metrics', timeRange],
    queryFn: () => dashboardAPI.getBusinessMetrics(timeRange),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 30 * 1000, // 30 seconds background refetch
    retry: 3
  });
};
```
**Acceptance Criteria**:
- [ ] All required hooks implemented
- [ ] Proper caching strategy applied
- [ ] Background refresh configured
- [ ] Error handling included
- [ ] TypeScript types enforced
**Testing**: Hooks return data and handle loading/error states
**Estimated Time**: 4 hours

### [T008] Implement BusinessMetrics Component [P1] [US1,US2,US3]
**File**: `frontend/src/components/dashboard/BusinessMetrics.tsx`
**Dependencies**: T007
**Description**: Create main business metrics display component
**Implementation**:
```typescript
interface BusinessMetricsProps {
  timeRange: TimeRange;
  showDetails?: boolean;
}

export const BusinessMetrics: React.FC<BusinessMetricsProps> = ({
  timeRange,
  showDetails = false
}) => {
  const { data: metrics, isLoading, error } = useBusinessMetrics(timeRange);
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Vendas Hoje"
        value={metrics?.sales.today}
        trend={metrics?.sales.trend}
        icon={<ShoppingCartIcon />}
      />
      {/* More metric cards */}
    </div>
  );
};
```
**Acceptance Criteria**:
- [ ] Displays sales, orders, fiscal, inventory metrics
- [ ] Responsive grid layout
- [ ] Loading states handled
- [ ] Error states displayed
- [ ] Accessible (WCAG 2.1 AA)
- [ ] Follows design system
**Testing**: Component renders all metrics correctly, handles all states
**Estimated Time**: 4 hours

### [T009] Implement SalesOverview Component [P1] [US1]
**File**: `frontend/src/components/dashboard/SalesOverview.tsx`
**Dependencies**: T007
**Description**: Create sales performance overview widget
**Implementation**:
```typescript
interface SalesOverviewProps {
  period: 'today' | 'week' | 'month';
  showTrends?: boolean;
}

export const SalesOverview: React.FC<SalesOverviewProps> = ({
  period,
  showTrends = true
}) => {
  const { data: salesData } = useSalesOverview(period);
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Vendas - {period}</h3>
        <Button 
          variant="outline" 
          onClick={() => navigate('/sales')}
          aria-label="Ver detalhes de vendas"
        >
          Ver Detalhes
        </Button>
      </div>
      {/* Sales metrics display */}
    </div>
  );
};
```
**Acceptance Criteria**:
- [ ] Shows sales total, trend, and performance
- [ ] Quick navigation to sales module
- [ ] Multiple time periods supported
- [ ] Accessible navigation
- [ ] Responsive design
**Testing**: Component displays sales data and navigates correctly
**Estimated Time**: 3 hours

### [T010] Implement FiscalStatus Component [P1] [US2]
**File**: `frontend/src/components/dashboard/FiscalStatus.tsx`
**Dependencies**: T007
**Description**: Create fiscal compliance and NFe status display
**Implementation**:
```typescript
interface FiscalStatusProps {
  showAlerts?: boolean;
  maxAlerts?: number;
}

export const FiscalStatus: React.FC<FiscalStatusProps> = ({
  showAlerts = true,
  maxAlerts = 5
}) => {
  const { data: fiscalData } = useFiscalStatus();
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Status Fiscal</h3>
      
      <div className="space-y-3">
        <div className="flex justify-between">
          <span>NFe Pendentes</span>
          <span className="font-semibold">{fiscalData?.nfe_pending}</span>
        </div>
        
        {showAlerts && fiscalData?.alerts?.map(alert => (
          <Alert key={alert.id} variant={alert.type}>
            {alert.message}
          </Alert>
        ))}
        
        <Button 
          onClick={() => navigate('/fiscal')}
          className="w-full"
          aria-label="Acessar módulo fiscal"
        >
          Gerenciar Fiscal/NFe
        </Button>
      </div>
    </div>
  );
};
```
**Acceptance Criteria**:
- [ ] Shows NFe pending count and status
- [ ] Displays compliance alerts
- [ ] Quick access to fiscal module  
- [ ] Alert severity properly shown
- [ ] Accessible interactions
**Testing**: Component shows fiscal data and handles navigation
**Estimated Time**: 3 hours

### [T011] Implement SystemMonitoring Component [P2] [P] [US3]
**File**: `frontend/src/components/dashboard/SystemMonitoring.tsx`
**Dependencies**: T007
**Description**: Create system health monitoring widget
**Implementation**:
```typescript
interface SystemMonitoringProps {
  showTechnicalDetails?: boolean;
}

export const SystemMonitoring: React.FC<SystemMonitoringProps> = ({
  showTechnicalDetails = false
}) => {
  const { data: systemData } = useSystemMonitoring();
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Monitoramento</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {systemData?.uptime}%
          </div>
          <div className="text-sm text-gray-600">Uptime</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold">
            {systemData?.activeUsers}
          </div>
          <div className="text-sm text-gray-600">Usuários Ativos</div>
        </div>
      </div>
    </div>
  );
};
```
**Acceptance Criteria**:
- [ ] Shows system uptime and health
- [ ] Displays active user count
- [ ] Performance indicators included
- [ ] Technical details configurable
- [ ] Responsive layout
**Testing**: Component displays system metrics correctly
**Estimated Time**: 2 hours

### [T012] Update Dashboard Main Component [P1] [US1,US2,US3,US4,US5]
**File**: `frontend/src/pages/Dashboard.tsx`
**Dependencies**: T008, T009, T010, T011
**Description**: Integrate new components and update quick actions
**Implementation**:
```typescript
// Replace tintometry quick actions with business actions
const businessQuickActions: DashboardQuickAction[] = [
  {
    id: 'sales',
    label: 'Vendas',
    icon: ShoppingCartIcon,
    path: '/sales',
    permission: 'pode_vender',
    priority: 'high'
  },
  {
    id: 'orders', 
    label: 'Pedidos',
    icon: ClipboardListIcon,
    path: '/orders',
    permission: 'pode_vender',
    priority: 'high'
  },
  {
    id: 'fiscal',
    label: 'Fiscal/NFe', 
    icon: DocumentTextIcon,
    path: '/fiscal',
    permission: 'pode_acessar_financeiro',
    priority: 'high'
  },
  {
    id: 'reports',
    label: 'Relatórios',
    icon: ChartBarIcon, 
    path: '/reports',
    permission: 'pode_administrar',
    priority: 'medium'
  },
  {
    id: 'monitoring',
    label: 'Monitoramento',
    icon: EyeIcon,
    path: '/monitoring', 
    permission: 'pode_administrar',
    priority: 'medium'
  },
  {
    id: 'inventory',
    label: 'Controle de Estoque',
    icon: CubeIcon,
    path: '/inventory',
    permission: 'pode_gerenciar_estoque',
    priority: 'high'
  }
];

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <BusinessMetrics timeRange="today" />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <SalesOverview period="today" />
        <FiscalStatus showAlerts={true} />
        <SystemMonitoring />
      </div>
      
      <QuickActionsGrid actions={businessQuickActions} />
    </div>
  );
};
```
**Acceptance Criteria**:
- [ ] Tintometry actions removed from main dashboard
- [ ] Business operations actions added
- [ ] New metrics components integrated
- [ ] Permission-based visibility maintained
- [ ] Responsive layout preserved
- [ ] Accessibility maintained
**Testing**: Dashboard shows new layout, all actions work, permissions respected
**Estimated Time**: 3 hours

### [T013] Create Reusable MetricCard Component [P2] [P] [US1,US2,US3,US4]
**File**: `frontend/src/components/dashboard/MetricCard.tsx`
**Dependencies**: T001
**Description**: Create reusable metric display component
**Implementation**:
```typescript
interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    percentage: number;
  };
  icon?: React.ReactNode;
  onClick?: () => void;
  loading?: boolean;
  error?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  trend,
  icon,
  onClick,
  loading,
  error
}) => {
  return (
    <div 
      className={`bg-white p-6 rounded-lg shadow-sm ${
        onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
      }`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-600">{title}</h4>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      
      {loading ? (
        <div className="animate-pulse h-8 bg-gray-200 rounded"></div>
      ) : error ? (
        <div className="text-red-500 text-sm">Erro ao carregar</div>
      ) : (
        <>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          {trend && (
            <div className={`text-sm flex items-center mt-1 ${
              trend.direction === 'up' ? 'text-green-600' : 
              trend.direction === 'down' ? 'text-red-600' : 
              'text-gray-600'
            }`}>
              {trend.direction === 'up' ? '↗' : trend.direction === 'down' ? '↘' : '→'}
              {trend.percentage}%
            </div>
          )}
        </>
      )}
    </div>
  );
};
```
**Acceptance Criteria**:
- [ ] Reusable across all metric displays
- [ ] Supports loading and error states
- [ ] Trend indicators included  
- [ ] Click handling for navigation
- [ ] Accessible (keyboard, screen reader)
- [ ] Follows design system
**Testing**: Component renders correctly in all states, accessible interactions work
**Estimated Time**: 2 hours

## Phase 4: Testing & Validation (Days 6-8)

### [T014] Create Unit Tests for Dashboard Components [P1] [US1,US2,US3,US4,US5]
**Files**:
- `frontend/src/components/dashboard/__tests__/BusinessMetrics.test.tsx`
- `frontend/src/components/dashboard/__tests__/SalesOverview.test.tsx`
- `frontend/src/components/dashboard/__tests__/FiscalStatus.test.tsx`
- `frontend/src/components/dashboard/__tests__/SystemMonitoring.test.tsx`
- `frontend/src/components/dashboard/__tests__/MetricCard.test.tsx`
**Dependencies**: T008, T009, T010, T011, T013
**Description**: Comprehensive unit testing for all dashboard components
**Implementation**:
```typescript
// Example: BusinessMetrics.test.tsx
describe('BusinessMetrics Component', () => {
  test('displays metrics correctly when data loads', async () => {
    const mockData = {
      sales: { today: 1500, trend: { direction: 'up', percentage: 12 }},
      orders: { pending: 5, completed: 23 }
    };
    
    server.use(
      rest.get('/api/dashboard/metrics', (req, res, ctx) => {
        return res(ctx.json(mockData));
      })
    );
    
    render(<BusinessMetrics timeRange="today" />);
    
    await waitFor(() => {
      expect(screen.getByText('1500')).toBeInTheDocument();
      expect(screen.getByText('↗ 12%')).toBeInTheDocument();
    });
  });
  
  test('handles loading state gracefully', () => {
    render(<BusinessMetrics timeRange="today" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
  
  test('shows error state when API fails', async () => {
    server.use(
      rest.get('/api/dashboard/metrics', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );
    
    render(<BusinessMetrics timeRange="today" />);
    
    await waitFor(() => {
      expect(screen.getByText(/erro/i)).toBeInTheDocument();
    });
  });
});
```
**Acceptance Criteria**:
- [ ] All components have comprehensive tests
- [ ] Loading, success, and error states tested
- [ ] User interactions tested
- [ ] Accessibility assertions included
- [ ] Mock API responses configured
- [ ] 95%+ code coverage achieved
**Testing**: All tests pass, coverage threshold met
**Estimated Time**: 6 hours

### [T015] Create Integration Tests [P1] [US1,US2,US3,US4,US5]
**Files**:
- `frontend/src/__tests__/dashboard-integration.test.tsx`
**Dependencies**: T012, T014
**Description**: Test dashboard components working together
**Implementation**:
```typescript
describe('Dashboard Integration', () => {
  test('dashboard loads with all business components', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Vendas - today')).toBeInTheDocument();
      expect(screen.getByText('Status Fiscal')).toBeInTheDocument();
      expect(screen.getByText('Monitoramento')).toBeInTheDocument();
    });
  });
  
  test('quick actions navigate correctly', async () => {
    const user = userEvent.setup();
    render(<Dashboard />);
    
    const salesAction = screen.getByRole('button', { name: /vendas/i });
    await user.click(salesAction);
    
    expect(mockNavigate).toHaveBeenCalledWith('/sales');
  });
  
  test('respects user permissions', async () => {
    const limitedUser = { permissions: ['pode_vender'] };
    render(<Dashboard />, { wrapper: AuthWrapper, initialState: { user: limitedUser }});
    
    expect(screen.getByRole('button', { name: /vendas/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /relatórios/i })).not.toBeInTheDocument();
  });
});
```
**Acceptance Criteria**:
- [ ] Full dashboard integration tested
- [ ] Navigation flows verified
- [ ] Permission-based visibility tested
- [ ] API integration confirmed
- [ ] Error boundaries tested
**Testing**: Integration tests pass, user flows work end-to-end
**Estimated Time**: 4 hours

### [T016] Create E2E Tests [P1] [US1,US2,US3,US4,US5]
**Files**:
- `frontend/tests/e2e/dashboard-reorganization.spec.ts`
**Dependencies**: T012, T015
**Description**: End-to-end testing of dashboard reorganization
**Implementation**:
```typescript
// dashboard-reorganization.spec.ts
test('user can access all business quick actions from dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Test Vendas access
  await page.click('[data-testid="quick-action-sales"]');
  await expect(page).toHaveURL('/sales');
  
  // Navigate back to dashboard
  await page.goto('/dashboard');
  
  // Test Fiscal access
  await page.click('[data-testid="quick-action-fiscal"]');
  await expect(page).toHaveURL('/fiscal');
});

test('dashboard loads within performance requirements', async ({ page }) => {
  const startTime = Date.now();
  
  await page.goto('/dashboard');
  await page.waitForSelector('[data-testid="business-metrics"]');
  
  const loadTime = Date.now() - startTime;
  expect(loadTime).toBeLessThan(2000); // 2 second requirement
});

test('tintometry actions are not visible on main dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  
  await expect(page.locator('[data-testid="quick-action-new-mixture"]')).not.toBeVisible();
  await expect(page.locator('[data-testid="quick-action-generate-label"]')).not.toBeVisible();
  await expect(page.locator('[data-testid="quick-action-color-catalog"]')).not.toBeVisible();
});

test('dashboard works on mobile devices', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); // iPhone 12 Pro
  
  await page.goto('/dashboard');
  
  // Verify responsive layout
  await expect(page.locator('[data-testid="business-metrics"]')).toBeVisible();
  await expect(page.locator('[data-testid="quick-actions"]')).toBeVisible();
});
```
**Acceptance Criteria**:
- [ ] All critical user workflows tested
- [ ] Performance requirements validated
- [ ] Mobile responsiveness verified
- [ ] Accessibility compliance tested
- [ ] Cross-browser compatibility confirmed
**Testing**: E2E tests pass on all target browsers and devices
**Estimated Time**: 4 hours

### [T017] Performance Optimization [P2] [P] [US1,US2,US3,US4]
**Files**: Various component files for optimization
**Dependencies**: T016
**Description**: Optimize dashboard performance for production
**Implementation**:
- Code splitting for dashboard components
- React.memo for expensive components
- useMemo for calculated values
- Optimize React Query cache settings
- Image optimization and lazy loading
**Acceptance Criteria**:
- [ ] Dashboard loads under 2 seconds on 3G
- [ ] All API calls respond under 500ms
- [ ] Bundle size increase under 50KB
- [ ] No memory leaks detected
- [ ] Core Web Vitals pass
**Testing**: Performance testing with Lighthouse, Bundle analyzer results
**Estimated Time**: 4 hours

### [T018] Accessibility Testing [P1] [US1,US2,US3,US4,US5]
**Files**: Update components for accessibility issues
**Dependencies**: T016
**Description**: Comprehensive accessibility testing and fixes
**Implementation**:
- Automated axe-core testing
- Manual screen reader testing  
- Keyboard navigation testing
- Color contrast verification
- Focus management testing
**Acceptance Criteria**:
- [ ] WCAG 2.1 AA compliance achieved
- [ ] Screen reader compatibility verified
- [ ] Keyboard navigation works completely
- [ ] Color contrast meets standards
- [ ] Focus indicators visible
**Testing**: Automated and manual accessibility tests pass
**Estimated Time**: 3 hours

### [T019] Documentation Update [P2] [P]
**Files**: 
- `README.md`
- Component JSDoc comments
- API documentation
**Dependencies**: T017, T018
**Description**: Update project documentation for new dashboard
**Implementation**:
- Update README with dashboard changes
- Document new components and hooks
- API endpoint documentation
- User guide updates
**Acceptance Criteria**:
- [ ] All new components documented
- [ ] API changes documented
- [ ] User guide updated
- [ ] Code examples included
**Testing**: Documentation review and validation
**Estimated Time**: 2 hours

### [T020] Verify Backend API Endpoints Status [P1] [US1,US2,US3]
**Files**: Backend API audit
**Dependencies**: T001
**Description**: Audit existing backend APIs and identify which dashboard endpoints need creation
**Implementation**:
- Check `/api/sales/dashboard/` endpoint exists
- Check `/api/fiscal/dashboard/` endpoint exists  
- Check `/api/monitoring/system-health/` endpoint exists
- Document required vs. existing endpoints
- Estimate backend development effort if needed
**Acceptance Criteria**:
- [x] All required endpoints documented
- [x] Existing vs. new endpoints identified
- [x] Backend development effort estimated
- [x] API response schemas validated
**Testing**: API endpoint availability confirmed
**Estimated Time**: 3 hours
**Status**: ✅ **COMPLETED** (2026-04-19) - See BACKEND_API_AUDIT_T020.md

### [T021] Create Navigation Menu Updates [P1] [US5]
**Files**: 
- `frontend/src/components/layout/Navigation.tsx`
- `frontend/src/components/layout/TintometryMenu.tsx` (new)
**Dependencies**: T012
**Description**: Update navigation to include tintometry functions in secondary menu
**Implementation**:
```typescript
// Add tintometry submenu to main navigation
const tintometrySubmenu = {
  id: 'tintometry',
  label: 'Tintometria',
  icon: ColorSwatchIcon,
  children: [
    { id: 'new-mixture', label: 'Nova Mistura', path: '/tintometry/mixture' },
    { id: 'generate-label', label: 'Gerar Etiqueta', path: '/tintometry/labels' },
    { id: 'color-catalog', label: 'Catálogo de Cores', path: '/tintometry/catalog' }
  ]
};
```
**Acceptance Criteria**:
- [ ] Tintometry submenu created in navigation
- [ ] All removed actions accessible via menu
- [ ] Menu follows existing design patterns
- [ ] Keyboard navigation works
- [ ] Screen reader accessible
**Testing**: All tintometry functions accessible through navigation
**Estimated Time**: 4 hours

### [T022] Validate Inventory Control Preservation [P1] [US4]
**Files**: 
- `frontend/src/components/dashboard/__tests__/InventoryPreservation.test.tsx`
- `frontend/tests/e2e/inventory-integration.spec.ts`
**Dependencies**: T012, T014
**Description**: Comprehensive testing to ensure inventory functionality is preserved
**Implementation**:
```typescript
describe('Inventory Control Preservation', () => {
  test('inventory quick action maintains existing behavior', () => {
    render(<Dashboard />);
    
    const inventoryAction = screen.getByRole('button', { name: /controle de estoque/i });
    fireEvent.click(inventoryAction);
    
    expect(mockNavigate).toHaveBeenCalledWith('/inventory');
  });
  
  test('inventory alerts display correctly in new dashboard', () => {
    const mockAlerts = [{ id: 1, type: 'low_stock', product: 'Tinta Branca' }];
    render(<Dashboard />);
    
    expect(screen.getByText('Tinta Branca')).toBeInTheDocument();
    expect(screen.getByText(/estoque baixo/i)).toBeInTheDocument();
  });
});
```
**Acceptance Criteria**:
- [ ] All existing inventory functions work unchanged
- [ ] Inventory alerts display correctly
- [ ] Stock management workflows preserved
- [ ] Permissions respect existing rules
- [ ] No breaking changes introduced
**Testing**: Full inventory workflow regression testing
**Estimated Time**: 3 hours

## Summary

### Task Overview
- **Total Tasks**: 22 implementation tasks
- **P1 (Critical)**: 15 tasks  
- **P2 (Important)**: 7 tasks
- **Parallelizable**: 9 tasks marked [P]

### Timeline Estimate
- **Phase 1** (Foundation): 1-2 days
- **Phase 2** (Backend Integration): 1-2 days
- **Phase 3** (Frontend Implementation): 2-3 days  
- **Phase 4** (Testing & Validation): 2 days

**Total Duration**: 6-8 working days

### Dependencies Summary
Most tasks have clear dependencies and can be executed in sequence. Parallelizable tasks marked with [P] can be worked on simultaneously to reduce overall timeline.

### Success Criteria
- All user stories from specification implemented
- All acceptance criteria met
- Tests passing with 95%+ coverage
- Performance requirements achieved
- Accessibility compliance verified
- Documentation updated

This task breakdown provides a clear roadmap for implementing the dashboard reorganization while maintaining code quality, performance, and accessibility standards.