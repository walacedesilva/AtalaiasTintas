import { apiClient } from './client';
import type {
  EstoqueLojaItem,
  EstoqueResumo,
  LoteProduto,
  EntradaMercadoria,
  PaginatedResponse,
} from '@/types';

export interface EstoqueFilters {
  loja_id?: number;
  search?: string;
  status?: 'ZERADO' | 'BAIXO' | 'NORMAL';
  page?: number;
  page_size?: number;
}

export const inventoryAPI = {
  // -----------------------------------------------------------------------
  // EstoqueLoja
  // -----------------------------------------------------------------------
  estoque: {
    async list(filters?: EstoqueFilters): Promise<PaginatedResponse<EstoqueLojaItem>> {
      const params = {
        loja_id: filters?.loja_id,
        search: filters?.search,
        status: filters?.status,
        page: filters?.page || 1,
        page_size: filters?.page_size || 30,
      };
      return apiClient.getData<PaginatedResponse<EstoqueLojaItem>>('/inventory/estoque-loja/', params);
    },

    async resumo(loja_id?: number): Promise<EstoqueResumo> {
      const params = loja_id ? { loja_id } : undefined;
      return apiClient.getData<EstoqueResumo>('/inventory/estoque-loja/resumo/', params);
    },
  },

  // -----------------------------------------------------------------------
  // Lotes (batch / expiry)
  // -----------------------------------------------------------------------
  lotes: {
    async list(loja_id?: number, status?: string): Promise<LoteProduto[]> {
      const params: Record<string, unknown> = {};
      if (loja_id) params.loja_id = loja_id;
      if (status) params.status = status;
      // API returns plain array (non-paginated)
      return apiClient.getData<LoteProduto[]>('/inventory/lotes/', params);
    },

    async proximosVencimento(loja_id: number, dias = 30): Promise<LoteProduto[]> {
      return apiClient.getData<LoteProduto[]>('/inventory/lotes/proximos-vencimento/', {
        loja_id,
        dias,
      });
    },
  },

  // -----------------------------------------------------------------------
  // Entradas de Mercadoria
  // -----------------------------------------------------------------------
  entradas: {
    async list(loja_id?: number): Promise<PaginatedResponse<EntradaMercadoria>> {
      const params = loja_id ? { loja_id } : undefined;
      return apiClient.getData<PaginatedResponse<EntradaMercadoria>>('/inventory/entradas/', params);
    },

    async importarXml(loja_id: number, xmlFile: File): Promise<EntradaMercadoria> {
      const form = new FormData();
      form.append('loja_id', String(loja_id));
      form.append('xml_file', xmlFile);
      const response = await apiClient.post<EntradaMercadoria>(
        '/inventory/entradas/importar-xml/',
        form,
      );
      return response.data;
    },

    async confirmar(id: number): Promise<EntradaMercadoria> {
      return apiClient.postData<EntradaMercadoria>(`/inventory/entradas/${id}/confirmar/`, {});
    },
  },
};
