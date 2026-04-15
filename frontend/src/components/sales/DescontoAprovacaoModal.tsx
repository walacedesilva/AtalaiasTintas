/**
 * T042 — DescontoAprovacaoModal: PIN-protected discount approval with focus trap.
 */
import { useEffect, useRef, useState } from 'react';
import { X, ShieldCheck, AlertTriangle } from 'lucide-react';
import { salesAPI } from '@/api/sales';
import type { AprovarDescontoPayload } from '@/types';

interface AprovadorOption {
  id: number;
  username: string;
  label: string;
}

interface DescontoAprovacaoModalProps {
  pedidoId: number;
  percentual: string;
  nivel: 'gerente' | 'diretor';
  tipo: 'TOTAL' | 'ITEM';
  itemId?: number;
  aprovadores: AprovadorOption[];
  onSuccess: () => void;
  onClose: () => void;
}

const MAX_TENTATIVAS = 3;

export default function DescontoAprovacaoModal({
  pedidoId,
  percentual,
  nivel,
  tipo,
  itemId,
  aprovadores,
  onSuccess,
  onClose,
}: DescontoAprovacaoModalProps) {
  const [aprovadorId, setAprovadorId] = useState<number | ''>(
    aprovadores.length === 1 ? aprovadores[0].id : ''
  );
  const [pin, setPin] = useState('');
  const [motivo, setMotivo] = useState('');
  const [tentativas, setTentativas] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const dialogRef = useRef<HTMLDivElement>(null);
  const pinRef = useRef<HTMLInputElement>(null);

  // Focus trap + initial focus
  useEffect(() => {
    pinRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); return; }
      if (e.key !== 'Tab') return;

      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const bloqueado = tentativas >= MAX_TENTATIVAS;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (bloqueado || !aprovadorId) return;
    if (!motivo.trim()) { setError('Motivo obrigatório'); return; }
    if (!pin) { setError('PIN obrigatório'); return; }

    setIsLoading(true);
    setError('');

    const payload: AprovarDescontoPayload = {
      percentual,
      motivo: motivo.trim(),
      pin,
      aprovador_id: aprovadorId as number,
      tipo,
      ...(itemId !== undefined ? { item_id: itemId } : {}),
    };

    try {
      await salesAPI.pedidos.aprovarDesconto(pedidoId, payload);
      onSuccess();
    } catch (err: unknown) {
      const tries = tentativas + 1;
      setTentativas(tries);
      if (tries >= MAX_TENTATIVAS) {
        setError('Número máximo de tentativas atingido. Contate o administrador.');
      } else {
        const msg = (err as { message?: string })?.message || 'PIN incorreto ou sem permissão';
        setError(`${msg} (tentativa ${tries}/${MAX_TENTATIVAS})`);
      }
      setPin('');
      pinRef.current?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      aria-modal="true"
      role="dialog"
      aria-labelledby="desconto-modal-title"
    >
      <div
        ref={dialogRef}
        className="w-full max-w-md rounded-2xl bg-white shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50">
              <ShieldCheck className="h-5 w-5 text-amber-600" aria-hidden="true" />
            </div>
            <div>
              <h2 id="desconto-modal-title" className="text-base font-semibold text-slate-900">
                Aprovação de Desconto
              </h2>
              <p className="text-xs text-slate-500">
                {percentual}% — nível: <span className="font-medium capitalize">{nivel}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Fechar modal"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* Aprovador */}
          <div>
            <label htmlFor="aprovador" className="block text-sm font-medium text-slate-700 mb-1">
              Aprovador ({nivel})
            </label>
            <select
              id="aprovador"
              value={aprovadorId}
              onChange={(e) => setAprovadorId(Number(e.target.value))}
              className="form-input w-full"
              required
              disabled={bloqueado}
            >
              <option value="">Selecione o aprovador…</option>
              {aprovadores.map((a) => (
                <option key={a.id} value={a.id}>{a.label}</option>
              ))}
            </select>
          </div>

          {/* Motivo */}
          <div>
            <label htmlFor="motivo" className="block text-sm font-medium text-slate-700 mb-1">
              Motivo
            </label>
            <input
              id="motivo"
              type="text"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              className="form-input w-full"
              placeholder="Justifique o desconto…"
              required
              disabled={bloqueado}
            />
          </div>

          {/* PIN */}
          <div>
            <label htmlFor="pin-input" className="block text-sm font-medium text-slate-700 mb-1">
              PIN do aprovador
              <span className="ml-2 text-xs text-slate-400" aria-live="polite">
                {tentativas > 0 && !bloqueado && `(${tentativas}/${MAX_TENTATIVAS} tentativas)`}
              </span>
            </label>
            <input
              ref={pinRef}
              id="pin-input"
              type="password"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="form-input w-full font-mono tracking-widest"
              placeholder="••••"
              autoComplete="current-password"
              required
              disabled={bloqueado}
              aria-describedby={error ? 'pin-error' : undefined}
            />
          </div>

          {/* Error */}
          {error && (
            <div id="pin-error" className="flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
              <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading || bloqueado || !aprovadorId}
              className="btn-primary disabled:opacity-50"
            >
              {isLoading ? 'Aprovando…' : 'Aprovar desconto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
