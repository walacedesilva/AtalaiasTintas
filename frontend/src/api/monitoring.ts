import { apiClient } from './client';
import type { SystemHealth } from '@/types/dashboard';

/**
 * Monitoring API
 * 
 * Handles system health monitoring, performance metrics, and service status.
 * Created for T006: Create System Monitoring API
 */

export const monitoringAPI = {
  // -----------------------------------------------------------------------
  // System Health & Monitoring (T006)
  // -----------------------------------------------------------------------
  async getSystemHealth(): Promise<SystemHealth> {
    // TODO: Connect to real endpoint when backend implements /api/monitoring/system-health/
    // For now, return mock data
    return mockSystemHealth();
  },

  async getPerformanceMetrics(): Promise<{
    responseTime: number;
    throughput: number;
    errorRate: number;
    uptime: number;
  }> {
    // TODO: Connect to real endpoint when backend implements /api/monitoring/performance/
    // For now, return mock data  
    return mockPerformanceMetrics();
  },

  async getServiceStatus(): Promise<Array<{
    name: string;
    status: 'healthy' | 'warning' | 'error';
    responseTime: number;
    uptime: number;
    lastCheck: string;
  }>> {
    // TODO: Connect to real endpoint when backend implements /api/monitoring/services/
    // For now, return mock data
    return mockServiceStatus();
  },

  async getActiveUsers(): Promise<{
    total: number;
    online: number;
    peak24h: number;
    averageSession: number;
  }> {
    // TODO: Connect to real endpoint when backend implements /api/monitoring/users/
    // For now, return mock data
    return mockActiveUsers();
  },
};

// ─── Mock Data for Monitoring (Remove when backend ready) ────────────────────

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
      },
      {
        name: 'Payment Gateway',
        status: 'healthy',
        responseTime: Math.floor(Math.random() * 500) + 100,
        uptime: 99.2,
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

function mockPerformanceMetrics(): {
  responseTime: number;
  throughput: number;
  errorRate: number;
  uptime: number;
} {
  return {
    responseTime: Math.floor(Math.random() * 200) + 100, // 100-300ms
    throughput: Math.floor(Math.random() * 1000) + 500,  // 500-1500 req/min
    errorRate: Number((Math.random() * 2).toFixed(2)),    // 0-2%
    uptime: Number((99 + Math.random()).toFixed(2))       // 99-100%
  };
}

function mockServiceStatus(): Array<{
  name: string;
  status: 'healthy' | 'warning' | 'error';
  responseTime: number;
  uptime: number;
  lastCheck: string;
}> {
  const services = [
    'Web Server',
    'Database',
    'Cache Redis',
    'File Storage',
    'Email Service',
    'Background Jobs'
  ];

  return services.map(service => ({
    name: service,
    status: Math.random() > 0.05 ? 'healthy' : (Math.random() > 0.5 ? 'warning' : 'error'),
    responseTime: Math.floor(Math.random() * 300) + 50,
    uptime: Number((98 + Math.random() * 2).toFixed(1)),
    lastCheck: new Date(Date.now() - Math.random() * 300000).toISOString() // Within 5 minutes
  }));
}

function mockActiveUsers(): {
  total: number;
  online: number;
  peak24h: number;
  averageSession: number;
} {
  const total = Math.floor(Math.random() * 50) + 10;
  const online = Math.floor(Math.random() * total) + 1;
  
  return {
    total,
    online,
    peak24h: Math.floor(Math.random() * 30) + total,
    averageSession: Math.floor(Math.random() * 60) + 15 // 15-75 minutes
  };
}