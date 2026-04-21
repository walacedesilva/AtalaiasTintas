import React from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Palette,
} from 'lucide-react';

const BRAND_COLORS = [
  { name: 'Azul', value: '#2563eb' },
  { name: 'Verde', value: '#16a34a' },
  { name: 'Violeta', value: '#7c3aed' },
  { name: 'Rosa', value: '#db2777' },
  { name: 'Laranja', value: '#ea580c' },
  { name: 'Ciano', value: '#0891b2' },
  { name: 'Índigo', value: '#4f46e5' },
  { name: 'Vermelho', value: '#dc2626' },
];

const PREF_KEY = 'atalaia_ui_prefs';

function loadPrefs(): { accentColor?: string; fontSize?: string } {
  try { return JSON.parse(localStorage.getItem(PREF_KEY) ?? '{}'); } catch { return {}; }
}

function applyAccentColor(hex: string): void {
  const root = document.documentElement;
  const shades: [string, string][] = [
    ['--color-brand-50',  `color-mix(in srgb, ${hex}  8%, white)`],
    ['--color-brand-100', `color-mix(in srgb, ${hex} 15%, white)`],
    ['--color-brand-200', `color-mix(in srgb, ${hex} 25%, white)`],
    ['--color-brand-300', `color-mix(in srgb, ${hex} 40%, white)`],
    ['--color-brand-400', `color-mix(in srgb, ${hex} 60%, white)`],
    ['--color-brand-500', `color-mix(in srgb, ${hex} 80%, white)`],
    ['--color-brand-600', hex],
    ['--color-brand-700', `color-mix(in srgb, ${hex} 80%, black)`],
    ['--color-brand-800', `color-mix(in srgb, ${hex} 65%, black)`],
    ['--color-brand-900', `color-mix(in srgb, ${hex} 50%, black)`],
    ['--color-brand-950', `color-mix(in srgb, ${hex} 35%, black)`],
  ];
  shades.forEach(([prop, val]) => root.style.setProperty(prop, val));
}

function applyFontSize(size: 'sm' | 'md' | 'lg'): void {
  document.documentElement.style.fontSize = { sm: '14px', md: '16px', lg: '18px' }[size];
}

/**
 * Settings Page - Configurações do Sistema
 */
export default function SettingsPage(): React.ReactElement {
  const savedPrefs = React.useMemo(loadPrefs, []);
  const [accentColor, setAccentColor] = React.useState(savedPrefs.accentColor ?? '#2563eb');
  const [fontSize, setFontSize] = React.useState<'sm' | 'md' | 'lg'>(
    (savedPrefs.fontSize as 'sm' | 'md' | 'lg') ?? 'md'
  );
  const [applied, setApplied] = React.useState(false);

  // Preferences are applied on app load by RootLayout.
  // Re-apply here only to handle the case where the user opens settings
  // before navigating elsewhere (component already mounted).

  function handleApply(): void {
    applyAccentColor(accentColor);
    applyFontSize(fontSize);
    localStorage.setItem(PREF_KEY, JSON.stringify({ accentColor, fontSize }));
    setApplied(true);
    setTimeout(() => setApplied(false), 2000);
  }

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

        {/* Appearance / Personalização */}
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-purple-50">
              <Palette className="h-5 w-5 text-purple-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Aparência</h2>
          </div>
          
          <div className="space-y-5">
            {/* Cor de destaque */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Cor principal
              </label>
              <div className="flex flex-wrap gap-2">
                {BRAND_COLORS.map((color) => (
                  <button
                    key={color.value}
                    title={color.name}
                    aria-label={color.name}
                    onClick={() => setAccentColor(color.value)}
                    className={`h-8 w-8 rounded-full transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                      accentColor === color.value
                        ? 'ring-2 ring-offset-2 ring-slate-400 scale-110'
                        : ''
                    }`}
                    style={{ backgroundColor: color.value }}
                  />
                ))}
                {/* Cor livre */}
                <label
                  className="h-8 w-8 rounded-full border-2 border-dashed border-slate-300 flex items-center justify-center cursor-pointer hover:border-slate-400 transition-colors"
                  title="Cor personalizada"
                  aria-label="Cor personalizada"
                >
                  <input
                    type="color"
                    className="sr-only"
                    value={accentColor}
                    onChange={(e) => setAccentColor(e.target.value)}
                  />
                  <Palette className="h-3.5 w-3.5 text-slate-400" />
                </label>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Cor selecionada:{' '}
                <span
                  className="inline-block px-2 py-0.5 rounded font-mono text-white text-xs"
                  style={{ backgroundColor: accentColor }}
                >
                  {accentColor}
                </span>
              </p>
            </div>

            {/* Tamanho de fonte */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Tamanho da fonte
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'sm', label: 'Compacto', sample: 'Aa' },
                  { value: 'md', label: 'Normal', sample: 'Aa' },
                  { value: 'lg', label: 'Grande', sample: 'Aa' },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setFontSize(opt.value as 'sm' | 'md' | 'lg')}
                    className={`flex flex-col items-center gap-1 p-3 border rounded-lg transition-colors ${
                      fontSize === opt.value
                        ? 'border-brand-500 bg-brand-50 text-brand-700'
                        : 'border-slate-200 hover:border-slate-300 text-slate-600'
                    }`}
                  >
                    <span
                      className="font-semibold leading-none"
                      style={{
                        fontSize: opt.value === 'sm' ? 14 : opt.value === 'md' ? 18 : 22,
                      }}
                    >
                      {opt.sample}
                    </span>
                    <span className="text-xs">{opt.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleApply}
              className="w-full px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
            >
              {applied ? 'Aplicado ✓' : 'Aplicar Personalização'}
            </button>
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

      </div>
    </div>
  );
}
