import React from 'react';
import { NavLink } from 'react-router-dom';
import { useDashboardStats } from '@/hooks/useTintometry';
import { usePermissions } from '@/hooks/useAuth';
import {
  LayoutDashboard,
  Beaker,
  Palette,
  FlaskConical,
  Layers,
  Package,
  Tag,
  ClipboardList,
  Users,
  Monitor,
  Receipt,
  FileText,
  Settings,
  HelpCircle,
  X,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ElementType;
  badge?: number;
  badgeDanger?: boolean;
}

interface NavigationProps {
  isOpen: boolean;
  onClose: () => void;
}

function Navigation({ isOpen, onClose }: NavigationProps) {
  const { data: stats } = useDashboardStats();
  const { hasTintometryAccess } = usePermissions();

  // Items básicos (sempre visíveis)
  const baseNavItems: NavItem[] = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  ];

  // Items de tintometria (ocultos temporariamente)
  const tintometryNavItems: NavItem[] = [];

  // Items gerais (sempre visíveis) 
  const generalNavItems: NavItem[] = [
    { path: '/sales/orders', label: 'Pedidos', icon: ClipboardList },
    { path: '/customers', label: 'Clientes', icon: Users },
    { path: '/inventory', label: 'Controle de Estoque', icon: Layers },
    { path: '/fiscal', label: 'Fiscal/NFe', icon: Receipt, badge: stats?.nfe_pendentes, badgeDanger: true },
    { path: '/reports', label: 'Relatórios', icon: FileText },
    { path: '/monitoring', label: 'Monitoramento', icon: Monitor },
    { path: '/settings', label: 'Configurações', icon: Settings },
    { path: '/help', label: 'Ajuda', icon: HelpCircle },
  ];

  // Montar lista final baseado nas permissões
  const navItems: NavItem[] = [
    ...baseNavItems,
    ...(hasTintometryAccess() ? tintometryNavItems : []),
    ...generalNavItems,
  ];

  return (
    <nav
      id="navigation"
      className={`custom-scrollbar fixed left-0 top-16 w-64 h-[calc(100vh-4rem)] bg-slate-900 border-r border-slate-800 overflow-y-auto flex flex-col z-30 transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}
      aria-label="Navegação principal"
    >
      {/* Mobile close button */}
      <button
        type="button"
        onClick={onClose}
        className="lg:hidden absolute top-3 right-3 flex items-center justify-center h-8 w-8 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
        aria-label="Fechar menu"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>

      <div className="flex-1 p-4 space-y-1">
        {/* Section label */}
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          Menu
        </p>

        {navItems.map(({ path, label, icon: Icon, badge, badgeDanger }) => (
          <NavLink
            key={path}
            to={path}
            onClick={onClose}
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

      </div>

      <div className="p-4 border-t border-slate-800">
        <p className="text-[10px] text-slate-600 text-center">Atalaia Tintas v1.0</p>
      </div>
    </nav>
  );
}

export default Navigation;