import React from 'react';
import { 
  Activity,
  Server,
  Database,
  Wifi,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  TrendingUp,
  HardDrive
} from 'lucide-react';

/**
 * Monitoring Page - Status do Sistema
 */
export default function MonitoringPage(): React.ReactElement {
  // Mock system status data
  const systemStatus = {
    overall: 'healthy',
    uptime: '15 dias, 7 horas',
    lastCheck: new Date().toLocaleTimeString('pt-BR'),
  };

  const services = [
    {
      name: 'Servidor Web',
      status: 'healthy',
      uptime: '99.9%',
      responseTime: '45ms',
      icon: Server,
    },
    {
      name: 'Base de Dados',
      status: 'healthy',
      uptime: '99.8%',
      responseTime: '12ms',
      icon: Database,
    },
    {
      name: 'Conectividade',
      status: 'healthy',
      uptime: '100%',
      responseTime: '23ms',
      icon: Wifi,
    },
    {
      name: 'Armazenamento',
      status: 'warning',
      uptime: '99.5%',
      responseTime: '89ms',
      icon: HardDrive,
    },
  ];

  const alerts = [
    {
      id: 1,
      type: 'warning',
      message: 'Espaço em disco baixo (85% utilizado)',
      timestamp: '2 horas atrás',
    },
    {
      id: 2,
      type: 'info',
      message: 'Backup automático concluído',
      timestamp: '6 horas atrás',
    },
    {
      id: 3,
      type: 'success',
      message: 'Sistema atualizado com sucesso',
      timestamp: '1 dia atrás',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-amber-500" />;
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-emerald-50 text-emerald-700 ring-emerald-200';
      case 'warning':
        return 'bg-amber-50 text-amber-700 ring-amber-200';
      case 'error':
        return 'bg-red-50 text-red-700 ring-red-200';
      default:
        return 'bg-slate-50 text-slate-700 ring-slate-200';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
      case 'info':
        return <Activity className="h-4 w-4 text-blue-500" />;
      default:
        return <Clock className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Monitoramento do Sistema</h1>
          <p className="text-sm text-slate-500 mt-1">
            Status em tempo real dos componentes do sistema
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Clock className="h-4 w-4" />
            Última verificação: {systemStatus.lastCheck}
          </div>
          <button className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors">
            <RefreshCw className="h-4 w-4" />
            Atualizar
          </button>
        </div>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50">
              {getStatusIcon(systemStatus.overall)}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900">Status Geral</p>
              <p className="text-lg font-bold text-emerald-600">Operacional</p>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50">
              <TrendingUp className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900">Tempo Ativo</p>
              <p className="text-lg font-bold text-slate-900">{systemStatus.uptime}</p>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-purple-50">
              <Activity className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900">Performance</p>
              <p className="text-lg font-bold text-slate-900">Ótima</p>
            </div>
          </div>
        </div>
      </div>

      {/* Services Status */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Status dos Serviços</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {services.map((service, index) => (
            <div key={index} className="border border-slate-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <service.icon className="h-5 w-5 text-slate-600" />
                  <h3 className="font-medium text-slate-900">{service.name}</h3>
                </div>
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ring-1 ring-inset ${getStatusColor(service.status)}`}>
                  {getStatusIcon(service.status)}
                  {service.status === 'healthy' ? 'Saudável' : service.status === 'warning' ? 'Atenção' : 'Erro'}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500">Disponibilidade</p>
                  <p className="font-semibold text-slate-900">{service.uptime}</p>
                </div>
                <div>
                  <p className="text-slate-500">Tempo Resposta</p>
                  <p className="font-semibold text-slate-900">{service.responseTime}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Alertas Recentes</h2>
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
              {getAlertIcon(alert.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900">{alert.message}</p>
                <p className="text-xs text-slate-500 mt-1">{alert.timestamp}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">CPU</h3>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900">23%</div>
            <div className="text-xs text-slate-500 mt-1">Utilização</div>
            <div className="mt-3 w-full bg-slate-200 rounded-full h-2">
              <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '23%' }}></div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Memória</h3>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900">67%</div>
            <div className="text-xs text-slate-500 mt-1">Utilização</div>
            <div className="mt-3 w-full bg-slate-200 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: '67%' }}></div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Disco</h3>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900">85%</div>
            <div className="text-xs text-slate-500 mt-1">Utilização</div>
            <div className="mt-3 w-full bg-slate-200 rounded-full h-2">
              <div className="bg-amber-500 h-2 rounded-full" style={{ width: '85%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}