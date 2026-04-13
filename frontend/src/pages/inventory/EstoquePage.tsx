import React from 'react';
import { Package, Plus, Search, ArrowUpDown } from 'lucide-react';

export default function EstoquePage(): React.ReactElement {
  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Controle de Estoque</h1>
          <p className="text-sm text-slate-500 mt-0.5">Inventário de pigmentos e movimentações</p>
        </div>
        <button className="btn-primary self-start sm:self-auto" disabled>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Entrada de Estoque
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {['Total de Itens', 'Estoque Baixo', 'Sem Estoque', 'Valor Total'].map((label) => (
          <div key={label} className="card p-4">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="text-xl font-bold text-slate-300 mt-1">—</p>
          </div>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input type="search" placeholder="Buscar pigmentos…" className="form-input pl-9" disabled />
        </div>
        <button className="btn-secondary" disabled>
          <ArrowUpDown className="h-4 w-4" aria-hidden="true" />
          Movimentações
        </button>
      </div>

      <div className="card flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-50 mb-4">
          <Package className="h-8 w-8 text-orange-600" aria-hidden="true" />
        </div>
        <h2 className="text-base font-semibold text-slate-900 mb-1">Módulo em desenvolvimento</h2>
        <p className="text-sm text-slate-500 max-w-xs">
          O controle de estoque com alertas automáticos de reposição estará disponível em breve.
        </p>
        <span className="mt-4 badge badge-blue">Em breve</span>
      </div>
    </div>
  );
}