import React from 'react';
import { Beaker, Plus, Search, Filter } from 'lucide-react';

export default function PigmentosPage(): React.ReactElement {
  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Pigmentos</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gerenciamento de pigmentos para misturas de tinta</p>
        </div>
        <button className="btn-primary self-start sm:self-auto" disabled>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Novo Pigmento
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input type="search" placeholder="Buscar pigmentos…" className="form-input pl-9" disabled />
        </div>
        <button className="btn-secondary" disabled>
          <Filter className="h-4 w-4" aria-hidden="true" />
          Filtros
        </button>
      </div>

      {/* Empty state */}
      <div className="card flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-50 mb-4">
          <Beaker className="h-8 w-8 text-teal-600" aria-hidden="true" />
        </div>
        <h2 className="text-base font-semibold text-slate-900 mb-1">Módulo em desenvolvimento</h2>
        <p className="text-sm text-slate-500 max-w-xs">
          Em breve você poderá cadastrar e gerenciar todos os pigmentos do sistema.
        </p>
        <span className="mt-4 badge badge-blue">Em breve</span>
      </div>
    </div>
  );
}