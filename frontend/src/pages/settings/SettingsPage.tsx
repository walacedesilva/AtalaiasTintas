import React from 'react';
import { 
  Settings, 
  User, 
  Bell, 
  Shield, 
  Database,
  Palette,
  Globe,
  Moon,
  Sun,
  Monitor
} from 'lucide-react';

/**
 * Settings Page - Configurações do Sistema
 */
export default function SettingsPage(): React.ReactElement {
  const [theme, setTheme] = React.useState<'light' | 'dark' | 'system'>('light');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Configurações</h1>
          <p className="text-sm text-slate-500 mt-1">
            Gerencie as configurações do sistema e preferências
          </p>
        </div>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Account Settings */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Conta</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Nome de Usuário
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                defaultValue="admin"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Email
              </label>
              <input
                type="email"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                defaultValue="admin@atalaia.com"
              />
            </div>
            
            <button className="w-full px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors">
              Salvar Alterações
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50">
              <Bell className="h-5 w-5 text-emerald-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Notificações</h2>
          </div>
          
          <div className="space-y-4">
            {[
              { label: 'Alertas de Estoque', description: 'Receber notificações quando produtos estiverem em baixo estoque', checked: true },
              { label: 'Vendas Diárias', description: 'Resumo diário de vendas e faturamento', checked: false },
              { label: 'Relatórios Semanais', description: 'Relatórios automáticos enviados por email', checked: true },
              { label: 'Atualizações do Sistema', description: 'Notificações sobre atualizações e manutenções', checked: true }
            ].map((notification, index) => (
              <div key={index} className="flex items-start gap-3 p-3 border border-slate-200 rounded-lg">
                <input
                  type="checkbox"
                  className="mt-1"
                  defaultChecked={notification.checked}
                />
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900">{notification.label}</p>
                  <p className="text-xs text-slate-500 mt-1">{notification.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Theme Settings */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-purple-50">
              <Palette className="h-5 w-5 text-purple-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Aparência</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Tema
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'light', label: 'Claro', icon: Sun },
                  { value: 'dark', label: 'Escuro', icon: Moon },
                  { value: 'system', label: 'Sistema', icon: Monitor }
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTheme(option.value as any)}
                    className={`flex flex-col items-center gap-2 p-3 border rounded-lg transition-colors ${
                      theme === option.value 
                        ? 'border-brand-500 bg-brand-50 text-brand-700' 
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <option.icon className="h-5 w-5" />
                    <span className="text-sm font-medium">{option.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-50">
              <Shield className="h-5 w-5 text-red-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Segurança</h2>
          </div>
          
          <div className="space-y-4">
            <button className="w-full text-left p-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
              <p className="text-sm font-medium text-slate-900">Alterar Senha</p>
              <p className="text-xs text-slate-500 mt-1">Última alteração há 30 dias</p>
            </button>
            
            <button className="w-full text-left p-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
              <p className="text-sm font-medium text-slate-900">Autenticação de Dois Fatores</p>
              <p className="text-xs text-slate-500 mt-1">Adicionar camada extra de segurança</p>
            </button>
            
            <button className="w-full text-left p-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
              <p className="text-sm font-medium text-slate-900">Sessões Ativas</p>
              <p className="text-xs text-slate-500 mt-1">Gerenciar dispositivos conectados</p>
            </button>
          </div>
        </div>

        {/* System Settings */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-orange-50">
              <Database className="h-5 w-5 text-orange-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Sistema</h2>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-slate-500">Versão</p>
                <p className="font-semibold text-slate-900">v2.1.3</p>
              </div>
              <div>
                <p className="text-slate-500">Banco de Dados</p>
                <p className="font-semibold text-slate-900">PostgreSQL</p>
              </div>
              <div>
                <p className="text-slate-500">Último Backup</p>
                <p className="font-semibold text-slate-900">Hoje, 03:00</p>
              </div>
              <div>
                <p className="text-slate-500">Uptime</p>
                <p className="font-semibold text-slate-900">15d 7h 23m</p>
              </div>
            </div>
            
            <div className="flex gap-3 pt-3 border-t border-slate-200">
              <button className="flex-1 px-4 py-2 border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors">
                Fazer Backup
              </button>
              <button className="flex-1 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors">
                Verificar Updates
              </button>
            </div>
          </div>
        </div>

        {/* Regional Settings */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-50">
              <Globe className="h-5 w-5 text-cyan-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Regionalização</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Idioma
              </label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500">
                <option value="pt-BR">Português (Brasil)</option>
                <option value="en-US">English (US)</option>
                <option value="es-ES">Español</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Fuso Horário
              </label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500">
                <option value="America/Sao_Paulo">América/São Paulo (GMT-3)</option>
                <option value="America/New_York">América/Nova York (GMT-5)</option>
                <option value="Europe/London">Europa/Londres (GMT+0)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Moeda
              </label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500">
                <option value="BRL">Real Brasileiro (R$)</option>
                <option value="USD">Dólar Americano ($)</option>
                <option value="EUR">Euro (€)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}