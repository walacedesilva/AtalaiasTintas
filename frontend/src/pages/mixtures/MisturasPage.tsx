import React from 'react';
import { Layers, Plus, Search, Clock } from 'lucide-react';

export default function MisturasPage(): React.ReactElement {
  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Misturas</h1>
          <p className="text-sm text-slate-500 mt-0.5">Controle de misturas de tinta em andamento e concluídas</p>
        </div>
        <button className="btn-primary self-start sm:self-auto" disabled>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Nova Mistura
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {['Todas', 'Em andamento', 'Concluídas', 'Canceladas'].map((tab) => (
          <button key={tab} disabled className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            tab === 'Todas'
              ? 'bg-teal-600 text-white'
              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}>{tab}</button>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input type="search" placeholder="Buscar misturas…" className="form-input pl-9" disabled />
        </div>
        <button className="btn-secondary" disabled>
          <Clock className="h-4 w-4" aria-hidden="true" />
          Histórico
        </button>
      </div>

      <div className="card flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 mb-4">
          <Layers className="h-8 w-8 text-amber-600" aria-hidden="true" />
        </div>
        <h2 className="text-base font-semibold text-slate-900 mb-1">Módulo em desenvolvimento</h2>
        <p className="text-sm text-slate-500 max-w-xs">
          O controle completo de misturas com rastreamento de status estará disponível em breve.
        </p>
        <span className="mt-4 badge badge-blue">Em breve</span>
      </div>
    </div>
  );
}