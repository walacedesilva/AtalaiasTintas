import { apiClient } from './client';
import type {
  Cliente,
  PedidoVenda,
  Venda,
  PaginatedResponse,
} from '@/types';

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

    async cancel(id: string, motivo: string): Promise<Venda> {
      return apiClient.postData<Venda>(`/sales/vendas/${id}/cancelar/`, { motivo });
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

    async get(id: number): Promise<PedidoVenda> {
      return apiClient.getData<PedidoVenda>(`/sales/pedidos/${id}/`);
    },

    async aprovar(id: number): Promise<PedidoVenda> {
      return apiClient.postData<PedidoVenda>(`/sales/pedidos/${id}/aprovar/`, {});
    },

    async finalizar(id: number): Promise<PedidoVenda> {
      return apiClient.postData<PedidoVenda>(`/sales/pedidos/${id}/finalizar/`, {});
    },

    async cancelar(id: number, motivo: string): Promise<PedidoVenda> {
      return apiClient.postData<PedidoVenda>(`/sales/pedidos/${id}/cancelar/`, { motivo });
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
};
