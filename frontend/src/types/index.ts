/**
 * Core domain types for Atalaia Tintas paint store system
 * These types match the Django API models and serializers
 */

// Base types
export interface BaseModel {
  id: number;
  created_at: string;
  updated_at: string;
}

// Loja
export interface Loja {
  id: number;
  nome: string;
  uf: string | null;
  cidade: string | null;
  ativa: boolean;
}

// Authentication types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
}

export interface AuthResponse {
  token: string;
  user: User;
  session_id: number;
  message: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

// Tintometry domain types
export interface Pigmento extends BaseModel {
  codigo: string;
  nome: string;
  cor_base: string;
  densidade: string; // Decimal field as string
  poder_tintorial: string; // Decimal field as string, 0-100 %
  fornecedor: string;
  codigo_fornecedor: string | null;
  concentracao_maxima: string; // Decimal field as string, 0-100 %
  r: number; // 0-255
  g: number; // 0-255
  b: number; // 0-255
  cor_hex: string; // readonly: #rrggbb derived from r,g,b
  ativo: boolean;
}

export interface LequeCorDefinida extends BaseModel {
  codigo_cor: string;
  nome_cor: string;
  descricao?: string;
  familia_cor: string;
  linha_produto: string;
  l_value: string; // CIE Lab L* 0-100
  a_value: string; // CIE Lab a* -128 to 127
  b_value: string; // CIE Lab b* -128 to 127
  r: number; // 0-255
  g: number; // 0-255
  b: number; // 0-255
  cor_hex: string; // readonly: #rrggbb
  amostra_cor?: string | null;
  ativo: boolean;
  data_criacao: string;
}

export interface ItemFormula {
  id: number;
  pigmento: number; // FK id
  pigmento_details?: Pigmento;
  quantidade: string; // ml, Decimal as string
  sequencia: number;
  observacoes?: string | null;
}

export interface FormulaTintometrica extends BaseModel {
  cor_definida: number; // FK id
  cor_definida_details?: LequeCorDefinida;
  base_produto: number; // FK id
  codigo_formula: string;
  nome_formula: string;
  versao: string;
  volume_base: string; // Decimal as string (litros)
  instrucoes?: string | null;
  tempo_mistura_minutos: number;
  aprovada: boolean;
  testada: boolean;
  data_aprovacao?: string | null;
  usuario_aprovacao?: number | null;
  ativa: boolean;
  itens: ItemFormula[];
  total_pigmentos: number;
  quantidade_total_pigmentos: number;
}

export interface ItemMistura {
  id: number;
  pigmento: number; // FK id
  pigmento_details?: Pigmento;
  quantidade_calculada: string; // ml
  quantidade_executada?: string | null;
  custo_unitario?: string | null;
  custo_total?: string | null;
  lote_utilizado?: string | null;
  estoque_antes?: string | null;
  estoque_depois?: string | null;
  sequencia: number;
  variacao_percentual?: number;
  quantidade_final?: string;
}

export interface MisturaTinta extends BaseModel {
  codigo_mistura: string;
  formula: number; // FK id
  formula_details?: FormulaTintometrica;
  loja: number; // FK id
  usuario_operacao?: number | null;
  cliente_nome: string;
  cliente_documento?: string | null;
  cliente_telefone?: string | null;
  cliente_email?: string | null;
  volume_solicitado: string; // Decimal as string (litros)
  volume_produzido?: string | null;
  custo_total?: string | null;
  custo_base?: string | null;
  custo_pigmentos?: string | null;
  situacao: 'CALCULADA' | 'CONFIRMADA' | 'PRODUZIDA' | 'ENTREGUE' | 'CANCELADA';
  data_confirmacao?: string | null;
  data_producao?: string | null;
  data_entrega?: string | null;
  data_cancelamento?: string | null;
  motivo_cancelamento?: string | null;
  observacoes_cliente?: string | null;
  observacoes_internas?: string | null;
  cor_aprovada_cliente?: boolean;
  data_aprovacao_cor?: string | null;
  pedido_venda_id?: string | null;
  itens: ItemMistura[];
  etiqueta?: EtiquetaMistura | null;
  fator_proporcao?: number;
  economia?: number;
}

export interface EstoquePigmento extends BaseModel {
  pigmento: Pigmento;
  loja: number; // FK id
  saldo_ml: string; // Decimal field as string (ml)
  saldo_minimo: string; // Decimal field as string (ml)
  saldo_maximo: string; // Decimal field as string (ml)
  custo_ml: string; // Decimal field as string
  ativo: boolean;
  /** @deprecated kept for backwards compat — use saldo_ml */
  quantidade_atual?: string;
  /** @deprecated kept for backwards compat — use saldo_minimo */
  quantidade_minima?: string;
}

export interface MovimentoEstoque extends BaseModel {
  pigmento: Pigmento;
  tipo_movimento: 'entrada' | 'saida' | 'ajuste' | 'perda';
  quantidade: string; // Decimal field as string
  saldo_anterior: string; // Decimal field as string
  saldo_atual: string; // Decimal field as string
  usuario: User;
  observacoes?: string;
  mistura_relacionada?: MisturaTinta;
}

export interface EtiquetaMistura extends BaseModel {
  codigo_etiqueta: string;
  qr_code_data?: string;
  codigo_barras?: string;
  impressa: boolean;
  data_impressao?: string | null;
  usuario_impressao?: number | null;
  reimpressoes: number;
  historico_reimpressoes?: unknown;
  titulo_personalizado?: string | null;
  observacoes_etiqueta?: string | null;
  dados_qr_formatados?: string;
}

// API request/response types
export interface MisturaCalculationRequest {
  formula_id: number;
  volume_desejado: string;
  ajustes_componentes?: {
    pigmento_id: number;
    novo_percentual: string;
  }[];
}

export interface MisturaCalculationResponse {
  volume_total: string;
  custo_estimado: string;
  componentes_calculados: ComponenteCalculado[];
  alertas_estoque: AlertaEstoque[];
  viabilidade: boolean;
  observacoes: string[];
}

export interface ComponenteCalculado {
  pigmento: Pigmento;
  quantidade_necessaria: string;
  quantidade_disponivel: string;
  custo_componente: string;
  suficiente: boolean;
}

export interface AlertaEstoque {
  pigmento: Pigmento;
  nivel_atual: string;
  nivel_minimo: string;
  status: 'ok' | 'baixo' | 'critico' | 'indisponivel';
  recomendacao: string;
}

export interface ColorAnalysisRequest {
  cor_hex?: string;
  cor_rgb?: {
    r: number;
    g: number;
    b: number;
  };
  tolerancia?: number;
}

export interface ColorAnalysisResponse {
  cores_similares: LequeCorDefinida[];
  analise_cientifica: {
    hue: number;
    saturation: number;
    lightness: number;
    lab_values: {
      l: number;
      a: number;
      b: number;
    };
  };
  sugestoes_formula: FormulaTintometrica[];
}

// Dashboard/UI specific types
export interface DashboardStats {
  total_templates: number;
  misturas_hoje: number;
  estoque_baixo: number;
  etiquetas_geradas: number;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  href: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

// Form validation types using Zod
export interface FormErrors {
  [key: string]: string | undefined;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// API error response
export interface APIError {
  detail?: string;
  message?: string;
  errors?: {
    [field: string]: string[];
  };
  status_code: number;
}

// User preferences
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  density: 'compact' | 'comfortable';
  accessibility_mode: boolean;
  default_volume_unit: 'litros' | 'mililitros';
  quick_actions: string[];
}

// search and filtering
export interface SearchFilters {
  query?: string;
  categoria?: string;
  cor_base?: string;
  include_inactive?: boolean;
  status?: string;
  date_from?: string;
  date_to?: string;
  user_id?: number;
  ordering?: string;
  page?: number;
  page_size?: number;
}

// ---------------------------------------------------------------------------
// Inventory (Estoque) domain types
// ---------------------------------------------------------------------------

export type StatusEstoque = 'NORMAL' | 'BAIXO' | 'ZERADO';

export interface EstoqueLojaItem {
  id: number;
  loja: number;
  produto_id: string;
  produto_codigo: string;
  produto_nome: string;
  produto_base_nome: string;
  marca_nome: string;
  unidade_sigla: string;
  estoque_minimo: string;
  preco_custo: string;
  preco_venda: string;
  quantidade_atual: string;
  quantidade_reservada: string;
  quantidade_disponivel: string;
  status_estoque: StatusEstoque;
  localizacao: string | null;
  data_ultima_movimentacao: string | null;
  bloqueado_venda: boolean;
}

export interface EstoqueResumo {
  total_itens: number;
  estoque_zerado: number;
  estoque_baixo: number;
  valor_total_custo: string;
}

export type StatusLote = 'ATIVO' | 'VENCIDO' | 'ESGOTADO' | 'BLOQUEADO' | 'QUARENTENA';

export interface LoteProduto {
  id: number;
  produto: string;       // UUID
  loja: number;
  numero_lote: string;
  data_fabricacao: string | null;
  data_validade: string | null;
  data_entrada: string;
  quantidade_inicial: string;
  quantidade_atual: string;
  unidade: number;
  custo_unitario: string | null;
  status: StatusLote;
  documento_entrada: string | null;
  observacoes: string | null;
  esta_vencido: boolean;
  dias_para_vencer: number | null;
}

export type StatusEntrada = 'RASCUNHO' | 'PENDENTE' | 'CONFIRMADA' | 'CANCELADA';

export interface EntradaMercadoriaItem {
  id: number;
  produto: string | null;
  descricao_nfe: string;
  codigo_nfe: string;
  ncm: string;
  cfop: string;
  cean: string;
  quantidade: string;
  unidade: number | null;
  unidade_nfe: string;
  valor_unitario: string;
  valor_total: string;
  desconto: string;
  valor_icms: string;
  valor_ipi: string;
  valor_pis: string;
  valor_cofins: string;
  lote: number | null;
  status: 'PENDENTE' | 'VINCULADO' | 'PROCESSADO' | 'IGNORADO';
}

export interface EntradaMercadoria {
  id: number;
  loja: number;
  tipo_entrada: string;
  fornecedor_cnpj: string;
  fornecedor_nome: string;
  chave_acesso_nfe: string | null;
  numero_nfe: string | null;
  serie_nfe: string | null;
  data_emissao_nfe: string | null;
  data_entrada: string;
  valor_total_nfe: string | null;
  valor_total_entrada: string;
  status: StatusEntrada;
  observacoes: string | null;
  itens: EntradaMercadoriaItem[];
}

// ─── Sales domain ─────────────────────────────────────────────────────────────
export type TipoCliente = 'PF' | 'PJ';

export interface Cliente {
  id: number;
  codigo_cliente: string;
  tipo_cliente: TipoCliente;
  nome: string;
  razao_social: string | null;
  nome_fantasia: string | null;
  cnpj: string | null;
  cpf: string | null;
  nome_completo: string;
  email: string | null;
  telefone_principal: string | null;
  celular: string | null;
  ativo: boolean;
  created_at: string;
}

export type SituacaoPedido =
  | 'ORCAMENTO'
  | 'APROVADO'
  | 'PRODUCAO'
  | 'PRONTO'
  | 'ENTREGUE'
  | 'CANCELADO';

export type NfeSituacao =
  | 'PENDENTE'
  | 'EMITIDA'
  | 'CANCELADA'
  | 'REJEITADA'
  | 'NAO_APLICAVEL';

export interface ItemPedidoVenda {
  id: number;
  produto_variacao: number;
  quantidade: string;
  preco_unitario: string;
  preco_total: string;
  unidade_venda: number;
  quantidade_base: string;
  fator_conversao_aplicado: string | null;
  desconto_valor: string;
  desconto_percentual: string;
  observacoes: string | null;
  sequencia: number;
}

export interface PedidoVenda {
  id: number;
  numero_pedido: string;
  loja: number;
  cliente: number;
  cliente_nome: string;
  vendedor: number | null;
  situacao: SituacaoPedido;
  situacao_display: string;
  data_pedido: string;
  data_aprovacao: string | null;
  data_entrega_prevista: string | null;
  valor_subtotal: string;
  valor_desconto: string;
  valor_total: string;
  forma_pagamento: string;
  parcelas: number;
  tipo_entrega: string;
  itens: ItemPedidoVenda[];
  observacoes: string | null;
}

export interface Venda {
  id: string;
  numero_venda: string;
  loja: number;
  cliente: number | null;
  cliente_nome: string;
  data_venda: string;
  valor_total: string;
  valor_desconto: string;
  valor_liquido: string;
  nfe_situacao: NfeSituacao;
  nfe_situacao_display: string;
  nfe_tipo_emissao: string;
  nfe_protocolo: string | null;
  nfe_chave_acesso: string | null;
  cancelada: boolean;
  motivo_cancelamento: string | null;
  data_cancelamento: string | null;
}