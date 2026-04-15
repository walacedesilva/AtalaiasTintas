import React, { useState } from 'react';
import { Phone, Search, RefreshCw, Clock, Pipette } from 'lucide-react';
import toast from 'react-hot-toast';
import { tintometryAPI } from '@/api';
import type { CustomerHistoryItem } from '@/types/tintometry';

interface CustomerColorHistoryProps {
  onReproduce?: (item: CustomerHistoryItem) => void;
}

/**
 * Searches a customer's color history by phone number.
 * Each result row offers a "Reproduzir" button that triggers onReproduce.
 */
export function CustomerColorHistory({ onReproduce }: CustomerColorHistoryProps): React.ReactElement {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<CustomerHistoryItem[]>([]);
  const [searched, setSearched] = useState(false);

  async function handleSearch() {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length < 8) {
      toast.error('Informe ao menos 8 dígitos do telefone');
      return;
    }
    setLoading(true);
    try {
      const res = await tintometryAPI.customerHistory.getByPhone(phone);
      setItems(res.results);
      setSearched(true);
      if (res.results.length === 0) {
        toast('Nenhum histórico encontrado para este telefone.');
      }
    } catch {
      toast.error('Erro ao buscar histórico do cliente');
    } finally {
      setLoading(false);
    }
  }

  function formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <Phone className="w-5 h-5 text-purple-600" />
        Histórico do Cliente
      </h3>

      {/* Search bar */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="(00) 00000-0000"
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center gap-1"
        >
          {loading ? (
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          ) : (
            <Search className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Results */}
      {searched && items.length === 0 && !loading && (
        <p className="text-sm text-gray-500 italic text-center py-4">
          Nenhuma compra anterior encontrada.
        </p>
      )}

      {items.length > 0 && (
        <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
          {items.map((item, idx) => (
            <li key={idx} className="px-4 py-3 flex items-center gap-3 text-sm">
              <Pipette className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-800 truncate">{item.cor}</p>
                <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(item.data_confirmacao)}
                  </span>
                  {item.volume_produzido && (
                    <span>{parseFloat(item.volume_produzido).toFixed(1)} L</span>
                  )}
                  <span className="font-mono text-gray-400">{item.codigo_mistura}</span>
                </div>
                {item.observacoes_cliente && (
                  <p className="text-xs text-gray-400 italic truncate">{item.observacoes_cliente}</p>
                )}
              </div>
              {onReproduce && (
                <button
                  onClick={() => onReproduce(item)}
                  className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-md transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  Reproduzir
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default CustomerColorHistory;
