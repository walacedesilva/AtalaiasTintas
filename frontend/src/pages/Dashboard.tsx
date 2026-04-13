import React from 'react';
import { Link } from 'react-router-dom';
import { useDashboardStats, useLowStock, usePopularCores } from '@/hooks/useTintometry';
import { useAuth } from '@/hooks/useAuth';

/**
 * Dashboard page component
 * Provides overview of system status, quick actions, and important metrics
 */
export default function Dashboard(): React.ReactElement {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: lowStock, isLoading: lowStockLoading } = useLowStock();
  const { data: popularColors, isLoading: colorsLoading } = usePopularCores(5);

  // Get greeting based on time of day
  const getGreeting = (): string => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Bom dia';
    if (hour < 18) return 'Boa tarde';
    return 'Boa noite';
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {getGreeting()}, {user?.first_name || user?.username}!
            </h1>
            <p className="text-gray-600 mt-1">
              Bem-vindo ao sistema de gestão de tintas
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">
              {new Date().toLocaleDateString('pt-BR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          to="/mixtures?action=new"
          className="bg-gradient-to-r from-green-500 to-green-600 p-6 rounded-lg text-white hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-sm hover:shadow-md group"
        >
          <div className="flex items-center">
            <div className="text-3xl mr-4">🧪</div>
            <div>
              <h3 className="text-lg font-semibold">Nova Mistura</h3>
              <p className="text-green-100 text-sm">Criar nova mistura de tinta</p>
            </div>
          </div>
        </Link>

        <Link
          to="/labels?action=generate"
          className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-lg text-white hover:from-blue-600 hover:to-blue-700 transition-all duration-200 shadow-sm hover:shadow-md group"
        >
          <div className="flex items-center">
            <div className="text-3xl mr-4">🏷️</div>
            <div>
              <h3 className="text-lg font-semibold">Gerar Etiqueta</h3>
              <p className="text-blue-100 text-sm">Criar etiquetas para misturas</p>
            </div>
          </div>
        </Link>

        <Link
          to="/colors"
          className="bg-gradient-to-r from-purple-500 to-purple-600 p-6 rounded-lg text-white hover:from-purple-600 hover:to-purple-700 transition-all duration-200 shadow-sm hover:shadow-md group"
        >
          <div className="flex items-center">
            <div className="text-3xl mr-4">🌈</div>
            <div>
              <h3 className="text-lg font-semibold">Catálogo de Cores</h3>
              <p className="text-purple-100 text-sm">Explorar cores disponíveis</p>
            </div>
          </div>
        </Link>

        <Link
          to="/inventory"
          className="bg-gradient-to-r from-orange-500 to-orange-600 p-6 rounded-lg text-white hover:from-orange-600 hover:to-orange-700 transition-all duration-200 shadow-sm hover:shadow-md group"
        >
          <div className="flex items-center">
            <div className="text-3xl mr-4">📦</div>
            <div>
              <h3 className="text-lg font-semibold">Controle de Estoque</h3>
              <p className="text-orange-100 text-sm">Gerenciar pigmentos</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Templates Counter */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <div className="text-3xl mr-4">📝</div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {statsLoading ? '...' : stats?.total_templates || 0}
              </p>
              <p className="text-gray-600 text-sm">Templates Ativos</p>
            </div>
          </div>
        </div>

        {/* Today's Mixtures */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <div className="text-3xl mr-4">🧪</div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {statsLoading ? '...' : stats?.misturas_hoje || 0}
              </p>
              <p className="text-gray-600 text-sm">Misturas Hoje</p>
            </div>
          </div>
        </div>

        {/* Low Stock Alert */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <div className="text-3xl mr-4">⚠️</div>
            <div>
              <p className={`text-2xl font-bold ${
                (stats?.estoque_baixo || 0) > 0 ? 'text-red-600' : 'text-gray-900'
              }`}>
                {statsLoading ? '...' : stats?.estoque_baixo || 0}
              </p>
              <p className="text-gray-600 text-sm">Estoque Baixo</p>
            </div>
          </div>
        </div>

        {/* Labels Generated */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <div className="text-3xl mr-4">🏷️</div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {statsLoading ? '...' : stats?.etiquetas_geradas || 0}
              </p>
              <p className="text-gray-600 text-sm">Etiquetas Hoje</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock Items */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Alertas de Estoque
            </h2>
            <Link
              to="/inventory"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Ver todos
            </Link>
          </div>
          
          {lowStockLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : lowStock && lowStock.length > 0 ? (
            <div className="space-y-3">
              {lowStock.slice(0, 5).map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 bg-red-50 rounded-md">
                  <div>
                    <p className="font-medium text-gray-900">{item.pigmento.nome}</p>
                    <p className="text-sm text-gray-600">Código: {item.pigmento.codigo}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-red-600">
                      {item.quantidade_atual} {item.unidade}
                    </p>
                    <p className="text-xs text-gray-500">
                      Mín: {item.quantidade_minima}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">
                ✅ Todos os pigmentos com estoque adequado
              </p>
            </div>
          )}
        </div>

        {/* Popular Colors */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Cores Populares
            </h2>
            <Link
              to="/colors"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Ver catálogo
            </Link>
          </div>
          
          {colorsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : popularColors && popularColors.length > 0 ? (
            <div className="space-y-3">
              {popularColors.map((cor) => (
                <div key={cor.id} className="flex items-center p-3 bg-gray-50 rounded-md">
                  <div 
                    className="w-8 h-8 rounded-full mr-3 border-2 border-gray-200"
                    style={{ backgroundColor: cor.cor_hex }}
                    aria-label={`Cor ${cor.nome}`}
                  />
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{cor.nome}</p>
                    <p className="text-sm text-gray-600">
                      {cor.codigo} • Popularidade: {cor.popularidade}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">Nenhuma cor disponível</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}