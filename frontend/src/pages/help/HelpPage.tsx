import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Palette,
  Tag,
  Receipt,
  BarChart2,
  Settings,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Lightbulb,
  ArrowRight,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface GuideAction {
  label: string;
  steps: string[];
}

interface GuideStep {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  description: string;
  actions: GuideAction[];
  tips: string[];
  route?: string;
  routeLabel?: string;
  accent: string; // tailwind bg color class for icon wrapper
  iconColor: string; // tailwind text color class
}

// ─── Conteúdo do Guia ─────────────────────────────────────────────────────────

const GUIDE_STEPS: GuideStep[] = [
  {
    icon: Sparkles,
    title: 'Bem-vindo ao Atalaia Tintas',
    subtitle: 'Seu sistema completo de gestão para tintas e tintometria',
    description:
      'Este guia vai mostrar como usar cada área do sistema de forma prática. Navegue pelos módulos abaixo ou siga o passo a passo usando os botões "Anterior" e "Próximo". Ao final, você estará pronto para operar o sistema com confiança.',
    actions: [
      {
        label: 'Como usar este guia',
        steps: [
          'Use a barra lateral esquerda para pular diretamente para qualquer módulo.',
          'Clique em "Próximo" para seguir a ordem recomendada de aprendizado.',
          'Ao final de cada módulo, clique em "Ir para a tela" para praticar.',
          'Pressione ← → no teclado para navegar rapidamente.',
        ],
      },
    ],
    tips: [
      'Você pode acessar este guia a qualquer momento pelo botão "Ajuda" no topo.',
      'Recomendamos seguir a ordem apresentada na primeira vez.',
    ],
    accent: 'bg-brand-50',
    iconColor: 'text-brand-600',
  },
  {
    icon: LayoutDashboard,
    title: 'Painel (Dashboard)',
    subtitle: 'Visão geral do negócio em tempo real',
    description:
      'O Painel é a primeira tela que você vê ao entrar no sistema. Ele centraliza as informações mais importantes: alertas de estoque, resumo de vendas e acesso rápido às funções principais.',
    actions: [
      {
        label: 'Verificar alertas de estoque',
        steps: [
          'Observe o card "Estoque Baixo" — número em vermelho indica produtos críticos.',
          'Clique no card para ir direto à lista de produtos abaixo do mínimo.',
        ],
      },
      {
        label: 'Acompanhar vendas do dia',
        steps: [
          'Os cards de métricas mostram total vendido, número de pedidos e ticket médio.',
          'Os dados se atualizam automaticamente a cada 60 segundos.',
        ],
      },
      {
        label: 'Usar acesso rápido',
        steps: [
          'Os botões coloridos levam diretamente para as ações mais usadas.',
          'Use-os como atalho para ganhar tempo no dia a dia.',
        ],
      },
    ],
    tips: [
      'Métricas com "—" indicam dados sendo carregados — aguarde alguns segundos.',
      'O Dashboard é personalizado por loja — cada unidade vê seus próprios dados.',
    ],
    route: '/dashboard',
    routeLabel: 'Ir para o Painel',
    accent: 'bg-blue-50',
    iconColor: 'text-blue-600',
  },
  {
    icon: Package,
    title: 'Controle de Estoque',
    subtitle: 'Gerencie produtos, entradas e quantidades',
    description:
      'O módulo de Estoque permite controlar todos os produtos da loja: saldos atuais, histórico de entradas, alertas de quantidade mínima e reposição. É a base para o bom funcionamento dos demais módulos.',
    actions: [
      {
        label: 'Verificar saldo de um produto',
        steps: [
          'Acesse "Estoque" no menu lateral.',
          'Use a barra de busca para encontrar o produto pelo nome ou código.',
          'O saldo atual aparece na coluna "Quantidade" — itens em vermelho estão abaixo do mínimo.',
        ],
      },
      {
        label: 'Registrar entrada de mercadoria',
        steps: [
          'Na aba "Entradas", clique em "Nova Entrada" ou "Entrada Manual".',
          'Informe os dados da nota fiscal: número, fornecedor, data e itens recebidos.',
          'Confirme — o estoque será atualizado automaticamente.',
        ],
      },
      {
        label: 'Configurar estoque mínimo',
        steps: [
          'Abra o produto desejado e clique em "Editar".',
          'Defina o campo "Estoque Mínimo" para ativar os alertas automáticos.',
          'Salve — o sistema alertará quando o produto atingir esse limite.',
        ],
      },
    ],
    tips: [
      'Sempre registre entradas assim que a mercadoria chegar para manter o saldo correto.',
      'Produtos com alerta vermelho aparecem também no Painel como prioridade.',
      'O histórico de movimentações fica registrado para auditoria.',
    ],
    route: '/inventory',
    routeLabel: 'Ir para o Estoque',
    accent: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
  },
  {
    icon: Palette,
    title: 'Tintometria',
    subtitle: 'Misturas de cores com fórmulas precisas',
    description:
      'A Tintometria é o coração do sistema para lojas de tintas. Aqui você cadastra fórmulas colorimétrias, realiza misturas para clientes e controla o histórico de cada cor produzida.',
    actions: [
      {
        label: 'Criar uma nova mistura para cliente',
        steps: [
          'Acesse "Tintometria" no menu e clique em "Nova Mistura".',
          'Selecione a fórmula da cor desejada pelo cliente.',
          'Informe o volume em litros e os dados do cliente.',
          'O sistema calcula automaticamente as quantidades de cada pigmento.',
          'Confirme — a mistura fica registrada e o estoque é reservado.',
        ],
      },
      {
        label: 'Buscar cor pelo código ou nome',
        steps: [
          'Use a busca por código (ex: RAL 9010, Coral, Suvinil).',
          'O sistema mostra a amostra visual e a fórmula correspondente.',
          'Selecione a cor e avance para o cálculo da mistura.',
        ],
      },
      {
        label: 'Consultar histórico de um cliente',
        steps: [
          'Na lista de misturas, filtre pelo telefone ou nome do cliente.',
          'Todas as misturas anteriores aparecem com cor, data e fórmula usada.',
          'Clique em qualquer registro para repetir a mistura com os mesmos dados.',
        ],
      },
    ],
    tips: [
      'Status da mistura: CALCULADA → CONFIRMADA → PRODUZIDA → ENTREGUE.',
      'Guarde o histórico de cada cliente para facilitar reposições futuras.',
      'Fórmulas podem ser editadas sem afetar o histórico de misturas já realizadas.',
    ],
    route: '/tintometry',
    routeLabel: 'Ir para Tintometria',
    accent: 'bg-purple-50',
    iconColor: 'text-purple-600',
  },
  {
    icon: Tag,
    title: 'Etiquetas',
    subtitle: 'Geração e impressão de etiquetas para latas',
    description:
      'O módulo de Etiquetas gera automaticamente as etiquetas com todas as informações da mistura: cor, fórmula, cliente, data, código QR e dados da loja. Essencial para rastreabilidade e profissionalismo.',
    actions: [
      {
        label: 'Gerar etiqueta de uma mistura',
        steps: [
          'Após confirmar uma mistura em Tintometria, a etiqueta é criada automaticamente.',
          'Acesse "Etiquetas" no menu e localize a mistura pelo nome ou data.',
          'Clique em "Visualizar" para conferir o layout antes de imprimir.',
        ],
      },
      {
        label: 'Imprimir etiqueta',
        steps: [
          'Abra a etiqueta e clique em "Imprimir".',
          'Selecione a impressora (térmica ou jato de tinta).',
          'Defina o número de cópias e confirme a impressão.',
          'O sistema registra a data e hora de cada impressão.',
        ],
      },
      {
        label: 'Personalizar o template',
        steps: [
          'Acesse as configurações de template dentro do módulo Etiquetas.',
          'Escolha entre os modelos: Padrão, Compacto ou Premium.',
          'Ative ou desative elementos como logo, QR Code e lista de pigmentos.',
          'Salve o template como padrão da sua loja.',
        ],
      },
    ],
    tips: [
      'O QR Code na etiqueta permite reimprimir e consultar a fórmula no futuro.',
      'Templates Premium incluem mais detalhes e são indicados para clientes exigentes.',
      'Reimprimir uma etiqueta fica registrado no histórico da mistura.',
    ],
    route: '/labels',
    routeLabel: 'Ir para Etiquetas',
    accent: 'bg-amber-50',
    iconColor: 'text-amber-600',
  },
  {
    icon: Receipt,
    title: 'Fiscal / NFe',
    subtitle: 'Notas fiscais e documentos eletrônicos',
    description:
      'O módulo Fiscal gerencia todas as notas fiscais eletrônicas da loja: emissão, recebimento, cancelamento e conformidade tributária. Mantém a loja regularizada e os registros contábeis organizados.',
    actions: [
      {
        label: 'Visualizar notas fiscais recebidas',
        steps: [
          'Acesse "Fiscal/NFe" no menu lateral.',
          'A aba "Entradas" lista todas as notas de compra registradas.',
          'Filtre por fornecedor, período ou status para localizar uma nota específica.',
        ],
      },
      {
        label: 'Importar NFe por XML',
        steps: [
          'Na aba Entradas, clique em "Importar XML".',
          'Selecione o arquivo XML da nota fiscal enviado pelo fornecedor.',
          'O sistema valida e importa todos os itens automaticamente.',
          'Confirme para vincular os produtos ao estoque.',
        ],
      },
      {
        label: 'Lançar entrada manual',
        steps: [
          'Clique em "Entrada Manual" para notas sem XML disponível.',
          'Preencha os dados da nota: número, série, CNPJ do fornecedor e itens.',
          'Confirme — a entrada fica registrada com origem "Manual".',
        ],
      },
    ],
    tips: [
      'Notas com status pendente aparecem em destaque no Painel.',
      'Guarde os XMLs das notas recebidas para importação posterior.',
      'O sistema valida o CNPJ do fornecedor automaticamente.',
    ],
    route: '/fiscal',
    routeLabel: 'Ir para Fiscal/NFe',
    accent: 'bg-rose-50',
    iconColor: 'text-rose-600',
  },
  {
    icon: BarChart2,
    title: 'Relatórios',
    subtitle: 'Análises, métricas e exportações',
    description:
      'O módulo de Relatórios consolida dados de todas as áreas do sistema em gráficos e tabelas prontos para análise. Use para tomar decisões baseadas em dados e compartilhar resultados com a gestão.',
    actions: [
      {
        label: 'Gerar relatório de vendas',
        steps: [
          'Acesse "Relatórios" e selecione o período desejado (dia, semana, mês).',
          'Escolha o tipo: Vendas, Estoque, Tintometria ou Clientes.',
          'Clique em "Gerar Relatório" para visualizar os dados.',
        ],
      },
      {
        label: 'Exportar dados',
        steps: [
          'Com o relatório gerado, clique em "Exportar".',
          'Escolha o formato: PDF para impressão ou Excel para análise.',
          'O arquivo é baixado diretamente no navegador.',
        ],
      },
      {
        label: 'Comparar períodos',
        steps: [
          'Selecione "Comparar Períodos" no topo do relatório.',
          'Defina dois intervalos de tempo para comparar lado a lado.',
          'Os gráficos mostram variação percentual entre os períodos.',
        ],
      },
    ],
    tips: [
      'Relatórios de Tintometria ajudam a identificar as cores mais solicitadas.',
      'Use o relatório de Estoque para planejar reposições antes que o mínimo seja atingido.',
      'Relatórios em PDF ficam com logo e cabeçalho da loja automaticamente.',
    ],
    route: '/reports',
    routeLabel: 'Ir para Relatórios',
    accent: 'bg-sky-50',
    iconColor: 'text-sky-600',
  },
  {
    icon: Settings,
    title: 'Configurações',
    subtitle: 'Personalize o sistema para sua loja',
    description:
      'Em Configurações você ajusta a aparência do sistema, gerencia dados da sua conta, configura notificações e define as preferências de segurança. Cada usuário pode personalizar sua própria experiência.',
    actions: [
      {
        label: 'Personalizar a cor do sistema',
        steps: [
          'Acesse "Configurações" no menu lateral.',
          'Na seção "Aparência", escolha uma das cores predefinidas ou use a cor personalizada.',
          'Ajuste o tamanho da fonte conforme sua preferência.',
          'Clique em "Aplicar Personalização" — as mudanças entram em vigor imediatamente.',
        ],
      },
      {
        label: 'Atualizar dados da conta',
        steps: [
          'Na seção "Conta", edite seu nome de usuário e email.',
          'Clique em "Salvar Alterações" para confirmar.',
        ],
      },
      {
        label: 'Configurar notificações',
        steps: [
          'Na seção "Notificações", ative ou desative cada tipo de alerta.',
          'Alertas de estoque baixo são recomendados para todos os usuários.',
        ],
      },
    ],
    tips: [
      'As personalizações de aparência ficam salvas para seu próximo acesso.',
      'Altere sua senha regularmente pela seção "Segurança".',
      'Cada usuário tem suas próprias configurações de notificação.',
    ],
    route: '/settings',
    routeLabel: 'Ir para Configurações',
    accent: 'bg-slate-100',
    iconColor: 'text-slate-600',
  },
];

// ─── Componente principal ──────────────────────────────────────────────────────

export default function HelpPage(): React.ReactElement {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = React.useState(0);

  const step = GUIDE_STEPS[currentStep];
  const isFirst = currentStep === 0;
  const isLast = currentStep === GUIDE_STEPS.length - 1;
  const progress = Math.round((currentStep / (GUIDE_STEPS.length - 1)) * 100);

  // Keyboard navigation
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      const isEditing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
      if (isEditing) return;
      if (e.key === 'ArrowRight' && !isLast) setCurrentStep((s) => s + 1);
      if (e.key === 'ArrowLeft' && !isFirst) setCurrentStep((s) => s - 1);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isFirst, isLast]);

  const Icon = step.icon;

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col">
      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="px-6 pt-6 pb-4 border-b border-slate-200 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-lg sm:text-xl font-bold text-slate-900">Guia do Sistema</h1>
              <p className="text-xs sm:text-sm text-slate-500">
                Passo {currentStep + 1} de {GUIDE_STEPS.length}
                <span className="hidden sm:inline"> — use ← → para navegar</span>
              </p>
            </div>
            <span className="text-sm font-semibold text-brand-600">
              {progress}%
            </span>
          </div>
          {/* Progress bar */}
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-600 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Progresso do guia"
            />
          </div>
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────── */}
      <div className="flex flex-1 max-w-5xl mx-auto w-full px-3 sm:px-6 py-4 sm:py-6 gap-6">

        {/* Sidebar — step index */}
        <aside className="hidden md:flex flex-col gap-1 w-44 shrink-0">
          {GUIDE_STEPS.map((s, idx) => {
            const SIcon = s.icon;
            return (
              <button
                key={idx}
                onClick={() => setCurrentStep(idx)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-sm transition-colors ${
                  idx === currentStep
                    ? 'bg-brand-600 text-white font-semibold'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
                aria-current={idx === currentStep ? 'step' : undefined}
              >
                <SIcon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                <span className="truncate leading-tight">{s.title.split(' ')[0] === 'Bem-vindo' ? 'Bem-vindo' : s.title}</span>
              </button>
            );
          })}
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0" aria-label={`Passo ${currentStep + 1}: ${step.title}`}>
          <div className="card p-4 sm:p-6 lg:p-8 flex flex-col gap-5 sm:gap-6 animate-fade-in">

            {/* Step header */}
            <div className="flex items-start gap-3 sm:gap-4">
              <div className={`flex h-11 w-11 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-xl sm:rounded-2xl ${step.accent}`}>
                <Icon className={`h-5 w-5 sm:h-7 sm:w-7 ${step.iconColor}`} aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-[10px] sm:text-xs font-semibold uppercase tracking-widest text-slate-400">
                    Módulo {currentStep === 0 ? '—' : currentStep}
                  </span>
                </div>
                <h2 className="text-base sm:text-xl font-bold text-slate-900 leading-snug">{step.title}</h2>
                <p className={`text-xs sm:text-sm font-medium ${step.iconColor}`}>{step.subtitle}</p>
              </div>
            </div>

            {/* Description */}
            <p className="text-slate-600 leading-relaxed">{step.description}</p>

            {/* Actions */}
            <div className="space-y-4">
              {step.actions.map((action, ai) => (
                <div key={ai} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-800 mb-3">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" aria-hidden="true" />
                    {action.label}
                  </h3>
                  <ol className="space-y-2">
                    {action.steps.map((s, si) => (
                      <li key={si} className="flex items-start gap-3 text-sm text-slate-600">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700 text-[11px] font-bold mt-0.5">
                          {si + 1}
                        </span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>

            {/* Tips */}
            {step.tips.length > 0 && (
              <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-800 mb-2">
                  <Lightbulb className="h-4 w-4 shrink-0" aria-hidden="true" />
                  Dicas práticas
                </h3>
                <ul className="space-y-1.5">
                  {step.tips.map((tip, ti) => (
                    <li key={ti} className="flex items-start gap-2 text-sm text-amber-700">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" aria-hidden="true" />
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Navigation buttons */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3 pt-3 border-t border-slate-100">
              {/* Prev / Next */}
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentStep((s) => s - 1)}
                  disabled={isFirst}
                  className="flex items-center gap-1.5 px-3 sm:px-4 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label="Passo anterior"
                >
                  <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                  Anterior
                </button>

                {!isLast ? (
                  <button
                    onClick={() => setCurrentStep((s) => s + 1)}
                    className="flex items-center gap-1.5 px-3 sm:px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition-colors"
                    aria-label="Próximo passo"
                  >
                    Próximo
                    <ChevronRight className="h-4 w-4" aria-hidden="true" />
                  </button>
                ) : (
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center gap-1.5 px-3 sm:px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
                  >
                    Começar a usar
                    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                  </button>
                )}
              </div>

              {/* Go to screen button */}
              {step.route && (
                <button
                  onClick={() => navigate(step.route!)}
                  className="flex w-full sm:w-auto items-center justify-center gap-1.5 px-3 sm:px-4 py-2 rounded-lg border border-brand-200 bg-brand-50 text-brand-700 text-sm font-medium hover:bg-brand-100 transition-colors"
                >
                  {step.routeLabel}
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </button>
              )}
            </div>

          </div>
        </main>
      </div>

      {/* Mobile step dots */}
      <div className="md:hidden flex justify-center gap-1.5 pb-6">
        {GUIDE_STEPS.map((_, idx) => (
          <button
            key={idx}
            onClick={() => setCurrentStep(idx)}
            className={`h-2 rounded-full transition-all ${
              idx === currentStep ? 'w-6 bg-brand-600' : 'w-2 bg-slate-300'
            }`}
            aria-label={`Ir para passo ${idx + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
