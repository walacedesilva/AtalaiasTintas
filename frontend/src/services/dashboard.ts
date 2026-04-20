/**
 * Dashboard Services
 * 
 * Mock services for dashboard metrics and data.
 * Simulates API calls with realistic data for development and testing.
 */

import type { BusinessMetrics, TimePeriod } from '../types/dashboard';

// Mock API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Simulated API base URL (replace with actual API in production)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// ===== BUSINESS METRICS SERVICES =====

export interface BusinessMetricsParams {
  timeRange: TimePeriod;
}

export const getBusinessMetrics = async (params: BusinessMetricsParams): Promise<BusinessMetrics> => {
  await delay(Math.random() * 1000 + 500); // Simulate network delay
  
  // Generate realistic mock data based on time range
  const multiplier = getMultiplierForTimeRange(params.timeRange);
  
  return {
    totalSales: {
      value: Math.floor(Math.random() * 50000 * multiplier) + 10000,
      change: (Math.random() - 0.5) * 20, // -10% to +10%
      trend: Math.random() > 0.5 ? 'up' : 'down',
    },
    orderCount: {
      value: Math.floor(Math.random() * 150 * multiplier) + 25,
      change: (Math.random() - 0.5) * 15,
      trend: Math.random() > 0.6 ? 'up' : 'down',
    },
    averageTicket: {
      value: Math.floor(Math.random() * 300) + 150,
      change: (Math.random() - 0.5) * 10,
      trend: Math.random() > 0.4 ? 'up' : 'down',
    },
    conversionRate: {
      value: Math.floor(Math.random() * 15) + 65, // 65-80%
      change: (Math.random() - 0.5) * 5,
      trend: Math.random() > 0.5 ? 'up' : 'down',
    },
    startDate: getStartDate(params.timeRange),
    endDate: new Date().toISOString(),
  };
};

// ===== SALES OVERVIEW SERVICES =====

export const getSalesOverview = async () => {
  await delay(Math.random() * 800 + 300);
  
  return {
    todaysSales: {
      count: Math.floor(Math.random() * 25) + 15,
      value: Math.floor(Math.random() * 15000) + 8000,
      progress: Math.floor(Math.random() * 40) + 60, // 60-100%
    },
    pendingOrders: {
      count: Math.floor(Math.random() * 8) + 2,
      value: Math.floor(Math.random() * 5000) + 2000,
      urgentCount: Math.floor(Math.random() * 3),
    },
    recentOrders: generateMockOrders(10),
  };
};

export const getSalesDashboard = async () => {
  return await getSalesOverview(); // Alias for compatibility
};

// ===== FISCAL STATUS SERVICES =====

export const getFiscalStatus = async () => {
  await delay(Math.random() * 600 + 400);
  
  return {
    nfeStatus: {
      issued: Math.floor(Math.random() * 50) + 20,
      pending: Math.floor(Math.random() * 5) + 1,
      errors: Math.floor(Math.random() * 3),
      lastUpdate: new Date().toISOString(),
    },
    certificateStatus: {
      isValid: Math.random() > 0.1, // 90% chance valid
      expiresAt: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(), // 90 days
      daysUntilExpiry: 90,
    },
    complianceScore: Math.floor(Math.random() * 15) + 85, // 85-100%
  };
};

export const getFiscalDashboard = async () => {
  return await getFiscalStatus(); // Alias for compatibility
};

export const getComplianceAlerts = async () => {
  await delay(Math.random() * 400 + 200);
  
  const alerts = [];
  if (Math.random() > 0.7) {
    alerts.push({
      id: '1',
      type: 'certificate',
      severity: 'warning',
      message: 'Certificado digital expira em 30 dias',
      createdAt: new Date().toISOString(),
    });
  }
  
  if (Math.random() > 0.8) {
    alerts.push({
      id: '2',
      type: 'nfe',
      severity: 'error',
      message: '3 NFe com erro de transmissão',
      createdAt: new Date().toISOString(),
    });
  }
  
  return alerts;
};

// ===== SYSTEM HEALTH SERVICES =====

export const getSystemHealth = async () => {
  await delay(Math.random() * 300 + 200);
  
  return {
    status: 'healthy',
    services: {
      api: 'online',
      database: 'online',
      cache: 'online',
      storage: 'online',
    },
    metrics: {
      uptime: Math.floor(Math.random() * 100000),
      cpu: Math.floor(Math.random() * 30) + 20,
      memory: Math.floor(Math.random() * 40) + 30,
      disk: Math.floor(Math.random() * 20) + 10,
    },
    lastUpdate: new Date().toISOString(),
  };
};

// ===== HELPER FUNCTIONS =====

function getMultiplierForTimeRange(timeRange: TimePeriod): number {
  switch (timeRange) {
    case '24h':
    case 'today':
      return 1;
    case '7d':
      return 7;
    case '30d':
      return 30;
    default:
      return 1;
  }
}

function getStartDate(timeRange: TimePeriod): string {
  const now = new Date();
  switch (timeRange) {
    case '24h':
    case 'today':
      return new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    case '7d':
      return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
    case '30d':
      return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
    default:
      return new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
  }
}

function generateMockOrders(count: number) {
  const customers = [
    'João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Oliveira', 'Carlos Ferreira',
    'Lucia Souza', 'Roberto Lima', 'Patricia Alves', 'Fernando Rocha', 'Juliana Pinto'
  ];
  
  const statuses = ['pending', 'confirmed', 'processing', 'ready', 'delivered'];
  
  return Array.from({ length: count }, (_, i) => ({
    id: `PED-${String(Date.now() + i).slice(-6)}`,
    customerName: customers[Math.floor(Math.random() * customers.length)],
    value: Math.floor(Math.random() * 2000) + 300,
    status: statuses[Math.floor(Math.random() * statuses.length)],
    createdAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
  }));
}

export default {
  getBusinessMetrics,
  getSalesOverview,
  getSalesDashboard,
  getFiscalStatus,
  getFiscalDashboard,
  getComplianceAlerts,
  getSystemHealth,
};