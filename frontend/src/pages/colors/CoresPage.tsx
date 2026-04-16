import React, { useState, useMemo } from 'react';
import { Palette, Plus, Search, Pencil, Trash2, ChevronUp, ChevronDown, ToggleLeft, ToggleRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { useCores, useCreateCor, useUpdateCor, useDeleteCor } from '@/hooks/useTintometry';
import type { LequeCorDefinida } from '@/types';

// ─── Color Swatch ────────────────────────────────────────────────────────────
function ColorSwatch({ hex, size = 'sm' }: { hex: string; size?: 'sm' | 'md' }) {
  const s = size === 'md' ? 'h-10 w-10' : 'h-6 w-6';
  return (
    <span
      className={`${s} rounded-full inline-block border border-slate-200 shrink-0`}
      style={{ backgroundColor: hex }}
      aria-hidden="true"
    />
  );
}

// ─── Modal (create / edit) ───────────────────────────────────────────────────
type CorForm = {
  codigo_cor: string;
  nome_cor: string;
  descricao: string;
  familia_cor: string;
  linha_produto: string;
  l_value: string;
  a_value: string;
  b_value: string;
  r: number;
  g: number;
  b: number;
  ativo: boolean;
};

const EMPTY_FORM: CorForm = {
  codigo_cor: '', nome_cor: '', descricao: '',
  familia_cor: '', linha_produto: '',
  l_value: '50', a_value: '0', b_value: '0',
  r: 128, g: 128, b: 128, ativo: true,
};

function CorModal({
  cor, onClose, onSave,
}: {
  cor: LequeCorDefinida | null;
  onClose: () => void;
  onSave: (data: CorForm) => void;
}) {
  const [form, setForm] = useState<CorForm>(
    cor
      ? {
          codigo_cor: cor.codigo_cor,
          nome_cor: cor.nome_cor,
          descricao: cor.descricao ?? '',
          familia_cor: cor.familia_cor,
          linha_produto: cor.linha_produto,
          l_value: cor.l_value,
          a_value: cor.a_value,
          b_value: cor.b_value,
          r: cor.r, g: cor.g, b: cor.b,
          ativo: cor.ativo,
        }
      : EMPTY_FORM
  );
  const [errors, setErrors] = useState<Partial<Record<keyof CorForm, string>>>({});

  const hexColor = useMemo(() => {
    const toHex = (n: number) => Math.min(255, Math.max(0, Math.round(n))).toString(16).padStart(2, '0');
    return `#${toHex(form.r)}${toHex(form.g)}${toHex(form.b)}`;
  }, [form.r, form.g, form.b]);

  function handleColorPicker(hex: string) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    setForm(f => ({ ...f, r, g, b }));
  }

  function validate(): boolean {
    const e: Partial<Record<keyof CorForm, string>> = {};
    if (!form.codigo_cor.trim()) e.codigo_cor = 'Código obrigatório';
    if (!form.nome_cor.trim()) e.nome_cor = 'Nome obrigatório';
    if (!form.familia_cor.trim()) e.familia_cor = 'Família obrigatória';
    if (!form.linha_produto.trim()) e.linha_produto = 'Linha obrigatória';
    const l = parseFloat(form.l_value);
    if (isNaN(l) || l < 0 || l > 100) e.l_value = 'L* deve ser 0–100';
    const a = parseFloat(form.a_value);
    if (isNaN(a) || a < -128 || a > 127) e.a_value = 'a* deve ser -128 a 127';
    const bv = parseFloat(form.b_value);
    if (isNaN(bv) || bv < -128 || bv > 127) e.b_value = 'b* deve ser -128 a 127';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (validate()) onSave(form);
  }

  function field(key: keyof CorForm, label: string, extra?: React.InputHTMLAttributes<HTMLInputElement>) {
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
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto custom-scrollbar" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 p-5 border-b border-slate-100">
          <ColorSwatch hex={hexColor} size="md" />
          <h2 className="text-lg font-semibold text-slate-900">{cor ? 'Editar Cor' : 'Nova Cor'}</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {field('codigo_cor', 'Código', { placeholder: 'Ex: AZ-001' })}
            {field('nome_cor', 'Nome da Cor', { placeholder: 'Ex: Azul Royal' })}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {field('familia_cor', 'Família / Categoria', { placeholder: 'Ex: Azuis' })}
            {field('linha_produto', 'Linha do Produto', { placeholder: 'Ex: Premium' })}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Descrição (opcional)</label>
            <textarea
              className="form-input text-sm h-16 resize-none"
              value={form.descricao}
              onChange={e => setForm(f => ({ ...f, descricao: e.target.value }))}
            />
          </div>

          {/* RGB color picker */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-2">Cor Visual (RGB)</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={hexColor}
                onChange={e => handleColorPicker(e.target.value)}
                className="h-10 w-14 rounded cursor-pointer border border-slate-200"
              />
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 flex-1">
                {(['r', 'g', 'b'] as const).map(ch => (
                  <div key={ch}>
                    <label className="block text-xs text-slate-500 mb-0.5 uppercase">{ch}</label>
                    <input
                      type="number"
                      min={0} max={255}
                      className="form-input text-sm text-center"
                      value={form[ch]}
                      onChange={e => setForm(f => ({ ...f, [ch]: Number(e.target.value) }))}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* CIE Lab values */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-2">Valores CIE Lab</label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {field('l_value', 'L* (0–100)', { type: 'number', step: '0.001' })}
              {field('a_value', 'a* (-128–127)', { type: 'number', step: '0.001' })}
              {field('b_value', 'b* (-128–127)', { type: 'number', step: '0.001' })}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button type="button" onClick={() => setForm(f => ({ ...f, ativo: !f.ativo }))}>
              {form.ativo
                ? <ToggleRight className="h-5 w-5 text-emerald-500" />
                : <ToggleLeft className="h-5 w-5 text-slate-400" />}
            </button>
            <span className="text-sm text-slate-700">Cor {form.ativo ? 'ativa' : 'inativa'}</span>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn-primary">
              {cor ? 'Salvar Alterações' : 'Criar Cor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Delete Confirm ──────────────────────────────────────────────────────────
function DeleteDialog({ cor, onClose, onConfirm }: { cor: LequeCorDefinida; onClose: () => void; onConfirm: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" role="dialog" aria-modal="true">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 shrink-0">
            <Trash2 className="h-5 w-5 text-red-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Excluir cor</h3>
            <p className="text-sm text-slate-500 mt-1">
              Tem certeza que deseja excluir <strong>{cor.nome_cor}</strong> ({cor.codigo_cor})?
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

// ─── Main Page ───────────────────────────────────────────────────────────────
type SortField = 'codigo_cor' | 'nome_cor' | 'familia_cor' | 'linha_produto';

export default function CoresPage(): React.ReactElement {
  const [query, setQuery] = useState('');
  const [familiaFiltro, setFamiliaFiltro] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [sortField, setSortField] = useState<SortField>('nome_cor');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [modalCor, setModalCor] = useState<LequeCorDefinida | null | 'new'>(null);
  const [deleteCor, setDeleteCor] = useState<LequeCorDefinida | null>(null);

  const { data, isLoading, isError, refetch } = useCores({
    query: query || undefined,
    categoria: familiaFiltro || undefined,
    include_inactive: showInactive,
    page_size: 100,
  });

  const createCor = useCreateCor();
  const updateCor = useUpdateCor();
  const deleteMutation = useDeleteCor();

  const sorted = useMemo(() => {
    const rows = data?.results ?? [];
    return [...rows].sort((a, b) => {
      const av = a[sortField] ?? '';
      const bv = b[sortField] ?? '';
      const cmp = String(av).localeCompare(String(bv));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [data, sortField, sortDir]);

  const familias = useMemo(() => {
    const set = new Set((data?.results ?? []).map(c => c.familia_cor).filter(Boolean));
    return Array.from(set).sort();
  }, [data]);

  function toggleSort(field: SortField) {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('asc'); }
  }

  function SortIcon({ field }: { field: SortField }) {
    if (sortField !== field) return <ChevronUp className="h-3 w-3 text-slate-300" />;
    return sortDir === 'asc' ? <ChevronUp className="h-3 w-3 text-violet-500" /> : <ChevronDown className="h-3 w-3 text-violet-500" />;
  }

  async function handleSave(form: CorForm) {
    try {
      if (modalCor === 'new') {
        await createCor.mutateAsync({
          ...form,
          data_criacao: new Date().toISOString(),
          cor_hex: '',
        } as Omit<LequeCorDefinida, 'id' | 'created_at' | 'updated_at'>);
        toast.success('Cor criada com sucesso!');
      } else if (modalCor) {
        await updateCor.mutateAsync({ id: modalCor.id, data: form });
        toast.success('Cor atualizada!');
      }
      setModalCor(null);
    } catch (err: unknown) {
      const e = err as { response?: { data?: Record<string, string[]> } };
      if (e?.response?.data) {
        const msgs = Object.values(e.response.data).flat().join(' ');
        toast.error(msgs);
      } else {
        toast.error('Erro ao salvar cor');
      }
    }
  }

  async function handleDelete() {
    if (!deleteCor) return;
    try {
      await deleteMutation.mutateAsync(deleteCor.id);
      toast.success('Cor excluída!');
      setDeleteCor(null);
    } catch {
      toast.error('Erro ao excluir cor');
    }
  }

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-6 max-w-7xl animate-fade-in">
        <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
        <div className="card space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
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
          <p className="text-slate-500 mb-3">Erro ao carregar cores.</p>
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
          <h1 className="text-2xl font-bold text-slate-900">Cores Definidas</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {total} {total === 1 ? 'cor cadastrada' : 'cores cadastradas'}
          </p>
        </div>
        <button className="btn-primary self-start sm:self-auto" onClick={() => setModalCor('new')}>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Nova Cor
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            placeholder="Buscar por código, nome ou família…"
            className="form-input pl-9"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
        <select
          className="form-input sm:w-48"
          value={familiaFiltro}
          onChange={e => setFamiliaFiltro(e.target.value)}
        >
          <option value="">Todas as famílias</option>
          {familias.map(f => <option key={f} value={f}>{f}</option>)}
        </select>
        <button
          className={`btn-secondary shrink-0 ${showInactive ? 'ring-2 ring-violet-400' : ''}`}
          onClick={() => setShowInactive(v => !v)}
        >
          {showInactive ? 'Mostrando todas' : 'Apenas ativas'}
        </button>
      </div>

      {/* Table */}
      {sorted.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-50 mb-4">
            <Palette className="h-8 w-8 text-violet-400" aria-hidden="true" />
          </div>
          {query || familiaFiltro
            ? <p className="text-slate-500">Nenhuma cor encontrada para os filtros aplicados.</p>
            : <>
                <p className="font-medium text-slate-700 mb-1">Nenhuma cor cadastrada ainda</p>
                <p className="text-sm text-slate-500 mb-4">Cadastre as cores do catálogo para usar nas fórmulas.</p>
                <button className="btn-primary" onClick={() => setModalCor('new')}>
                  <Plus className="h-4 w-4" />Nova Cor
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
                  <th className="px-4 py-3 text-left font-medium text-slate-500 w-12" />
                  <th
                    className="px-4 py-3 text-left font-medium text-slate-500 cursor-pointer select-none"
                    onClick={() => toggleSort('codigo_cor')}
                  >
                    <span className="inline-flex items-center gap-1">Código <SortIcon field="codigo_cor" /></span>
                  </th>
                  <th
                    className="px-4 py-3 text-left font-medium text-slate-500 cursor-pointer select-none"
                    onClick={() => toggleSort('nome_cor')}
                  >
                    <span className="inline-flex items-center gap-1">Nome <SortIcon field="nome_cor" /></span>
                  </th>
                  <th
                    className="px-4 py-3 text-left font-medium text-slate-500 cursor-pointer select-none"
                    onClick={() => toggleSort('familia_cor')}
                  >
                    <span className="inline-flex items-center gap-1">Família <SortIcon field="familia_cor" /></span>
                  </th>
                  <th
                    className="px-4 py-3 text-left font-medium text-slate-500 cursor-pointer select-none"
                    onClick={() => toggleSort('linha_produto')}
                  >
                    <span className="inline-flex items-center gap-1">Linha <SortIcon field="linha_produto" /></span>
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500">Lab</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-500">Status</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-500">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sorted.map(cor => (
                  <tr key={cor.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <ColorSwatch hex={cor.cor_hex} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">{cor.codigo_cor}</td>
                    <td className="px-4 py-3 font-medium text-slate-900">{cor.nome_cor}</td>
                    <td className="px-4 py-3 text-slate-600">
                      <span className="badge badge-blue">{cor.familia_cor}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{cor.linha_produto}</td>
                    <td className="px-4 py-3 text-center text-xs text-slate-500 font-mono">
                      L{parseFloat(cor.l_value).toFixed(1)} a{parseFloat(cor.a_value).toFixed(1)} b{parseFloat(cor.b_value).toFixed(1)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`badge ${cor.ativo ? 'badge-green' : 'badge-gray'}`}>
                        {cor.ativo ? 'Ativa' : 'Inativa'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="btn-ghost h-8 w-8 p-0 flex items-center justify-center"
                          onClick={() => setModalCor(cor)}
                          title="Editar"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          className="btn-ghost h-8 w-8 p-0 flex items-center justify-center text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setDeleteCor(cor)}
                          title="Excluir"
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
      {modalCor !== null && (
        <CorModal
          cor={modalCor === 'new' ? null : modalCor}
          onClose={() => setModalCor(null)}
          onSave={handleSave}
        />
      )}
      {deleteCor && (
        <DeleteDialog cor={deleteCor} onClose={() => setDeleteCor(null)} onConfirm={handleDelete} />
      )}
    </div>
  );
}