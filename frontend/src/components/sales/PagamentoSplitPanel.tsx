/**
 * T043 — PagamentoSplitPanel: multi-payment form with troco calc.
 * aria-live on troco display (ACC-7). Disables confirm when sum ≠ total.
 */
import { useState, useId } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import type { FormaPagamento } from '@/types';

interface PagamentoEntry {
  id: string;
  forma: FormaPagamento;
  valor: string; // string for controlled input
}

interface PagamentoSplitPanelProps {
  valorLiquido: number;
  onConfirm: (pagamentos: Array<{ forma: FormaPagamento; valor: number }>) => void;
  disabled?: boolean;
}

const FORMAS: Array<{ value: FormaPagamento; label: string }> = [
  { value: 'DINHEIRO', label: 'Dinheiro' },
  { value: 'PIX', label: 'PIX' },
  { value: 'CARTAO_DEBITO', label: 'Cartão Débito' },
  { value: 'CARTAO_CREDITO', label: 'Cartão Crédito' },
  { value: 'CREDIARIO', label: 'Crediário' },
  { value: 'TRANSFERENCIA', label: 'Transferência' },
];

function newEntry(): PagamentoEntry {
  return { id: crypto.randomUUID(), forma: 'DINHEIRO', valor: '' };
}

export default function PagamentoSplitPanel({
  valorLiquido,
  onConfirm,
  disabled = false,
}: PagamentoSplitPanelProps) {
  const [entries, setEntries] = useState<PagamentoEntry[]>(() => [newEntry()]);
  const headingId = useId();

  const somaValores = entries.reduce((acc, e) => {
    const v = parseFloat(e.valor);
    return acc + (isNaN(v) ? 0 : v);
  }, 0);

  const troco =
    entries.some((e) => e.forma === 'DINHEIRO')
      ? Math.max(0, somaValores - valorLiquido)
      : 0;

  const diff = Math.abs(somaValores - valorLiquido);
  const isBalanceado = diff < 0.005;

  const addEntry = () => setEntries((prev) => [...prev, newEntry()]);

  const removeEntry = (id: string) =>
    setEntries((prev) => (prev.length > 1 ? prev.filter((e) => e.id !== id) : prev));

  const updateEntry = (id: string, field: keyof PagamentoEntry, value: string) =>
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, [field]: value } : e))
    );

  const handleConfirm = () => {
    if (!isBalanceado || disabled) return;
    onConfirm(
      entries.map((e) => ({
        forma: e.forma,
        valor: parseFloat(e.valor) || 0,
      }))
    );
  };

  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-4">
      <h3 id={headingId} className="text-sm font-semibold text-slate-700">
        Formas de Pagamento
      </h3>

      <div className="space-y-2">
        {entries.map((entry, idx) => (
          <div key={entry.id} className="flex items-center gap-2">
            <label className="sr-only" htmlFor={`forma-${entry.id}`}>
              Forma de pagamento {idx + 1}
            </label>
            <select
              id={`forma-${entry.id}`}
              value={entry.forma}
              onChange={(e) => updateEntry(entry.id, 'forma', e.target.value)}
              className="form-input flex-1"
              disabled={disabled}
            >
              {FORMAS.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>

            <label className="sr-only" htmlFor={`valor-${entry.id}`}>
              Valor {idx + 1}
            </label>
            <input
              id={`valor-${entry.id}`}
              type="number"
              min="0.01"
              step="0.01"
              value={entry.valor}
              onChange={(e) => updateEntry(entry.id, 'valor', e.target.value)}
              className="form-input w-32 text-right"
              placeholder="0,00"
              disabled={disabled}
            />

            <button
              type="button"
              onClick={() => removeEntry(entry.id)}
              disabled={entries.length === 1 || disabled}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-30"
              aria-label={`Remover pagamento ${idx + 1}`}
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={addEntry}
        disabled={disabled}
        className="flex items-center gap-1.5 self-start text-sm text-blue-600 hover:text-blue-700 disabled:opacity-40"
      >
        <Plus className="h-4 w-4" aria-hidden="true" />
        Adicionar forma
      </button>

      {/* Totais */}
      <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 space-y-1.5 text-sm">
        <div className="flex justify-between">
          <span className="text-slate-600">Total a pagar</span>
          <span className="font-medium text-slate-900">
            R$ {valorLiquido.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-600">Total informado</span>
          <span
            className={`font-medium ${isBalanceado ? 'text-emerald-600' : 'text-rose-600'}`}
          >
            R$ {somaValores.toFixed(2)}
          </span>
        </div>
        {troco > 0 && (
          <div
            className="flex justify-between border-t border-slate-200 pt-1.5"
            aria-live="polite"
          >
            <span className="font-medium text-slate-700">Troco</span>
            <span className="font-semibold text-emerald-700">
              R$ {troco.toFixed(2)}
            </span>
          </div>
        )}
        {!isBalanceado && somaValores > 0 && (
          <p className="text-xs text-rose-600" aria-live="polite" role="alert">
            {somaValores < valorLiquido
              ? `Faltam R$ ${(valorLiquido - somaValores).toFixed(2)}`
              : `Excede em R$ ${(somaValores - valorLiquido).toFixed(2)}`}
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={handleConfirm}
        disabled={!isBalanceado || disabled}
        className="btn-primary w-full disabled:opacity-50"
        aria-disabled={!isBalanceado || disabled}
      >
        Confirmar pagamento
      </button>
    </section>
  );
}
