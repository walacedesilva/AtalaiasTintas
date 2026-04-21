import React from 'react';
import { Link } from 'react-router-dom';
import { useDashboardStats, useLowStock } from '@/hooks/useTintometry';
import { useAuth } from '@/hooks/useAuth';
import { BusinessMetrics } from '@/components/dashboard/BusinessMetrics';
import { SalesOverview } from '@/components/dashboard/SalesOverview';
import { FiscalStatus } from '@/components/dashboard/FiscalStatus';
import { TopProducts } from '@/components/dashboard/TopProducts';
import {
  Plus,
  Tag,
  Palette,
  Package,
  FlaskConical,
  TrendingUp,
  AlertTriangle,
  Layers,
  ChevronRight,
  Settings,
} from 'lucide-react';

interface StatCardProps {
  label: string; 
  value?: number; 
  icon: React.ElementType; 
  danger?: boolean; 
  loading?: boolean;
}

function StatCard({ 
  label, value, icon: Icon, danger = false, loading = false,
}: StatCardProps) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${danger && (value ?? 0) > 0 ? 'bg-rose-100' : 'bg-brand-50'}`}>
        <Icon className={`h-6 w-6 ${danger && (value ?? 0) > 0 ? 'text-rose-600' : 'text-brand-600'}`} aria-hidden="true" />
      </div>
      <div>
        <p className={`text-2xl font-bold leading-none ${danger && (value ?? 0) > 0 ? 'text-rose-600' : 'text-slate-900'}`}>
          {loading ? <span className="text-slate-300">—</span> : (value ?? 0)}
        </p>
        <p className="text-xs font-medium text-slate-400 mt-1">{label}</p>
      </div>
    </div>
  );
}

interface QuickActionProps {
  to: string;
  icon: React.ElementType;
  title: string;
  description: string;
  color: string;
}

function QuickAction({ to, icon: Icon, title, description, color }: QuickActionProps) {
  return (
    <Link to={to} className={`group relative overflow-hidden rounded-xl ${color} p-5 transition-transform hover:scale-105`}>
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/20 group-hover:bg-white/30 transition-colors">
        <Icon className="h-5 w-5 text-white" aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white leading-none">{title}</p>
        <p className="text-xs text-white/80 mt-1">{description}</p>
      </div>
    </Link>
  );
}

export default function Dashboard(): React.ReactElement {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: lowStock, isLoading: lowStockLoading } = useLowStock();

  const getGreeting = (): string => {
    const h = new Date().getHours();
    if (h < 12) return 'Bom dia';
    if (h < 18) return 'Boa tarde';
    return 'Boa noite';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          {getGreeting()}, {user?.first_name || user?.username || 'Usuário'}! 👋
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Aqui está o resumo das atividades do seu negócio hoje.
        </p>
      </div>

      {/* Status Metrics - Simple overview with focus on sales and low stock */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard 
          label="Vendas do Dia" 
          value={stats?.vendas_hoje || 0} 
          icon={TrendingUp} 
          loading={statsLoading}
        />
        <StatCard 
          label="Produtos com Estoque Baixo" 
          value={lowStock?.length || 0} 
          icon={Package} 
          danger={true}
          loading={lowStockLoading}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <QuickAction 
          to="/sales" 
          icon={TrendingUp} 
          title="Vendas" 
          description="Gestão de vendas e PDV" 
          color="bg-gradient-to-br from-emerald-500 to-emerald-600" 
        />
        <QuickAction 
          to="/sales/orders" 
          icon={Package} 
          title="Pedidos" 
          description="Controle de pedidos" 
          color="bg-gradient-to-br from-blue-500 to-blue-600" 
        />
        <QuickAction 
          to="/fiscal" 
          icon={Tag} 
          title="Fiscal/NFe" 
          description="Gestão fiscal e notas" 
          color="bg-gradient-to-br from-purple-500 to-purple-600" 
        />
        <QuickAction 
          to="/reports" 
          icon={Plus} 
          title="Relatórios" 
          description="Relatórios gerenciais" 
          color="bg-gradient-to-br from-sky-500 to-sky-600" 
        />
        <QuickAction 
          to="/monitoring" 
          icon={AlertTriangle} 
          title="Monitoramento" 
          description="Status do sistema" 
          color="bg-gradient-to-br from-red-500 to-red-600" 
        />
        <QuickAction 
          to="/inventory" 
          icon={Layers} 
          title="Controle de Estoque" 
          description="Gerenciar pigmentos" 
          color="bg-gradient-to-br from-orange-500 to-orange-600" 
        />
        <QuickAction 
          to="/settings" 
          icon={Settings} 
          title="Configurações" 
          description="Sistema e preferências" 
          color="bg-gradient-to-br from-slate-500 to-slate-600" 
        />
      </div>

      {/* Business Metrics Section */}
      <div className="space-y-6">
        <BusinessMetrics timeRange="today" />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <SalesOverview period="today" />
          <FiscalStatus showAlerts={true} />
          <TopProducts />
        </div>
      </div>

      {/* Low Stock Alerts */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-slate-900">Produtos com Estoque Baixo</h2>
          <Link to="/inventory" className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors flex items-center gap-1">
            Ver estoque <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>

        {lowStockLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 rounded-lg bg-slate-100 animate-pulse" />
            ))}
          </div>
        ) : lowStock && lowStock.length > 0 ? (
          <div className="space-y-2">
            {lowStock.slice(0, 5).map((produto: any) => (
              <div key={produto.id} className="flex items-center gap-3 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2.5">
                <div className="h-8 w-8 shrink-0 rounded bg-slate-200 flex items-center justify-center">
                  <Package className="h-4 w-4 text-slate-400" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 leading-none truncate">{produto.nome}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{produto.categoria}</p>
                </div>
                <span className="badge badge-danger shrink-0">{produto.estoque_atual}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 mb-3">
              <Package className="h-5 w-5 text-emerald-600" aria-hidden="true" />
            </div>
            <p className="text-sm font-medium text-slate-700">Estoque em ordem</p>
            <p className="text-xs text-slate-400 mt-1">Todos os produtos com estoque adequado</p>
          </div>
        )}
      </div>
    </div>
  );
}
