/**
 * T040 — CarrinhoTable: editable PDV cart with keyboard support.
 */
import { useRef } from 'react';
import { Trash2, Package2 } from 'lucide-react';
import type { PDVCartItem } from '@/types';

interface CarrinhoTableProps {
  items: PDVCartItem[];
  onUpdate: (produto_variacao_id: string, qty: string) => void;
  onRemove: (produto_variacao_id: string) => void;
}

const fmt = (v: string) =>
  parseFloat(v || '0').toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export default function CarrinhoTable({ items, onUpdate, onRemove }: CarrinhoTableProps) {
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 py-12 text-center">
        <Package2 className="mb-2 h-10 w-10 text-slate-300" aria-hidden="true" />
        <p className="text-sm text-slate-400">Carrinho vazio</p>
        <p className="text-xs text-slate-300">Busque um produto para adicionar</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="grid" aria-label="Carrinho de compras">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-slate-500">Produto</th>
              <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-slate-500">Qtde</th>
              <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-slate-500">Unit.</th>
              <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-slate-500">Total</th>
              <th scope="col" className="px-2 py-2 text-center text-xs font-medium text-slate-500">
                <span className="sr-only">Remover</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr
                key={item.produto_variacao_id}
                ref={(el) => { rowRefs.current[i] = el; }}
                className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
                onKeyDown={(e) => {
                  if (e.key === 'Delete') onRemove(item.produto_variacao_id);
                }}
                tabIndex={0}
                aria-label={`Item ${item.nome}`}
              >
                <td className="px-3 py-2">
                  <div className="font-medium text-slate-800">{item.nome}</div>
                  <div className="text-[11px] text-slate-400">{item.sku}</div>
                </td>
                <td className="px-3 py-2">
                  <input
                    type="number"
                    value={item.quantidade}
                    min="0.001"
                    step="1"
                    onChange={(e) => onUpdate(item.produto_variacao_id, e.target.value)}
                    className="w-20 rounded-lg border border-slate-200 px-2 py-1 text-right text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    aria-label={`Quantidade de ${item.nome}`}
                  />
                </td>
                <td className="px-3 py-2 text-right text-slate-600">
                  {fmt(item.preco_unitario)}
                </td>
                <td className="px-3 py-2 text-right font-medium text-slate-800">
                  {fmt(item.preco_total)}
                </td>
                <td className="px-2 py-2 text-center">
                  <button
                    type="button"
                    onClick={() => onRemove(item.produto_variacao_id)}
                    className="rounded-lg p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-500"
                    aria-label={`Remover ${item.nome}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
