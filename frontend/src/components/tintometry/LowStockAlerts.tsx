import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { tintometryAPI } from '@/api';
import type { StockAlert } from '@/types/tintometry';

interface LowStockAlertsProps {
  lojaId?: number;
}

function severity(alert: StockAlert): 'critical' | 'warning' {
  const pct = alert.saldo_minimo > 0
    ? (alert.saldo_ml / alert.saldo_minimo) * 100
    : 0;
  return pct < 50 || alert.saldo_ml <= 0 ? 'critical' : 'warning';
}

/**
 * Lists pigments that are below minimum stock.
 * Critical (< 50% of minimum) shown in red, warning (50–99%) in yellow.
 * Auto-refreshes every 2 minutes.
 */
export function LowStockAlerts({ lojaId }: LowStockAlertsProps): React.ReactElement {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['tintometry', 'estoque', 'low_stock_alerts', lojaId],
    queryFn: () => tintometryAPI.estoque.getLowStockAlerts(lojaId),
    staleTime: 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
  });

  // Support both flat array and { alerts: [] } shapes from the API
  const alerts: StockAlert[] = Array.isArray(data)
    ? (data as unknown as StockAlert[])
    : (data?.alerts ?? []);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
        <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400" />
        Verificando estoque...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4" />
        Erro ao carregar alertas de estoque.
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-700 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-green-500" />
        Estoque OK — nenhum pigmento abaixo do mínimo.
      </div>
    );
  }

  const critical = alerts.filter((a) => severity(a) === 'critical');
  const warnings = alerts.filter((a) => severity(a) === 'warning');

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          Alertas de Estoque Baixo
          <span className="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
            {alerts.length}
          </span>
        </h4>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${isFetching ? 'animate-spin' : ''}`} />
          Atualizar
        </button>
      </div>

      {critical.length > 0 && (
        <AlertList alerts={critical} variant="critical" />
      )}
      {warnings.length > 0 && (
        <AlertList alerts={warnings} variant="warning" />
      )}
    </div>
  );
}

interface AlertListProps {
  alerts: StockAlert[];
  variant: 'critical' | 'warning';
}

function AlertList({ alerts, variant }: AlertListProps): React.ReactElement {
  const isCritical = variant === 'critical';

  return (
    <ul
      className={`divide-y rounded-lg border text-sm ${
        isCritical
          ? 'divide-red-100 border-red-200 bg-red-50'
          : 'divide-yellow-100 border-yellow-200 bg-yellow-50'
      }`}
    >
      {alerts.map((alert) => {
        const pct = alert.saldo_minimo > 0
          ? Math.round((alert.saldo_ml / alert.saldo_minimo) * 100)
          : 0;
        const barWidth = Math.min(pct, 100);

        return (
          <li key={alert.id} className="px-4 py-3 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {alert.pigmento.cor_hex && (
                  <span
                    className="w-3.5 h-3.5 rounded-full border border-gray-300"
                    style={{ backgroundColor: alert.pigmento.cor_hex }}
                  />
                )}
                <span className="font-medium text-gray-800">{alert.pigmento.nome}</span>
                <span className="text-xs text-gray-500">{alert.pigmento.codigo}</span>
              </div>
              <div className="text-right text-xs">
                <span className={isCritical ? 'font-semibold text-red-700' : 'font-semibold text-yellow-700'}>
                  {alert.saldo_ml.toFixed(0)} ml
                </span>
                <span className="text-gray-400"> / mín {alert.saldo_minimo.toFixed(0)} ml</span>
              </div>
            </div>

            {/* Progress bar */}
            <div className="h-1.5 rounded-full bg-gray-200 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  isCritical ? 'bg-red-500' : 'bg-yellow-500'
                }`}
                style={{ width: `${barWidth}%` }}
              />
            </div>
            <p className={`text-xs ${isCritical ? 'text-red-600' : 'text-yellow-700'}`}>
              {pct}% do mínimo
            </p>
          </li>
        );
      })}
    </ul>
  );
}

export default LowStockAlerts;
