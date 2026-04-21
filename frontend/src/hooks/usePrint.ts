import { useCallback } from 'react';

/**
 * Hook para impressão de documentos via window.print().
 *
 * O componente de impressão deve estar presente no DOM com a classe
 * `print-root` e ser visível apenas durante a impressão (via CSS @media print).
 *
 * Uso:
 *   const { triggerPrint } = usePrint();
 *   // ... render <div className="print-root" id="my-doc">...</div>
 *   <button onClick={() => triggerPrint()}>Imprimir</button>
 */
export function usePrint() {
  const triggerPrint = useCallback(() => {
    // Garante que o browser renderizou antes de abrir o diálogo
    requestAnimationFrame(() => {
      window.print();
    });
  }, []);

  return { triggerPrint };
}
