import React, { useState, useRef } from 'react';
import {
  Package,
  Plus,
  Search,
  AlertTriangle,
  XCircle,
  Clock,
  Upload,
  CheckCircle,
  ChevronDown,
  RefreshCw,
} from 'lucide-react';
import {
  useEstoqueResumo,
  useEstoqueLoja,
  useLotesProximosVencimento,
  useEntradas,
  useImportarXmlNFe,
  useConfirmarEntrada,
} from '@/hooks/useInventory';
import type { EstoqueLojaItem, LoteProduto, EntradaMercadoria, StatusEstoque } from '@/types';

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
      )}
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

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
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
          <p className="text-sm text-slate-500">Nenhuma entrada registrada. Importe um XML de NF-e.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">NF-e</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Fornecedor</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Data</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Valor</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Itens</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {entradas.map((entrada) => (
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
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = 'estoque' | 'lotes' | 'entradas';

export default function EstoquePage(): React.ReactElement {
  const [tab, setTab] = useState<Tab>('estoque');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // For now use loja_id=1 (first store). TODO: store selector when multi-store.
  const loja_id = 1;

  const tabs: { key: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { key: 'estoque', label: 'Produtos', icon: Package },
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

      {tab === 'lotes' && <LotesTab loja_id={loja_id} />}
      {tab === 'entradas' && <EntradasTab loja_id={loja_id} />}
    </div>
  );
}
