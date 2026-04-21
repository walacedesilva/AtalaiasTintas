/**
 * BusinessMetrics Component
 * 
 * Displays key business metrics including sales, orders, fiscal status, and inventory.
 * Uses React Query hooks for real-time data with proper loading and error states.
 */

import React from 'react';
import { useBusinessMetrics } from '../../hooks/dashboard';
import { TimePeriod } from '../../types/dashboard';
import { MetricCard } from './MetricCard';

interface BusinessMetricsProps {
  timeRange?: TimePeriod;
  showDetails?: boolean;
  className?: string;
}

export const BusinessMetrics: React.FC<BusinessMetricsProps> = ({
  timeRange = '24h',
  showDetails = false,
  className = ''
}) => {
  const { data: metrics, isLoading, error } = useBusinessMetrics(timeRange);

  if (isLoading) {
    return (
      <div className={`business-metrics ${className}`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`business-metrics ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium">Erro ao carregar métricas</h3>
          <p className="text-red-600 text-sm mt-1">
            Não foi possível carregar os dados. Tente novamente em alguns instantes.
          </p>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className={`business-metrics ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Métricas do Negócio
        </h2>
        <p className="text-gray-600 text-sm">
          Período: {getPeriodLabel(timeRange)} • Última atualização: {new Date().toLocaleTimeString()}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Sales */}
        <MetricCard
          title="Vendas Totais"
          value={formatCurrency(metrics.totalSales.value)}
          change={metrics.totalSales.change}
          trend={metrics.totalSales.trend}
          icon={<CurrencyIcon />}
          color="blue"
        />

        {/* Order Count */}
        <MetricCard
          title="Pedidos"
          value={metrics.orderCount.value.toString()}
          change={metrics.orderCount.change}
          trend={metrics.orderCount.trend}
          icon={<OrderIcon />}
          color="green"
        />

        {/* Average Ticket */}
        <MetricCard
          title="Ticket Médio"
          value={formatCurrency(metrics.averageTicket.value)}
          change={metrics.averageTicket.change}
          trend={metrics.averageTicket.trend}
          icon={<TicketIcon />}
          color="purple"
        />

        {/* Conversion Rate */}
        <MetricCard
          title="Taxa de Conversão"
          value={`${metrics.conversionRate.value}%`}
          change={metrics.conversionRate.change}
          trend={metrics.conversionRate.trend}
          icon={<ConversionIcon />}
          color="orange"
        />
      </div>

      {showDetails && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Additional detailed metrics can be added here */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Período Selecionado</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <p><strong>Início:</strong> {new Date(metrics.startDate).toLocaleDateString()}</p>
              <p><strong>Fim:</strong> {new Date(metrics.endDate).toLocaleDateString()}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper functions
function getPeriodLabel(period: TimePeriod): string {
  switch (period) {
    case '24h': return 'Últimas 24 horas';
    case '7d': return 'Últimos 7 dias';
    case '30d': return 'Últimos 30 dias';
    default: return period;
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
}

// Simple icon components (can be replaced with actual icon library)
const CurrencyIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
  </svg>
);

const OrderIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
  </svg>
);

const TicketIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
  </svg>
);

const ConversionIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

export default BusinessMetrics;