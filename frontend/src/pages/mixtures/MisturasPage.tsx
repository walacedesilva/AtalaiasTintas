import React, { useState, useMemo } from 'react';
import {
  Layers, Plus, Search, Play, CheckCheck,
  XCircle, Trash2, Eye, ChevronDown, ChevronUp,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  useMisturas, useCreateMistura, useStartMistura,
  useCompleteMistura, useCancelMistura, useDeleteMistura,
  useFormulas,
} from '@/hooks/useTintometry';
import type { MisturaTinta } from '@/types';

// ─── Status tab types ─────────────────────────────────────────────────────────
type SituacaoFilter = 'TODAS' | 'PENDENTE' | 'PRODUCAO' | 'CONCLUIDA' | 'CANCELADA';

const TAB_LABELS: Record<SituacaoFilter, string> = {
  TODAS: 'Todas',
  PENDENTE: 'Pendentes',
  PRODUCAO: 'Em Produção',
  CONCLUIDA: 'Concluídas',
  CANCELADA: 'Canceladas',
};

const TAB_BADGE: Record<SituacaoFilter, string> = {
  TODAS: 'badge-gray',
  PENDENTE: 'badge-yellow',
  PRODUCAO: 'badge-blue',
  CONCLUIDA: 'badge-green',
  CANCELADA: 'badge-red',
};

// ─── Nova Mistura Modal ───────────────────────────────────────────────────────
type NovaMisturaForm = {
  formula: number;
  volume_solicitado: string;
  cliente_nome: string;
  cliente_telefone: string;
  cliente_documento: string;
};

const EMPTY_FORM: NovaMisturaForm = {
  formula: 0, volume_solicitado: '3.60',
  cliente_nome: '', cliente_telefone: '', cliente_documento: '',
};

function NovaMisturaModal({ onClose, onSave }: { onClose: () => void; onSave: (f: NovaMisturaForm) => void }) {
  const [form, setForm] = useState<NovaMisturaForm>(EMPTY_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof NovaMisturaForm, string>>>({});
  const { data: formulasData } = useFormulas({ include_inactive: false, page_size: 200 });
  const formulas = formulasData?.results ?? [];

  function validate() {
    const e: Partial<Record<keyof NovaMisturaForm, string>> = {};
    if (!form.formula) e.formula = 'Selecione uma fórmula';
    if (!form.cliente_nome.trim()) e.cliente_nome = 'Nome do cliente obrigatório';
    const vol = parseFloat(form.volume_solicitado);
    if (isNaN(vol) || vol <= 0) e.volume_solicitado = 'Volume deve ser positivo';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handle(e: React.FormEvent) {
    e.preventDefault();
    if (validate()) onSave(form);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" onClick={onClose} role="dialog" aria-modal="true">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 p-5 border-b border-slate-100">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-100">
            <Layers className="h-5 w-5 text-amber-600" />
          </div>
          <h2 className="text-lg font-semibold text-slate-900">Nova Mistura</h2>
        </div>
        <form onSubmit={handle} className="p-5 space-y-4">
          {/* Fórmula */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Fórmula Tintométrica</label>
            <select
              className={`form-input text-sm ${errors.formula ? 'form-input-error' : ''}`}
              value={form.formula || ''}
              onChange={e => { setForm(f => ({ ...f, formula: Number(e.target.value) })); setErrors(er => ({ ...er, formula: undefined })); }}
            >
              <option value="">Selecionar fórmula…</option>
              {formulas.map(f => (
                <option key={f.id} value={f.id}>
                  {f.codigo_formula} — {f.nome_formula} ({f.volume_base}L)
                </option>
              ))}
            </select>
            {errors.formula && <p className="mt-0.5 text-xs text-red-600">{errors.formula}</p>}
          </div>

          {/* Volume */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Volume Solicitado (L)</label>
            <input
              type="number" step="0.01" min="0.01"
              className={`form-input text-sm ${errors.volume_solicitado ? 'form-input-error' : ''}`}
              value={form.volume_solicitado}
              onChange={e => { setForm(f => ({ ...f, volume_solicitado: e.target.value })); setErrors(er => ({ ...er, volume_solicitado: undefined })); }}
            />
            {errors.volume_solicitado && <p className="mt-0.5 text-xs text-red-600">{errors.volume_solicitado}</p>}
          </div>

          {/* Cliente */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Nome do Cliente</label>
            <input
              type="text"
              className={`form-input text-sm ${errors.cliente_nome ? 'form-input-error' : ''}`}
              placeholder="Ex: João Silva"
              value={form.cliente_nome}
              onChange={e => { setForm(f => ({ ...f, cliente_nome: e.target.value })); setErrors(er => ({ ...er, cliente_nome: undefined })); }}
            />
            {errors.cliente_nome && <p className="mt-0.5 text-xs text-red-600">{errors.cliente_nome}</p>}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Telefone</label>
              <input type="tel" className="form-input text-sm" placeholder="(11) 99999-0000" value={form.cliente_telefone} onChange={e => setForm(f => ({ ...f, cliente_telefone: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">CPF / CNPJ</label>
              <input type="text" className="form-input text-sm" placeholder="Opcional" value={form.cliente_documento} onChange={e => setForm(f => ({ ...f, cliente_documento: e.target.value }))} />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary">Criar Mistura</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Cancel Dialog ────────────────────────────────────────────────────────────
function CancelDialog({ mistura, onClose, onConfirm }: { mistura: MisturaTinta; onClose: () => void; onConfirm: (motivo: string) => void }) {
  const [motivo, setMotivo] = useState('');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" role="dialog" aria-modal="true">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 shrink-0">
            <XCircle className="h-5 w-5 text-red-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Cancelar mistura</h3>
            <p className="text-sm text-slate-500 mt-1">
              Cancelar <strong>{mistura.codigo_mistura}</strong> para {mistura.cliente_nome}?
            </p>
          </div>
        </div>
        <textarea
          className="form-input text-sm resize-none h-20 w-full"
          placeholder="Motivo do cancelamento (optional)…"
          value={motivo}
          onChange={e => setMotivo(e.target.value)}
        />
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={onClose}>Voltar</button>
          <button className="btn-danger" onClick={() => onConfirm(motivo)}>Confirmar Cancelamento</button>
        </div>
      </div>
    </div>
  );
}

// ─── Detail Drawer (inline expand) ───────────────────────────────────────────
function DetailRow({ mistura }: { mistura: MisturaTinta }) {
  return (
    <tr className="bg-slate-50">
      <td colSpan={9} className="px-6 py-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          {mistura.formula_details && (
            <div>
              <p className="text-xs text-slate-500 font-medium">Fórmula</p>
              <p className="text-slate-800">{mistura.formula_details.codigo_formula} — {mistura.formula_details.nome_formula}</p>
            </div>
          )}
          {mistura.cliente_telefone && (
            <div>
              <p className="text-xs text-slate-500 font-medium">Telefone</p>
              <p className="text-slate-800">{mistura.cliente_telefone}</p>
            </div>
          )}
          {mistura.volume_produzido && (
            <div>
              <p className="text-xs text-slate-500 font-medium">Vol. Produzido</p>
              <p className="text-slate-800">{mistura.volume_produzido} L</p>
            </div>
          )}
          {mistura.custo_total && (
            <div>
              <p className="text-xs text-slate-500 font-medium">Custo Total</p>
              <p className="text-slate-800">
                {parseFloat(mistura.custo_total).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </p>
            </div>
          )}
          {mistura.fator_proporcao !== undefined && (
            <div>
              <p className="text-xs text-slate-500 font-medium">Fator de Proporção</p>
              <p className="text-slate-800">{mistura.fator_proporcao.toFixed(4)}x</p>
            </div>
          )}
          {mistura.itens?.length > 0 && (
            <div className="col-span-full">
              <p className="text-xs text-slate-500 font-medium mb-1">Pigmentos</p>
              <div className="flex flex-wrap gap-2">
                {mistura.itens.map(it => (
                  <span key={it.id} className="badge badge-blue text-xs">
                    {it.pigmento_details?.codigo ?? `#${it.pigmento}`}: {parseFloat(it.quantidade_calculada).toFixed(2)} ml
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function MisturasPage(): React.ReactElement {
  const [activeTab, setActiveTab] = useState<SituacaoFilter>('TODAS');
  const [query, setQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [cancelTarget, setCancelTarget] = useState<MisturaTinta | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const { data, isLoading, isError, refetch } = useMisturas({
    status: activeTab === 'TODAS' ? undefined : activeTab,
    query: query || undefined,
    page_size: 100,
  });

  const createMistura = useCreateMistura();
  const startMistura = useStartMistura();
  const completeMistura = useCompleteMistura();
  const cancelMistura = useCancelMistura();
  const deleteMistura = useDeleteMistura();

  const sorted = useMemo(() => {
    const rows = data?.results ?? [];
    return [...rows].sort((a, b) => {
      const av = a.created_at ?? '';
      const bv = b.created_at ?? '';
      return sortDir === 'desc' ? bv.localeCompare(av) : av.localeCompare(bv);
    });
  }, [data, sortDir]);

  async function handleCreate(form: NovaMisturaForm) {
    try {
      await createMistura.mutateAsync({
        formula: form.formula,
        volume_solicitado: form.volume_solicitado,
        cliente_nome: form.cliente_nome,
        cliente_telefone: form.cliente_telefone || null,
        cliente_documento: form.cliente_documento || null,
      } as unknown as Omit<MisturaTinta, 'id' | 'created_at' | 'updated_at'>);
      toast.success('Mistura criada!');
      setShowModal(false);
    } catch {
      toast.error('Erro ao criar mistura');
    }
  }

  async function handleStart(id: number) {
    try {
      await startMistura.mutateAsync(id);
      toast.success('Produção iniciada!');
    } catch {
      toast.error('Erro ao iniciar produção');
    }
  }

  async function handleComplete(id: number) {
    try {
      await completeMistura.mutateAsync({ id, observacoes: '' });
      toast.success('Mistura concluída!');
    } catch {
      toast.error('Erro ao concluir mistura');
    }
  }

  async function handleCancel(motivo: string) {
    if (!cancelTarget) return;
    try {
      await cancelMistura.mutateAsync({ id: cancelTarget.id, motivo });
      toast.success('Mistura cancelada.');
      setCancelTarget(null);
    } catch {
      toast.error('Erro ao cancelar mistura');
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteMistura.mutateAsync(id);
      toast.success('Mistura excluída.');
    } catch {
      toast.error('Erro ao excluir mistura');
    }
  }

  function situacaoBadge(s: MisturaTinta['situacao']) {
    const map: Record<MisturaTinta['situacao'], string> = {
      PENDENTE: 'badge badge-yellow',
      PRODUCAO: 'badge badge-blue',
      CONCLUIDA: 'badge badge-green',
      CANCELADA: 'badge badge-red',
    };
    const label: Record<MisturaTinta['situacao'], string> = {
      PENDENTE: 'Pendente', PRODUCAO: 'Em Produção', CONCLUIDA: 'Concluída', CANCELADA: 'Cancelada',
    };
    return <span className={map[s]}>{label[s]}</span>;
  }

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-7xl animate-fade-in">
        <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
        <div className="card space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-slate-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6 max-w-7xl">
        <div className="card flex flex-col items-center py-16 text-center">
          <p className="text-slate-500 mb-3">Erro ao carregar misturas.</p>
          <button className="btn-secondary" onClick={() => refetch()}>Tentar novamente</button>
        </div>
      </div>
    );
  }

  const total = data?.count ?? 0;

  return (
    <div className="space-y-6 max-w-7xl animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Misturas</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {total} {total === 1 ? 'mistura registrada' : 'misturas registradas'}
          </p>
        </div>
        <button className="btn-primary self-start sm:self-auto" onClick={() => setShowModal(true)}>
          <Plus className="h-4 w-4" />
          Nova Mistura
        </button>
      </div>

      {/* Status Tabs */}
      <div className="flex flex-wrap gap-2">
        {(Object.keys(TAB_LABELS) as SituacaoFilter[]).map(tab => (
          <button
            key={tab}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              activeTab === tab
                ? 'bg-amber-500 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {TAB_LABELS[tab]}
          </button>
        ))}
      </div>

      {/* Search + Sort */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            placeholder="Buscar por código ou cliente…"
            className="form-input pl-9"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
        <button
          className="btn-secondary shrink-0"
          onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}
          title={sortDir === 'desc' ? 'Mais recentes primeiro' : 'Mais antigas primeiro'}
        >
          {sortDir === 'desc' ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          Data
        </button>
      </div>

      {/* Table */}
      {sorted.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 mb-4">
            <Layers className="h-8 w-8 text-amber-400" />
          </div>
          {query
            ? <p className="text-slate-500">Nenhuma mistura encontrada para "{query}".</p>
            : <>
                <p className="font-medium text-slate-700 mb-1">Nenhuma mistura registrada</p>
                <p className="text-sm text-slate-500 mb-4">Crie uma nova mistura selecionando uma fórmula do catálogo.</p>
                <button className="btn-primary" onClick={() => setShowModal(true)}>
                  <Plus className="h-4 w-4" />Nova Mistura
                </button>
              </>
          }
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-100 bg-slate-50">
                <tr>
                  <th className="w-8 px-3 py-3" />
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Código</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Cliente</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Fórmula</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500">Volume (L)</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500">Situação</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Data</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-500">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sorted.map(m => (
                  <React.Fragment key={m.id}>
                    <tr className="hover:bg-slate-50 transition-colors">
                      {/* Expand toggle */}
                      <td className="px-3 py-3">
                        <button
                          className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-slate-400"
                          onClick={() => setExpandedId(id => id === m.id ? null : m.id)}
                          title={expandedId === m.id ? 'Recolher' : 'Ver detalhes'}
                        >
                          {expandedId === m.id ? <ChevronUp className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-700">{m.codigo_mistura}</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{m.cliente_nome}</td>
                      <td className="px-4 py-3 text-slate-600 text-xs">
                        {m.formula_details
                          ? `${m.formula_details.codigo_formula} — ${m.formula_details.nome_formula}`
                          : `#${m.formula}`}
                      </td>
                      <td className="px-4 py-3 text-center text-slate-600">
                        {parseFloat(m.volume_solicitado).toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-center">{situacaoBadge(m.situacao)}</td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {m.created_at ? new Date(m.created_at).toLocaleDateString('pt-BR') : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          {m.situacao === 'PENDENTE' && (
                            <button
                              className="btn-ghost h-8 px-2 flex items-center gap-1 text-xs text-blue-600 hover:bg-blue-50"
                              title="Iniciar produção"
                              onClick={() => handleStart(m.id)}
                            >
                              <Play className="h-3.5 w-3.5" /> Iniciar
                            </button>
                          )}
                          {m.situacao === 'PRODUCAO' && (
                            <button
                              className="btn-ghost h-8 px-2 flex items-center gap-1 text-xs text-emerald-600 hover:bg-emerald-50"
                              title="Concluir mistura"
                              onClick={() => handleComplete(m.id)}
                            >
                              <CheckCheck className="h-3.5 w-3.5" /> Concluir
                            </button>
                          )}
                          {(m.situacao === 'PENDENTE' || m.situacao === 'PRODUCAO') && (
                            <button
                              className="btn-ghost h-8 px-2 flex items-center gap-1 text-xs text-red-500 hover:bg-red-50"
                              title="Cancelar"
                              onClick={() => setCancelTarget(m)}
                            >
                              <XCircle className="h-3.5 w-3.5" /> Cancelar
                            </button>
                          )}
                          {(m.situacao === 'CONCLUIDA' || m.situacao === 'CANCELADA') && (
                            <button
                              className="btn-ghost h-8 w-8 p-0 flex items-center justify-center text-red-400 hover:text-red-600 hover:bg-red-50"
                              title="Excluir"
                              onClick={() => handleDelete(m.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {expandedId === m.id && <DetailRow mistura={m} />}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      {showModal && <NovaMisturaModal onClose={() => setShowModal(false)} onSave={handleCreate} />}
      {cancelTarget && <CancelDialog mistura={cancelTarget} onClose={() => setCancelTarget(null)} onConfirm={handleCancel} />}
    </div>
  );
}
