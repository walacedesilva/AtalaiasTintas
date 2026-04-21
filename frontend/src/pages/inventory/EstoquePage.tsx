import React, { useState, useRef } from 'react';
import {
  Archive,
  Package,
  Pencil,
  Plus,
  Search,
  AlertTriangle,
  XCircle,
  Clock,
  Upload,
  CheckCircle,
  ChevronDown,
  RefreshCw,
  PenLine,
  CloudDownload,
  Trash2,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  useEstoqueResumo,
  useEstoqueLoja,
  useLotesProximosVencimento,
  useEntradas,
  useImportarXmlNFe,
  useConfirmarEntrada,
  useCriarEntradaManual,
} from '@/hooks/useInventory';
import { inventoryAPI } from '@/api';
import type {
  Categoria,
  EstoqueLojaItem,
  LoteProduto,
  EntradaMercadoria,
  Marca,
  ProdutoBase,
  ProdutoBasePayload,
  StatusEstoque,
} from '@/types';
import type { EntradaManualItemPayload } from '@/api/inventory';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_LABEL: Record<StatusEstoque, string> = {
  NORMAL: 'Normal',
  BAIXO: 'Baixo',
  ZERADO: 'Zerado',
};

const STATUS_BADGE: Record<StatusEstoque, string> = {
  NORMAL: 'badge badge-green',
  BAIXO: 'badge badge-yellow',
  ZERADO: 'badge badge-red',
};

function fmt(value: string | null | undefined): string {
  if (!value) return '—';
  const n = parseFloat(value);
  return isNaN(n) ? value : n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}

function fmtCurrency(value: string | null | undefined): string {
  if (!value) return '—';
  const n = parseFloat(value);
  if (isNaN(n)) return value;
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

// ---------------------------------------------------------------------------
// Summary cards
// ---------------------------------------------------------------------------

function SummaryCards({ loja_id }: { loja_id?: number }) {
  const { data, isLoading } = useEstoqueResumo(loja_id);

  const cards = [
    {
      label: 'Total de Itens',
      value: isLoading ? undefined : data?.total_itens,
      icon: Package,
      color: 'text-teal-600',
      bg: 'bg-teal-50',
    },
    {
      label: 'Estoque Baixo',
      value: isLoading ? undefined : data?.estoque_baixo,
      icon: AlertTriangle,
      color: data?.estoque_baixo ? 'text-amber-600' : 'text-slate-400',
      bg: data?.estoque_baixo ? 'bg-amber-50' : 'bg-slate-50',
      danger: true,
    },
    {
      label: 'Sem Estoque',
      value: isLoading ? undefined : data?.estoque_zerado,
      icon: XCircle,
      color: data?.estoque_zerado ? 'text-rose-600' : 'text-slate-400',
      bg: data?.estoque_zerado ? 'bg-rose-50' : 'bg-slate-50',
      danger: true,
    },
    {
      label: 'Valor em Estoque',
      value: isLoading ? undefined : fmtCurrency(data?.valor_total_custo),
      icon: Package,
      color: 'text-sky-600',
      bg: 'bg-sky-50',
      isText: true,
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="card p-4 flex items-center gap-3">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${c.bg}`}>
            <c.icon className={`h-5 w-5 ${c.color}`} aria-hidden="true" />
          </div>
          <div>
            {isLoading ? (
              <p className="text-xl font-bold text-slate-300">—</p>
            ) : c.isText ? (
              <p className={`text-base font-bold leading-tight ${c.danger && c.value ? 'text-rose-600' : 'text-slate-900'}`}>
                {c.value ?? '—'}
              </p>
            ) : (
              <p className={`text-2xl font-bold leading-none ${c.danger && (c.value as number) > 0 ? (c.color) : 'text-slate-900'}`}>
                {c.value ?? 0}
              </p>
            )}
            <p className="text-xs text-slate-500 mt-0.5">{c.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stock table
// ---------------------------------------------------------------------------

function EstoqueTable({
  search,
  statusFilter,
  loja_id,
}: {
  search: string;
  statusFilter: string;
  loja_id?: number;
}) {
  const { data, isLoading, error, refetch } = useEstoqueLoja({
    search: search || undefined,
    status: (statusFilter as EstoqueLojaItem['status_estoque']) || undefined,
    loja_id,
    page_size: 50,
  });

  if (isLoading) {
    return (
      <div className="card divide-y divide-slate-100">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="px-4 py-3 flex items-center gap-4 animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-24" />
            <div className="h-4 bg-slate-200 rounded flex-1" />
            <div className="h-4 bg-slate-200 rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="card flex flex-col items-center justify-center py-16 text-center">
        <XCircle className="h-8 w-8 text-rose-400 mb-2" aria-hidden="true" />
        <p className="text-sm text-slate-600">Erro ao carregar estoque.</p>
        <button className="btn-secondary mt-3 text-xs" onClick={() => refetch()}>
          <RefreshCw className="h-3 w-3" /> Tentar novamente
        </button>
      </div>
    );
  }

  const items: EstoqueLojaItem[] = data?.results ?? [];

  if (items.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-50 mb-4">
          <Package className="h-8 w-8 text-slate-400" aria-hidden="true" />
        </div>
        <h2 className="text-sm font-semibold text-slate-900 mb-1">Nenhum produto encontrado</h2>
        <p className="text-xs text-slate-500">
          {search ? 'Tente outra busca.' : 'Cadastre produtos ou importe uma NF-e para criar registros de estoque.'}
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Código</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Produto</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Marca</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Disponível</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Mínimo</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Reservado</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Última mov.</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-slate-500">{item.produto_codigo}</td>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900 leading-tight">{item.produto_nome}</p>
                  <p className="text-xs text-slate-400">{item.produto_base_nome}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{item.marca_nome}</td>
                <td className="px-4 py-3 text-right font-medium tabular-nums">
                  {fmt(item.quantidade_disponivel)} <span className="text-xs text-slate-400">{item.unidade_sigla}</span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-500">
                  {fmt(item.estoque_minimo)} <span className="text-xs text-slate-400">{item.unidade_sigla}</span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-500">
                  {fmt(item.quantidade_reservada)} <span className="text-xs text-slate-400">{item.unidade_sigla}</span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={STATUS_BADGE[item.status_estoque]}>{STATUS_LABEL[item.status_estoque]}</span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">{fmtDate(item.data_ultima_movimentacao)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(data?.count ?? 0) > items.length && (
        <div className="px-4 py-3 border-t border-slate-100 text-center text-xs text-slate-500">
          Mostrando {items.length} de {data?.count} itens
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Lotes tab
// ---------------------------------------------------------------------------

const DIAS_OPTIONS = [7, 15, 30, 60, 90];

function LotesTab({ loja_id }: { loja_id: number }) {
  const [dias, setDias] = useState(30);
  const { data: lotes = [], isLoading } = useLotesProximosVencimento(loja_id, dias);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="text-sm text-slate-600 shrink-0">Vencendo nos próximos</label>
        <div className="flex gap-1">
          {DIAS_OPTIONS.map((d) => (
            <button
              key={d}
              onClick={() => setDias(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                dias === d
                  ? 'bg-teal-600 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {d} dias
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="card divide-y divide-slate-100">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="px-4 py-3 flex gap-4 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-32" />
              <div className="h-4 bg-slate-200 rounded flex-1" />
            </div>
          ))}
        </div>
      ) : lotes.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-14 text-center">
          <CheckCircle className="h-8 w-8 text-emerald-400 mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-700">Nenhum lote vencendo nos próximos {dias} dias</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Lote</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Validade</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Dias</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Qtd. atual</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {(lotes as LoteProduto[]).map((lote) => {
                const urgente = (lote.dias_para_vencer ?? 999) <= 7;
                return (
                  <tr key={lote.id} className={`hover:bg-slate-50 ${urgente ? 'bg-rose-50/40' : ''}`}>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">{lote.numero_lote}</td>
                    <td className="px-4 py-3">{fmtDate(lote.data_validade)}</td>
                    <td className={`px-4 py-3 text-right font-bold tabular-nums ${urgente ? 'text-rose-600' : 'text-amber-600'}`}>
                      {lote.dias_para_vencer ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{fmt(lote.quantidade_atual)}</td>
                    <td className="px-4 py-3 text-center">
                      {lote.esta_vencido ? (
                        <span className="badge badge-red">Vencido</span>
                      ) : urgente ? (
                        <span className="badge badge-red">Urgente</span>
                      ) : (
                        <span className="badge badge-yellow">Atenção</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// EntradaManualModal — T6
// ---------------------------------------------------------------------------

interface ItemForm extends EntradaManualItemPayload {
  _key: number;
}

const emptyItem = (key: number): ItemForm => ({
  _key: key,
  descricao_nfe: '',
  codigo_nfe: '',
  ncm: '',
  cfop: '',
  quantidade: 1,
  unidade_nfe: 'UN',
  valor_unitario: 0,
});

function EntradaManualModal({
  loja_id,
  onClose,
}: {
  loja_id: number;
  onClose: () => void;
}) {
  const criar = useCriarEntradaManual();
  const [nextKey, setNextKey] = useState(1);
  const [itens, setItens] = useState<ItemForm[]>([emptyItem(0)]);
  const [form, setForm] = useState({
    numero_nfe: '',
    serie_nfe: '1',
    fornecedor_cnpj: '',
    fornecedor_nome: '',
    fornecedor_uf: '',
    data_emissao_nfe: '',
    valor_total_nfe: '',
    chave_acesso_nfe: '',
    observacoes: '',
  });
  const [error, setError] = useState<string | null>(null);

  function addItem() {
    setItens((prev) => [...prev, emptyItem(nextKey)]);
    setNextKey((k) => k + 1);
  }

  function removeItem(key: number) {
    setItens((prev) => prev.filter((i) => i._key !== key));
  }

  function updateItem(key: number, field: keyof EntradaManualItemPayload, value: string | number) {
    setItens((prev) =>
      prev.map((i) => (i._key === key ? { ...i, [field]: value } : i)),
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (itens.length === 0) {
      setError('Adicione pelo menos um item.');
      return;
    }
    try {
      await criar.mutateAsync({
        loja_id,
        numero_nfe: form.numero_nfe,
        serie_nfe: form.serie_nfe || '1',
        fornecedor_cnpj: form.fornecedor_cnpj,
        fornecedor_nome: form.fornecedor_nome || undefined,
        fornecedor_uf: form.fornecedor_uf || undefined,
        data_emissao_nfe: form.data_emissao_nfe || null,
        valor_total_nfe: form.valor_total_nfe ? Number(form.valor_total_nfe) : null,
        chave_acesso_nfe: form.chave_acesso_nfe || null,
        observacoes: form.observacoes,
        itens: itens.map(({ _key: _k, ...rest }) => ({
          ...rest,
          quantidade: Number(rest.quantidade),
          valor_unitario: Number(rest.valor_unitario),
        })),
      });
      onClose();
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail;
      setError(detail ?? 'Erro ao salvar entrada.');
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Nova entrada manual de NF-e"
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-10 pb-6 px-4 overflow-y-auto"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-base font-semibold text-slate-900">Entrada Manual de NF-e</h2>
          <button
            type="button"
            className="text-slate-400 hover:text-slate-600"
            onClick={onClose}
            aria-label="Fechar"
          >
            <XCircle className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            {/* NF-e header */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1" htmlFor="em-numero">
                  Número NF-e *
                </label>
                <input
                  id="em-numero"
                  type="text"
                  maxLength={9}
                  required
                  autoFocus
                  className="input-field"
                  value={form.numero_nfe}
                  onChange={(e) => setForm({ ...form, numero_nfe: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1" htmlFor="em-serie">
                  Série
                </label>
                <input
                  id="em-serie"
                  type="text"
                  maxLength={3}
                  className="input-field"
                  value={form.serie_nfe}
                  onChange={(e) => setForm({ ...form, serie_nfe: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1" htmlFor="em-data">
                  Data Emissão
                </label>
                <input
                  id="em-data"
                  type="date"
                  className="input-field"
                  value={form.data_emissao_nfe}
                  onChange={(e) => setForm({ ...form, data_emissao_nfe: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1" htmlFor="em-valor">
                  Valor Total (R$)
                </label>
                <input
                  id="em-valor"
                  type="number"
                  step="0.01"
                  min="0"
                  className="input-field"
                  value={form.valor_total_nfe}
                  onChange={(e) => setForm({ ...form, valor_total_nfe: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1" htmlFor="em-cnpj">
                  CNPJ / CPF Fornecedor *
                </label>
                <input
                  id="em-cnpj"
                  type="text"
                  maxLength={18}
                  required
                  placeholder="00.000.000/0000-00"
                  className="input-field font-mono"
                  value={form.fornecedor_cnpj}
                  onChange={(e) => setForm({ ...form, fornecedor_cnpj: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1" htmlFor="em-nome">
                  Nome Fornecedor
                </label>
                <input
                  id="em-nome"
                  type="text"
                  maxLength={200}
                  className="input-field"
                  value={form.fornecedor_nome}
                  onChange={(e) => setForm({ ...form, fornecedor_nome: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1" htmlFor="em-chave">
                Chave de Acesso (44 dígitos, opcional)
              </label>
              <input
                id="em-chave"
                type="text"
                maxLength={44}
                placeholder="00000000000000000000000000000000000000000000"
                className="input-field font-mono text-xs"
                value={form.chave_acesso_nfe}
                onChange={(e) => setForm({ ...form, chave_acesso_nfe: e.target.value.replace(/\D/g, '') })}
              />
            </div>

            {/* Items */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-600">Itens *</p>
                <button
                  type="button"
                  className="btn-secondary text-xs py-1 px-2"
                  onClick={addItem}
                >
                  <Plus className="h-3 w-3" />
                  Adicionar Item
                </button>
              </div>
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="min-w-full text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-2 py-2 text-left font-medium text-slate-500">Descrição *</th>
                      <th className="px-2 py-2 text-left font-medium text-slate-500 w-24">Cód.</th>
                      <th className="px-2 py-2 text-left font-medium text-slate-500 w-20">NCM</th>
                      <th className="px-2 py-2 text-left font-medium text-slate-500 w-16">Qtd *</th>
                      <th className="px-2 py-2 text-left font-medium text-slate-500 w-16">Un.</th>
                      <th className="px-2 py-2 text-right font-medium text-slate-500 w-24">Vlr Unit *</th>
                      <th className="px-2 py-2 w-8" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {itens.map((item) => (
                      <tr key={item._key}>
                        <td className="px-2 py-1">
                          <input
                            type="text"
                            required
                            aria-label="Descrição do item"
                            className="input-field text-xs py-1"
                            value={item.descricao_nfe}
                            onChange={(e) => updateItem(item._key, 'descricao_nfe', e.target.value)}
                          />
                        </td>
                        <td className="px-2 py-1">
                          <input
                            type="text"
                            maxLength={60}
                            aria-label="Código NF-e"
                            className="input-field text-xs py-1"
                            value={item.codigo_nfe ?? ''}
                            onChange={(e) => updateItem(item._key, 'codigo_nfe', e.target.value)}
                          />
                        </td>
                        <td className="px-2 py-1">
                          <input
                            type="text"
                            maxLength={10}
                            aria-label="NCM"
                            className="input-field text-xs py-1"
                            value={item.ncm ?? ''}
                            onChange={(e) => updateItem(item._key, 'ncm', e.target.value)}
                          />
                        </td>
                        <td className="px-2 py-1">
                          <input
                            type="number"
                            min="0"
                            step="0.0001"
                            required
                            aria-label="Quantidade"
                            className="input-field text-xs py-1"
                            value={item.quantidade}
                            onChange={(e) => updateItem(item._key, 'quantidade', e.target.value)}
                          />
                        </td>
                        <td className="px-2 py-1">
                          <input
                            type="text"
                            maxLength={6}
                            aria-label="Unidade"
                            className="input-field text-xs py-1"
                            value={item.unidade_nfe ?? ''}
                            onChange={(e) => updateItem(item._key, 'unidade_nfe', e.target.value)}
                          />
                        </td>
                        <td className="px-2 py-1">
                          <input
                            type="number"
                            min="0"
                            step="0.0001"
                            required
                            aria-label="Valor unitário"
                            className="input-field text-xs py-1 text-right"
                            value={item.valor_unitario}
                            onChange={(e) => updateItem(item._key, 'valor_unitario', e.target.value)}
                          />
                        </td>
                        <td className="px-2 py-1 text-center">
                          <button
                            type="button"
                            aria-label="Remover item"
                            className="text-rose-400 hover:text-rose-600"
                            onClick={() => removeItem(item._key)}
                            disabled={itens.length === 1}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {error && (
              <p className="text-xs text-rose-600 bg-rose-50 px-3 py-2 rounded-lg">{error}</p>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={criar.isPending}>
              {criar.isPending ? 'Salvando…' : 'Salvar Entrada'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// NF-e import tab
// ---------------------------------------------------------------------------

function EntradasTab({ loja_id }: { loja_id: number }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const { data, isLoading, refetch } = useEntradas(loja_id || undefined);
  const importar = useImportarXmlNFe();
  const confirmar = useConfirmarEntrada();
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [showManual, setShowManual] = useState(false);

  const entradas: EntradaMercadoria[] = data?.results ?? [];

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !loja_id) return;
    setImporting(true);
    setImportError(null);
    try {
      await importar.mutateAsync({ loja_id, file });
    } catch (err: unknown) {
      const msg = (err as { detail?: string })?.detail ?? 'Erro ao importar XML';
      setImportError(msg);
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  const STATUS_ENTRADA_BADGE: Record<string, string> = {
    RASCUNHO: 'badge badge-gray',
    PENDENTE: 'badge badge-yellow',
    CONFIRMADA: 'badge badge-green',
    CANCELADA: 'badge badge-red',
  };

  const ORIGEM_BADGE: Record<string, { cls: string; icon: React.ReactNode; label: string }> = {
    XML_UPLOAD: {
      cls: 'bg-blue-50 text-blue-700',
      icon: <Upload className="h-3 w-3" aria-hidden="true" />,
      label: 'XML',
    },
    MANUAL: {
      cls: 'bg-amber-50 text-amber-700',
      icon: <PenLine className="h-3 w-3" aria-hidden="true" />,
      label: 'Manual',
    },
    SEFAZ_DOWNLOAD: {
      cls: 'bg-emerald-50 text-emerald-700',
      icon: <CloudDownload className="h-3 w-3" aria-hidden="true" />,
      label: 'SEFAZ',
    },
  };

  return (
    <div className="space-y-4">
      {showManual && loja_id && (
        <EntradaManualModal loja_id={loja_id} onClose={() => setShowManual(false)} />
      )}

      <div className="flex items-center gap-3 flex-wrap">
        <input
          ref={fileRef}
          type="file"
          accept=".xml"
          className="hidden"
          onChange={handleFile}
          disabled={!loja_id || importing}
        />
        <button
          className="btn-primary"
          onClick={() => fileRef.current?.click()}
          disabled={!loja_id || importing}
        >
          <Upload className="h-4 w-4" aria-hidden="true" />
          {importing ? 'Importando…' : 'Importar XML NF-e'}
        </button>
        <button
          className="btn-secondary"
          onClick={() => setShowManual(true)}
          disabled={!loja_id}
        >
          <PenLine className="h-4 w-4" aria-hidden="true" />
          Entrada Manual
        </button>
        {importError && (
          <p className="text-xs text-rose-600">{importError}</p>
        )}
      </div>

      {isLoading ? (
        <div className="card divide-y divide-slate-100">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="px-4 py-3 flex gap-4 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-32" />
              <div className="h-4 bg-slate-200 rounded flex-1" />
            </div>
          ))}
        </div>
      ) : entradas.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-14 text-center">
          <Upload className="h-8 w-8 text-slate-300 mb-2" aria-hidden="true" />
          <p className="text-sm text-slate-500">Nenhuma entrada registrada. Importe um XML ou crie uma entrada manual.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">NF-e</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Fornecedor</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Data</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Valor</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Itens</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wide">Origem</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {entradas.map((entrada) => {
                const origem = ORIGEM_BADGE[entrada.origem_entrada ?? 'XML_UPLOAD'];
                return (
                  <tr key={entrada.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">
                      {entrada.numero_nfe ? `${entrada.numero_nfe}/${entrada.serie_nfe}` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900 truncate max-w-[200px]">{entrada.fornecedor_nome || '—'}</p>
                      <p className="text-xs text-slate-400">{entrada.fornecedor_cnpj}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-600 text-xs">{fmtDate(entrada.data_entrada)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{fmtCurrency(entrada.valor_total_entrada)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{entrada.itens.length}</td>
                    <td className="px-4 py-3 text-center">
                      {origem && (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${origem.cls}`}>
                          {origem.icon}
                          {origem.label}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={STATUS_ENTRADA_BADGE[entrada.status] ?? 'badge badge-gray'}>
                        {entrada.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {entrada.status === 'PENDENTE' && (
                        <button
                          className="btn-secondary text-xs py-1 px-2"
                          onClick={() => confirmar.mutate(entrada.id)}
                          disabled={confirmar.isPending}
                        >
                          <CheckCircle className="h-3 w-3" />
                          Confirmar
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = 'estoque' | 'lotes' | 'entradas' | 'produtos';

// ---------------------------------------------------------------------------
// ProdutosTab — CRUD de ProdutoBase
// ---------------------------------------------------------------------------

const TIPO_LABEL: Record<string, string> = {
  SIMPLES: 'Simples',
  COMPOSTO: 'Composto',
  INSUMO: 'Insumo',
  KIT: 'Kit',
};

function ProdutosTab(): React.ReactElement {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterCategoria, setFilterCategoria] = useState('');
  const [filterMarca, setFilterMarca] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ProdutoBase | null>(null);
  const [form, setForm] = useState<Partial<ProdutoBasePayload>>({
    tipo_produto: 'SIMPLES',
    ativo: true,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['produtos', search, filterCategoria, filterMarca],
    queryFn: () => {
      const params: Parameters<typeof inventoryAPI.produtos.list>[0] = {};
      if (search) params.search = search;
      if (filterCategoria) params.categoria_id = Number(filterCategoria);
      if (filterMarca) params.marca_id = Number(filterMarca);
      return inventoryAPI.produtos.list(params);
    },
  });

  const { data: categorias = [] } = useQuery({
    queryKey: ['categorias'],
    queryFn: () => inventoryAPI.categorias.list(),
  });

  const { data: marcas = [] } = useQuery({
    queryKey: ['marcas'],
    queryFn: () => inventoryAPI.marcas.list(),
  });

  const saveMutation = useMutation({
    mutationFn: (payload: ProdutoBasePayload) =>
      editing
        ? inventoryAPI.produtos.update(editing.id, payload)
        : inventoryAPI.produtos.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['produtos'] });
      closeModal();
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => inventoryAPI.produtos.deactivate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['produtos'] }),
  });

  function openCreate() {
    setEditing(null);
    setForm({ tipo_produto: 'SIMPLES', ativo: true });
    setModalOpen(true);
  }

  function openEdit(p: ProdutoBase) {
    setEditing(p);
    setForm({
      codigo: p.codigo,
      nome: p.nome,
      descricao: p.descricao ?? '',
      categoria: p.categoria,
      marca: p.marca,
      tipo_produto: p.tipo_produto,
      base_tintometrica: p.base_tintometrica ?? '',
      linha_produto: p.linha_produto ?? '',
      ativo: p.ativo,
    });
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setEditing(null);
    setForm({ tipo_produto: 'SIMPLES', ativo: true });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.codigo || !form.nome || !form.categoria || !form.marca || !form.tipo_produto) return;
    saveMutation.mutate(form as ProdutoBasePayload);
  }

  const produtos: ProdutoBase[] = (data as { results?: ProdutoBase[] } | ProdutoBase[] | undefined)
    ? Array.isArray(data) ? data : (data as { results: ProdutoBase[] }).results ?? []
    : [];

  return (
    <>
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            placeholder="Buscar por código ou nome…"
            className="form-input pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="relative">
          <select
            className="form-input appearance-none pr-8 min-w-[140px]"
            value={filterCategoria}
            onChange={(e) => setFilterCategoria(e.target.value)}
          >
            <option value="">Todas categorias</option>
            {(categorias as Categoria[]).map((c) => (
              <option key={c.id} value={String(c.id)}>{c.nome}</option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
        </div>
        <div className="relative">
          <select
            className="form-input appearance-none pr-8 min-w-[120px]"
            value={filterMarca}
            onChange={(e) => setFilterMarca(e.target.value)}
          >
            <option value="">Todas marcas</option>
            {(marcas as Marca[]).map((m) => (
              <option key={m.id} value={String(m.id)}>{m.nome}</option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
        </div>
        <button className="btn-primary self-start" onClick={openCreate}>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Novo Produto
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Código</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Nome</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Categoria</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Marca</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Tipo</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Variações</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-500">Carregando…</td></tr>
              ) : produtos.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-500">Nenhum produto encontrado.</td></tr>
              ) : produtos.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{p.codigo}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{p.nome}</td>
                  <td className="px-4 py-3 text-slate-600">{p.categoria_nome}</td>
                  <td className="px-4 py-3 text-slate-600">{p.marca_nome}</td>
                  <td className="px-4 py-3">
                    <span className="badge badge-blue">{TIPO_LABEL[p.tipo_produto] ?? p.tipo_produto}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 tabular-nums">{p.variacoes.length}</td>
                  <td className="px-4 py-3">
                    <span className={p.ativo ? 'badge badge-green' : 'badge badge-red'}>
                      {p.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        className="btn-ghost text-xs"
                        onClick={() => openEdit(p)}
                        aria-label={`Editar ${p.nome}`}
                      >
                        <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
                        Editar
                      </button>
                      {p.ativo && (
                        <button
                          className="btn-ghost text-xs text-rose-600 hover:text-rose-800"
                          onClick={() => {
                            if (confirm(`Desativar "${p.nome}"?`)) deactivateMutation.mutate(p.id);
                          }}
                          aria-label={`Desativar ${p.nome}`}
                        >
                          <Archive className="h-3.5 w-3.5" aria-hidden="true" />
                          Desativar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {modalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="produto-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        >
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 id="produto-modal-title" className="text-lg font-semibold">
                {editing ? 'Editar Produto' : 'Novo Produto'}
              </h2>
              <button onClick={closeModal} className="btn-ghost" aria-label="Fechar">
                <XCircle className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="p-codigo">Código *</label>
                  <input
                    id="p-codigo"
                    className="form-input"
                    required
                    value={form.codigo ?? ''}
                    onChange={(e) => setForm((f) => ({ ...f, codigo: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="label" htmlFor="p-tipo">Tipo *</label>
                  <select
                    id="p-tipo"
                    className="form-input"
                    required
                    value={form.tipo_produto ?? 'SIMPLES'}
                    onChange={(e) => setForm((f) => ({ ...f, tipo_produto: e.target.value as ProdutoBasePayload['tipo_produto'] }))}
                  >
                    <option value="SIMPLES">Simples</option>
                    <option value="COMPOSTO">Composto (Tinta)</option>
                    <option value="INSUMO">Insumo (Pigmento)</option>
                    <option value="KIT">Kit</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="label" htmlFor="p-nome">Nome *</label>
                <input
                  id="p-nome"
                  className="form-input"
                  required
                  value={form.nome ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label" htmlFor="p-categoria">Categoria *</label>
                  <select
                    id="p-categoria"
                    className="form-input"
                    required
                    value={form.categoria ?? ''}
                    onChange={(e) => setForm((f) => ({ ...f, categoria: Number(e.target.value) }))}
                  >
                    <option value="">Selecione…</option>
                    {(categorias as Categoria[]).map((c) => (
                      <option key={c.id} value={c.id}>{c.nome}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label" htmlFor="p-marca">Marca *</label>
                  <select
                    id="p-marca"
                    className="form-input"
                    required
                    value={form.marca ?? ''}
                    onChange={(e) => setForm((f) => ({ ...f, marca: Number(e.target.value) }))}
                  >
                    <option value="">Selecione…</option>
                    {(marcas as Marca[]).map((m) => (
                      <option key={m.id} value={m.id}>{m.nome}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="label" htmlFor="p-linha">Linha do Produto</label>
                <input
                  id="p-linha"
                  className="form-input"
                  value={form.linha_produto ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, linha_produto: e.target.value }))}
                />
              </div>
              <div>
                <label className="label" htmlFor="p-base">Base Tintométrica</label>
                <input
                  id="p-base"
                  className="form-input"
                  value={form.base_tintometrica ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, base_tintometrica: e.target.value }))}
                />
              </div>
              {saveMutation.isError && (
                <p className="text-sm text-rose-600">
                  {(saveMutation.error as Error)?.message ?? 'Erro ao salvar produto.'}
                </p>
              )}
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" className="btn-secondary" onClick={closeModal}>Cancelar</button>
                <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
                  {saveMutation.isPending ? 'Salvando…' : editing ? 'Salvar Alterações' : 'Criar Produto'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default function EstoquePage(): React.ReactElement {
  const [tab, setTab] = useState<Tab>('produtos');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // For now use loja_id=1 (first store). TODO: store selector when multi-store.
  const loja_id = 1;

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: 'produtos', label: 'Produtos', icon: Package },
    { key: 'estoque', label: 'Saldo por Loja', icon: Archive },
    { key: 'lotes', label: 'Validade', icon: Clock },
    { key: 'entradas', label: 'Entradas NF-e', icon: Upload },
  ];

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Controle de Estoque</h1>
          <p className="text-sm text-slate-500 mt-0.5">Produtos, lotes, validade e entradas de mercadoria</p>
        </div>
        <button
          className="btn-primary self-start sm:self-auto"
          onClick={() => setTab('entradas')}
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Entrada de Estoque
        </button>
      </div>

      {/* Summary cards */}
      <SummaryCards loja_id={loja_id} />

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1" aria-label="Abas de estoque">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === key
                  ? 'border-teal-600 text-teal-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {tab === 'estoque' && (
        <div className="space-y-4">
          {/* Toolbar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400"
                aria-hidden="true"
              />
              <input
                type="search"
                placeholder="Buscar por código, nome ou produto base…"
                className="form-input pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="relative">
              <select
                className="form-input appearance-none pr-8 min-w-[140px]"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">Todos os status</option>
                <option value="NORMAL">Normal</option>
                <option value="BAIXO">Estoque Baixo</option>
                <option value="ZERADO">Sem Estoque</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
            </div>
          </div>
          <EstoqueTable search={search} statusFilter={statusFilter} loja_id={loja_id} />
        </div>
      )}

      {tab === 'produtos' && <ProdutosTab />}
      {tab === 'lotes' && <LotesTab loja_id={loja_id} />}
      {tab === 'entradas' && <EntradasTab loja_id={loja_id} />}
    </div>
  );
}
