import React, { useState } from 'react';
import { FlaskConical, CheckCircle } from 'lucide-react';
import { FormulaCalculator } from '@/components/tintometry/FormulaCalculator';
import { MixtureConfirmation } from '@/components/tintometry/MixtureConfirmation';
import { CustomerColorHistory } from '@/components/tintometry/CustomerColorHistory';
import { LowStockAlerts } from '@/components/tintometry/LowStockAlerts';
import type { CalculationResult, CustomerHistoryItem } from '@/types/tintometry';

// TODO: replace with real loja from auth context when available
const LOJA_ID = 1;

type FlowStep = 'calculator' | 'confirmation' | 'done';

/**
 * Main tintometry page — full mixing flow.
 * Left column: customer history search.
 * Right column: formula calculator → confirmation → done.
 * Top: low stock alerts banner.
 */
export default function TintometryPage(): React.ReactElement {
  const [step, setStep] = useState<FlowStep>('calculator');
  const [calcResult, setCalcResult] = useState<CalculationResult | null>(null);
  const [confirmedId, setConfirmedId] = useState<number | null>(null);

  function handleCalculationComplete(result: CalculationResult) {
    setCalcResult(result);
    setStep('confirmation');
  }

  function handleConfirmed(misturaId: number) {
    setConfirmedId(misturaId);
    setStep('done');
  }

  function handleNewMixture() {
    setStep('calculator');
    setCalcResult(null);
    setConfirmedId(null);
  }

  function handleReproduce(_item: CustomerHistoryItem) {
    // Reset to calculator; user will re-select the formula
    // with the color pre-filled in the future iteration
    setStep('calculator');
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FlaskConical className="w-7 h-7 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tintometria</h1>
          <p className="text-sm text-gray-500">Calcule e produzca misturas de tinta personalizadas</p>
        </div>
      </div>

      {/* Low stock alerts */}
      <LowStockAlerts lojaId={LOJA_ID} />

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Customer history */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <CustomerColorHistory onReproduce={handleReproduce} />
          </div>
        </div>

        {/* Right: Calculator → Confirmation → Done */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            {step === 'calculator' && (
              <FormulaCalculator
                lojaId={LOJA_ID}
                onCalculationComplete={handleCalculationComplete}
              />
            )}

            {step === 'confirmation' && calcResult && (
              <MixtureConfirmation
                calculationResult={calcResult}
                onConfirmed={handleConfirmed}
                onCancel={() => setStep('calculator')}
              />
            )}

            {step === 'done' && (
              <div className="flex flex-col items-center justify-center py-12 gap-4 text-center">
                <CheckCircle className="w-16 h-16 text-green-500" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Mistura confirmada!
                </h2>
                {confirmedId && (
                  <p className="text-sm text-gray-500">
                    Mistura #{confirmedId} foi confirmada para produção.
                  </p>
                )}
                <button
                  onClick={handleNewMixture}
                  className="mt-2 px-6 py-2.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <FlaskConical className="w-4 h-4" />
                  Nova Mistura
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
