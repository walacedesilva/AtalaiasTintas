/**
 * Extended tintometry domain types for Phase 6 components.
 * Supplements the base types in @/types/index.ts.
 */

// ---------------------------------------------------------------------------
// Calculation types (create_calculation / quick-calculate responses)
// ---------------------------------------------------------------------------

export interface CalculationPigmentoItem {
  pigmento: {
    id: number;
    codigo: string;
    nome: string;
    cor_hex?: string;
  };
  quantidades: {
    calculada_final: number;
    /** ml */
  };
  custos: {
    total: number;
  };
  stock_disponivel?: number;
  stock_suficiente?: boolean;
}

export interface CalculationResult {
  success: boolean;
  mistura?: {
    id: number;
    codigo: string;
    situacao: string;
    created_at: string;
  };
  calculation?: {
    pigmentos: CalculationPigmentoItem[];
    custos: {
      total: number;
      base: number;
      pigmentos: number;
    };
    validacao: {
      stock_ok: boolean;
      warnings: string[];
    };
    volume_total?: string;
    fator_proporcao?: number;
  };
  /** Present on quick-calculate responses */
  formula?: {
    id: number;
    nome_formula: string;
    codigo_formula?: string;
  };
  volume?: string;
  items_created?: number;
  next_steps?: string[];
  error?: string;
  details?: string[];
}

// ---------------------------------------------------------------------------
// Stock alert types (low_stock_alerts endpoint)
// ---------------------------------------------------------------------------

export interface StockAlert {
  id: number;
  pigmento: {
    id: number;
    codigo: string;
    nome: string;
    cor_hex?: string;
  };
  saldo_ml: number;
  saldo_minimo: number;
  /** saldo_ml / saldo_minimo * 100 — computed on frontend if absent */
  percentual?: number;
  loja: number;
}

export interface LowStockAlertsResponse {
  alerts: StockAlert[];
  count: number;
  critical_count?: number;
}

// ---------------------------------------------------------------------------
// Customer history types (customer-history endpoint)
// ---------------------------------------------------------------------------

export interface CustomerHistoryItem {
  codigo_mistura: string;
  cor: string;
  data_confirmacao: string | null;
  volume_produzido: string | null;
  observacoes_cliente: string | null;
  formula_id: number;
  mistura_id: number;
  loja_id?: number;
}

export interface CustomerHistoryResponse {
  count: number;
  cliente_telefone: string;
  results: CustomerHistoryItem[];
}

// ---------------------------------------------------------------------------
// Payload types
// ---------------------------------------------------------------------------

export interface CreateCalculationPayload {
  formula_id: number;
  volume_solicitado: string;
  loja_id: number;
  cliente_nome: string;
  cliente_telefone?: string;
  cliente_email?: string;
  observacoes_cliente?: string;
}

export interface QuickCalculatePayload {
  formula_id: number;
  volume: string;
  loja_id: number;
}
