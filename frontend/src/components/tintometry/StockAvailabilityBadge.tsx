import React from 'react';

interface StockAvailabilityBadgeProps {
  saldo_ml: number;
  saldo_minimo: number;
  showText?: boolean;
  size?: 'sm' | 'md';
}

/**
 * Color-coded badge indicating pigment stock availability.
 * Green  ≥ 150% of minimum
 * Yellow  50–149% of minimum
 * Red    < 50% of minimum (or zero)
 */
export function StockAvailabilityBadge({
  saldo_ml,
  saldo_minimo,
  showText = true,
  size = 'sm',
}: StockAvailabilityBadgeProps): React.ReactElement {
  const percentual = saldo_minimo > 0 ? (saldo_ml / saldo_minimo) * 100 : 0;

  let colorClass: string;
  let label: string;

  if (saldo_ml <= 0) {
    colorClass = 'bg-red-100 text-red-800';
    label = 'Sem estoque';
  } else if (percentual >= 150) {
    colorClass = 'bg-green-100 text-green-800';
    label = 'OK';
  } else if (percentual >= 50) {
    colorClass = 'bg-yellow-100 text-yellow-800';
    label = 'Atenção';
  } else {
    colorClass = 'bg-red-100 text-red-800';
    label = 'Crítico';
  }

  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ${colorClass} ${sizeClass}`}>
      <span
        className={`rounded-full ${size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2'} ${
          saldo_ml <= 0 || percentual < 50
            ? 'bg-red-500'
            : percentual < 150
            ? 'bg-yellow-500'
            : 'bg-green-500'
        }`}
      />
      {showText && label}
      {saldo_minimo > 0 && (
        <span className="opacity-70">{Math.round(percentual)}%</span>
      )}
    </span>
  );
}

export default StockAvailabilityBadge;
