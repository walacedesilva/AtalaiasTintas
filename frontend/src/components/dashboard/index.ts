/**
 * Dashboard Components Index
 * 
 * Centralized exports for all dashboard components.
 */

export { BusinessMetrics } from './BusinessMetrics';
export { SalesOverview } from './SalesOverview';
export { FiscalStatus } from './FiscalStatus';
export { SystemMonitoring } from './SystemMonitoring';
export { MetricCard } from './MetricCard';

// Re-export types for convenience
export type {
  BusinessMetrics as BusinessMetricsType,
  SalesOverview as SalesOverviewType,
  FiscalStatus as FiscalStatusType,
  SystemHealth as SystemHealthType
} from '../../types/dashboard';