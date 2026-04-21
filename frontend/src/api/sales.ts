import { apiClient } from './client';
import type {
  AprovarDescontoPayload,
  Cliente,
  ItemPedidoVenda,
  PDVCheckoutPayload,
  PDVCheckoutResponse,
  PedidoVenda,
  PaginatedResponse,
  Recebivel,
  Venda,
} from '@/types';
import type { 
  SalesOverview, 
  BusinessMetricsRequest,
  TimePeriod 
} from '@/types/dashboard';

// ─── Filters ─────────────────────────────────────────────────────────────────
export interface ClienteFilters {
  search?: string | undefined;
  tipo_cliente?: 'PF' | 'PJ' | undefined;
  ativo?: boolean | undefined;
  page?: number | undefined;
  page_size?: number | undefined;
}

export interface VendaFilters {
  search?: string | undefined;
  cancelada?: boolean | undefined;
  nfe_situacao?: string | undefined;
  data_inicio?: string | undefined;
  data_fim?: string | undefined;
  page?: number | undefined;
  page_size?: number | undefined;
}

export interface PedidoFilters {
  search?: string | undefined;
  situacao?: string | undefined;
  cliente?: number | undefined;
  data_inicio?: string | undefined;
  data_fim?: string | undefined;
  page?: number | undefined;
  page_size?: number | undefined;
}

// ─── Payloads ────────────────────────────────────────────────────────────────
export interface ClientePayload {
  tipo_cliente: 'PF' | 'PJ';
  nome: string;
  razao_social?: string | null;
  nome_fantasia?: string | null;
  cnpj?: string | null;
  cpf?: string | null;
  email?: string | null;
  telefone_principal?: string | null;
  celular?: string | null;
}

export interface EstoqueDisponivelQuery {
  loja_id: number;
  produto_variacao_id: number;
}

export interface EstoqueDisponivelResult {
  produto_variacao_id: number;
  quantidade_disponivel: string;
  unidade: string;
}

export interface PedidoCreatePayload {
  loja: number;
  cliente: number;
  forma_pagamento: string;
  parcelas?: number;
  tipo_entrega?: string;
  observacoes?: string | null;
}

export interface ItemAddPayload {
  produto_variacao: string;   // UUID
  quantidade: string;
  preco_unitario: string;
  desconto_valor?: string;
  observacoes?: string | null;
}

export interface RecebivelFilters {
  cliente?: number | undefined;
  situacao?: string | undefined;
  loja?: number | undefined;
  data_vencimento__lte?: string | undefined;
  data_vencimento__gte?: string | undefined;
  page?: number | undefined;
  page_size?: number | undefined;
}

// ─── API ─────────────────────────────────────────────────────────────────────
export const salesAPI = {
  // -----------------------------------------------------------------------
  // Clientes
  // -----------------------------------------------------------------------
  clientes: {
    async list(filters?: ClienteFilters): Promise<PaginatedResponse<Cliente>> {
      const params = {
        search: filters?.search,
        tipo_cliente: filters?.tipo_cliente,
        ativo: filters?.ativo,
        page: filters?.page || 1,
        page_size: filters?.page_size || 30,
      };
      return apiClient.getData<PaginatedResponse<Cliente>>('/sales/clientes/', params);
    },

    async get(id: number): Promise<Cliente> {
      return apiClient.getData<Cliente>(`/sales/clientes/${id}/`);
    },

    async create(data: ClientePayload): Promise<Cliente> {
      return apiClient.postData<Cliente>('/sales/clientes/', data);
    },

    async update(id: number, data: Partial<ClientePayload>): Promise<Cliente> {
      return apiClient.patchData<Cliente>(`/sales/clientes/${id}/`, data);
    },

    async toggleAtivo(id: number): Promise<Cliente> {
      return apiClient.postData<Cliente>(`/sales/clientes/${id}/toggle-ativo/`, {});
    },

    async historico(id: number, params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<PedidoVenda>> {
      return apiClient.getData<PaginatedResponse<PedidoVenda>>(`/sales/clientes/${id}/historico/`, params);
    },
  },

  // -----------------------------------------------------------------------
  // Vendas (cupons/NFC-e finalizados)
  // -----------------------------------------------------------------------
  vendas: {
    async list(filters?: VendaFilters): Promise<PaginatedResponse<Venda>> {
      const params = {
        search: filters?.search,
        cancelada: filters?.cancelada,
        nfe_situacao: filters?.nfe_situacao,
        data_inicio: filters?.data_inicio,
        data_fim: filters?.data_fim,
        page: filters?.page || 1,
        page_size: filters?.page_size || 30,
      };
      return apiClient.getData<PaginatedResponse<Venda>>('/sales/vendas/', params);
    },

    async get(id: string): Promise<Venda> {
      return apiClient.getData<Venda>(`/sales/vendas/${id}/`);
    },

    async cancel(id: string, motivo: string, pin: string): Promise<{ status: string; venda_id: string }> {
      return apiClient.postData(`/sales/vendas/${id}/cancelar/`, { motivo, pin });
    },

    async devolver(id: string, payload: { motivo: string; itens?: Array<{ item_id: number; quantidade: string }> }): Promise<{ status: string; venda_id: string; movimentacoes_entrada: unknown[] }> {
      return apiClient.postData(`/sales/vendas/${id}/devolver/`, payload);
    },

    async nfeStatus(id: string): Promise<{ situacao: string; protocolo: string | null }> {
      return apiClient.getData(`/sales/vendas/${id}/nfe-status/`);
    },
  },

  // -----------------------------------------------------------------------
  // Pedidos de Venda
  // -----------------------------------------------------------------------
  pedidos: {
    async list(filters?: PedidoFilters): Promise<PaginatedResponse<PedidoVenda>> {
      const params = {
        search: filters?.search,
        situacao: filters?.situacao,
        cliente: filters?.cliente,
        data_inicio: filters?.data_inicio,
        data_fim: filters?.data_fim,
        page: filters?.page || 1,
        page_size: filters?.page_size || 30,
      };
      return apiClient.getData<PaginatedResponse<PedidoVenda>>('/sales/pedidos/', params);
    },

    async get(id: string): Promise<PedidoVenda> {
      return apiClient.getData<PedidoVenda>(`/sales/pedidos/${id}/`);
    },

    async create(data: PedidoCreatePayload): Promise<PedidoVenda> {
      return apiClient.postData<PedidoVenda>('/sales/pedidos/', data);
    },

    async addItem(pedidoId: string, item: ItemAddPayload): Promise<ItemPedidoVenda> {
      return apiClient.postData<ItemPedidoVenda>(`/sales/pedidos/${pedidoId}/add-item/`, item);
    },

    async removeItem(pedidoId: string, itemId: number): Promise<void> {
      await apiClient.deleteData(`/sales/pedidos/${pedidoId}/remove-item/${itemId}/`);
    },

    async aprovar(id: string, data_entrega_prevista?: string): Promise<PedidoVenda> {
      return apiClient.postData<PedidoVenda>(`/sales/pedidos/${id}/aprovar/`, { data_entrega_prevista });
    },

    async iniciarCheckout(id: string): Promise<{ sessao_checkout: string; reservas_criadas: number; avisos: string[] }> {
      return apiClient.postData(`/sales/pedidos/${id}/iniciar-checkout/`, {});
    },

    async finalizar(pedidoId: string, sessaoCheckout: string): Promise<Venda> {
      return apiClient.postData<Venda>(`/sales/pedidos/${pedidoId}/finalizar/`, {
        sessao_checkout: sessaoCheckout,
      });
    },

    async cancelar(id: string, motivo: string): Promise<PedidoVenda> {
      return apiClient.postData<PedidoVenda>(`/sales/pedidos/${id}/cancelar/`, { motivo });
    },

    async aprovarDesconto(id: string, payload: AprovarDescontoPayload): Promise<PedidoVenda> {
      return apiClient.postData<PedidoVenda>(`/sales/pedidos/${id}/aprovar-desconto/`, payload);
    },

    async finalizarEntrega(id: string): Promise<{ pedido_id: string; venda_id: string; numero_venda: string }> {
      return apiClient.postData(`/sales/pedidos/${id}/finalizar-entrega/`, {});
    },
  },

  // -----------------------------------------------------------------------
  // Estoque disponível (consulta antes de criar pedido)
  // -----------------------------------------------------------------------
  async estoqueDisponivel(
    query: EstoqueDisponivelQuery,
  ): Promise<EstoqueDisponivelResult> {
    return apiClient.getData<EstoqueDisponivelResult>('/sales/estoque-disponivel/', query);
  },

  // -----------------------------------------------------------------------
  // T038-T039: Recebíveis
  // -----------------------------------------------------------------------
  recebiveis: {
    async list(filters?: RecebivelFilters): Promise<PaginatedResponse<Recebivel>> {
      return apiClient.getData<PaginatedResponse<Recebivel>>('/sales/recebiveis/', filters);
    },

    async get(id: number): Promise<Recebivel> {
      return apiClient.getData<Recebivel>(`/sales/recebiveis/${id}/`);
    },

    async baixar(id: number, valor_pago: string, forma_pagamento?: string, observacoes?: string): Promise<Recebivel> {
      return apiClient.postData<Recebivel>(`/sales/recebiveis/${id}/baixar/`, {
        valor_pago,
        forma_pagamento,
        observacoes,
      });
    },

    async cancelar(id: number, motivo: string): Promise<Recebivel> {
      return apiClient.postData<Recebivel>(`/sales/recebiveis/${id}/cancelar/`, { motivo });
    },
  },

  // -----------------------------------------------------------------------
  // T038-T039: PDV Checkout
  // -----------------------------------------------------------------------
  pdv: {
    async checkout(payload: PDVCheckoutPayload): Promise<PDVCheckoutResponse> {
      return apiClient.postData<PDVCheckoutResponse>('/sales/pdv/checkout/', payload);
    },
  },

  // -----------------------------------------------------------------------
  // Dashboard Methods (T004)
  // -----------------------------------------------------------------------
  dashboard: {
    async getOverview(): Promise<SalesOverview> {
      // TODO: Connect to real endpoint when backend implements /api/sales/dashboard/
      // For now, return mock data
      return mockSalesOverview();
    },

    async getMetrics(timeRange: TimePeriod): Promise<{ 
      totalSales: { value: number; change: number; trend: 'up' | 'down' };
      orderCount: { value: number; change: number; trend: 'up' | 'down' };
      averageTicket: { value: number; change: number; trend: 'up' | 'down' };
    }> {
      // TODO: Connect to real endpoint when backend implements /api/sales/metrics/
      // For now, return mock data
      return mockSalesMetrics(timeRange);
    },
  },
};

// ─── Mock Data for Dashboard (Remove when backend ready) ─────────────────────

function mockSalesOverview(): SalesOverview {
  return {
    todaysSales: {
      count: Math.floor(Math.random() * 50) + 10,
      value: Math.floor(Math.random() * 20000) + 5000,
      target: 30000,
      progress: Number(((Math.random() * 80) + 20).toFixed(1))
    },
    pendingOrders: {
      count: Math.floor(Math.random() * 20) + 5,
      value: Math.floor(Math.random() * 15000) + 3000,
      urgentCount: Math.floor(Math.random() * 5) + 1
    },
    recentOrders: Array.from({ length: 5 }, (_, i) => ({
      id: `ORD-${1000 + i}`,
      customerName: [`Cliente A`, `Cliente B`, `Cliente C`, `Cliente D`, `Cliente E`][i],
      value: Math.floor(Math.random() * 2000) + 500,
      status: ['pending', 'confirmed', 'processing', 'ready', 'delivered'][Math.floor(Math.random() * 5)] as any,
      createdAt: new Date(Date.now() - Math.random() * 86400000 * 3).toISOString()
    })),
    topProducts: Array.from({ length: 5 }, (_, i) => ({
      id: `PROD-${100 + i}`,
      name: [`Tinta Premium Branca`, `Tinta Standard Azul`, `Verniz Acetinado`, `Primer Universal`, `Tinta Fosca Verde`][i],
      salesCount: Math.floor(Math.random() * 50) + 10,
      revenue: Math.floor(Math.random() * 5000) + 1000,
      category: 'tinta'
    }))
  };
}

function mockSalesMetrics(timeRange: TimePeriod): {
  totalSales: { value: number; change: number; trend: 'up' | 'down' };
  orderCount: { value: number; change: number; trend: 'up' | 'down' };
  averageTicket: { value: number; change: number; trend: 'up' | 'down' };
} {
  return {
    totalSales: {
      value: Math.floor(Math.random() * 100000) + 50000,
      change: Math.floor(Math.random() * 30) - 15,
      trend: Math.random() > 0.5 ? 'up' : 'down'
    },
    orderCount: {
      value: Math.floor(Math.random() * 200) + 50,
      change: Math.floor(Math.random() * 20) - 10,
      trend: Math.random() > 0.5 ? 'up' : 'down'
    },
    averageTicket: {
      value: Math.floor(Math.random() * 1000) + 200,
      change: Math.floor(Math.random() * 15) - 7,
      trend: Math.random() > 0.5 ? 'up' : 'down'
    }
  };
}
