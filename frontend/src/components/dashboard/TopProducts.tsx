/**
 * TopProducts Component
 *
 * Shows the top 5 best-selling products today, ranked by revenue.
 * Data comes from the real dashboard API endpoint.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { TrendingUp, Package, ChevronRight } from 'lucide-react';
import { getDashboardRawData } from '@/services/dashboard';

export const TopProducts: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-raw'],
    queryFn: getDashboardRawData,
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
  });

  const products = data?.produtos_mais_vendidos ?? [];
  const maxReceita = products.length > 0 ? products[0].receita : 0;

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50">
            <TrendingUp className="h-4 w-4 text-brand-600" aria-hidden="true" />
          </div>
          <h2 className="text-sm font-semibold text-slate-900">Produtos Mais Vendidos</h2>
        </div>
        <Link
          to="/reports"
          className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors flex items-center gap-1"
        >
          Ver relatório <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 rounded-lg bg-slate-100 animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 mb-3">
            <Package className="h-5 w-5 text-red-600" aria-hidden="true" />
          </div>
          <p className="text-sm font-medium text-slate-700">Erro ao carregar dados</p>
          <p className="text-xs text-slate-400 mt-1">Verifique a conexão com o servidor</p>
        </div>
      ) : products.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 mb-3">
            <Package className="h-5 w-5 text-slate-400" aria-hidden="true" />
          </div>
          <p className="text-sm font-medium text-slate-700">Nenhuma venda hoje</p>
          <p className="text-xs text-slate-400 mt-1">Os produtos mais vendidos aparecerão aqui</p>
        </div>
      ) : (
        <ol className="space-y-2">
          {products.map((product, index) => {
            const barWidth = maxReceita > 0 ? (product.receita / maxReceita) * 100 : 0;
            return (
              <li key={product.id} className="flex items-center gap-3">
                {/* Rank */}
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
                    index === 0
                      ? 'bg-amber-100 text-amber-700'
                      : index === 1
                      ? 'bg-slate-200 text-slate-600'
                      : index === 2
                      ? 'bg-orange-100 text-orange-700'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {index + 1}
                </span>

                {/* Name + bar */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-xs font-medium text-slate-800 truncate leading-none">
                      {product.nome}
                    </p>
                    <span className="text-xs font-semibold text-slate-700 ml-2 shrink-0">
                      {formatCurrency(product.receita)}
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-brand-400 transition-all duration-500"
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {product.quantidade % 1 === 0
                      ? product.quantidade.toFixed(0)
                      : product.quantidade.toFixed(1)}{' '}
                    un.
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      {data?.updated_at && (
        <p className="text-[10px] text-slate-400 mt-4 text-right">
          Atualizado: {new Date(data.updated_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </p>
      )}
    </div>
  );
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

export default TopProducts;
