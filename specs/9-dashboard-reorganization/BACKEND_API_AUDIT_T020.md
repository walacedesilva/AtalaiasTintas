# Backend API Endpoints Audit - Dashboard Reorganization

**Task**: [T020] Verify Backend API Endpoints Status  
**Date**: 2026-04-19  
**Feature**: Dashboard Interface Reorganization  

## Executive Summary

Audit completed for existing backend APIs to support dashboard reorganization feature. Analysis shows **mixed readiness** - some endpoints exist but dashboard-specific aggregation endpoints need to be created.

## Current Backend API Status

### ✅ EXISTING ENDPOINTS (Ready for Use)

#### Sales Module (`/api/sales/`)
- **Vendas (Sales)**: `/sales/vendas/` - List and manage completed sales
  - `GET /sales/vendas/` - List sales with filters (search, date range, pagination)
  - `GET /sales/vendas/{id}/` - Get specific sale details
  - `GET /sales/vendas/{id}/nfe-status/` - Get NFe status for sale

- **Pedidos (Orders)**: `/sales/pedidos/` - List and manage orders  
  - `GET /sales/pedidos/` - List orders with filters (status, customer, date range)
  - `GET /sales/pedidos/{id}/` - Get specific order details

- **Clientes (Customers)**: `/sales/clientes/` - Customer management
  - `GET /sales/clientes/` - List customers with search and pagination
  - `GET /sales/clientes/{id}/historico/` - Customer order history

#### Fiscal Module (`/api/fiscal/`)  
- **NFe Management**: 
  - `GET /fiscal/nfe-automacao/pendentes/` - Get pending NFe ✅
  - `GET /fiscal/nfe-automacao/falhadas/` - Get failed NFe ✅
  - `GET /fiscal/sefaz/` - Get SEFAZ online status ✅
  - `GET /fiscal/notas-fiscais/` - List fiscal notes with filters

#### Tintometry Module (`/api/tintometry/`)
- **Dashboard Stats**: `GET /tintometry/dashboard/stats/` ✅
  - Already provides tintometry-specific dashboard data
  - Returns: `DashboardStats` type with mixing statistics

#### Inventory Module (`/api/inventory/`)
- **Estoque (Stock)**: `/inventory/estoque/` - Stock management
  - `GET /inventory/estoque/` - List stock with status filters (ZERADO, BAIXO, NORMAL)
  - Low stock identification available through status filtering

### ❌ MISSING ENDPOINTS (Need Creation)

#### Sales Dashboard Aggregation
- `GET /sales/dashboard/overview/` **[MISSING]**
  - Should return: today's sales summary, recent orders, sales metrics
  - Required data: sales count, total value, average ticket, pending orders

- `GET /sales/dashboard/metrics/` **[MISSING]** 
  - Should accept time range parameter (24h, 7d, 30d)
  - Required data: sales trends, conversion rates, top products

#### Fiscal Dashboard Status  
- `GET /fiscal/dashboard/status/` **[MISSING]**
  - Should aggregate NFe status, compliance alerts, tax summary
  - Required data: consolidated fiscal health for dashboard display

#### System Monitoring
- `GET /monitoring/system-health/` **[MISSING]**
  - Should return: system uptime, service status, performance metrics
  - Required data: API health, database status, active users, error rates

#### Business Intelligence Aggregation
- `GET /dashboard/business-metrics/` **[MISSING]**
  - Cross-module business intelligence endpoint
  - Should aggregate sales, fiscal, inventory metrics in single call

## Implementation Requirements

### Phase 2A: Extend Existing APIs (2-3 hours)

1. **Sales API Extension** (`backend/apps/sales/views.py`)
   ```python
   @api_view(['GET'])
   def dashboard_overview(request):
       # Aggregate today's sales, pending orders, sales metrics
       pass

   @api_view(['GET'])  
   def dashboard_metrics(request):
       # Time-based sales analytics with trends
       pass
   ```

2. **Fiscal API Extension** (`backend/apps/fiscal/views.py`)
   ```python
   @api_view(['GET'])
   def dashboard_status(request):
       # Aggregate NFe status, compliance, tax summary
       pass
   ```

### Phase 2B: Create New Monitoring Module (4-5 hours)

3. **New Monitoring App** (`backend/apps/monitoring/`)
   ```python
   # New Django app for system monitoring
   @api_view(['GET'])
   def system_health(request):
       # System metrics, service status, health checks
       pass
   ```

### Phase 2C: Business Intelligence Aggregation (2 hours)

4. **Cross-Module Dashboard Endpoint** 
   ```python
   @api_view(['GET'])
   def business_metrics(request):
       # Calls sales, fiscal, inventory APIs and aggregates
       pass  
   ```

## URL Routing Updates Required

```python
# backend/apps/sales/urls.py
urlpatterns += [
    path('dashboard/overview/', views.dashboard_overview, name='sales_dashboard_overview'),
    path('dashboard/metrics/', views.dashboard_metrics, name='sales_dashboard_metrics'),
]

# backend/apps/fiscal/urls.py  
urlpatterns += [
    path('dashboard/status/', views.dashboard_status, name='fiscal_dashboard_status'),
]

# backend/apps/monitoring/urls.py (new)
urlpatterns = [
    path('system-health/', views.system_health, name='monitoring_system_health'),
]

# backend/tintas_system/urls.py
urlpatterns += [
    path('api/dashboard/', include('dashboard.urls')),  # New aggregation endpoints
]
```

## Backend Development Effort Estimate

| Component | Effort | Developer Time |
|-----------|--------|----------------|
| Sales dashboard endpoints | 3 hours | Backend Dev |
| Fiscal dashboard endpoints | 2 hours | Backend Dev |  
| Monitoring module creation | 5 hours | Backend Dev |
| Business aggregation endpoint | 2 hours | Backend Dev |
| Testing & integration | 3 hours | Backend Dev |
| **TOTAL BACKEND EFFORT** | **15 hours** | **~2 days** |

## Risk Assessment

### 🟡 MEDIUM RISK
- **Dependency**: Frontend implementation can proceed with mock data while backend APIs are developed
- **Parallel Development**: Frontend and backend can work in parallel using OpenAPI contracts
- **Database Performance**: New aggregation queries may need optimization for large datasets

### ✅ LOW RISK  
- **Existing Patterns**: All new endpoints follow established API patterns
- **Authentication**: Existing authentication system covers new endpoints
- **Error Handling**: Existing error handling framework applies

## Next Steps

1. **Immediate (T004-T006)**: Extend existing API files to add dashboard methods using mock responses
2. **Backend Coordination**: Share this audit with backend team for sprint planning
3. **API Contracts**: Define OpenAPI schemas for new endpoints to enable parallel development
4. **Performance Testing**: Load test aggregation endpoints with production data volumes

## Conclusion

**Dashboard reorganization is FEASIBLE** with moderate backend development effort. Frontend can proceed with implementation using existing endpoints and mock data for missing endpoints. Backend APIs follow established patterns making implementation straightforward.

**Recommendation**: Proceed with frontend implementation (Phase 1) while coordinating backend API development (Phase 2) in parallel.