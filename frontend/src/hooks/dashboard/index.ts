/**
 * Dashboard Hooks Index
 * 
 * Centralized exports for all dashboard React Query hooks.
 */

export { useBusinessMetrics } from './useBusinessMetrics';
export { useSalesOverview } from './useSalesOverview';
export { useFiscalStatus } from './useFiscalStatus';
export { useSystemHealth } from './useSystemHealth';

// Additional specialized hooks
export { useSalesMetrics, useSalesDashboard } from './useSalesMetrics';
export { useFiscalDashboard, useComplianceAlerts } from './useFiscalDashboard';
export { 
  useSystemMonitoring, 
  usePerformanceMetrics, 
  useServiceStatus, 
  useActiveUsers 
} from './useMonitoring';