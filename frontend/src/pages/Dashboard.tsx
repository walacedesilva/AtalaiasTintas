import React from 'react';
import { Link } from 'react-router-dom';
import { useDashboardStats, useLowStock, usePopularCores } from '@/hooks/useTintometry';
import { useAuth } from '@/hooks/useAuth';
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
} from 'lucide-react';

function StatCard({
  label, value, icon: Icon, danger = false, loading = false,
}: {
  label: string; value: number | undefined; icon: React.ComponentType<{ className?: string | undefined }>;
  danger?: boolean; loading?: boolean;
}) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${danger && (value ?? 0) > 0 ? 'bg-rose-100' : 'bg-teal-50'}`}>
        <Icon className={`h-5 w-5 ${danger && (value ?? 0) > 0 ? 'text-rose-600' : 'text-teal-600'}`} aria-hidden="true" />
      </div>
      <div>
        <p className={`text-2xl font-bold leading-none ${danger && (value ?? 0) > 0 ? 'text-rose-600' : 'text-slate-900'}`}>
          {loading ? <span className="text-slate-300">—</span> : (value ?? 0)}
        </p>
        <p className="text-xs text-slate-500 mt-1">{label}</p>
      </div>
    </div>
  );
}

function QuickAction({
  to, icon: Icon, title, description, color,
}: {
  to: string; icon: React.ComponentType<{ className?: string | undefined }>; title: string; description: string; color: string;
}) {
  return (
    <Link
      to={to}
      className={`group card p-5 flex items-center gap-4 hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 ${color}`}
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/20 group-hover:bg-white/30 transition-colors">
        <Icon className="h-5 w-5 text-white" aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white leading-none">{title}</p>
        <p className="text-xs text-white/70 mt-1 truncate">{description}</p>
      </div>
      <ChevronRight className="h-4 w-4 text-white/50 group-hover:text-white/80 group-hover:translate-x-0.5 transition-all shrink-0" aria-hidden="true" />
    </Link>
  );
}

export default function Dashboard(): React.ReactElement {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: lowStock, isLoading: lowStockLoading } = useLowStock();
  const { data: popularColors, isLoading: colorsLoading } = usePopularCores(5);

  const getGreeting = (): string => {
    const h = new Date().getHours();
    if (h < 12) return 'Bom dia';
    if (h < 18) return 'Boa tarde';
    return 'Boa noite';
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {getGreeting()}, {user?.first_name || user?.username}!
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {new Date().toLocaleDateString('pt-BR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <Link to="/mixtures?action=new" className="btn-primary self-start sm:self-auto">
          <Plus className="h-4 w-4" aria-hidden="true" />
          Nova Mistura
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Modelos Ativos"  value={stats?.total_templates}  icon={FlaskConical}  loading={statsLoading} />
        <StatCard label="Misturas Hoje"     value={stats?.misturas_hoje}    icon={Layers}        loading={statsLoading} />
        <StatCard label="Estoque Baixo"     value={stats?.estoque_baixo}    icon={AlertTriangle} loading={statsLoading} danger />
        <StatCard label="Etiquetas Hoje"    value={stats?.etiquetas_geradas} icon={TrendingUp}   loading={statsLoading} />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <QuickAction to="/mixtures?action=new"     icon={Plus}     title="Nova Mistura"       description="Criar mistura de tinta"        color="bg-gradient-to-br from-emerald-500 to-emerald-600" />
        <QuickAction to="/labels?action=generate"  icon={Tag}      title="Gerar Etiqueta"     description="Etiquetas para misturas"       color="bg-gradient-to-br from-sky-500 to-sky-600" />
        <QuickAction to="/colors"                  icon={Palette}  title="Catálogo de Cores"  description="Explorar cores disponíveis"    color="bg-gradient-to-br from-violet-500 to-violet-600" />
        <QuickAction to="/inventory"               icon={Package}  title="Controle de Estoque" description="Gerenciar pigmentos"          color="bg-gradient-to-br from-orange-500 to-orange-600" />
      </div>

      {/* Detail panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Alertas de Estoque</h2>
            <Link to="/inventory" className="text-xs font-medium text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-1">
              Ver todos <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </div>

          {lowStockLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 rounded-lg bg-slate-100 animate-pulse" />
              ))}
            </div>
          ) : lowStock && lowStock.length > 0 ? (
            <div className="space-y-2">
              {lowStock.slice(0, 5).map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-lg bg-rose-50 border border-rose-100 px-3 py-2.5">
                  <div>
                    <p className="text-sm font-medium text-slate-900 leading-none">{item.pigmento.nome}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Cód: {item.pigmento.codigo}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-rose-600 leading-none">
                      {item.quantidade_atual} {item.unidade}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">Mín: {item.quantidade_minima}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 mb-3">
                <Package className="h-5 w-5 text-emerald-600" aria-hidden="true" />
              </div>
              <p className="text-sm font-medium text-slate-700">Estoque OK</p>
              <p className="text-xs text-slate-400 mt-1">Todos os pigmentos com nível adequado</p>
            </div>
          )}
        </div>

        {/* Popular Colors */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-900">Cores Populares</h2>
            <Link to="/colors" className="text-xs font-medium text-teal-600 hover:text-teal-700 transition-colors flex items-center gap-1">
              Ver catálogo <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </div>

          {colorsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-12 rounded-lg bg-slate-100 animate-pulse" />
              ))}
            </div>
          ) : popularColors && popularColors.length > 0 ? (
            <div className="space-y-2">
              {popularColors.map((cor) => (
                <div key={cor.id} className="flex items-center gap-3 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2.5">
                  <div
                    className="h-8 w-8 shrink-0 rounded-lg border-2 border-white shadow-sm"
                    style={{ backgroundColor: cor.cor_hex }}
                    aria-label={`Cor ${cor.nome}`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 leading-none truncate">{cor.nome}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{cor.codigo}</p>
                  </div>
                  <span className="badge badge-gray shrink-0">{cor.popularidade}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-100 mb-3">
                <Palette className="h-5 w-5 text-violet-600" aria-hidden="true" />
              </div>
              <p className="text-sm font-medium text-slate-700">Nenhuma cor cadastrada</p>
              <p className="text-xs text-slate-400 mt-1">Adicione cores ao catálogo</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}