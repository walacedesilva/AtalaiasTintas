import React from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  ShoppingBag,
  Calendar,
  Filter
} from 'lucide-react';

/**
 * Reports Page - Relatórios Gerenciais
 */
export default function ReportsPage(): React.ReactElement {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Relatórios</h1>
          <p className="text-sm text-slate-500 mt-1">
            Relatórios gerenciais e análises de desempenho
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
            <Calendar className="h-4 w-4" />
            Período
          </button>
          <button className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
            <Filter className="h-4 w-4" />
            Filtros
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50">
              <DollarSign className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">R$ 24.580</p>
              <p className="text-xs font-medium text-slate-400 mt-1">Vendas do Mês</p>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50">
              <ShoppingBag className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">147</p>
              <p className="text-xs font-medium text-slate-400 mt-1">Pedidos</p>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-purple-50">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">+12%</p>
              <p className="text-xs font-medium text-slate-400 mt-1">Crescimento</p>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-orange-50">
              <BarChart3 className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">R$ 186</p>
              <p className="text-xs font-medium text-slate-400 mt-1">Ticket Médio</p>
            </div>
          </div>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Vendas por Período</h2>
          <div className="flex items-center justify-center h-64 bg-slate-50 rounded-lg">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 mx-auto text-slate-300 mb-2" />
              <p className="text-sm text-slate-500">Gráfico de vendas será exibido aqui</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Produtos Mais Vendidos</h2>
          <div className="space-y-3">
            {[
              { nome: 'Tinta Acrílica Branca', vendas: 45, valor: 'R$ 2.250' },
              { nome: 'Tinta Látex Premium', vendas: 32, valor: 'R$ 1.920' },
              { nome: 'Esmalte Sintético Azul', vendas: 28, valor: 'R$ 1.680' },
              { nome: 'Primer Branco', vendas: 22, valor: 'R$ 1.100' },
            ].map((produto, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-slate-900">{produto.nome}</p>
                  <p className="text-xs text-slate-500">{produto.vendas} unidades</p>
                </div>
                <p className="text-sm font-semibold text-emerald-600">{produto.valor}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Additional Reports */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Relatórios Disponíveis</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            'Vendas por Cliente',
            'Análise de Estoque',
            'Relatório Fiscal',
            'Performance de Vendedores',
            'Margem de Lucro',
            'Fluxo de Caixa'
          ].map((relatorio, index) => (
            <button
              key={index}
              className="p-4 text-left border border-slate-200 rounded-lg hover:border-brand-300 hover:bg-brand-50 transition-colors group"
            >
              <p className="text-sm font-medium text-slate-900 group-hover:text-brand-700">
                {relatorio}
              </p>
              <p className="text-xs text-slate-500 mt-1">Clique para gerar</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}