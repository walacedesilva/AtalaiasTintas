import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShoppingCart,
  Search,
  Filter,
  RefreshCw,
  XCircle,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Ban,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { salesAPI } from '@/api/sales';
import type { Venda, NfeSituacao } from '@/types';

// ─── NFe Status badge ─────────────────────────────────────────────────────────
const NFE_CONFIG: Record<
  NfeSituacao,
  { label: string; className: string; icon: React.ReactNode }
> = {
  EMITIDA: {
    label: 'Emitida',
    className: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  PENDENTE: {
    label: 'Pendente',
    className: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    icon: <Clock className="h-3 w-3" />,
  },
  CANCELADA: {
    label: 'Cancelada',
    className: 'bg-red-50 text-red-700 ring-1 ring-red-200',
    icon: <Ban className="h-3 w-3" />,
  },
  REJEITADA: {
    label: 'Rejeitada',
    className: 'bg-rose-50 text-rose-700 ring-1 ring-rose-200',
    icon: <AlertTriangle className="h-3 w-3" />,
  },
  NAO_APLICAVEL: {
    label: 'N/A',
    className: 'bg-slate-100 text-slate-500 ring-1 ring-slate-200',
    icon: <FileText className="h-3 w-3" />,
  },
};

function NfeBadge({ situacao }: { situacao: NfeSituacao }) {
  const cfg = NFE_CONFIG[situacao] ?? NFE_CONFIG.NAO_APLICAVEL;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cfg.className}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ─── Cancel modal ─────────────────────────────────────────────────────────────
interface CancelModalProps {
  venda: Venda;
  onConfirm: (motivo: string) => void;
  onClose: () => void;
  isPending: boolean;
}

function CancelModal({ venda, onConfirm, onClose, isPending }: CancelModalProps) {
  const [motivo, setMotivo] = useState('');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-50">
            <XCircle className="h-5 w-5 text-red-600" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Cancelar Venda</h2>
            <p className="text-sm text-slate-500">Nº {venda.numero_venda}</p>
          </div>
        </div>
        <p className="mb-4 text-sm text-slate-600">
          Esta ação não pode ser desfeita. Informe o motivo do cancelamento.
        </p>
        <textarea
          className="form-input w-full resize-none"
          rows={3}
          placeholder="Motivo do cancelamento…"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          autoFocus
        />
        <div className="mt-4 flex justify-end gap-2">
          <button className="btn-secondary" onClick={onClose} disabled={isPending}>
            Voltar
          </button>
          <button
            className="btn-danger"
            disabled={!motivo.trim() || isPending}
            onClick={() => onConfirm(motivo.trim())}
          >
            {isPending ? 'Cancelando…' : 'Confirmar cancelamento'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function VendasPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState('');
  const [nfeSituacao, setNfeSituacao] = useState('');
  const [mostrarCanceladas, setMostrarCanceladas] = useState(false);
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [page, setPage] = useState(1);

  const [selectedVenda, setSelectedVenda] = useState<Venda | null>(null);

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['vendas', search, nfeSituacao, mostrarCanceladas, dataInicio, dataFim, page],
    queryFn: () =>
      salesAPI.vendas.list({
        search: search || undefined,
        nfe_situacao: nfeSituacao || undefined,
        cancelada: mostrarCanceladas ? undefined : false,
        data_inicio: dataInicio || undefined,
        data_fim: dataFim || undefined,
        page,
        page_size: 20,
      }),
    staleTime: 30_000,
  });

  const cancelMutation = useMutation({
    mutationFn: ({ id, motivo }: { id: string; motivo: string }) =>
      salesAPI.vendas.cancel(id, motivo),
    onSuccess: () => {
      toast.success('Venda cancelada com sucesso.');
      setSelectedVenda(null);
      qc.invalidateQueries({ queryKey: ['vendas'] });
    },
    onError: () => toast.error('Erro ao cancelar a venda.'),
  });

  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  const formatCurrency = (value: string) =>
    parseFloat(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  return (
    <>
      {/* Cancel modal */}
      {selectedVenda && (
        <CancelModal
          venda={selectedVenda}
          onClose={() => setSelectedVenda(null)}
          onConfirm={(motivo) => cancelMutation.mutate({ id: selectedVenda.id, motivo })}
          isPending={cancelMutation.isPending}
        />
      )}

      <div className="flex-1 overflow-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600">
              <ShoppingCart className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Vendas</h1>
              <p className="text-sm text-slate-500">
                {data ? `${data.count} registro${data.count !== 1 ? 's' : ''}` : ''}
              </p>
            </div>
          </div>
          <button
            className="btn-secondary flex items-center gap-2"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>

        {/* Filters */}
        <div className="mb-4 flex flex-wrap gap-3">
          <label className="relative flex flex-1 min-w-[200px] items-center">
            <Search className="absolute left-3 h-4 w-4 text-slate-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Buscar por nº venda ou cliente…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="form-input pl-9 w-full"
            />
          </label>

          <select
            value={nfeSituacao}
            onChange={(e) => { setNfeSituacao(e.target.value); setPage(1); }}
            className="form-input min-w-[160px]"
          >
            <option value="">Todas NF-e</option>
            <option value="PENDENTE">Pendente</option>
            <option value="EMITIDA">Emitida</option>
            <option value="CANCELADA">Cancelada</option>
            <option value="REJEITADA">Rejeitada</option>
            <option value="NAO_APLICAVEL">N/A</option>
          </select>

          <input
            type="date"
            value={dataInicio}
            onChange={(e) => { setDataInicio(e.target.value); setPage(1); }}
            className="form-input"
            title="Data início"
          />
          <input
            type="date"
            value={dataFim}
            onChange={(e) => { setDataFim(e.target.value); setPage(1); }}
            className="form-input"
            title="Data fim"
          />

          <label className="flex items-center gap-2 cursor-pointer select-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
            <input
              type="checkbox"
              checked={mostrarCanceladas}
              onChange={(e) => { setMostrarCanceladas(e.target.checked); setPage(1); }}
              className="h-4 w-4 rounded accent-brand-600"
            />
            Mostrar canceladas
          </label>

          {(search || nfeSituacao || dataInicio || dataFim || mostrarCanceladas) && (
            <button
              className="btn-ghost flex items-center gap-1 text-sm"
              onClick={() => {
                setSearch('');
                setNfeSituacao('');
                setDataInicio('');
                setDataFim('');
                setMostrarCanceladas(false);
                setPage(1);
              }}
            >
              <Filter className="h-3.5 w-3.5" />
              Limpar filtros
            </button>
          )}
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Nº Venda</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Cliente</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Data</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600">Valor</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">NF-e</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">Status</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600">Ações</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-slate-100 animate-pulse">
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 rounded bg-slate-100" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : data?.results.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-16 text-center">
                      <ShoppingCart className="mx-auto mb-3 h-10 w-10 text-slate-200" />
                      <p className="text-sm text-slate-400">Nenhuma venda encontrada</p>
                    </td>
                  </tr>
                ) : (
                  data?.results.map((venda) => (
                    <tr
                      key={venda.id}
                      className={`border-b border-slate-100 transition-colors hover:bg-slate-50 ${
                        venda.cancelada ? 'opacity-60' : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-mono text-xs font-medium text-slate-900">
                        {venda.numero_venda}
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {venda.cliente_nome || (
                          <span className="text-slate-400 italic">Consumidor</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                        {formatDate(venda.data_venda)}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-slate-900">
                        {formatCurrency(venda.valor_liquido)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <NfeBadge situacao={venda.nfe_situacao} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        {venda.cancelada ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 ring-1 ring-red-200">
                            <XCircle className="h-3 w-3" />
                            Cancelada
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
                            <CheckCircle2 className="h-3 w-3" />
                            Ativa
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {!venda.cancelada && (
                          <button
                            className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-white px-2.5 py-1 text-xs font-medium text-red-600 transition hover:bg-red-50"
                            onClick={() => setSelectedVenda(venda)}
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            Cancelar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-4 py-3">
              <span className="text-xs text-slate-500">
                Página {page} de {totalPages} · {data?.count} registros
              </span>
              <div className="flex gap-1">
                <button
                  className="btn-secondary px-3 py-1 text-xs"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Anterior
                </button>
                <button
                  className="btn-secondary px-3 py-1 text-xs"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Próxima
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
