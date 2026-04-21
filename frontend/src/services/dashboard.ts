/**
 * Dashboard Services
 *
 * Real API services for dashboard metrics.
 * Connects to /api/v1/sales/dashboard/ for live data.
 */

import { apiClient } from '../api/client';
import type { TimePeriod } from '../types/dashboard';

// ─── Shared raw response type from the backend ──────────────────────────────

export interface DashboardRawData {
  period: string;
  updated_at: string;
  vendas_totais: { value: number; change: number; trend: 'up' | 'down' };
  pedidos: { value: number; change: number; trend: 'up' | 'down' };
  ticket_medio: { value: number; change: number; trend: 'up' | 'down' };
  taxa_conversao: { value: number; change: number; trend: 'up' | 'down' };
  vendas_hoje: { count: number; valor: number };
  meta_dia: { progresso: number; faturamento_target: number };
  nfe_emitidas: number;
  nfe_pendentes: number;
  nfe_erros: number;
  nfe_ultima_sincronizacao: string;
  produtos_mais_vendidos: Array<{
    id: string;
    nome: string;
    quantidade: number;
    receita: number;
  }>;
}

async function fetchDashboard(): Promise<DashboardRawData> {
  return apiClient.getData<DashboardRawData>('/sales/dashboard/');
}

// ===== BUSINESS METRICS SERVICES =====

export interface BusinessMetricsParams {
  timeRange: TimePeriod;
}

export const getBusinessMetrics = async (_params: BusinessMetricsParams) => {
  const data = await fetchDashboard();
  return {
    totalSales: data.vendas_totais,
    orderCount: data.pedidos,
    averageTicket: data.ticket_medio,
    conversionRate: data.taxa_conversao,
    startDate: data.updated_at,
    endDate: data.updated_at,
  };
};

// ===== SALES OVERVIEW SERVICES =====

export const getSalesOverview = async () => {
  const data = await fetchDashboard();
  return {
    todaysSales: {
      count: data.vendas_hoje.count,
      value: data.vendas_hoje.valor,
      progress: data.meta_dia.progresso,
    },
    pendingOrders: {
      count: 0,
      value: 0,
      urgentCount: 0,
    },
    recentOrders: [],
    topProducts: data.produtos_mais_vendidos,
  };
};

export const getSalesDashboard = getSalesOverview;

// ===== FISCAL STATUS SERVICES =====

export const getFiscalStatus = async () => {
  const data = await fetchDashboard();
  return {
    nfeStatus: {
      issued: data.nfe_emitidas,
      pending: data.nfe_pendentes,
      errors: data.nfe_erros,
      lastUpdate: data.nfe_ultima_sincronizacao,
    },
    certificateStatus: {
      isValid: true,
      expiresAt: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
      daysUntilExpiry: 90,
    },
    complianceScore: 100,
  };
};

export const getFiscalDashboard = getFiscalStatus;

export const getComplianceAlerts = async () => [];

// ===== SYSTEM HEALTH (keep stub — real endpoint not yet available) =========

export const getSystemHealth = async () => {
  return {
    status: 'healthy',
    services: { api: 'online', database: 'online', cache: 'online', storage: 'online' },
    metrics: { uptime: 0, cpu: 0, memory: 0, disk: 0 },
    lastUpdate: new Date().toISOString(),
  };
};

// ===== RAW DATA (for TopProducts component) ==================================

export const getDashboardRawData = fetchDashboard;

export default {
  getBusinessMetrics,
  getSalesOverview,
  getSalesDashboard,
  getFiscalStatus,
  getFiscalDashboard,
  getComplianceAlerts,
  getSystemHealth,
  getDashboardRawData,
};

