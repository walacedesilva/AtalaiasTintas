/**
 * MetricCard Component
 * 
 * Reusable metric display component for dashboard cards.
 * Displays metric value, trend indicators, and optional actions.
 */

import React from 'react';

interface MetricCardProps {
  title: string;
  value: string;
  change?: number;
  trend?: 'up' | 'down';
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red';
  loading?: boolean;
  error?: string;
  onClick?: () => void;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  trend,
  icon,
  color = 'blue',
  loading = false,
  error,
  onClick,
  className = ''
}) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50 border-blue-200',
    green: 'text-green-600 bg-green-50 border-green-200',
    purple: 'text-purple-600 bg-purple-50 border-purple-200',
    orange: 'text-orange-600 bg-orange-50 border-orange-200',
    red: 'text-red-600 bg-red-50 border-red-200',
  };

  const cardClasses = `
    bg-white rounded-lg shadow border p-6 hover:shadow-md transition-shadow
    ${onClick ? 'cursor-pointer hover:bg-gray-50' : ''}
    ${className}
  `.trim();

  if (loading) {
    return (
      <div className={cardClasses}>
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-6 w-6 bg-gray-200 rounded"></div>
          </div>
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/3"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cardClasses}>
        <div className="text-red-600">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-900">{title}</h3>
            <ExclamationIcon />
          </div>
          <p className="text-sm">Erro ao carregar</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cardClasses} onClick={onClick}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        {icon && (
          <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
        )}
      </div>
      
      <div className="mb-2">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>

      {(change !== undefined && trend) && (
        <div className="flex items-center">
          <span
            className={`inline-flex items-center text-sm font-medium ${
              trend === 'up' ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {trend === 'up' ? (
              <TrendUpIcon />
            ) : (
              <TrendDownIcon />
            )}
            {Math.abs(change)}%
          </span>
          <span className="ml-2 text-sm text-gray-500">
            vs período anterior
          </span>
        </div>
      )}
    </div>
  );
};

// Simple icon components
const TrendUpIcon = () => (
  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7m0 10h-10" />
  </svg>
);

const TrendDownIcon = () => (
  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10m0-10h10" />
  </svg>
);

const ExclamationIcon = () => (
  <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

export default MetricCard;