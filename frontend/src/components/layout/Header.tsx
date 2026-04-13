import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth, useAuthActions } from '@/hooks/useAuth';
import { APP_NAME } from '@/utils/env';

/**
 * Header component
 * Provides top navigation bar with branding, user menu, and quick actions
 */
export default function Header(): React.ReactElement {
  const location = useLocation();
  const { user } = useAuth();
  const { logout } = useAuthActions();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const handleLogout = (): void => {
    logout.mutate();
  };

  // Get page title based on current route
  const getPageTitle = (): string => {
    const pathMap: Record<string, string> = {
      '/dashboard': 'Dashboard',
      '/pigments': 'Pigmentos',
      '/colors': 'Cores Definidas',
      '/formulas': 'Fórmulas Tintométricas',
      '/mixtures': 'Misturas',
      '/inventory': 'Controle de Estoque',
      '/labels': 'Etiquetas',
      '/profile': 'Perfil do Usuário'
    };
    return pathMap[location.pathname] || 'Atalaia Tintas';
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 h-16 fixed top-0 left-0 right-0 z-40">
      <div className="flex items-center justify-between h-full px-4">
        {/* Logo and Brand */}
        <div className="flex items-center space-x-4">
          <Link 
            to="/dashboard" 
            className="flex items-center space-x-3 text-blue-600 hover:text-blue-700 transition-colors"
            aria-label="Ir para dashboard"
          >
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AT</span>
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-semibold text-gray-900">{APP_NAME}</h1>
              <p className="text-xs text-gray-500">Sistema de Etiquetas</p>
            </div>
          </Link>
        </div>

        {/* Page Title */}
        <div className="hidden md:block">
          <h2 className="text-lg font-medium text-gray-700">
            {getPageTitle()}
          </h2>
        </div>

        {/* User Menu and Actions */}
        <div className="flex items-center space-x-4">
          {/* Quick Actions */}
          <nav className="hidden lg:flex items-center space-x-2" aria-label="Ações rápidas">
            <Link
              to="/mixtures"
              className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              aria-label="Nova mistura"
            >
              Nova Mistura
            </Link>
            <Link
              to="/labels"
              className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              aria-label="Gerar etiquetas"
            >
              Gerar Etiquetas
            </Link>
          </nav>

          {/* User Menu */}
          <div className="relative">
            <button
              type="button"
              className="flex items-center space-x-3 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              aria-expanded={isUserMenuOpen}
              aria-haspopup="true"
              aria-label="Menu do usuário"
            >
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-medium text-sm">
                  {user?.first_name?.[0] || user?.username?.[0] || '?'}
                </span>
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-gray-900 font-medium">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${
                  isUserMenuOpen ? 'transform rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* User Dropdown */}
            {isUserMenuOpen && (
              <>
                {/* Backdrop */}
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setIsUserMenuOpen(false)}
                  aria-hidden="true"
                />
                
                {/* Menu */}
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-20 border border-gray-200">
                  <Link
                    to="/profile"
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    onClick={() => setIsUserMenuOpen(false)}
                  >
                    Meu Perfil
                  </Link>
                  <hr className="my-1" />
                  <button
                    type="button"
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    onClick={handleLogout}
                    disabled={logout.isPending}
                  >
                    {logout.isPending ? 'Saindo...' : 'Sair'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}