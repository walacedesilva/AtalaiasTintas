/**
 * SalesOverview Component
 * 
 * Sales performance widget with recent orders and sales metrics.
 * Uses React Query hooks for real-time sales data display.
 */

import React from 'react';
import { useSalesOverview, useSalesDashboard } from '../../hooks/dashboard';
import { MetricCard } from './MetricCard';

interface SalesOverviewProps {
  period?: 'today' | 'week' | 'month';
  showTrends?: boolean;
  showRecentOrders?: boolean;
  className?: string;
}

export const SalesOverview: React.FC<SalesOverviewProps> = ({
  period = 'today',
  showTrends = true,
  showRecentOrders = true,
  className = ''
}) => {
  const { data: salesData, isLoading, error } = useSalesOverview();
  const { data: dashboardData, isLoading: isDashboardLoading } = useSalesDashboard();

  if (isLoading || isDashboardLoading) {
    return (
      <div className={`sales-overview ${className}`}>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-24 bg-gray-200 rounded"></div>
              ))}
            </div>
            {showRecentOrders && (
              <div>
                <div className="h-5 bg-gray-200 rounded w-1/4 mb-3"></div>
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="h-12 bg-gray-200 rounded"></div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`sales-overview ${className}`}>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-red-800 font-medium">Erro ao carregar vendas</h3>
            <p className="text-red-600 text-sm mt-1">
              Não foi possível carregar os dados de vendas. Tente novamente em alguns instantes.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`sales-overview ${className}`}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Resumo de Vendas
            </h2>
            <span className="text-sm text-gray-500">
              Atualizado: {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>

        <div className="p-6">
          {/* Sales Metrics Cards */}
          {dashboardData && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <MetricCard
                title="Vendas de Hoje"
                value={`${dashboardData.todaysSales.count} vendas`}
                icon={<SalesIcon />}
                color="green"
              />
              <MetricCard
                title="Faturamento Hoje"
                value={formatCurrency(dashboardData.todaysSales.value)}
                icon={<RevenueIcon />}
                color="blue"
              />
              <MetricCard
                title="Meta do Dia"
                value={`${dashboardData.todaysSales.progress}%`}
                icon={<TargetIcon />}
                color="purple"
              />
            </div>
          )}

          {/* Pending Orders Summary */}
          {dashboardData && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-orange-800 font-medium">Pedidos Pendentes</h3>
                  <p className="text-orange-600 text-sm">
                    {dashboardData.pendingOrders.count} pedidos • {formatCurrency(dashboardData.pendingOrders.value)}
                  </p>
                </div>
                {dashboardData.pendingOrders.urgentCount > 0 && (
                  <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full">
                    {dashboardData.pendingOrders.urgentCount} urgentes
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Recent Orders */}
          {showRecentOrders && dashboardData && dashboardData.recentOrders.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Pedidos Recentes
              </h3>
              <div className="space-y-3">
                {dashboardData.recentOrders.slice(0, 5).map((order) => (
                  <div key={order.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <OrderStatusBadge status={order.status} />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {order.customerName}
                        </p>
                        <p className="text-xs text-gray-500">
                          {order.id} • {new Date(order.createdAt).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-900">
                        {formatCurrency(order.value)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              
              {dashboardData.recentOrders.length > 5 && (
                <div className="mt-4 text-center">
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Ver todos os pedidos ({dashboardData.recentOrders.length})
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper Components
const OrderStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'confirmed': return 'bg-blue-100 text-blue-800';
      case 'processing': return 'bg-purple-100 text-purple-800';
      case 'ready': return 'bg-green-100 text-green-800';
      case 'delivered': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'Pendente';
      case 'confirmed': return 'Confirmado';
      case 'processing': return 'Processando';
      case 'ready': return 'Pronto';
      case 'delivered': return 'Entregue';
      default: return status;
    }
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}`}>
      {getStatusLabel(status)}
    </span>
  );
};

// Helper functions
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
}

// Icon Components
const SalesIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
  </svg>
);

const RevenueIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
  </svg>
);

const TargetIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
  </svg>
);

export default SalesOverview;