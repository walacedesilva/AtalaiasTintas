import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth, useAuthActions } from '@/hooks/useAuth';
import { APP_NAME } from '@/utils/env';
import { User, LogOut, ChevronDown, Paintbrush } from 'lucide-react';

const PAGE_TITLES: Record<string, string> = {
  '/dashboard':  'Painel',
  '/pigments':   'Pigmentos',
  '/colors':     'Cores Definidas',
  '/formulas':   'Fórmulas Tintométricas',
  '/mixtures':   'Misturas',
  '/inventory':  'Controle de Estoque',
  '/labels':     'Etiquetas',
  '/profile':    'Meu Perfil',
};

export default function Header(): React.ReactElement {
  const location = useLocation();
  const { user } = useAuth();
  const { logout } = useAuthActions();
  const [menuOpen, setMenuOpen] = useState(false);

  const pageTitle = PAGE_TITLES[location.pathname] ?? APP_NAME;
  const initials =
    user?.first_name && user?.last_name
      ? `${user.first_name[0]}${user.last_name[0]}`
      : (user?.username?.[0] ?? '?').toUpperCase();

  return (
    <header className="fixed top-0 left-0 right-0 z-40 h-16 bg-slate-900 border-b border-slate-800 flex items-center px-4 gap-4">
      {/* Brand */}
      <Link
        to="/dashboard"
        className="flex items-center gap-2.5 shrink-0 group"
        aria-label="Ir para dashboard"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 shadow-md group-hover:bg-teal-500 transition-colors">
          <Paintbrush className="h-4 w-4 text-white" aria-hidden="true" />
        </div>
        <span className="hidden sm:block text-sm font-semibold text-white tracking-tight">
          {APP_NAME}
        </span>
      </Link>

      {/* Page title */}
      <div className="hidden md:flex items-center gap-2 px-3 h-8 bg-slate-800 rounded-lg border border-slate-700">
        <span className="text-xs font-medium text-slate-300">{pageTitle}</span>
      </div>

      <div className="flex-1" />

      {/* Quick actions */}
      <nav className="hidden lg:flex items-center gap-1" aria-label="AÃ§Ãµes rÃ¡pidas">
        <Link
          to="/mixtures?action=new"
          className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
        >
          Nova Mistura
        </Link>
        <Link
          to="/labels?action=generate"
          className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
        >
          Gerar Etiqueta
        </Link>
      </nav>

      {/* User menu */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setMenuOpen((v) => !v)}
          aria-expanded={menuOpen}
          aria-haspopup="true"
          aria-label="Menu do usuário"
          className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-slate-900"
        >
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-teal-600 text-xs font-semibold text-white">
            {initials}
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-semibold text-white leading-none">
              {user?.first_name || user?.username}
            </p>
            <p className="text-[10px] text-slate-400 leading-none mt-0.5">{user?.email}</p>
          </div>
          <ChevronDown
            className={`hidden sm:block h-3.5 w-3.5 text-slate-400 transition-transform duration-150 ${menuOpen ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </button>

        {menuOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setMenuOpen(false)}
              aria-hidden="true"
            />
            <div className="absolute right-0 mt-2 w-52 rounded-xl bg-white shadow-xl ring-1 ring-slate-200 z-20 overflow-hidden animate-fade-in">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-900">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-slate-500 truncate">{user?.email}</p>
              </div>
              <Link
                to="/profile"
                className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                onClick={() => setMenuOpen(false)}
              >
                <User className="h-4 w-4 text-slate-400" aria-hidden="true" />
                Meu Perfil
              </Link>
              <div className="border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { logout.mutate(); setMenuOpen(false); }}
                  disabled={logout.isPending}
                  className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-50"
                >
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  {logout.isPending ? 'Saindo…' : 'Sair'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </header>
  );
}
