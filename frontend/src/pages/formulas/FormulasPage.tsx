import React, { useState, useMemo } from 'react';
import {
  FlaskConical, Plus, Search, Pencil, Trash2,
  ChevronUp, ChevronDown, CheckCircle, Clock, Copy,
} from 'lucide-react';
import toast from 'react-hot-toast';
import {
  useFormulas, useCreateFormula, useUpdateFormula, useDeleteFormula,
  useCores, usePigmentos,
} from '@/hooks/useTintometry';
import type { FormulaTintometrica, ItemFormula } from '@/types';

// ─── Color swatch helper ──────────────────────────────────────────────────────
function CorPreview({ cor_hex }: { cor_hex?: string }) {
  if (!cor_hex) return null;
  return (
    <span
      className="h-5 w-5 rounded-full inline-block border border-slate-200 shrink-0"
      style={{ backgroundColor: cor_hex }}
      aria-hidden="true"
    />
  );
}

// ─── Item Formula row (inside modal) ─────────────────────────────────────────
type ItemFormRow = { pigmento_id: number; quantidade: string; sequencia: number; observacoes: string };

function ItemRow({
  item, pigmentOptions, onChange, onRemove,
}: {
  item: ItemFormRow;
  pigmentOptions: { id: number; codigo: string; nome: string }[];
  onChange: (v: Partial<ItemFormRow>) => void;
  onRemove: () => void;
}) {
  return (
    <div className="grid grid-cols-[2fr_1fr_1fr_auto] gap-2 items-center">
      <select
        className="form-input text-sm"
        value={item.pigmento_id || ''}
        onChange={e => onChange({ pigmento_id: Number(e.target.value) })}
      >
        <option value="">Selecionar pigmento…</option>
        {pigmentOptions.map(p => (
          <option key={p.id} value={p.id}>{p.codigo} — {p.nome}</option>
        ))}
      </select>
      <input
        type="number"
        min="0.0001"
        step="0.1"
        placeholder="ml"
        className="form-input text-sm"
        value={item.quantidade}
        onChange={e => onChange({ quantidade: e.target.value })}
      />
      <input
        type="number"
        min="1"
        placeholder="Seq."
        className="form-input text-sm"
        value={item.sequencia}
        onChange={e => onChange({ sequencia: Number(e.target.value) })}
      />
      <button
        type="button"
        className="btn-ghost h-8 w-8 p-0 flex items-center justify-center text-red-500 hover:bg-red-50"
        onClick={onRemove}
        title="Remover pigmento"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
}

// ─── Modal create / edit ─────────────────────────────────────────────────────
type FormulaForm = {
  cor_definida: number;
  base_produto: number;
  codigo_formula: string;
  nome_formula: string;
  versao: string;
  volume_base: string;
  instrucoes: string;
  tempo_mistura_minutos: number;
  ativa: boolean;
};

const EMPTY_FORMULA: FormulaForm = {
  cor_definida: 0, base_produto: 0,
  codigo_formula: '', nome_formula: '',
  versao: '1.0', volume_base: '1.00',
  instrucoes: '', tempo_mistura_minutos: 5,
  ativa: true,
};

function FormulaModal({
  formula, onClose, onSave,
}: {
  formula: FormulaTintometrica | null;
  onClose: () => void;
  onSave: (form: FormulaForm, itens: ItemFormRow[]) => void;
}) {
  const [form, setForm] = useState<FormulaForm>(
    formula
      ? {
          cor_definida: formula.cor_definida,
          base_produto: formula.base_produto,
          codigo_formula: formula.codigo_formula,
          nome_formula: formula.nome_formula,
          versao: formula.versao,
          volume_base: formula.volume_base,
          instrucoes: formula.instrucoes ?? '',
          tempo_mistura_minutos: formula.tempo_mistura_minutos,
          ativa: formula.ativa,
        }
      : EMPTY_FORMULA
  );

  const [itens, setItens] = useState<ItemFormRow[]>(
    formula?.itens.map((it: ItemFormula, i: number) => ({
      pigmento_id: it.pigmento,
      quantidade: it.quantidade,
      sequencia: it.sequencia ?? i + 1,
      observacoes: it.observacoes ?? '',
    })) ?? []
  );

  const [errors, setErrors] = useState<Partial<Record<string, string>>>({});

  const { data: coresData } = useCores({ page_size: 200 });
  const { data: pigmentosData } = usePigmentos({ page_size: 200 });

  const corOptions = coresData?.results ?? [];
  const pigmentOptions = (pigmentosData?.results ?? []).map(p => ({ id: p.id, codigo: p.codigo, nome: p.nome }));
  const selectedCor = corOptions.find(c => c.id === form.cor_definida);

  function validate(): boolean {
    const e: Record<string, string> = {};
    if (!form.codigo_formula.trim()) e.codigo_formula = 'Código obrigatório';
    if (!form.nome_formula.trim()) e.nome_formula = 'Nome obrigatório';
    if (!form.cor_definida) e.cor_definida = 'Selecione uma cor';
    if (!form.base_produto) e.base_produto = 'Base do produto obrigatória';
    const vol = parseFloat(form.volume_base);
    if (isNaN(vol) || vol <= 0) e.volume_base = 'Volume deve ser positivo';
    if (itens.some(it => !it.pigmento_id || !it.quantidade)) e.itens = 'Preencha todos os pigmentos';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (validate()) onSave(form, itens);
  }

  function addItem() {
    setItens(prev => [...prev, { pigmento_id: 0, quantidade: '', sequencia: prev.length + 1, observacoes: '' }]);
  }

  function updateItem(i: number, v: Partial<ItemFormRow>) {
    setItens(prev => prev.map((it, idx) => idx === i ? { ...it, ...v } : it));
  }

  function removeItem(i: number) {
    setItens(prev => prev.filter((_, idx) => idx !== i));
  }

  function F(key: keyof FormulaForm, label: string, extra?: React.InputHTMLAttributes<HTMLInputElement>) {
    const value = String(form[key]);
    return (
      <div>
        <label className="block text-xs font-medium text-slate-700 mb-1">{label}</label>
        <input
          {...extra}
          className={`form-input text-sm ${errors[key] ? 'form-input-error' : ''}`}
          value={value}
          onChange={e => {
            const v = extra?.type === 'number' ? Number(e.target.value) : e.target.value;
            setForm(f => ({ ...f, [key]: v }));
            setErrors(er => ({ ...er, [key]: undefined }));
          }}
        />
        {errors[key] && <p className="mt-0.5 text-xs text-red-600">{errors[key]}</p>}
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" onClick={onClose} role="dialog" aria-modal="true">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[92vh] overflow-y-auto custom-scrollbar" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 p-5 border-b border-slate-100">
          <FlaskConical className="h-6 w-6 text-emerald-500" />
          <h2 className="text-lg font-semibold text-slate-900">{formula ? 'Editar Fórmula' : 'Nova Fórmula'}</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Identification */}
          <div className="grid grid-cols-2 gap-3">
            {F('codigo_formula', 'Código da Fórmula', { placeholder: 'Ex: FORM-AZ-001' })}
            {F('nome_formula', 'Nome', { placeholder: 'Ex: Azul Royal 3.6L' })}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {F('versao', 'Versão', { placeholder: '1.0' })}
            {F('volume_base', 'Volume Base (L)', { type: 'number', step: '0.01', min: '0.01' })}
          </div>

          {/* Cor */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Cor do Catálogo</label>
            <div className="flex items-center gap-2">
              <CorPreview cor_hex={selectedCor?.cor_hex} />
              <select
                className={`form-input flex-1 text-sm ${errors.cor_definida ? 'form-input-error' : ''}`}
                value={form.cor_definida || ''}
                onChange={e => { setForm(f => ({ ...f, cor_definida: Number(e.target.value) })); setErrors(er => ({ ...er, cor_definida: undefined })); }}
              >
                <option value="">Selecionar cor…</option>
                {corOptions.map(c => <option key={c.id} value={c.id}>{c.codigo_cor} — {c.nome_cor}</option>)}
              </select>
            </div>
            {errors.cor_definida && <p className="mt-0.5 text-xs text-red-600">{errors.cor_definida}</p>}
          </div>

          {/* Base produto (FK int) */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">ID do Produto Base</label>
            <input
              type="number"
              min="1"
              className={`form-input text-sm ${errors.base_produto ? 'form-input-error' : ''}`}
              placeholder="ID do ProdutoVariacao"
              value={form.base_produto || ''}
              onChange={e => { setForm(f => ({ ...f, base_produto: Number(e.target.value) })); setErrors(er => ({ ...er, base_produto: undefined })); }}
            />
            {errors.base_produto && <p className="mt-0.5 text-xs text-red-600">{errors.base_produto}</p>}
          </div>

          {/* Instrucoes */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Instruções de preparo</label>
            <textarea
              className="form-input text-sm h-20 resize-none"
              value={form.instrucoes}
              onChange={e => setForm(f => ({ ...f, instrucoes: e.target.value }))}
              placeholder="Passos especiais de mistura…"
            />
          </div>
          {F('tempo_mistura_minutos', 'Tempo de Mistura (min)', { type: 'number', min: '1' })}

          {/* Itens / Pigmentos */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-slate-700">Pigmentos da Fórmula</label>
              <button type="button" className="btn-secondary text-xs h-7 px-2" onClick={addItem}>
                <Plus className="h-3 w-3" /> Adicionar pigmento
              </button>
            </div>
            {errors.itens && <p className="mb-1 text-xs text-red-600">{errors.itens}</p>}
            {itens.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-4 border border-dashed border-slate-200 rounded-lg">
                Nenhum pigmento adicionado ainda.
              </p>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-[2fr_1fr_1fr_auto] gap-2 text-xs text-slate-500 px-0.5">
                  <span>Pigmento</span><span>Qtde (ml)</span><span>Seq.</span><span />
                </div>
                {itens.map((it, i) => (
                  <ItemRow
                    key={i}
                    item={it}
                    pigmentOptions={pigmentOptions}
                    onChange={v => updateItem(i, v)}
                    onRemove={() => removeItem(i)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Ativa toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.ativa}
              onChange={e => setForm(f => ({ ...f, ativa: e.target.checked }))}
              className="h-4 w-4 rounded"
            />
            <span className="text-sm text-slate-700">Fórmula ativa</span>
          </label>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary">
              {formula ? 'Salvar Alterações' : 'Criar Fórmula'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Delete Dialog ────────────────────────────────────────────────────────────
function DeleteDialog({ formula, onClose, onConfirm }: { formula: FormulaTintometrica; onClose: () => void; onConfirm: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" role="dialog" aria-modal="true">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 shrink-0">
            <Trash2 className="h-5 w-5 text-red-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Excluir fórmula</h3>
            <p className="text-sm text-slate-500 mt-1">
              Tem certeza que deseja excluir <strong>{formula.nome_formula}</strong>?
              Esta ação não pode ser desfeita.
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={onClose}>Cancelar</button>
          <button className="btn-danger" onClick={onConfirm}>Excluir</button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
type SortField = 'codigo_formula' | 'nome_formula' | 'versao' | 'volume_base';

export default function FormulasPage(): React.ReactElement {
  const [query, setQuery] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [sortField, setSortField] = useState<SortField>('nome_formula');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [modalFormula, setModalFormula] = useState<FormulaTintometrica | null | 'new'>(null);
  const [deleteFormula, setDeleteFormula] = useState<FormulaTintometrica | null>(null);

  const { data, isLoading, isError, refetch } = useFormulas({
    query: query || undefined,
    include_inactive: showInactive,
    page_size: 100,
  });

  const createFormula = useCreateFormula();
  const updateFormula = useUpdateFormula();
  const deleteMutation = useDeleteFormula();

  const sorted = useMemo(() => {
    const rows = data?.results ?? [];
    return [...rows].sort((a, b) => {
      const av = String(a[sortField] ?? '');
      const bv = String(b[sortField] ?? '');
      const cmp = av.localeCompare(bv);
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [data, sortField, sortDir]);

  function toggleSort(field: SortField) {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('asc'); }
  }

  function SortIcon({ field }: { field: SortField }) {
    if (sortField !== field) return <ChevronUp className="h-3 w-3 text-slate-300" />;
    return sortDir === 'asc' ? <ChevronUp className="h-3 w-3 text-emerald-500" /> : <ChevronDown className="h-3 w-3 text-emerald-500" />;
  }

  async function handleSave(form: FormulaForm, itens: ItemFormRow[]) {
    const payload = {
      ...form,
      itens: itens.map(it => ({
        pigmento: it.pigmento_id,
        quantidade: it.quantidade,
        sequencia: it.sequencia,
        observacoes: it.observacoes || null,
      })),
      aprovada: false,
      testada: false,
      total_pigmentos: itens.length,
      quantidade_total_pigmentos: itens.reduce((s, it) => s + parseFloat(it.quantidade || '0'), 0),
    };

    try {
      if (modalFormula === 'new') {
        await createFormula.mutateAsync(payload as unknown as Omit<FormulaTintometrica, 'id' | 'created_at' | 'updated_at'>);
        toast.success('Fórmula criada!');
      } else if (modalFormula) {
        await updateFormula.mutateAsync({ id: modalFormula.id, data: payload });
        toast.success('Fórmula atualizada!');
      }
      setModalFormula(null);
    } catch (err: unknown) {
      const e = err as { response?: { data?: Record<string, string[]> } };
      if (e?.response?.data) {
        const msgs = Object.values(e.response.data).flat().join(' ');
        toast.error(msgs);
      } else {
        toast.error('Erro ao salvar fórmula');
      }
    }
  }

  async function handleDelete() {
    if (!deleteFormula) return;
    try {
      await deleteMutation.mutateAsync(deleteFormula.id);
      toast.success('Fórmula excluída!');
      setDeleteFormula(null);
    } catch {
      toast.error('Erro ao excluir fórmula');
    }
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
          <p className="text-slate-500 mb-3">Erro ao carregar fórmulas.</p>
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
          <h1 className="text-2xl font-bold text-slate-900">Fórmulas Tintométricas</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {total} {total === 1 ? 'fórmula cadastrada' : 'fórmulas cadastradas'}
          </p>
        </div>
        <button className="btn-primary self-start sm:self-auto" onClick={() => setModalFormula('new')}>
          <Plus className="h-4 w-4" />
          Nova Fórmula
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            placeholder="Buscar por código ou nome…"
            className="form-input pl-9"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
        <button
          className={`btn-secondary shrink-0 ${showInactive ? 'ring-2 ring-emerald-400' : ''}`}
          onClick={() => setShowInactive(v => !v)}
        >
          {showInactive ? 'Mostrando todas' : 'Apenas ativas'}
        </button>
      </div>

      {/* Table */}
      {sorted.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50 mb-4">
            <FlaskConical className="h-8 w-8 text-emerald-400" />
          </div>
          {query
            ? <p className="text-slate-500">Nenhuma fórmula encontrada para "{query}".</p>
            : <>
                <p className="font-medium text-slate-700 mb-1">Nenhuma fórmula cadastrada ainda</p>
                <p className="text-sm text-slate-500 mb-4">Crie fórmulas vinculadas às cores do catálogo para usar nas misturas.</p>
                <button className="btn-primary" onClick={() => setModalFormula('new')}>
                  <Plus className="h-4 w-4" />Nova Fórmula
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
                  <th className="px-4 py-3 text-left font-medium text-slate-500 cursor-pointer select-none" onClick={() => toggleSort('codigo_formula')}>
                    <span className="inline-flex items-center gap-1">Código <SortIcon field="codigo_formula" /></span>
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500 cursor-pointer select-none" onClick={() => toggleSort('nome_formula')}>
                    <span className="inline-flex items-center gap-1">Nome <SortIcon field="nome_formula" /></span>
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Cor</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500 cursor-pointer select-none" onClick={() => toggleSort('versao')}>
                    <span className="inline-flex items-center justify-center gap-1">Versão <SortIcon field="versao" /></span>
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500 cursor-pointer select-none" onClick={() => toggleSort('volume_base')}>
                    <span className="inline-flex items-center justify-center gap-1">Vol. Base (L) <SortIcon field="volume_base" /></span>
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500">Pigmentos</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500">QA</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500">Status</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-500">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sorted.map(formula => (
                  <tr key={formula.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">{formula.codigo_formula}</td>
                    <td className="px-4 py-3 font-medium text-slate-900">{formula.nome_formula}</td>
                    <td className="px-4 py-3">
                      {formula.cor_definida_details ? (
                        <div className="flex items-center gap-2">
                          <span
                            className="h-4 w-4 rounded-full border border-slate-200 shrink-0"
                            style={{ backgroundColor: formula.cor_definida_details.cor_hex }}
                          />
                          <span className="text-slate-600 text-xs">{formula.cor_definida_details.nome_cor}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center text-slate-600">{formula.versao}</td>
                    <td className="px-4 py-3 text-center text-slate-600">{parseFloat(formula.volume_base).toFixed(2)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="badge badge-blue">{formula.total_pigmentos} pig.</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <span title={formula.testada ? 'Testada' : 'Não testada'}>
                          {formula.testada
                            ? <CheckCircle className="h-4 w-4 text-emerald-500" />
                            : <Clock className="h-4 w-4 text-slate-300" />}
                        </span>
                        <span title={formula.aprovada ? 'Aprovada' : 'Não aprovada'}>
                          {formula.aprovada
                            ? <CheckCircle className="h-4 w-4 text-violet-500" />
                            : <Clock className="h-4 w-4 text-slate-300" />}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`badge ${formula.ativa ? 'badge-green' : 'badge-gray'}`}>
                        {formula.ativa ? 'Ativa' : 'Inativa'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="btn-ghost h-8 w-8 p-0 flex items-center justify-center"
                          title="Duplicar"
                          onClick={() => toast('Duplicar — em breve!')}
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                        <button
                          className="btn-ghost h-8 w-8 p-0 flex items-center justify-center"
                          title="Editar"
                          onClick={() => setModalFormula(formula)}
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          className="btn-ghost h-8 w-8 p-0 flex items-center justify-center text-red-500 hover:text-red-700 hover:bg-red-50"
                          title="Excluir"
                          onClick={() => setDeleteFormula(formula)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      {modalFormula !== null && (
        <FormulaModal
          formula={modalFormula === 'new' ? null : modalFormula}
          onClose={() => setModalFormula(null)}
          onSave={handleSave}
        />
      )}
      {deleteFormula && (
        <DeleteDialog formula={deleteFormula} onClose={() => setDeleteFormula(null)} onConfirm={handleDelete} />
      )}
    </div>
  );
}

