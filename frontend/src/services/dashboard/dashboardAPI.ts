/**
 * Dashboard API Service
 * 
 * API service for dashboard-specific endpoints.
 * Follows existing API patterns using apiClient.
 */

import { apiClient } from '../../api/client';
import { 
  BusinessMetrics, 
  SalesOverview, 
  FiscalStatus, 
  SystemHealth,
  BusinessMetricsRequest,
  TimePeriod 
} from '../../types/dashboard';

// ─── Dashboard API Functions ─────────────────────────────────────────────────

/**
 * Get consolidated business metrics for dashboard display
 */
export async function getBusinessMetrics(request: BusinessMetricsRequest): Promise<BusinessMetrics> {
  // TODO: Connect to real API endpoint in Phase 2 (T020)
  // For now, return mock data
  await mockDelay();
  return mockBusinessMetrics(request.timeRange);
}

/**
 * Get sales overview data for dashboard
 */
export async function getSalesOverview(): Promise<SalesOverview> {
  // TODO: Connect to real API endpoint in Phase 2 (T004) 
  // For now, return mock data
  await mockDelay();
  return mockSalesOverview();
}

/**
 * Get fiscal status and compliance information
 */
export async function getFiscalStatus(): Promise<FiscalStatus> {
  // TODO: Connect to real API endpoint in Phase 2 (T005)
  // For now, return mock data  
  await mockDelay();
  return mockFiscalStatus();
}

/**
 * Get system health and monitoring data
 */
export async function getSystemHealth(): Promise<SystemHealth> {
  // TODO: Connect to real API endpoint in Phase 2 (T006)
  // For now, return mock data
  await mockDelay();
  return mockSystemHealth();
}

// ─── Mock Utilities (Remove in Phase 2) ─────────────────────────────────────

async function mockDelay(ms: number = 500): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ─── Mock Data Generators (Remove in Phase 2) ──────────────────────────────

function mockBusinessMetrics(timeRange: TimePeriod): BusinessMetrics {
  const now = new Date();
  const pastDate = new Date();
  
  switch (timeRange) {
    case '24h':
      pastDate.setHours(pastDate.getHours() - 24);
      break;
    case '7d':
      pastDate.setDate(pastDate.getDate() - 7);
      break;
    case '30d':
      pastDate.setDate(pastDate.getDate() - 30);
      break;
  }

  return {
    period: timeRange,
    startDate: pastDate.toISOString(),
    endDate: now.toISOString(),
    totalSales: {
      value: Math.floor(Math.random() * 100000) + 50000,
      change: Math.floor(Math.random() * 30) - 15,
      trend: Math.random() > 0.5 ? 'up' : 'down'
    },
    orderCount: {
      value: Math.floor(Math.random() * 200) + 50,
      change: Math.floor(Math.random() * 20) - 10,
      trend: Math.random() > 0.5 ? 'up' : 'down'
    },
    averageTicket: {
      value: Math.floor(Math.random() * 1000) + 200,
      change: Math.floor(Math.random() * 15) - 7,
      trend: Math.random() > 0.5 ? 'up' : 'down'
    },
    conversionRate: {
      value: Number((Math.random() * 10 + 5).toFixed(1)),
      change: Number((Math.random() * 5 - 2.5).toFixed(1)),
      trend: Math.random() > 0.5 ? 'up' : 'down'
    }
  };
}

function mockSalesOverview(): SalesOverview {
  return {
    todaysSales: {
      count: Math.floor(Math.random() * 50) + 10,
      value: Math.floor(Math.random() * 20000) + 5000,
      target: 30000,
      progress: Number(((Math.random() * 80) + 20).toFixed(1))
    },
    pendingOrders: {
      count: Math.floor(Math.random() * 20) + 5,
      value: Math.floor(Math.random() * 15000) + 3000,
      urgentCount: Math.floor(Math.random() * 5) + 1
    },
    recentOrders: Array.from({ length: 5 }, (_, i) => ({
      id: `ORD-${1000 + i}`,
      customerName: [`Cliente A`, `Cliente B`, `Cliente C`, `Cliente D`, `Cliente E`][i],
      value: Math.floor(Math.random() * 2000) + 500,
      status: ['pending', 'confirmed', 'processing', 'ready', 'delivered'][Math.floor(Math.random() * 5)] as any,
      createdAt: new Date(Date.now() - Math.random() * 86400000 * 3).toISOString()
    })),
    topProducts: Array.from({ length: 5 }, (_, i) => ({
      id: `PROD-${100 + i}`,
      name: [`Tinta Premium Branca`, `Tinta Standard Azul`, `Verniz Acetinado`, `Primer Universal`, `Tinta Fosca Verde`][i],
      salesCount: Math.floor(Math.random() * 50) + 10,
      revenue: Math.floor(Math.random() * 5000) + 1000,
      category: 'tinta'
    }))
  };
}

function mockFiscalStatus(): FiscalStatus {
  return {
    nfeStatus: {
      issued: Math.floor(Math.random() * 100) + 50,
      pending: Math.floor(Math.random() * 10) + 2,
      errors: Math.floor(Math.random() * 3),
      lastUpdate: new Date().toISOString()
    },
    complianceAlerts: [
      {
        id: 'ALERT-001',
        type: 'warning',
        message: 'NFe pendente há mais de 2 horas',
        priority: 'medium',
        createdAt: new Date(Date.now() - 7200000).toISOString()
      }
    ],
    certificateStatus: {
      isValid: true,
      expiresAt: new Date(Date.now() + 86400000 * 180).toISOString(),
      daysUntilExpiry: 180,
      issuer: 'AC SERASA'
    },
    taxSummary: {
      icms: Number((Math.random() * 5000 + 1000).toFixed(2)),
      ipi: Number((Math.random() * 1000 + 200).toFixed(2)),
      pis: Number((Math.random() * 500 + 100).toFixed(2)),
      cofins: Number((Math.random() * 1000 + 300).toFixed(2))
    }
  };
}

function mockSystemHealth(): SystemHealth {
  return {
    overallStatus: Math.random() > 0.1 ? 'healthy' : 'warning',
    services: [
      {
        name: 'API Backend',
        status: 'healthy',
        responseTime: Math.floor(Math.random() * 200) + 50,
        uptime: 99.8,
        lastCheck: new Date().toISOString()
      },
      {
        name: 'Database',
        status: 'healthy',
        responseTime: Math.floor(Math.random() * 50) + 10,
        uptime: 99.9,
        lastCheck: new Date().toISOString()
      },
      {
        name: 'NFe Service',
        status: Math.random() > 0.9 ? 'warning' : 'healthy',
        responseTime: Math.floor(Math.random() * 1000) + 200,
        uptime: 98.5,
        lastCheck: new Date().toISOString()
      }
    ],
    metrics: {
      cpuUsage: Number((Math.random() * 60 + 20).toFixed(1)),
      memoryUsage: Number((Math.random() * 50 + 30).toFixed(1)),
      diskUsage: Number((Math.random() * 40 + 40).toFixed(1)),
      activeUsers: Math.floor(Math.random() * 20) + 5
    },
    alerts: [
      {
        id: 'SYS-001',
        level: 'info',
        message: 'Sistema funcionando normalmente',
        timestamp: new Date().toISOString(),
        service: 'system'
      }
    ]
  };
}