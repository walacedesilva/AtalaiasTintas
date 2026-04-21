/**
 * Dashboard Services Index
 * 
 * Centralized exports for all dashboard API services.
 */

export { 
  getBusinessMetrics,
  getSalesOverview, 
  getFiscalStatus,
  getSystemHealth
} from './dashboardAPI';

// Re-export types for convenience
export type {
  BusinessMetricsRequest,
  DashboardPreferences,
  MetricFilters
} from '../../types/dashboard';