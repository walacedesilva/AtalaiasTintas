import React, { useMemo, useState } from 'react';
import {
  Beaker,
  Plus,
  Search,
  Edit2,
  Trash2,
  ToggleLeft,
  ToggleRight,
  X,
  ChevronUp,
  ChevronDown,
  Loader2,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import {
  usePigmentos,
  useCreatePigmento,
  useUpdatePigmento,
  useDeletePigmento,
} from '@/hooks/useTintometry';
import type { Pigmento } from '@/types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function ColorSwatch({ hex, size = 'sm' }: { hex: string; size?: 'sm' | 'lg' }) {
  const dim = size === 'sm' ? 'h-6 w-6' : 'h-12 w-12';
  return (
    <span
      className={`${dim} rounded-full border border-black/10 inline-block flex-shrink-0`}
      style={{ backgroundColor: hex }}
      aria-hidden="true"
    />
  );
}

type SortKey = 'codigo' | 'nome' | 'cor_base' | 'fornecedor' | 'densidade' | 'poder_tintorial';

// ---------------------------------------------------------------------------
// Modal: Create / Edit
// ---------------------------------------------------------------------------

const EMPTY_FORM = {
  codigo: '',
  nome: '',
  cor_base: '',
  densidade: '',
  poder_tintorial: '',
  fornecedor: '',
  codigo_fornecedor: '',
  concentracao_maxima: '',
  r: 128,
  g: 128,
  b: 128,
  ativo: true,
};

type FormState = typeof EMPTY_FORM;

function pigmentoToForm(p: Pigmento): FormState {
  return {
    codigo: p.codigo,
    nome: p.nome,
    cor_base: p.cor_base,
    densidade: p.densidade,
    poder_tintorial: p.poder_tintorial,
    fornecedor: p.fornecedor,
    codigo_fornecedor: p.codigo_fornecedor ?? '',
    concentracao_maxima: p.concentracao_maxima,
    r: p.r,
    g: p.g,
    b: p.b,
    ativo: p.ativo,
  };
}

interface PigmentoModalProps {
  editing: Pigmento | null;
  onClose: () => void;
}

function PigmentoModal({ editing, onClose }: PigmentoModalProps) {
  const [form, setForm] = useState<FormState>(
    editing ? pigmentoToForm(editing) : { ...EMPTY_FORM }
  );
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});

  const create = useCreatePigmento();
  const update = useUpdatePigmento();
  const isPending = create.isPending || update.isPending;

  const previewHex = `#${form.r.toString(16).padStart(2, '0')}${form.g.toString(16).padStart(2, '0')}${form.b.toString(16).padStart(2, '0')}`;

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  }

  function validate(): boolean {
    const e: Partial<Record<keyof FormState, string>> = {};
    if (!form.codigo.trim()) e.codigo = 'Obrigatório';
    if (!form.nome.trim()) e.nome = 'Obrigatório';
    if (!form.cor_base.trim()) e.cor_base = 'Obrigatório';
    if (!form.fornecedor.trim()) e.fornecedor = 'Obrigatório';
    if (!form.densidade || isNaN(Number(form.densidade)) || Number(form.densidade) <= 0)
      e.densidade = 'Deve ser um número positivo';
    if (!form.poder_tintorial || isNaN(Number(form.poder_tintorial)) || Number(form.poder_tintorial) <= 0 || Number(form.poder_tintorial) > 100)
      e.poder_tintorial = 'Deve ser entre 0.01 e 100';
    if (!form.concentracao_maxima || isNaN(Number(form.concentracao_maxima)) || Number(form.concentracao_maxima) <= 0 || Number(form.concentracao_maxima) > 100)
      e.concentracao_maxima = 'Deve ser entre 0.01 e 100';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    const payload = {
      codigo: form.codigo.trim(),
      nome: form.nome.trim(),
      cor_base: form.cor_base.trim(),
      densidade: form.densidade,
      poder_tintorial: form.poder_tintorial,
      fornecedor: form.fornecedor.trim(),
      codigo_fornecedor: form.codigo_fornecedor.trim() || null,
      concentracao_maxima: form.concentracao_maxima,
      r: form.r,
      g: form.g,
      b: form.b,
      ativo: form.ativo,
    };

    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, data: payload });
        toast.success('Pigmento atualizado com sucesso.');
      } else {
        await create.mutateAsync(payload as Omit<Pigmento, 'id' | 'created_at' | 'updated_at' | 'cor_hex'>);
        toast.success('Pigmento criado com sucesso.');
      }
      onClose();
    } catch (err: any) {
      // Show field-level errors returned by Django if any
      const detail = err?.response?.data;
      if (detail && typeof detail === 'object') {
        const apiErrors: Partial<Record<keyof FormState, string>> = {};
        for (const [k, msgs] of Object.entries(detail)) {
          const msg = Array.isArray(msgs) ? msgs[0] : String(msgs);
          apiErrors[k as keyof FormState] = msg;
        }
        setErrors(apiErrors);
      } else {
        toast.error('Erro ao salvar pigmento. Verifique os dados e tente novamente.');
      }
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={editing ? 'Editar Pigmento' : 'Novo Pigmento'}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <ColorSwatch hex={previewHex} size="lg" />
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                {editing ? 'Editar Pigmento' : 'Novo Pigmento'}
              </h2>
              <p className="text-xs text-slate-500">Preencha os dados técnicos do pigmento</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors" aria-label="Fechar">
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="px-6 py-5 space-y-5">
            {/* Row 1: Código + Nome */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Código *" error={errors.codigo}>
                <input className={`form-input ${errors.codigo ? 'form-input-error' : ''}`} value={form.codigo} onChange={(e) => set('codigo', e.target.value)} placeholder="Ex: PIG-001" />
              </Field>
              <Field label="Nome *" error={errors.nome}>
                <input className={`form-input ${errors.nome ? 'form-input-error' : ''}`} value={form.nome} onChange={(e) => set('nome', e.target.value)} placeholder="Ex: Óxido de Titânio" />
              </Field>
            </div>

            {/* Row 2: Cor Base + Fornecedor */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Cor Base *" error={errors.cor_base}>
                <input className={`form-input ${errors.cor_base ? 'form-input-error' : ''}`} value={form.cor_base} onChange={(e) => set('cor_base', e.target.value)} placeholder="Ex: Branco, Azul, Vermelho" />
              </Field>
              <Field label="Fornecedor *" error={errors.fornecedor}>
                <input className={`form-input ${errors.fornecedor ? 'form-input-error' : ''}`} value={form.fornecedor} onChange={(e) => set('fornecedor', e.target.value)} placeholder="Ex: Basf, Clariant" />
              </Field>
            </div>

            {/* Row 3: Fornecedor code + concentration */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Field label="Cód. Fornecedor" error={errors.codigo_fornecedor}>
                <input className="form-input" value={form.codigo_fornecedor} onChange={(e) => set('codigo_fornecedor', e.target.value)} placeholder="Opcional" />
              </Field>
              <Field label="Densidade (g/ml) *" error={errors.densidade}>
                <input type="number" step="0.001" min="0.001" className={`form-input ${errors.densidade ? 'form-input-error' : ''}`} value={form.densidade} onChange={(e) => set('densidade', e.target.value)} placeholder="Ex: 1.25" />
              </Field>
              <Field label="Conc. Máxima (%) *" error={errors.concentracao_maxima}>
                <input type="number" step="0.01" min="0.01" max="100" className={`form-input ${errors.concentracao_maxima ? 'form-input-error' : ''}`} value={form.concentracao_maxima} onChange={(e) => set('concentracao_maxima', e.target.value)} placeholder="Ex: 15" />
              </Field>
            </div>

            {/* Poder tintorial */}
            <Field label="Poder Tintorial (%) *" error={errors.poder_tintorial}>
              <input type="number" step="0.01" min="0.01" max="100" className={`form-input ${errors.poder_tintorial ? 'form-input-error' : ''}`} value={form.poder_tintorial} onChange={(e) => set('poder_tintorial', e.target.value)} placeholder="Ex: 85" />
            </Field>

            {/* Color RGB */}
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Cor de referência visual</p>
              <div className="flex items-center gap-4">
                <ColorSwatch hex={previewHex} size="lg" />
                <div className="grid grid-cols-3 gap-3 flex-1">
                  {(['r', 'g', 'b'] as const).map((ch) => (
                    <Field key={ch} label={ch.toUpperCase()} error={undefined}>
                      <input
                        type="number"
                        min={0}
                        max={255}
                        className="form-input text-center"
                        value={form[ch]}
                        onChange={(e) => set(ch, Math.min(255, Math.max(0, parseInt(e.target.value) || 0)))}
                      />
                    </Field>
                  ))}
                </div>
                <input
                  type="color"
                  value={previewHex}
                  className="h-10 w-10 rounded-lg border border-slate-300 cursor-pointer p-0.5"
                  title="Selecionar cor"
                  onChange={(e) => {
                    const hex = e.target.value;
                    const r = parseInt(hex.slice(1, 3), 16);
                    const g = parseInt(hex.slice(3, 5), 16);
                    const b = parseInt(hex.slice(5, 7), 16);
                    setForm((prev) => ({ ...prev, r, g, b }));
                  }}
                />
              </div>
            </div>

            {/* Active toggle */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                role="switch"
                aria-checked={form.ativo}
                onClick={() => set('ativo', !form.ativo)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 ${form.ativo ? 'bg-teal-600' : 'bg-slate-300'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${form.ativo ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
              <span className="text-sm font-medium text-slate-700">
                {form.ativo ? 'Pigmento ativo' : 'Pigmento inativo'}
              </span>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={isPending}>
              {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              {editing ? 'Salvar alterações' : 'Criar pigmento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-700 mb-1">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Delete confirmation dialog
// ---------------------------------------------------------------------------

interface DeleteDialogProps {
  pigmento: Pigmento;
  onCancel: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteDialog({ pigmento, onCancel, onConfirm, isLoading }: DeleteDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6" role="dialog" aria-modal="true">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-rose-100">
            <Trash2 className="h-5 w-5 text-rose-600" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Excluir pigmento</h2>
            <p className="text-sm text-slate-500 mt-1">
              Tem certeza que deseja excluir <strong>{pigmento.nome}</strong> ({pigmento.codigo})?
              Esta ação não pode ser desfeita.
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <button className="btn-secondary" onClick={onCancel} disabled={isLoading}>
            Cancelar
          </button>
          <button className="btn-danger" onClick={onConfirm} disabled={isLoading}>
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            Excluir
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function PigmentosPage(): React.ReactElement {
  const [search, setSearch] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>('nome');
  const [sortAsc, setSortAsc] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPigmento, setEditingPigmento] = useState<Pigmento | null>(null);
  const [deletingPigmento, setDeletingPigmento] = useState<Pigmento | null>(null);

  const { data, isLoading, isError } = usePigmentos({ include_inactive: showInactive });
  const deletePigmento = useDeletePigmento();
  const updatePigmento = useUpdatePigmento();

  const allPigmentos = data?.results ?? [];

  // Client-side search + sort
  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    let list = q
      ? allPigmentos.filter(
          (p) =>
            p.nome.toLowerCase().includes(q) ||
            p.codigo.toLowerCase().includes(q) ||
            p.fornecedor.toLowerCase().includes(q) ||
            p.cor_base.toLowerCase().includes(q)
        )
      : [...allPigmentos];

    list.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp = String(av).localeCompare(String(bv), 'pt-BR', { numeric: true });
      return sortAsc ? cmp : -cmp;
    });

    return list;
  }, [allPigmentos, search, sortKey, sortAsc]);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((v) => !v);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  function openCreate() {
    setEditingPigmento(null);
    setModalOpen(true);
  }

  function openEdit(p: Pigmento) {
    setEditingPigmento(p);
    setModalOpen(true);
  }

  async function handleToggleActive(p: Pigmento) {
    try {
      await updatePigmento.mutateAsync({ id: p.id, data: { ativo: !p.ativo } });
      toast.success(p.ativo ? 'Pigmento desativado.' : 'Pigmento reativado.');
    } catch {
      toast.error('Erro ao alterar status do pigmento.');
    }
  }

  async function handleDelete() {
    if (!deletingPigmento) return;
    try {
      await deletePigmento.mutateAsync(deletingPigmento.id);
      toast.success('Pigmento excluído.');
      setDeletingPigmento(null);
    } catch {
      toast.error('Não foi possível excluir o pigmento. Ele pode estar em uso em fórmulas.');
    }
  }

  function SortIcon({ k }: { k: SortKey }) {
    if (sortKey !== k) return null;
    return sortAsc ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />;
  }

  function ThBtn({ k, children }: { k: SortKey; children: React.ReactNode }) {
    return (
      <button
        onClick={() => handleSort(k)}
        className="flex items-center gap-1 font-medium text-slate-600 hover:text-slate-900 transition-colors"
      >
        {children}
        <SortIcon k={k} />
      </button>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Pigmentos</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {isLoading ? 'Carregando…' : `${filtered.length} pigmento${filtered.length !== 1 ? 's' : ''}${showInactive ? '' : ' ativos'}`}
          </p>
        </div>
        <button className="btn-primary self-start sm:self-auto" onClick={openCreate}>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Novo Pigmento
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            placeholder="Buscar por nome, código, fornecedor ou cor base…"
            className="form-input pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button
          className={`btn-secondary gap-2 ${showInactive ? 'border-teal-400 text-teal-700' : ''}`}
          onClick={() => setShowInactive((v) => !v)}
          title="Mostrar pigmentos inativos"
        >
          {showInactive ? <ToggleRight className="h-4 w-4 text-teal-600" /> : <ToggleLeft className="h-4 w-4 text-slate-400" />}
          {showInactive ? 'Todos (inclusive inativos)' : 'Apenas ativos'}
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-20 gap-2 text-slate-500">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Carregando pigmentos…</span>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-sm font-medium text-rose-600 mb-1">Erro ao carregar pigmentos</p>
            <p className="text-xs text-slate-400">Verifique a conexão com o servidor Django.</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-50 mb-4">
              <Beaker className="h-8 w-8 text-teal-600" aria-hidden="true" />
            </div>
            {search ? (
              <>
                <h2 className="text-base font-semibold text-slate-900 mb-1">Nenhum resultado</h2>
                <p className="text-sm text-slate-500 max-w-xs">Nenhum pigmento encontrado para "{search}".</p>
                <button className="mt-3 text-sm text-teal-600 hover:underline" onClick={() => setSearch('')}>Limpar busca</button>
              </>
            ) : (
              <>
                <h2 className="text-base font-semibold text-slate-900 mb-1">Nenhum pigmento cadastrado</h2>
                <p className="text-sm text-slate-500 max-w-xs">Comece cadastrando os pigmentos usados nas misturas.</p>
                <button className="mt-4 btn-primary" onClick={openCreate}>
                  <Plus className="h-4 w-4" /> Cadastrar primeiro pigmento
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-4 py-3 text-left w-10" aria-label="Cor" />
                  <th className="px-4 py-3 text-left"><ThBtn k="codigo">Código</ThBtn></th>
                  <th className="px-4 py-3 text-left"><ThBtn k="nome">Nome</ThBtn></th>
                  <th className="px-4 py-3 text-left hidden md:table-cell"><ThBtn k="cor_base">Cor Base</ThBtn></th>
                  <th className="px-4 py-3 text-left hidden lg:table-cell"><ThBtn k="fornecedor">Fornecedor</ThBtn></th>
                  <th className="px-4 py-3 text-right hidden lg:table-cell"><ThBtn k="densidade">Densidade</ThBtn></th>
                  <th className="px-4 py-3 text-right hidden xl:table-cell"><ThBtn k="poder_tintorial">Pod. Tintorial</ThBtn></th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <ColorSwatch hex={p.cor_hex} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">{p.codigo}</td>
                    <td className="px-4 py-3 font-medium text-slate-900">{p.nome}</td>
                    <td className="px-4 py-3 text-slate-600 hidden md:table-cell">{p.cor_base}</td>
                    <td className="px-4 py-3 text-slate-600 hidden lg:table-cell">{p.fornecedor}</td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-slate-600 hidden lg:table-cell">
                      {Number(p.densidade).toFixed(4)} g/ml
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-slate-600 hidden xl:table-cell">
                      {Number(p.poder_tintorial).toFixed(2)} %
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`badge ${p.ativo ? 'badge-green' : 'badge-gray'}`}>
                        {p.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => openEdit(p)}
                          className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                          title="Editar pigmento"
                          aria-label={`Editar ${p.nome}`}
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleToggleActive(p)}
                          className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-amber-600 transition-colors"
                          title={p.ativo ? 'Desativar pigmento' : 'Reativar pigmento'}
                          aria-label={p.ativo ? `Desativar ${p.nome}` : `Reativar ${p.nome}`}
                        >
                          {p.ativo ? <ToggleRight className="h-4 w-4 text-teal-600" /> : <ToggleLeft className="h-4 w-4" />}
                        </button>
                        <button
                          onClick={() => setDeletingPigmento(p)}
                          className="p-1.5 rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"
                          title="Excluir pigmento"
                          aria-label={`Excluir ${p.nome}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination info */}
            {data && data.count > data.results.length && (
              <div className="px-4 py-3 border-t border-slate-200 bg-slate-50 text-xs text-slate-500">
                Exibindo {data.results.length} de {data.count} pigmentos
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {modalOpen && (
        <PigmentoModal
          editing={editingPigmento}
          onClose={() => { setModalOpen(false); setEditingPigmento(null); }}
        />
      )}

      {deletingPigmento && (
        <DeleteDialog
          pigmento={deletingPigmento}
          onCancel={() => setDeletingPigmento(null)}
          onConfirm={handleDelete}
          isLoading={deletePigmento.isPending}
        />
      )}
    </div>
  );
}
