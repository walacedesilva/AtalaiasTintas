import { useEffect } from 'react';
import { Printer, X } from 'lucide-react';
import { usePrint } from '@/hooks/usePrint';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  /** Conteúdo a ser visualizado e impresso (OrcamentoPrintLayout ou ReciboPrintLayout) */
  children: React.ReactNode;
  /** Classe de z-index Tailwind. Padrão: 'z-50' */
  zClassName?: string;
}

/**
 * Modal de pré-visualização antes de imprimir.
 *
 * O conteúdo (children) é renderizado tanto na pré-visualização quanto
 * durante window.print() graças às regras CSS em print.css.
 *
 * Estratégia de impressão:
 * - O children contém um elemento com className="print-root"
 * - @media print: oculta #root, exibe apenas .print-root
 */
export function PrintPreviewModal({ isOpen, onClose, title, children, zClassName = 'z-50' }: Props) {
  const { triggerPrint } = usePrint();

  // Fecha com ESC
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className={`fixed inset-0 ${zClassName} flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-8 backdrop-blur-sm`}
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div className="w-full max-w-3xl rounded-xl bg-white shadow-2xl">
          {/* ── Header ── */}
          <div className="flex items-center justify-between rounded-t-xl border-b border-slate-200 bg-slate-50 px-6 py-4">
            <div className="flex items-center gap-3">
              <Printer className="h-5 w-5 text-slate-600" />
              <h2 className="text-base font-semibold text-slate-800">{title}</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={triggerPrint}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <Printer className="h-4 w-4" />
                Imprimir
              </button>
              <button
                onClick={onClose}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-300"
              >
                <X className="h-4 w-4" />
                Fechar
              </button>
            </div>
          </div>

          {/* ── Preview area ── */}
          <div className="overflow-auto p-6">
            {/* Simula fundo de papel A4 */}
            <div
              className="print-preview-container mx-auto rounded border border-slate-200 bg-white p-8 shadow-sm"
              style={{ minHeight: '600px', width: '100%', maxWidth: '794px' }}
            >
              {children}
            </div>
          </div>

          {/* ── Footer ── */}
          <div className="flex items-center justify-end gap-3 rounded-b-xl border-t border-slate-200 bg-slate-50 px-6 py-3">
            <span className="text-xs text-slate-500">
              A pré-visualização pode diferir ligeiramente do resultado impresso.
            </span>
            <button
              onClick={triggerPrint}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              <Printer className="h-4 w-4" />
              Imprimir
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
