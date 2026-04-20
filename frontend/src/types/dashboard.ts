/**
 * Dashboard Interface Types
 * 
 * TypeScript definitions for the dashboard reorganization feature.
 * Supports business operations focus with sales, orders, fiscal, and monitoring data.
 */

import { ReactComponentElement } from 'react';

// ===== CORE DASHBOARD TYPES =====

export interface BusinessMetrics {
  sales: SalesMetrics;
  orders: OrdersMetrics;
  fiscal: FiscalMetrics;
  inventory: InventoryMetrics;
  system: SystemMetrics;
}

export interface DashboardQuickAction {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<any>;
  path: string;
  permission?: string;
  priority: 'high' | 'medium' | 'low';
  badge?: string | number;
}

// ===== SALES METRICS TYPES =====

export interface SalesMetrics {
  today: number;
  week: number;
  month: number;
  trend: TrendIndicator;
  averageTicket: number;
  transactionCount: number;
  topProducts: TopProduct[];
  pendingPayments: number;
}

export interface SalesOverview {
  period: TimePeriod;
  totalSales: number;
  salesCount: number;
  averageTicket: number;
  trendPercentage: number;
  periodComparison: PeriodComparison;
  recentTransactions: RecentTransaction[];
}

export interface RecentTransaction {
  id: string;
  customerName: string;
  amount: number;
  timestamp: Date;
  status: 'completed' | 'pending' | 'failed';
}

export interface TopProduct {
  id: string;
  name: string;
  salesCount: number;
  revenue: number;
}

// ===== ORDERS METRICS TYPES =====

export interface OrdersMetrics {
  pending: number;
  processing: number;
  completedToday: number;
  overdue: number;
  agingAnalysis: AgingAnalysis;
  recentOrders: RecentOrder[];
}

export interface AgingAnalysis {
  '0-7_days': number;
  '8-15_days': number;
  '15+_days': number;
}

export interface RecentOrder {
  id: string;
  customerName: string;
  items: number;
  total: number;
  status: OrderStatus;
  createdAt: Date;
  dueDate?: Date;
}

export type OrderStatus = 
  | 'pending' 
  | 'processing' 
  | 'ready' 
  | 'completed' 
  | 'cancelled' 
  | 'overdue';

// ===== FISCAL METRICS TYPES =====

export interface FiscalMetrics {
  nfePending: number;
  nfeFailed: number;
  sefazStatus: SefazStatus;
  complianceScore: number;
  alerts: FiscalAlert[];
  monthlyTaxes: MonthlyTaxInfo;
}

export interface FiscalStatus {
  nfePending: number;
  nfeFailed: number;
  sefazStatus: SefazStatus;
  complianceAlerts: FiscalAlert[];
  lastSync: Date;
  nextDeadline?: TaxDeadline;
}

export interface FiscalAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  actionUrl?: string;
  actionLabel?: string;
  timestamp: Date;
}

export interface MonthlyTaxInfo {
  totalTaxes: number;
  paidTaxes: number;
  pendingTaxes: number;
  dueDate: Date;
}

export interface TaxDeadline {
  type: string;
  description: string;
  dueDate: Date;
  amount?: number;
}

export type SefazStatus = 'online' | 'offline' | 'instable' | 'maintenance';

// ===== INVENTORY METRICS TYPES =====

export interface InventoryMetrics {
  lowStockItems: number;
  outOfStockItems: number;
  totalProducts: number;
  stockValue: number;
  criticalAlerts: InventoryAlert[];
  topMovingProducts: TopProduct[];
}

export interface InventoryAlert {
  id: string;
  productId: string;
  productName: string;
  currentStock: number;
  minimumStock: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  businessImpact: BusinessImpact;
  suggestedAction: string;
}

export interface BusinessImpact {
  affectedSales: number;
  lostRevenue: number;
  customerImpact: 'none' | 'low' | 'medium' | 'high';
}

// ===== SYSTEM METRICS TYPES =====

export interface SystemMetrics {
  uptime: number;
  uptimePercentage: number;
  responseTime: number;
  errorRate: number;
  activeUsers: number;
  databaseHealth: HealthStatus;
  lastUpdate: Date;
}

export interface SystemHealth {
  uptime: number;
  responseTimeMs: number;
  errorRate: number;
  activeUsers: number;
  databaseHealth: HealthStatus;
  services: ServiceStatus[];
  alerts: SystemAlert[];
}

export interface ServiceStatus {
  name: string;
  status: HealthStatus;
  responseTime: number;
  lastCheck: Date;
}

export interface SystemAlert {
  id: string;
  service: string;
  message: string;
  severity: AlertSeverity;
  timestamp: Date;
  resolved: boolean;
}

export type HealthStatus = 'good' | 'warning' | 'critical' | 'offline';
export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';

// ===== SHARED UTILITY TYPES =====

export interface TrendIndicator {
  direction: 'up' | 'down' | 'neutral';
  percentage: number;
  period: string;
  isPositive: boolean;
}

export interface PeriodComparison {
  previousTotal: number;
  growthRate: number;
  period: string;
}

export type TimePeriod = 'today' | 'week' | 'month' | 'quarter' | 'year';

export interface DateRange {
  start: Date;
  end: Date;
}

// ===== API RESPONSE TYPES =====

export interface BusinessMetricsResponse {
  data: BusinessMetrics;
  timestamp: Date;
  status: 'success' | 'partial' | 'error';
  errors?: string[];
}

export interface SalesDashboardData {
  overview: SalesOverview;
  metrics: SalesMetrics;
  lastUpdated: Date;
}

export interface FiscalDashboardData {
  status: FiscalStatus;
  metrics: FiscalMetrics;
  lastUpdated: Date;
}

export interface DashboardPreferences {
  userId: string;
  timeRange: TimePeriod;
  visibleMetrics: string[];
  refreshInterval: number;
  compactMode: boolean;
  notifications: NotificationPreferences;
}

export interface NotificationPreferences {
  fiscalAlerts: boolean;
  inventoryAlerts: boolean;
  systemAlerts: boolean;
  salesReports: boolean;
}

// ===== REQUEST TYPES =====

export interface BusinessMetricsRequest {
  timeRange: TimePeriod;
  includeComparisons?: boolean;
  lojaId?: number;
  filters?: MetricFilters;
}

export interface MetricFilters {
  productCategories?: string[];
  customerTypes?: string[];
  salesChannels?: string[];
  excludeReturns?: boolean;
}

export interface DashboardUpdateRequest {
  preferences: Partial<DashboardPreferences>;
  timestamp: Date;
}

// ===== COMPONENT PROP TYPES =====

export interface BaseMetricCardProps {
  title: string;
  value: string | number;
  loading?: boolean;
  error?: string;
  onClick?: () => void;
  className?: string;
}

export interface TrendMetricCardProps extends BaseMetricCardProps {
  trend?: TrendIndicator;
  subtitle?: string;
  icon?: React.ReactNode;
}

export interface AlertMetricCardProps extends BaseMetricCardProps {
  alerts: (FiscalAlert | InventoryAlert | SystemAlert)[];
  maxAlertsShown?: number;
  onAlertClick?: (alert: any) => void;
}

// ===== DASHBOARD LAYOUT TYPES =====

export interface DashboardLayout {
  quickActions: DashboardQuickAction[];
  metricCards: MetricCardConfig[];
  widgets: WidgetConfig[];
  refreshInterval: number;
}

export interface MetricCardConfig {
  id: string;
  type: 'sales' | 'orders' | 'fiscal' | 'inventory' | 'system';
  size: 'small' | 'medium' | 'large';
  position: GridPosition;
  visible: boolean;
}

export interface WidgetConfig {
  id: string;
  type: 'chart' | 'list' | 'table' | 'summary';
  title: string;
  size: WidgetSize;
  position: GridPosition;
  dataSource: string;
  refreshInterval?: number;
}

export interface GridPosition {
  row: number;
  column: number;
  rowSpan?: number;
  columnSpan?: number;
}

export type WidgetSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';

// ===== EXPORT ALL TYPES =====

export type {
  // Re-export all types for easy importing
} from './dashboard';