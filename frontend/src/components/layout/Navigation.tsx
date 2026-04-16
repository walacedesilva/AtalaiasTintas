import React from 'react';
import { NavLink } from 'react-router-dom';
import { useDashboardStats } from '@/hooks/useTintometry';
import {
  LayoutDashboard,
  Beaker,
  Palette,
  FlaskConical,
  Layers,
  Package,
  Tag,
  Plus,
  Printer,
  ShoppingCart,
  ClipboardList,
  Users,
  Pipette,
  Monitor,
  Receipt,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string | undefined }>;
  badge?: number | undefined;
  badgeDanger?: boolean | undefined;
}

export default function Navigation(): React.ReactElement {
  const { data: stats } = useDashboardStats();

  const navItems: NavItem[] = [
    { path: '/dashboard',  label: 'Painel',           icon: LayoutDashboard },
    { path: '/pdv',        label: 'PDV',              icon: Monitor },
    { path: '/sales/orders', label: 'Pedidos',         icon: ClipboardList, badge: undefined },
    { path: '/sales',      label: 'Vendas',           icon: ShoppingCart,  badge: undefined },
    { path: '/recebiveis', label: 'Recebíveis',       icon: Receipt },
    { path: '/customers',  label: 'Clientes',         icon: Users },
    { path: '/pigments',   label: 'Pigmentos',        icon: Beaker },
    { path: '/colors',     label: 'Cores Definidas',  icon: Palette,      badge: stats?.total_templates },
    { path: '/formulas',   label: 'Fórmulas',          icon: FlaskConical },
    { path: '/mixtures',   label: 'Misturas',         icon: Layers,       badge: stats?.misturas_hoje },
    {
      path: '/inventory',
      label: 'Estoque',
      icon: Package,
      badge: (stats?.estoque_baixo ?? 0) > 0 ? stats?.estoque_baixo : undefined,
      badgeDanger: (stats?.estoque_baixo ?? 0) > 0,
    },
    { path: '/labels',     label: 'Etiquetas',        icon: Tag,          badge: stats?.etiquetas_geradas },
    { path: '/tintometry', label: 'Tintometria',      icon: Pipette,      badge: undefined },
    { path: '/tintometry/stock', label: 'Estoque Pigmentos', icon: Beaker, badge: undefined },
  ];

  return (
    <nav
      id="navigation"
      className="custom-scrollbar fixed left-0 top-16 w-64 h-[calc(100vh-4rem)] bg-slate-900 border-r border-slate-800 overflow-y-auto flex flex-col"
      aria-label="Navegação principal"
    >
      <div className="flex-1 p-4 space-y-1">
        {/* Section label */}
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          Menu
        </p>

        {navItems.map(({ path, label, icon: Icon, badge, badgeDanger }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `group flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-brand-600/20 text-brand-400 ring-1 ring-brand-600/30'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              }`
            }
            aria-label={label}
          >
            <div className="flex items-center gap-3">
              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{label}</span>
            </div>
            {badge !== undefined && (
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-semibold leading-none ${
                  badgeDanger
                    ? 'bg-rose-500/20 text-rose-400'
                    : 'bg-slate-700 text-slate-300'
                }`}
              >
                {badge > 99 ? '99+' : badge}
              </span>
            )}
          </NavLink>
        ))}

        {/* Quick actions */}
        <div className="pt-4">
          <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Ações Rápidas
          </p>
          <NavLink
            to="/mixtures?action=new"
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-emerald-400 hover:bg-emerald-600/10 transition-colors"
          >
            <Plus className="h-4 w-4 shrink-0" aria-hidden="true" />
            Nova Mistura
          </NavLink>
          <NavLink
            to="/tintometry"
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-violet-400 hover:bg-violet-600/10 transition-colors"
          >
            <Pipette className="h-4 w-4 shrink-0" aria-hidden="true" />
            Nova Tintometria
          </NavLink>
          <NavLink
            to="/labels?action=generate"
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-sky-400 hover:bg-sky-600/10 transition-colors"
          >
            <Printer className="h-4 w-4 shrink-0" aria-hidden="true" />
            Gerar Etiqueta
          </NavLink>
        </div>
      </div>

      {/* Status summary */}
      {stats && (
        <div className="p-4 border-t border-slate-800 space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-2">
            Status
          </p>
          {[
            { label: 'Misturas Hoje',    value: stats.misturas_hoje,    danger: false },
            { label: 'Modelos Ativos',   value: stats.total_templates,  danger: false },
            { label: 'Estoque Baixo',    value: stats.estoque_baixo,    danger: stats.estoque_baixo > 0 },
            { label: 'Etiquetas Hoje',   value: stats.etiquetas_geradas, danger: false },
          ].map(({ label, value, danger }) => (
            <div key={label} className="flex justify-between text-xs">
              <span className={danger ? 'text-rose-400' : 'text-slate-500'}>{label}</span>
              <span className={`font-semibold ${danger ? 'text-rose-400' : 'text-slate-300'}`}>{value}</span>
            </div>
          ))}
        </div>
      )}

      <div className="p-4 border-t border-slate-800">
        <p className="text-[10px] text-slate-600 text-center">Atalaia Tintas v1.0</p>
      </div>
    </nav>
  );
}
