import {
  LayoutDashboard,
  Beaker,
  Palette,
  FlaskConical,
  Layers,
  Package,
  Tag,
  type LucideIcon,
} from 'lucide-react';

export interface HelpStep {
  text: string;
}

export interface HelpAction {
  title: string;
  steps: string[];
}

export interface ScreenHelp {
  route: string;
  label: string;
  icon: LucideIcon;
  description: string;
  actions: HelpAction[];
  tips: string[];
  shortcuts?: string[];
  comingSoon?: boolean;
}

export const HELP_DATA: ScreenHelp[] = [
  {
    route: '/dashboard',
    label: 'Painel',
    icon: LayoutDashboard,
    description:
      'Visão geral do sistema com métricas em tempo real, alertas de estoque baixo e acesso rápido às principais funções.',
    actions: [
      {
        title: 'Verificar alertas de estoque',
        steps: [
          'Observe o card "Estoque Baixo" no topo — número em vermelho indica itens críticos.',
          'Clique no card ou no link "Ver todos" para ir direto à tela de Estoque filtrada.',
        ],
      },
      {
        title: 'Acessar ações rápidas',
        steps: [
          'Os botões coloridos na seção "Acesso Rápido" levam às ações mais comuns.',
          'Clique em "Nova Mistura" para iniciar uma mistura de cor imediatamente.',
          'Clique em "Imprimir Etiqueta" para gerar etiqueta de uma mistura existente.',
        ],
      },
      {
        title: 'Consultar cores populares',
        steps: [
          'Role a página para ver o painel "Cores Mais Solicitadas".',
          'Clique no nome da cor para abrir a fórmula correspondente.',
        ],
      },
    ],
    tips: [
      'O Painel é atualizado automaticamente a cada 60 segundos.',
      'Métricas com "—" indicam que os dados ainda estão sendo carregados.',
      'O número em vermelho no card Estoque alerta para itens abaixo do mínimo.',
    ],
    shortcuts: ['? — Abrir este menu de ajuda'],
  },

  {
    route: '/pigments',
    label: 'Pigmentos',
    icon: Beaker,
    description:
      'Cadastro e gerenciamento de todos os pigmentos utilizados nas misturas de tinta. Cada pigmento possui código, cor base, densidade e custo por ml.',
    actions: [
      {
        title: 'Cadastrar novo pigmento',
        steps: [
          'Clique no botão "Novo Pigmento" no canto superior direito.',
          'Preencha os campos: Código, Nome, Cor Base, Fornecedor, Densidade e Custo/ml.',
          'Clique em "Salvar" para registrar o pigmento no sistema.',
        ],
      },
      {
        title: 'Buscar pigmento',
        steps: [
          'Digite o código ou nome do pigmento no campo de busca.',
          'Use o botão "Filtros" para filtrar por cor base, fornecedor ou status.',
          'Clique no pigmento para abrir seus detalhes.',
        ],
      },
      {
        title: 'Editar ou desativar pigmento',
        steps: [
          'Abra o pigmento clicando no item da lista.',
          'Clique em "Editar" para alterar dados (custo, fornecedor, etc.).',
          'Para desativar, use o toggle "Ativo/Inativo" — pigmentos inativos não aparecem nas fórmulas.',
        ],
      },
    ],
    tips: [
      'O código do pigmento deve ser único — geralmente segue o padrão do fabricante.',
      'Mantenha o custo/ml atualizado para garantir cálculos precisos de mistura.',
      'Pigmentos inativos ainda aparecem em misturas históricas, mas não em novas.',
    ],
    comingSoon: true,
  },

  {
    route: '/colors',
    label: 'Cores Definidas',
    icon: Palette,
    description:
      'Catálogo de cores do leque tintométrico. Cada cor possui código, nome, valores LAB para comparação colorimétrica e imagem de amostra.',
    actions: [
      {
        title: 'Adicionar cor ao catálogo',
        steps: [
          'Clique em "Nova Cor" para abrir o formulário.',
          'Informe o Código da Cor, Nome e os valores L*, a*, b* (do espectrofotômetro).',
          'Faça upload da imagem de amostra (opcional).',
          'Salve para tornar a cor disponível para vinculação com fórmulas.',
        ],
      },
      {
        title: 'Vincular cor a uma fórmula',
        steps: [
          'Abra a cor desejada na lista.',
          'Na seção "Fórmulas Vinculadas", clique em "Vincular Fórmula".',
          'Selecione a fórmula existente ou crie uma nova.',
        ],
      },
      {
        title: 'Comparar cor pelo código',
        steps: [
          'Use o campo de busca para digitar o código da cor (ex: RAL 9010, NCS S 0500-N).',
          'Os resultados mostram a amostra visual e os valores colorimétricos.',
        ],
      },
    ],
    tips: [
      'Cores sem fórmula vinculada aparecem com indicador "Sem fórmula".',
      'Os valores LAB permitem comparação matemática de cores (Delta E).',
      'Use a busca por código para localizar cores de catálogos físicos rapidamente.',
    ],
    comingSoon: true,
  },

  {
    route: '/formulas',
    label: 'Fórmulas',
    icon: FlaskConical,
    description:
      'Gerenciamento das fórmulas tintométricas. Cada fórmula define quais pigmentos usar e em que proporção para reproduzir uma cor específica.',
    actions: [
      {
        title: 'Criar nova fórmula',
        steps: [
          'Clique em "Nova Fórmula" e informe o nome e a cor que ela reproduz.',
          'Defina o volume base (ex: 1 litro).',
          'Adicione cada pigmento com sua quantidade em ml.',
          'Salve — o sistema calculará as proporções automaticamente.',
        ],
      },
      {
        title: 'Calcular mistura a partir da fórmula',
        steps: [
          'Abra a fórmula desejada na lista.',
          'Clique em "Calcular Mistura".',
          'Informe o volume solicitado pelo cliente.',
          'O sistema ajusta todas as quantidades proporcionalmente.',
        ],
      },
      {
        title: 'Editar proporções',
        steps: [
          'Abra a fórmula e clique em "Editar".',
          'Ajuste as quantidades dos pigmentos conforme necessário.',
          'Salve — mis‌turas já realizadas com esta fórmula não são afetadas.',
        ],
      },
    ],
    tips: [
      'Uma fórmula pode estar vinculada a uma cor do leque ou ser personalizada.',
      'Fórmulas inativas não aparecem ao criar novas misturas, mas o histórico é mantido.',
      'O campo "Volume Base" define a referência para cálculos proporcionais.',
    ],
    comingSoon: true,
  },

  {
    route: '/mixtures',
    label: 'Misturas',
    icon: Layers,
    description:
      'Controle completo do ciclo de vida das misturas de tinta: da solicitação do cliente até a entrega. Acompanhe status, custos e histórico por cliente.',
    actions: [
      {
        title: 'Criar nova mistura',
        steps: [
          'Clique em "Nova Mistura".',
          'Selecione a fórmula desejada e informe o volume solicitado.',
          'Preencha os dados do cliente (nome, telefone).',
          'O sistema calculará os pigmentos necessários e verificará o estoque.',
          'Confirme para reservar o estoque e gerar a etiqueta.',
        ],
      },
      {
        title: 'Registrar execução da mistura',
        steps: [
          'Localize a mistura com status "Confirmada" na lista.',
          'Clique em "Executar" após realizar a mistura física.',
          'Informe as quantidades reais utilizadas (se diferirem do calculado).',
          'O sistema descontará do estoque e atualizará o status para "Produzida".',
        ],
      },
      {
        title: 'Cancelar mistura',
        steps: [
          'Abra a mistura com status "Calculada" ou "Confirmada".',
          'Clique em "Cancelar Mistura".',
          'Informe o motivo do cancelamento.',
          'O estoque reservado será automaticamente devolvido.',
        ],
      },
      {
        title: 'Consultar histórico do cliente',
        steps: [
          'Use o campo de busca e filtre por telefone do cliente.',
          'Todas as misturas do cliente serão listadas com cores e datas.',
          'Clique em qualquer mistura para ver a fórmula usada.',
        ],
      },
    ],
    tips: [
      'Status: CALCULADA → CONFIRMADA → PRODUZIDA → ENTREGUE (ou CANCELADA).',
      'Apenas misturas CALCULADA ou CONFIRMADA podem ser canceladas.',
      'O histórico de cliente facilita reproduzir uma cor já usada.',
    ],
    comingSoon: true,
  },

  {
    route: '/inventory',
    label: 'Controle de Estoque',
    icon: Package,
    description:
      'Monitoramento e gestão do estoque de pigmentos por loja. Controle saldos, alertas de mínimo, lotes e reposições.',
    actions: [
      {
        title: 'Verificar estoque atual',
        steps: [
          'A lista principal mostra todos os pigmentos com saldo atual.',
          'Itens em vermelho estão abaixo do estoque mínimo configurado.',
          'Use o filtro "Alertas" para ver apenas os críticos.',
        ],
      },
      {
        title: 'Registrar entrada de estoque',
        steps: [
          'Clique no pigmento e selecione "Adicionar Estoque".',
          'Informe a quantidade (em ml), custo/ml atualizado e número do lote.',
          'Confirme — o saldo será atualizado e o alerta desativado automaticamente.',
        ],
      },
      {
        title: 'Ajustar estoque manualmente',
        steps: [
          'Acesse o pigmento e clique em "Ajuste Manual".',
          'Informe a quantidade correta após inventário físico.',
          'Selecione o tipo: Entrada, Saída ou Correção.',
          'O sistema registrará o ajuste com data e usuário responsável.',
        ],
      },
      {
        title: 'Configurar estoque mínimo',
        steps: [
          'Abra o pigmento e clique em "Configurar Alertas".',
          'Defina o saldo mínimo em ml para disparar alertas.',
          'Defina também o saldo máximo recomendado para reposição.',
        ],
      },
    ],
    tips: [
      'O alerta de estoque baixo aparece automaticamente no Painel.',
      'Sempre informe o número do lote na entrada para rastreabilidade.',
      'Pigmentos com validade vencida aparecem com indicador de atenção.',
    ],
    comingSoon: true,
  },

  {
    route: '/labels',
    label: 'Etiquetas',
    icon: Tag,
    description:
      'Geração, personalização e impressão de etiquetas para identificação das latas de tinta misturadas. Inclui QR Code e código de rastreio.',
    actions: [
      {
        title: 'Gerar etiqueta para uma mistura',
        steps: [
          'Vá para a tela de Misturas e abra a mistura desejada.',
          'Clique em "Gerar Etiqueta" — a etiqueta é criada automaticamente ao confirmar a mistura.',
          'Na tela de Etiquetas, localize a mistura e clique em "Visualizar".',
        ],
      },
      {
        title: 'Imprimir etiqueta',
        steps: [
          'Abra a etiqueta gerada e clique em "Imprimir".',
          'Selecione a impressora configurada (térmica ou jato de tinta).',
          'Defina o número de cópias e confirme.',
          'O sistema registra data/hora da impressão para controle.',
        ],
      },
      {
        title: 'Personalizar template de etiqueta',
        steps: [
          'Acesse "Configurações de Template" no menu da tela.',
          'Escolha o template base: Padrão, Compacto ou Premium.',
          'Ative ou desative elementos: QR Code, logo, lista de pigmentos, custo.',
          'Salve como template padrão para sua loja.',
        ],
      },
    ],
    tips: [
      'A etiqueta inclui QR Code com todos os dados da mistura para reimpressão futura.',
      'Templates "Premium" incluem mais informações e são indicados para clientes exigentes.',
      'A reimpressão de etiqueta fica registrada no histórico da mistura.',
    ],
    comingSoon: true,
  },
];

export function getHelpForRoute(pathname: string): ScreenHelp | undefined {
  return HELP_DATA.find((s) => s.route === pathname);
}
