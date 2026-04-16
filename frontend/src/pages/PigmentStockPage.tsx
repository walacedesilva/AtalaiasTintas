import React, { useState } from 'react';
import { Package, Plus, Search } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { tintometryAPI } from '@/api';
import { LowStockAlerts } from '@/components/tintometry/LowStockAlerts';
import { StockAvailabilityBadge } from '@/components/tintometry/StockAvailabilityBadge';
import type { EstoquePigmento } from '@/types';

// TODO: replace with real loja from auth context when available
const LOJA_ID = 1;

interface AddStockModalProps {
  pigmentoId: number;
  pigmentoNome: string;
  onClose: () => void;
}

function AddStockModal({ pigmentoId, pigmentoNome, onClose }: AddStockModalProps): React.ReactElement {
  const queryClient = useQueryClient();
  const [quantidade, setQuantidade] = useState('');
  const [observacoes, setObservacoes] = useState('');

  const mutation = useMutation({
    mutationFn: () =>
      tintometryAPI.estoque.addStock(pigmentoId, quantidade, observacoes || undefined),
    onSuccess: () => {
      toast.success('Estoque atualizado!');
      queryClient.invalidateQueries({ queryKey: ['tintometry', 'estoque'] });
      onClose();
    },
    onError: () => toast.error('Erro ao adicionar estoque'),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Adicionar Estoque — {pigmentoNome}
        </h2>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quantidade (ml) <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            min="1"
            step="1"
            value={quantidade}
            onChange={(e) => setQuantidade(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Ex: 500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Observações
          </label>
          <input
            type="text"
            value={observacoes}
            onChange={(e) => setObservacoes(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Compra, lote, etc."
          />
        </div>

        <div className="flex gap-3 pt-1">
          <button
            onClick={onClose}
            className="flex-1 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !quantidade}
            className="flex-1 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {mutation.isPending ? 'Adicionando...' : 'Confirmar'}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Pigment stock management page (/tintometry/stock).
 * Shows low-stock alerts at the top, then the full stock list with
 * availability badges and per-pigment add-stock action.
 */
export default function PigmentStockPage(): React.ReactElement {
  const [search, setSearch] = useState('');
  const [addStockFor, setAddStockFor] = useState<{ id: number; nome: string } | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['tintometry', 'estoque', 'list', search],
    queryFn: () =>
      tintometryAPI.estoque.list({
        ...(search ? { query: search } : {}),
        page_size: 100,
        ordering: 'pigmento__nome',
      }),
    staleTime: 60 * 1000,
  });

  const items: EstoquePigmento[] = data?.results ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Package className="w-7 h-7 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Estoque de Pigmentos</h1>
          <p className="text-sm text-gray-500">Gerencie o saldo de pigmentos por loja</p>
        </div>
      </div>

      {/* Low stock banner */}
      <LowStockAlerts lojaId={LOJA_ID} />

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar pigmento..."
          className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <span className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        )}

        {isError && (
          <div className="text-center py-12 text-sm text-red-600">
            Erro ao carregar estoque.
          </div>
        )}

        {!isLoading && !isError && items.length === 0 && (
          <div className="text-center py-12 text-sm text-gray-500">
            Nenhum item encontrado.
          </div>
        )}

        {!isLoading && items.length > 0 && (
          <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Pigmento
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Saldo (ml)
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Mínimo (ml)
                </th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Custo/ml
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => {
                const saldoMl = parseFloat(item.saldo_ml ?? item.quantidade_atual ?? '0');
                const saldoMin = parseFloat(item.saldo_minimo ?? item.quantidade_minima ?? '0');

                return (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {item.pigmento.cor_hex && (
                          <span
                            className="w-4 h-4 rounded-full border border-gray-300 flex-shrink-0"
                            style={{ backgroundColor: item.pigmento.cor_hex }}
                          />
                        )}
                        <div>
                          <p className="font-medium text-gray-800">{item.pigmento.nome}</p>
                          <p className="text-xs text-gray-400">{item.pigmento.codigo}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-medium text-gray-800">
                      {saldoMl.toFixed(0)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-500">
                      {saldoMin.toFixed(0)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StockAvailabilityBadge saldo_ml={saldoMl} saldo_minimo={saldoMin} />
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {item.custo_ml ? `R$ ${parseFloat(item.custo_ml).toFixed(4)}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() =>
                          setAddStockFor({ id: item.pigmento.id, nome: item.pigmento.nome })
                        }
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
                      >
                        <Plus className="w-3 h-3" />
                        Adicionar
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          </div>
        )}
      </div>

      {/* Add stock modal */}
      {addStockFor && (
        <AddStockModal
          pigmentoId={addStockFor.id}
          pigmentoNome={addStockFor.nome}
          onClose={() => setAddStockFor(null)}
        />
      )}
    </div>
  );
}
