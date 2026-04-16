import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Ban,
  Search,
  RotateCcw,
  Send,
  Wifi,
  WifiOff,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { fiscalAPI } from '@/api/fiscal';

// ─── Types ─────────────────────────────────────────────────────────────────
type NfeSituacao =
  | 'EMITIDA'
  | 'PENDENTE'
  | 'PROCESSANDO'
  | 'CANCELADA'
  | 'REJEITADA'
  | 'ERRO_TECNICO'
  | 'AGUARDANDO_RETRY'
  | 'NAO_APLICAVEL';

interface NotaFiscal {
  id: number;
  numero: string | null;
  serie: string | null;
  chave_acesso: string | null;
  situacao: NfeSituacao;
  tipo_nota: string;
  valor_total_nota: string;
  data_emissao: string | null;
  data_autorizacao: string | null;
  protocolo_autorizacao: string | null;
  motivo_cancelamento: string | null;
}

interface VendaNfe {
  id: number;
  numero_venda: string;
  nfe_situacao: NfeSituacao;
  nfe_erro?: string;
  nfe_tentativas?: number;
  nfe_ultima_tentativa?: string;
  nfe_requer_retry_manual?: boolean;
}

// ─── Status config ─────────────────────────────────────────────────────────
const STATUS_CONFIG: Record<NfeSituacao, { label: string; className: string; icon: React.ReactNode }> = {
  EMITIDA:          { label: 'Emitida',         className: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200', icon: <CheckCircle2 className="h-3 w-3" /> },
  PENDENTE:         { label: 'Pendente',         className: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',      icon: <Clock className="h-3 w-3" /> },
  PROCESSANDO:      { label: 'Processando',      className: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200',         icon: <RefreshCw className="h-3 w-3 animate-spin" /> },
  CANCELADA:        { label: 'Cancelada',        className: 'bg-red-50 text-red-700 ring-1 ring-red-200',            icon: <Ban className="h-3 w-3" /> },
  REJEITADA:        { label: 'Rejeitada',        className: 'bg-rose-50 text-rose-700 ring-1 ring-rose-200',         icon: <AlertTriangle className="h-3 w-3" /> },
  ERRO_TECNICO:     { label: 'Erro Técnico',     className: 'bg-rose-50 text-rose-700 ring-1 ring-rose-200',         icon: <AlertTriangle className="h-3 w-3" /> },
  AGUARDANDO_RETRY: { label: 'Aguard. Retry',    className: 'bg-orange-50 text-orange-700 ring-1 ring-orange-200',   icon: <Clock className="h-3 w-3" /> },
  NAO_APLICAVEL:    { label: 'N/A',              className: 'bg-slate-100 text-slate-500 ring-1 ring-slate-200',     icon: <FileText className="h-3 w-3" /> },
};

function NfeBadge({ situacao }: { situacao: NfeSituacao }) {
  const cfg = STATUS_CONFIG[situacao] ?? STATUS_CONFIG.NAO_APLICAVEL;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cfg.className}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function fmt(date?: string | null) {
  if (!date) return '—';
  return new Date(date).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// ─── Main Page ──────────────────────────────────────────────────────────────
export default function NotaFiscalPage(): React.ReactElement {
  const qc = useQueryClient();
  const [tab, setTab] = useState<'notas' | 'pendentes' | 'falhadas'>('notas');
  const [search, setSearch] = useState('');

  // Notas Fiscais emitidas
  const { data: notas, isLoading: notasLoading, refetch: refetchNotas } = useQuery<NotaFiscal[]>({
    queryKey: ['notas-fiscais'],
    queryFn: () => fiscalAPI.listarNotas(),
    staleTime: 30_000,
  });

  // Vendas pendentes de NF-e
  const { data: pendentes, isLoading: pendentesLoading, refetch: refetchPendentes } = useQuery<VendaNfe[]>({
    queryKey: ['nfe-pendentes'],
    queryFn: () => fiscalAPI.pendentes(),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });

  // Vendas com NF-e falhada
  const { data: falhadas, isLoading: falhadasLoading, refetch: refetchFalhadas } = useQuery<VendaNfe[]>({
    queryKey: ['nfe-falhadas'],
    queryFn: () => fiscalAPI.falhadas(),
    staleTime: 15_000,
  });

  // Status SEFAZ
  const { data: sefazStatus } = useQuery<{ disponivel: boolean; ambiente?: string }>({
    queryKey: ['sefaz-status'],
    queryFn: () => fiscalAPI.statusSefaz(),
    staleTime: 60_000,
    retry: false,
  });

  // Mutations
  const emitirMutation = useMutation({
    mutationFn: (vendaId: string) => fiscalAPI.nfe.emitir(vendaId),
    onSuccess: (_, vendaId) => {
      toast.success(`NF-e agendada para venda #${vendaId}`);
      qc.invalidateQueries({ queryKey: ['nfe-pendentes'] });
      qc.invalidateQueries({ queryKey: ['nfe-falhadas'] });
    },
    onError: () => toast.error('Erro ao emitir NF-e'),
  });

  const reprocessarMutation = useMutation({
    mutationFn: (vendaId: string) => fiscalAPI.nfe.reprocessar(vendaId),
    onSuccess: (_, vendaId) => {
      toast.success(`NF-e reenviada para reprocessamento: venda #${vendaId}`);
      qc.invalidateQueries({ queryKey: ['nfe-falhadas'] });
    },
    onError: () => toast.error('Erro ao reprocessar NF-e'),
  });

  // Filtro local
  const notasFiltradas = (notas ?? []).filter((n) => {
    const q = search.toLowerCase();
    return (
      n.numero?.toLowerCase().includes(q) ||
      n.chave_acesso?.toLowerCase().includes(q) ||
      n.situacao.toLowerCase().includes(q)
    );
  });

  const refetchAll = () => { refetchNotas(); refetchPendentes(); refetchFalhadas(); };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Nota Fiscal Eletrônica</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestão de NF-e e NFC-e</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Status SEFAZ */}
          <div className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ring-1 ${
            sefazStatus?.disponivel
              ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
              : 'bg-rose-50 text-rose-700 ring-rose-200'
          }`}>
            {sefazStatus?.disponivel
              ? <><Wifi className="h-3.5 w-3.5" /> SEFAZ Online</>
              : <><WifiOff className="h-3.5 w-3.5" /> SEFAZ Offline</>
            }
          </div>
          <button
            onClick={refetchAll}
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 border border-slate-200 bg-white hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Atualizar
          </button>
        </div>
      </div>

      {/* Resumo cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="card p-4">
          <p className="text-xs text-slate-500">Notas Emitidas</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">
            {notasLoading ? '—' : (notas ?? []).filter(n => n.situacao === 'EMITIDA').length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-500">Pendentes</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">
            {pendentesLoading ? '—' : (pendentes ?? []).length}
          </p>
        </div>
        <div className="card p-4 col-span-2 sm:col-span-1">
          <p className="text-xs text-slate-500">Com Falha</p>
          <p className={`text-2xl font-bold mt-1 ${(falhadas ?? []).length > 0 ? 'text-rose-600' : 'text-slate-400'}`}>
            {falhadasLoading ? '—' : (falhadas ?? []).length}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1 -mb-px overflow-x-auto" aria-label="Abas">
          {([
            { id: 'notas',     label: 'Notas Fiscais',  count: (notas ?? []).length },
            { id: 'pendentes', label: 'Pendentes',      count: (pendentes ?? []).length },
            { id: 'falhadas',  label: 'Falhadas',       count: (falhadas ?? []).length },
          ] as const).map(({ id, label, count }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`shrink-0 flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === id
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
              {count > 0 && (
                <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold leading-none ${
                  tab === id ? 'bg-brand-100 text-brand-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  {count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab: Notas Fiscais */}
      {tab === 'notas' && (
        <div className="space-y-4">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Buscar por número, chave…"
              className="form-input pl-9 w-full"
            />
          </div>

          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Número</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Tipo</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Situação</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Valor</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide hidden sm:table-cell">Emissão</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide hidden md:table-cell">Protocolo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {notasLoading && (
                    <tr><td colSpan={6} className="py-12 text-center text-sm text-slate-400">Carregando…</td></tr>
                  )}
                  {!notasLoading && notasFiltradas.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-12 text-center">
                        <FileText className="mx-auto h-10 w-10 text-slate-300 mb-2" />
                        <p className="text-sm text-slate-400">Nenhuma nota fiscal encontrada</p>
                      </td>
                    </tr>
                  )}
                  {notasFiltradas.map(nota => (
                    <tr key={nota.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-slate-800">
                        {nota.numero ? `${nota.serie}-${nota.numero}` : '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{nota.tipo_nota}</td>
                      <td className="px-4 py-3"><NfeBadge situacao={nota.situacao} /></td>
                      <td className="px-4 py-3 text-right font-medium text-slate-800">
                        {nota.valor_total_nota
                          ? `R$ ${parseFloat(nota.valor_total_nota).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                          : '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-500 hidden sm:table-cell">{fmt(nota.data_emissao)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-400 hidden md:table-cell">
                        {nota.protocolo_autorizacao ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Pendentes */}
      {tab === 'pendentes' && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Venda</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Situação NF-e</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Tentativas</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide hidden sm:table-cell">Última tentativa</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pendentesLoading && (
                  <tr><td colSpan={5} className="py-12 text-center text-sm text-slate-400">Carregando…</td></tr>
                )}
                {!pendentesLoading && (pendentes ?? []).length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-12 text-center">
                      <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-300 mb-2" />
                      <p className="text-sm text-slate-400">Nenhuma NF-e pendente</p>
                    </td>
                  </tr>
                )}
                {(pendentes ?? []).map(v => (
                  <tr key={v.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-800">#{v.numero_venda}</td>
                    <td className="px-4 py-3"><NfeBadge situacao={v.nfe_situacao} /></td>
                    <td className="px-4 py-3 text-right text-slate-500">{v.nfe_tentativas ?? 0}</td>
                    <td className="px-4 py-3 text-slate-500 hidden sm:table-cell">{fmt(v.nfe_ultima_tentativa)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => emitirMutation.mutate(String(v.id))}
                        disabled={emitirMutation.isPending}
                        className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
                      >
                        <Send className="h-3 w-3" />
                        Emitir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Falhadas */}
      {tab === 'falhadas' && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Venda</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Situação</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide hidden sm:table-cell">Erro</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Tentativas</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {falhadasLoading && (
                  <tr><td colSpan={5} className="py-12 text-center text-sm text-slate-400">Carregando…</td></tr>
                )}
                {!falhadasLoading && (falhadas ?? []).length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-12 text-center">
                      <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-300 mb-2" />
                      <p className="text-sm text-slate-400">Nenhuma NF-e com falha</p>
                    </td>
                  </tr>
                )}
                {(falhadas ?? []).map(v => (
                  <tr key={v.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-800">#{v.numero_venda}</td>
                    <td className="px-4 py-3"><NfeBadge situacao={v.nfe_situacao} /></td>
                    <td className="px-4 py-3 text-xs text-rose-600 max-w-xs truncate hidden sm:table-cell">
                      {v.nfe_erro ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-500">{v.nfe_tentativas ?? 0}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => reprocessarMutation.mutate(String(v.id))}
                        disabled={reprocessarMutation.isPending}
                        className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-50 transition-colors"
                      >
                        <RotateCcw className="h-3 w-3" />
                        Reprocessar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
