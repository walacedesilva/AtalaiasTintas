import React, { useState } from 'react';
import { CheckCircle, FlaskConical, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { tintometryAPI } from '@/api';
import type { CalculationResult } from '@/types/tintometry';

interface MixtureConfirmationProps {
  calculationResult: CalculationResult;
  onConfirmed: (misturaId: number) => void;
  onCancel?: () => void;
}

/**
 * Displays a calculation summary and provides a "Confirmar Produção" action.
 * Calls misturas.confirm(id) on confirm, then invokes onConfirmed.
 */
export function MixtureConfirmation({
  calculationResult,
  onConfirmed,
  onCancel,
}: MixtureConfirmationProps): React.ReactElement {
  const [confirming, setConfirming] = useState(false);

  const mistura = calculationResult.mistura;
  const calc = calculationResult.calculation;

  async function handleConfirm() {
    if (!mistura) return;
    setConfirming(true);
    try {
      const res = await tintometryAPI.misturas.confirm(mistura.id);
      if (res.success) {
        toast.success('Mistura confirmada com sucesso!');
        onConfirmed(mistura.id);
      } else {
        toast.error(res.error || 'Erro ao confirmar mistura');
      }
    } catch {
      toast.error('Erro ao confirmar mistura');
    } finally {
      setConfirming(false);
    }
  }

  if (!mistura || !calc) {
    return (
      <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
        Dados de cálculo insuficientes para confirmação.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <FlaskConical className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Confirmar Produção</h3>
      </div>

      {/* Mistura info */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm">
        <p className="font-medium text-gray-700">
          Código: <span className="font-mono text-gray-900">{mistura.codigo}</span>
        </p>
        <p className="text-gray-500 mt-0.5">Situação: {mistura.situacao}</p>
      </div>

      {/* Stock warning */}
      {!calc.validacao.stock_ok && (
        <div className="flex items-start gap-2 rounded-md bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium">Estoque insuficiente para alguns pigmentos</p>
            <ul className="list-disc list-inside mt-1 space-y-0.5 text-xs">
              {calc.validacao.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Pigment list */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Pigmentos</h4>
        <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200 text-sm">
          {calc.pigmentos.map((item, idx) => (
            <li key={idx} className="flex items-center justify-between px-4 py-2.5">
              <div className="flex items-center gap-2">
                {item.pigmento.cor_hex && (
                  <span
                    className="w-4 h-4 rounded-full border border-gray-300"
                    style={{ backgroundColor: item.pigmento.cor_hex }}
                  />
                )}
                <span className="font-medium">{item.pigmento.nome}</span>
              </div>
              <div className="flex items-center gap-4 text-right">
                <span className="font-mono">{item.quantidades.calculada_final.toFixed(1)} ml</span>
                <span className="text-gray-500 w-20">R$ {item.custos.total.toFixed(2)}</span>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Cost summary */}
      <div className="flex justify-between text-sm font-semibold text-gray-800 border-t pt-3">
        <span>Custo total estimado</span>
        <span>R$ {calc.custos.total.toFixed(2)}</span>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-1">
        {onCancel && (
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
        )}
        <button
          onClick={handleConfirm}
          disabled={confirming}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          {confirming ? (
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          ) : (
            <CheckCircle className="w-4 h-4" />
          )}
          {confirming ? 'Confirmando...' : 'Confirmar Produção'}
        </button>
      </div>
    </div>
  );
}

export default MixtureConfirmation;
