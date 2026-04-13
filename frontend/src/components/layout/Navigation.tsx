import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useDashboardStats } from '@/hooks/useTintometry';

/**
 * Navigation component
 * Provides sidebar navigation with menu items and status indicators
 */

interface NavItem {
  path: string;
  label: string;
  icon: string;
  badge?: string | number;
  description?: string;
}

export default function Navigation(): React.ReactElement {
  const location = useLocation();
  const { data: stats } = useDashboardStats();

  // Navigation items configuration
  const navItems: NavItem[] = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: '📊',
      description: 'Visão geral do sistema'
    },
    {
      path: '/pigments',
      label: 'Pigmentos',
      icon: '🎨',
      description: 'Gestão de pigmentos'
    },
    {
      path: '/colors',
      label: 'Cores Definidas',
      icon: '🌈',
      badge: stats?.total_templates,
      description: 'Catálogo de cores'
    },
    {
      path: '/formulas',
      label: 'Fórmulas',
      icon: '⚗️',
      description: 'Fórmulas tintométricas'
    },
    {
      path: '/mixtures',
      label: 'Misturas',
      icon: '🧪',
      badge: stats?.misturas_hoje,
      description: 'Controle de misturas'
    },
    {
      path: '/inventory',
      label: 'Estoque',
      icon: '📦',
      badge: stats?.estoque_baixo > 0 ? stats.estoque_baixo : undefined,
      description: 'Controle de inventário'
    },
    {
      path: '/labels',
      label: 'Etiquetas',
      icon: '🏷️',
      badge: stats?.etiquetas_geradas,
      description: 'Geração de etiquetas'
    }
  ];

  const isCurrentPath = (path: string): boolean => {
    return location.pathname === path;
  };

  const isParentPath = (path: string): boolean => {
    return location.pathname.startsWith(path) && path !== '/';
  };

  return (
    <nav 
      id="navigation"
      className="fixed left-0 top-16 w-64 h-screen bg-white border-r border-gray-200 overflow-y-auto"
      aria-label="Navegação principal"
    >
      <div className="p-6">
        {/* Navigation Header */}
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Menu Principal
          </h2>
        </div>

        {/* Navigation Items */}
        <ul className="space-y-2" role="list">
          {navItems.map((item) => {
            const isActive = isCurrentPath(item.path) || isParentPath(item.path);
            
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-3 text-sm font-medium rounded-lg transition-all duration-200 group ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border-blue-200 border'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`
                  }
                  aria-current={isActive ? 'page' : undefined}
                  title={item.description}
                >
                  <div className="flex items-center">
                    <span className="text-lg mr-3" aria-hidden="true">
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </div>

                  {/* Badge/Counter */}
                  {item.badge !== undefined && (
                    <span 
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        isActive
                          ? 'bg-blue-100 text-blue-800'
                          : item.path === '/inventory' && typeof item.badge === 'number' && item.badge > 0
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                      }`}
                      aria-label={`${item.badge} ${item.label.toLowerCase()}`}
                    >
                      {typeof item.badge === 'number' && item.badge > 99 ? '99+' : item.badge}
                    </span>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>

        {/* Quick Actions Section */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Ações Rápidas
          </h3>
          
          <div className="space-y-2">
            <NavLink
              to="/mixtures?action=new"
              className="flex items-center px-3 py-2 text-sm font-medium text-green-700 bg-green-50 rounded-lg hover:bg-green-100 transition-colors group"
            >
              <span className="text-lg mr-3" aria-hidden="true">➕</span>
              Nova Mistura
            </NavLink>
            
            <NavLink
              to="/labels?action=generate"
              className="flex items-center px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors group"
            >
              <span className="text-lg mr-3" aria-hidden="true">🖨️</span>
              Gerar Etiqueta
            </NavLink>
          </div>
        </div>

        {/* Status Indicators */}
        {stats && (
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Status do Sistema
            </h3>
            
            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Misturas Hoje</span>
                <span className="font-medium text-gray-900">{stats.misturas_hoje}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Templates Ativos</span>
                <span className="font-medium text-gray-900">{stats.total_templates}</span>
              </div>
              
              <div className="flex justify-between">
                <span className={`${stats.estoque_baixo > 0 ? 'text-red-600' : 'text-gray-600'}`}>
                  Estoque Baixo
                </span>
                <span className={`font-medium ${stats.estoque_baixo > 0 ? 'text-red-900' : 'text-gray-900'}`}>
                  {stats.estoque_baixo}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Etiquetas Hoje</span>
                <span className="font-medium text-gray-900">{stats.etiquetas_geradas}</span>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Atalaia Tintas v1.0<br/>
            Sistema de Gestão
          </p>
        </div>
      </div>
    </nav>
  );
}