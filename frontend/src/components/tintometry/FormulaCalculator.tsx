import React, { useState } from 'react';
import { FlaskConical, Search, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { tintometryAPI } from '@/api';
import type { LequeCorDefinida, FormulaTintometrica } from '@/types';
import type { CalculationResult, CreateCalculationPayload } from '@/types/tintometry';
import { StockAvailabilityBadge } from './StockAvailabilityBadge';

interface FormulaCalculatorProps {
  lojaId: number;
  onCalculationComplete?: (result: CalculationResult) => void;
}

interface CustomerData {
  nome: string;
  telefone: string;
}

/**
 * Two-step formula calculator:
 * Step 1: search/select color → select formula → set volume → customer data
 * Step 2: show calculation result summary, ready for confirmation
 */
export function FormulaCalculator({ lojaId, onCalculationComplete }: FormulaCalculatorProps): React.ReactElement {
  const [step, setStep] = useState<1 | 2>(1);
  const [colorSearch, setColorSearch] = useState('');
  const [colorResults, setColorResults] = useState<LequeCorDefinida[]>([]);
  const [selectedColor, setSelectedColor] = useState<LequeCorDefinida | null>(null);
  const [formulas, setFormulas] = useState<FormulaTintometrica[]>([]);
  const [selectedFormula, setSelectedFormula] = useState<FormulaTintometrica | null>(null);
  const [volume, setVolume] = useState('1.0');
  const [customer, setCustomer] = useState<CustomerData>({ nome: '', telefone: '' });
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState<CalculationResult | null>(null);

  async function handleColorSearch() {
    if (!colorSearch.trim()) return;
    try {
      const results = await tintometryAPI.cores.search(colorSearch);
      setColorResults(results);
    } catch {
      toast.error('Erro ao buscar cores');
    }
  }

  async function handleSelectColor(cor: LequeCorDefinida) {
    setSelectedColor(cor);
    setSelectedFormula(null);
    setColorResults([]);
    setColorSearch('');
    try {
      const res = await tintometryAPI.formulas.list({ page_size: 50 });
      const formulasForColor = res.results.filter(
        (f) => f.cor_definida === cor.id && f.ativa
      );
      setFormulas(formulasForColor);
    } catch {
      toast.error('Erro ao carregar fórmulas');
    }
  }

  async function handleCalculate() {
    if (!selectedFormula) return;
    if (!customer.nome.trim()) {
      toast.error('Informe o nome do cliente');
      return;
    }
    const vol = parseFloat(volume);
    if (isNaN(vol) || vol < 0.1) {
      toast.error('Volume mínimo de 0,1 litros');
      return;
    }

    setCalculating(true);
    try {
      const payload: CreateCalculationPayload = {
        formula_id: selectedFormula.id,
        volume_solicitado: volume,
        loja_id: lojaId,
        cliente_nome: customer.nome,
        ...(customer.telefone ? { cliente_telefone: customer.telefone } : {}),
      };
      const calcResult = await tintometryAPI.misturas.createCalculation(payload);
      if (calcResult.success) {
        setResult(calcResult);
        setStep(2);
        onCalculationComplete?.(calcResult);
      } else {
        toast.error(calcResult.error || 'Erro ao calcular mistura');
      }
    } catch {
      toast.error('Erro ao calcular mistura');
    } finally {
      setCalculating(false);
    }
  }

  function handleReset() {
    setStep(1);
    setSelectedColor(null);
    setSelectedFormula(null);
    setFormulas([]);
    setColorSearch('');
    setColorResults([]);
    setVolume('1.0');
    setCustomer({ nome: '', telefone: '' });
    setResult(null);
  }

  if (step === 2 && result) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-blue-600" />
            Cálculo Realizado
          </h3>
          <button onClick={handleReset} className="text-sm text-blue-600 hover:underline">
            Nova Mistura
          </button>
        </div>

        {result.mistura && (
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <p className="text-sm font-medium text-green-800">
              Mistura criada: <span className="font-mono">{result.mistura.codigo}</span>
            </p>
          </div>
        )}

        {result.calculation && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-700">Pigmentos calculados</h4>
            <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
              {result.calculation.pigmentos.map((item, idx) => (
                <li key={idx} className="flex items-center justify-between px-4 py-3 text-sm">
                  <div className="flex items-center gap-2">
                    {item.pigmento.cor_hex && (
                      <span
                        className="w-4 h-4 rounded-full border border-gray-300"
                        style={{ backgroundColor: item.pigmento.cor_hex }}
                      />
                    )}
                    <span className="font-medium">{item.pigmento.nome}</span>
                    <span className="text-gray-500 text-xs">{item.pigmento.codigo}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <StockAvailabilityBadge
                      saldo_ml={item.stock_disponivel ?? item.quantidades.calculada_final * 2}
                      saldo_minimo={item.quantidades.calculada_final}
                      showText={false}
                    />
                    <span className="font-mono text-right">
                      {item.quantidades.calculada_final.toFixed(1)} ml
                    </span>
                  </div>
                </li>
              ))}
            </ul>

            <div className="flex justify-between text-sm font-semibold text-gray-700 pt-1">
              <span>Custo total estimado</span>
              <span>R$ {result.calculation.custos.total.toFixed(2)}</span>
            </div>

            {!result.calculation.validacao.stock_ok && (
              <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
                <p className="font-medium mb-1">Avisos de estoque:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {result.calculation.validacao.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <FlaskConical className="w-5 h-5 text-blue-600" />
        Calcular Mistura de Tinta
      </h3>

      {/* Color search */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Cor desejada
        </label>
        {selectedColor ? (
          <div className="flex items-center gap-2 p-2 rounded-md border border-blue-300 bg-blue-50">
            {selectedColor.cor_hex && (
              <span
                className="w-5 h-5 rounded-full border border-gray-300 flex-shrink-0"
                style={{ backgroundColor: selectedColor.cor_hex }}
              />
            )}
            <span className="text-sm font-medium text-blue-900">
              {selectedColor.nome_cor}
            </span>
            <span className="text-xs text-blue-600">{selectedColor.codigo_cor}</span>
            <button
              onClick={() => { setSelectedColor(null); setFormulas([]); setSelectedFormula(null); }}
              className="ml-auto text-xs text-blue-500 hover:text-blue-700"
            >
              Alterar
            </button>
          </div>
        ) : (
          <div className="flex gap-2">
            <input
              type="text"
              value={colorSearch}
              onChange={(e) => setColorSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleColorSearch()}
              placeholder="Buscar por nome ou código..."
              className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleColorSearch}
              className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Search className="w-4 h-4" />
            </button>
          </div>
        )}

        {colorResults.length > 0 && !selectedColor && (
          <ul className="mt-1 rounded-md border border-gray-200 shadow-sm bg-white max-h-48 overflow-y-auto">
            {colorResults.map((cor) => (
              <li key={cor.id}>
                <button
                  onClick={() => handleSelectColor(cor)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 text-left"
                >
                  {cor.cor_hex && (
                    <span
                      className="w-4 h-4 rounded-full border border-gray-300 flex-shrink-0"
                      style={{ backgroundColor: cor.cor_hex }}
                    />
                  )}
                  <span className="font-medium">{cor.nome_cor}</span>
                  <span className="ml-auto text-gray-400 text-xs">{cor.codigo_cor}</span>
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Formula selection */}
      {selectedColor && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Fórmula
          </label>
          {formulas.length === 0 ? (
            <p className="text-sm text-gray-500 italic">Nenhuma fórmula ativa para esta cor.</p>
          ) : (
            <select
              value={selectedFormula?.id ?? ''}
              onChange={(e) => {
                const f = formulas.find((f) => f.id === Number(e.target.value));
                setSelectedFormula(f ?? null);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Selecione uma fórmula...</option>
              {formulas.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.nome_formula} — base {f.volume_base}L
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {/* Volume */}
      {selectedFormula && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Volume (litros)
          </label>
          <input
            type="number"
            min="0.1"
            step="0.1"
            value={volume}
            onChange={(e) => setVolume(e.target.value)}
            className="w-32 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Customer info */}
      {selectedFormula && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome do cliente <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={customer.nome}
              onChange={(e) => setCustomer({ ...customer, nome: e.target.value })}
              placeholder="Nome completo"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telefone
            </label>
            <input
              type="tel"
              value={customer.telefone}
              onChange={(e) => setCustomer({ ...customer, telefone: e.target.value })}
              placeholder="(00) 00000-0000"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {/* Action */}
      {selectedFormula && (
        <button
          onClick={handleCalculate}
          disabled={calculating || !customer.nome.trim()}
          className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {calculating ? (
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          ) : (
            <FlaskConical className="w-4 h-4" />
          )}
          {calculating ? 'Calculando...' : 'Calcular Mistura'}
        </button>
      )}
    </div>
  );
}

export default FormulaCalculator;
