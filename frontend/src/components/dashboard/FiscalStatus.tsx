/**
 * FiscalStatus Component
 * 
 * Fiscal compliance and NFe status monitoring widget.
 * Displays NFe status, tax summary, compliance alerts, and certificate status.
 */

import React from 'react';
import { useFiscalStatus, useFiscalDashboard, useComplianceAlerts } from '../../hooks/dashboard';
import { MetricCard } from './MetricCard';

interface FiscalStatusProps {
  showAlerts?: boolean;
  maxAlerts?: number;
  showTaxSummary?: boolean;
  className?: string;
}

export const FiscalStatus: React.FC<FiscalStatusProps> = ({
  showAlerts = true,
  maxAlerts = 5,
  showTaxSummary = true,
  className = ''
}) => {
  const { data: fiscalData, isLoading, error } = useFiscalStatus();
  const { data: dashboardData, isLoading: isDashboardLoading } = useFiscalDashboard();
  const { data: alerts, isLoading: isAlertsLoading } = useComplianceAlerts();

  if (isLoading || isDashboardLoading) {
    return (
      <div className={`fiscal-status ${className}`}>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-24 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`fiscal-status ${className}`}>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-red-800 font-medium">Erro ao carregar status fiscal</h3>
            <p className="text-red-600 text-sm mt-1">
              Não foi possível carregar os dados fiscais. Tente novamente em alguns instantes.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`fiscal-status ${className}`}>
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Status Fiscal
            </h2>
            <span className="text-sm text-gray-500">
              Última sincronização: {fiscalData ? new Date(fiscalData.nfeStatus.lastUpdate).toLocaleTimeString() : '--'}
            </span>
          </div>
        </div>

        <div className="p-6">
          {/* NFe Status Cards */}
          {fiscalData && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <MetricCard
                title="NFe Emitidas"
                value={fiscalData.nfeStatus.issued.toString()}
                icon={<DocumentCheckIcon />}
                color="green"
              />
              <MetricCard
                title="NFe Pendentes"
                value={fiscalData.nfeStatus.pending.toString()}
                icon={<ClockIcon />}
                color="orange"
              />
              <MetricCard
                title="NFe com Erro"
                value={fiscalData.nfeStatus.errors.toString()}
                icon={<ExclamationIcon />}
                color="red"
              />
            </div>
          )}

          {/* Certificate Status */}
          {fiscalData && fiscalData.certificateStatus && (
            <div className="mb-6">
              <div className={`p-4 rounded-lg border ${
                fiscalData.certificateStatus.isValid 
                  ? fiscalData.certificateStatus.daysUntilExpiry < 30
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className={`font-medium ${
                      fiscalData.certificateStatus.isValid 
                        ? fiscalData.certificateStatus.daysUntilExpiry < 30
                          ? 'text-yellow-800'
                          : 'text-green-800'
                        : 'text-red-800'
                    }`}>
                      Certificado Digital
                    </h3>
                    <p className={`text-sm ${
                      fiscalData.certificateStatus.isValid 
                        ? fiscalData.certificateStatus.daysUntilExpiry < 30
                          ? 'text-yellow-600'
                          : 'text-green-600'
                        : 'text-red-600'
                    }`}>
                      {fiscalData.certificateStatus.isValid 
                        ? `Válido até ${new Date(fiscalData.certificateStatus.expiresAt).toLocaleDateString()} (${fiscalData.certificateStatus.daysUntilExpiry} dias)`
                        : 'Certificado inválido ou expirado'
                      }
                    </p>
                  </div>
                  <CertificateIcon 
                    className={`w-8 h-8 ${
                      fiscalData.certificateStatus.isValid 
                        ? fiscalData.certificateStatus.daysUntilExpiry < 30
                          ? 'text-yellow-600'
                          : 'text-green-600'
                        : 'text-red-600'
                    }`}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tax Summary */}
          {showTaxSummary && fiscalData && fiscalData.taxSummary && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Resumo de Impostos
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="text-blue-800 text-sm font-medium">ICMS</div>
                  <div className="text-blue-900 text-lg font-semibold">
                    {formatCurrency(fiscalData.taxSummary.icms)}
                  </div>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                  <div className="text-purple-800 text-sm font-medium">IPI</div>
                  <div className="text-purple-900 text-lg font-semibold">
                    {formatCurrency(fiscalData.taxSummary.ipi)}
                  </div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <div className="text-green-800 text-sm font-medium">PIS</div>
                  <div className="text-green-900 text-lg font-semibold">
                    {formatCurrency(fiscalData.taxSummary.pis)}
                  </div>
                </div>
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                  <div className="text-orange-800 text-sm font-medium">COFINS</div>
                  <div className="text-orange-900 text-lg font-semibold">
                    {formatCurrency(fiscalData.taxSummary.cofins)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Compliance Alerts */}
          {showAlerts && !isAlertsLoading && alerts && alerts.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Alertas de Compliance
              </h3>
              <div className="space-y-3">
                {alerts.slice(0, maxAlerts).map((alert) => (
                  <div key={alert.id} className={`p-4 rounded-lg border ${getAlertStyles(alert.type)}`}>
                    <div className="flex items-start">
                      <div className="flex-shrink-0 mr-3">
                        {getAlertIcon(alert.type)}
                      </div>
                      <div className="flex-grow">
                        <p className={`font-medium ${getAlertTextColor(alert.type)}`}>
                          {alert.message}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Prioridade: {getAlertPriorityLabel(alert.priority)} • 
                          {new Date(alert.createdAt).toLocaleString()}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getAlertBadgeStyles(alert.priority)}`}>
                        {getAlertPriorityLabel(alert.priority)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              
              {alerts.length > maxAlerts && (
                <div className="mt-4 text-center">
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Ver todos os alertas ({alerts.length})
                  </button>
                </div>
              )}
            </div>
          )}

          {showAlerts && !isAlertsLoading && (!alerts || alerts.length === 0) && (
            <div className="text-center py-8">
              <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600">Nenhum alerta de compliance pendente</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper functions
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
}

function getAlertStyles(type: 'info' | 'warning' | 'error'): string {
  switch (type) {
    case 'info': return 'bg-blue-50 border-blue-200';
    case 'warning': return 'bg-yellow-50 border-yellow-200';
    case 'error': return 'bg-red-50 border-red-200';
    default: return 'bg-gray-50 border-gray-200';
  }
}

function getAlertTextColor(type: 'info' | 'warning' | 'error'): string {
  switch (type) {
    case 'info': return 'text-blue-800';
    case 'warning': return 'text-yellow-800';
    case 'error': return 'text-red-800';
    default: return 'text-gray-800';
  }
}

function getAlertBadgeStyles(priority: 'low' | 'medium' | 'high'): string {
  switch (priority) {
    case 'low': return 'bg-gray-100 text-gray-800';
    case 'medium': return 'bg-yellow-100 text-yellow-800';
    case 'high': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

function getAlertPriorityLabel(priority: 'low' | 'medium' | 'high'): string {
  switch (priority) {
    case 'low': return 'Baixa';
    case 'medium': return 'Média';
    case 'high': return 'Alta';
    default: return priority;
  }
}

function getAlertIcon(type: 'info' | 'warning' | 'error') {
  switch (type) {
    case 'info':
      return <InformationIcon className="w-5 h-5 text-blue-500" />;
    case 'warning':
      return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
    case 'error':
      return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
    default:
      return <InformationIcon className="w-5 h-5 text-gray-500" />;
  }
}

// Icon Components
const DocumentCheckIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExclamationIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const CertificateIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
  </svg>
);

const InformationIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExclamationTriangleIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const ExclamationCircleIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CheckCircleIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

export default FiscalStatus;