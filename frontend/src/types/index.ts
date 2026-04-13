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
  densidade: string; // Decimal field as string
  preco_litro: string; // Decimal field as string
  cor_hex: string;
  ativo: boolean;
  observacoes?: string;
}

export interface LequeCorDefinida extends BaseModel {
  codigo: string;
  nome: string;
  descricao?: string;
  cor_rgb: string;
  cor_hex: string;
  formula_base?: FormulaTintometrica;
  categoria: string;
  popularidade: number;
  ativo: boolean;
}

export interface FormulaTintometrica extends BaseModel {
  codigo: string;
  nome: string;
  base_tinta: string;
  volume_litros: string; // Decimal field as string
  densidade_final: string; // Decimal field as string
  cor_resultante_hex: string;
  observacoes?: string;
  ativo: boolean;
  componentes: ComponenteFormula[];
}

export interface ComponenteFormula {
  pigmento: Pigmento;
  quantidade_gramas: string; // Decimal field as string
  percentual: string; // Decimal field as string
}

export interface MisturaTinta extends BaseModel {
  formula: FormulaTintometrica;
  quantidade_produzida: string; // Decimal field as string
  data_mistura: string;
  operador: User;
  status: 'planejada' | 'em_preparacao' | 'concluida' | 'falhada';
  observacoes?: string;
  custo_total: string; // Decimal field as string
  etiqueta_gerada?: EtiquetaMistura;
  movimentos_estoque: MovimentoEstoque[];
}

export interface EstoquePigmento extends BaseModel {
  pigmento: Pigmento;
  quantidade_atual: string; // Decimal field as string
  quantidade_minima: string; // Decimal field as string
  unidade: string;
  localizacao?: string;
  ultimo_movimento?: MovimentoEstoque;
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
  mistura: MisturaTinta;
  codigo_barras: string;
  qr_code: string;
  cor_hex: string;
  nome_cor: string;
  volume_litros: string; // Decimal field as string
  data_producao: string;
  validade: string;
  observacoes?: string;
  template_usado?: string;
  impressa: boolean;
  data_impressao?: string;
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
  status?: string;
  date_from?: string;
  date_to?: string;
  user_id?: number;
  ordering?: string;
  page?: number;
  page_size?: number;
}