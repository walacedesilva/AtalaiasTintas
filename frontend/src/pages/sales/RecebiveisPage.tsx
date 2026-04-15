/**
 * T045 — RecebiveisPage: receivables table with status badges, baixar + cancelar.
 * ACC-6: never color alone — always includes text label.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Receipt, Search, RefreshCw, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import toast from 'react-hot-toast';
import { salesAPI } from '@/api/sales';
import { companiesAPI } from '@/api/companies';
import type { Recebivel, SituacaoRecebivel, FormaPagamento, Loja } from '@/types';

// ─── Status badge (ACC-6: text + color) ──────────────────────────────────────

function dateDiffDays(iso: string): number {
  const now = new Date(); now.setHours(0, 0, 0, 0);
  const d = new Date(iso); d.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - now.getTime()) / 86_400_000);
}

function SituacaoBadge({ recebivel }: { recebivel: Recebivel }) {
  if (recebivel.situacao === 'PAGO') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
        <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
        PAGO
      </span>
    );
  }
  if (recebivel.situacao === 'CANCELADO') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500 ring-1 ring-slate-200">
        CANCELADO
      </span>
    );
  }
  if (recebivel.situacao === 'VENCIDO') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 ring-1 ring-rose-200">
        <AlertTriangle className="h-3 w-3" aria-hidden="true" />
        VENCIDO
      </span>
    );
  }
  // ABERTO or PARCIAL — check date
  const diff = dateDiffDays(recebivel.data_vencimento);
  if (diff < 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 ring-1 ring-rose-200">
        <AlertTriangle className="h-3 w-3" aria-hidden="true" />
        VENCIDO
      </span>
    );
  }
  if (diff === 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-amber-200">
        <Clock className="h-3 w-3" aria-hidden="true" />
        VENCE HOJE
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
      <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
      EM DIA
    </span>
  );
}

// ─── Baixar (register payment) modal ─────────────────────────────────────────

const FORMAS: Array<{ value: FormaPagamento; label: string }> = [
  { value: 'DINHEIRO', label: 'Dinheiro' },
  { value: 'PIX', label: 'PIX' },
  { value: 'CARTAO_DEBITO', label: 'Cartão Débito' },
  { value: 'CARTAO_CREDITO', label: 'Cartão Crédito' },
  { value: 'CREDIARIO', label: 'Crediário' },
  { value: 'TRANSFERENCIA', label: 'Transferência' },
];

function BaixarModal({
  recebivel,
  onClose,
  onSuccess,
}: {
  recebivel: Recebivel;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [valor, setValor] = useState(recebivel.valor_saldo);
  const [forma, setForma] = useState<FormaPagamento>('DINHEIRO');
  const [obs, setObs] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await salesAPI.recebiveis.baixar(recebivel.id, parseFloat(valor), forma, obs || undefined);
      toast.success('Pagamento registrado!');
      onSuccess();
    } catch (err: unknown) {
      toast.error((err as { message?: string })?.message || 'Erro ao registrar pagamento');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="baixar-title">
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-2xl">
        <div className="border-b border-slate-100 px-6 py-4">
          <h2 id="baixar-title" className="font-semibold text-slate-900">Registrar Pagamento</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {recebivel.cliente_nome} — vence {new Date(recebivel.data_vencimento).toLocaleDateString('pt-BR')}
          </p>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          <div>
            <label htmlFor="baixar-valor" className="block text-sm font-medium text-slate-700 mb-1">Valor recebido</label>
            <input id="baixar-valor" type="number" min="0.01" step="0.01" value={valor} onChange={(e) => setValor(e.target.value)} className="form-input w-full" required />
          </div>
          <div>
            <label htmlFor="baixar-forma" className="block text-sm font-medium text-slate-700 mb-1">Forma de pagamento</label>
            <select id="baixar-forma" value={forma} onChange={(e) => setForma(e.target.value as FormaPagamento)} className="form-input w-full">
              {FORMAS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="baixar-obs" className="block text-sm font-medium text-slate-700 mb-1">Observações</label>
            <input id="baixar-obs" type="text" value={obs} onChange={(e) => setObs(e.target.value)} className="form-input w-full" placeholder="Opcional" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
            <button type="submit" disabled={isLoading} className="btn-primary disabled:opacity-50">
              {isLoading ? 'Registrando…' : 'Confirmar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Cancelar confirmation ────────────────────────────────────────────────────

function CancelarModal({
  recebivel,
  onClose,
  onSuccess,
}: {
  recebivel: Recebivel;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [motivo, setMotivo] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!motivo.trim()) return;
    setIsLoading(true);
    try {
      await salesAPI.recebiveis.cancelar(recebivel.id, motivo.trim());
      toast.success('Recebível cancelado');
      onSuccess();
    } catch (err: unknown) {
      toast.error((err as { message?: string })?.message || 'Erro ao cancelar');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="cancelar-title">
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-2xl">
        <div className="border-b border-slate-100 px-6 py-4">
          <h2 id="cancelar-title" className="font-semibold text-slate-900">Cancelar Recebível</h2>
          <p className="text-xs text-slate-500 mt-0.5">{recebivel.cliente_nome}</p>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          <div>
            <label htmlFor="cancelar-motivo" className="block text-sm font-medium text-slate-700 mb-1">Motivo (obrigatório)</label>
            <input id="cancelar-motivo" type="text" value={motivo} onChange={(e) => setMotivo(e.target.value)} className="form-input w-full" required />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Voltar</button>
            <button type="submit" disabled={isLoading || !motivo.trim()} className="btn-primary bg-rose-600 hover:bg-rose-700 disabled:opacity-50">
              {isLoading ? 'Cancelando…' : 'Cancelar recebível'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function RecebiveisPage() {
  const qc = useQueryClient();

  const [situacao, setSituacao] = useState<SituacaoRecebivel | ''>('');
  const [lojaId, setLojaId] = useState<number | ''>('');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [search, setSearch] = useState('');

  const [baixarTarget, setBaixarTarget] = useState<Recebivel | null>(null);
  const [cancelarTarget, setCancelarTarget] = useState<Recebivel | null>(null);

  const { data: lojas = [] } = useQuery<Loja[]>({
    queryKey: ['companies', 'lojas'],
    queryFn: companiesAPI.lojas.list,
    staleTime: 60_000,
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['recebiveis', { situacao, lojaId, dataInicio, dataFim, search }],
    queryFn: () =>
      salesAPI.recebiveis.list({
        situacao: situacao || undefined,
        loja: lojaId || undefined,
        data_vencimento_inicio: dataInicio || undefined,
        data_vencimento_fim: dataFim || undefined,
        search: search || undefined,
      }),
    staleTime: 30_000,
  });

  const recebiveis: Recebivel[] = (data as { results?: Recebivel[] })?.results ?? (data as Recebivel[] | undefined) ?? [];

  const invalidate = () => qc.invalidateQueries({ queryKey: ['recebiveis'] });

  const fmt = (v: string) =>
    parseFloat(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
            <Receipt className="h-5 w-5 text-blue-600" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Recebíveis</h1>
            <p className="text-xs text-slate-500">{recebiveis.length} registro(s)</p>
          </div>
        </div>
        <button onClick={() => refetch()} className="btn-secondary flex items-center gap-1.5 text-sm" aria-label="Atualizar">
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Atualizar
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 rounded-2xl bg-slate-50 p-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar cliente…"
            className="form-input pl-8 text-sm"
            aria-label="Buscar por cliente"
          />
        </div>
        <select value={situacao} onChange={(e) => setSituacao(e.target.value as SituacaoRecebivel | '')} className="form-input text-sm" aria-label="Filtrar por situação">
          <option value="">Todas situações</option>
          <option value="ABERTO">Em aberto</option>
          <option value="PARCIAL">Parcialmente pago</option>
          <option value="PAGO">Pago</option>
          <option value="VENCIDO">Vencido</option>
          <option value="CANCELADO">Cancelado</option>
        </select>
        {lojas.length > 1 && (
          <select value={lojaId} onChange={(e) => setLojaId(Number(e.target.value) || '')} className="form-input text-sm" aria-label="Filtrar por loja">
            <option value="">Todas as lojas</option>
            {lojas.map((l) => <option key={l.id} value={l.id}>{l.nome}</option>)}
          </select>
        )}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500" htmlFor="data-inicio">De</label>
          <input id="data-inicio" type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} className="form-input text-sm" />
          <label className="text-xs text-slate-500" htmlFor="data-fim">Até</label>
          <input id="data-fim" type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} className="form-input text-sm" />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
        <table className="w-full text-sm" aria-label="Recebíveis">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
              <th className="px-4 py-3 text-left">Cliente</th>
              <th className="px-4 py-3 text-left">Vencimento</th>
              <th className="px-4 py-3 text-right">Valor original</th>
              <th className="px-4 py-3 text-right">Saldo</th>
              <th className="px-4 py-3 text-center">Situação</th>
              <th className="px-4 py-3 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">Carregando…</td>
              </tr>
            )}
            {!isLoading && recebiveis.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">Nenhum recebível encontrado</td>
              </tr>
            )}
            {recebiveis.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50/50">
                <td className="px-4 py-3 font-medium text-slate-800">{r.cliente_nome}</td>
                <td className="px-4 py-3 text-slate-600">
                  {new Date(r.data_vencimento).toLocaleDateString('pt-BR')}
                </td>
                <td className="px-4 py-3 text-right text-slate-600">{fmt(r.valor_original)}</td>
                <td className="px-4 py-3 text-right font-semibold text-slate-800">{fmt(r.valor_saldo)}</td>
                <td className="px-4 py-3 text-center">
                  <SituacaoBadge recebivel={r} />
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {(r.situacao === 'ABERTO' || r.situacao === 'PARCIAL' || r.situacao === 'VENCIDO') && (
                      <button onClick={() => setBaixarTarget(r)} className="btn-primary text-xs py-1 px-2">
                        Registrar pgto
                      </button>
                    )}
                    {r.situacao !== 'CANCELADO' && r.situacao !== 'PAGO' && (
                      <button onClick={() => setCancelarTarget(r)} className="btn-secondary text-xs py-1 px-2 text-rose-600 hover:bg-rose-50">
                        Cancelar
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {baixarTarget && (
        <BaixarModal
          recebivel={baixarTarget}
          onClose={() => setBaixarTarget(null)}
          onSuccess={() => { setBaixarTarget(null); invalidate(); }}
        />
      )}
      {cancelarTarget && (
        <CancelarModal
          recebivel={cancelarTarget}
          onClose={() => setCancelarTarget(null)}
          onSuccess={() => { setCancelarTarget(null); invalidate(); }}
        />
      )}
    </div>
  );
}
