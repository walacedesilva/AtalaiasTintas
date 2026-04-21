import { apiClient } from './client';
import type {
  Categoria,
  EstoqueLojaItem,
  EstoqueResumo,
  LoteProduto,
  EntradaMercadoria,
  Marca,
  PaginatedResponse,
  ProdutoBase,
  ProdutoBasePayload,
  ProdutoVariacao,
  ProdutoVariacaoPayload,
} from '@/types';

export interface EstoqueFilters {
  loja_id?: number;
  search?: string;
  status?: 'ZERADO' | 'BAIXO' | 'NORMAL';
  page?: number;
  page_size?: number;
}

export interface EntradaManualItemPayload {
  descricao_nfe: string;
  codigo_nfe?: string;
  ncm?: string;
  cfop?: string;
  quantidade: number;
  unidade_nfe?: string;
  valor_unitario: number;
}

export interface EntradaManualPayload {
  loja_id: number;
  numero_nfe: string;
  serie_nfe?: string;
  fornecedor_cnpj: string;
  fornecedor_nome?: string;
  fornecedor_uf?: string;
  data_emissao_nfe?: string | null;
  valor_total_nfe?: number | null;
  chave_acesso_nfe?: string | null;
  observacoes?: string;
  itens: EntradaManualItemPayload[];
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

    async criarManual(payload: EntradaManualPayload): Promise<EntradaMercadoria> {
      return apiClient.postData<EntradaMercadoria>('/inventory/entradas/criar-manual/', payload);
    },
  },

  // -------------------------------------------------------------------------
  // Produtos (ProdutoBase + ProdutoVariacao CRUD)
  // -------------------------------------------------------------------------
  produtos: {
    async list(params?: {
      search?: string;
      categoria_id?: number;
      marca_id?: number;
      tipo_produto?: string;
      ativo?: boolean;
    }): Promise<PaginatedResponse<ProdutoBase>> {
      return apiClient.getData<PaginatedResponse<ProdutoBase>>('/inventory/produtos/', params);
    },

    async get(id: string): Promise<ProdutoBase> {
      return apiClient.getData<ProdutoBase>(`/inventory/produtos/${id}/`);
    },

    async create(data: ProdutoBasePayload): Promise<ProdutoBase> {
      return apiClient.postData<ProdutoBase>('/inventory/produtos/', data);
    },

    async update(id: string, data: Partial<ProdutoBasePayload>): Promise<ProdutoBase> {
      const response = await apiClient.patch<ProdutoBase>(`/inventory/produtos/${id}/`, data);
      return response.data;
    },

    async deactivate(id: string): Promise<void> {
      await apiClient.delete(`/inventory/produtos/${id}/`);
    },

    async listVariacoes(produtoId: string): Promise<ProdutoVariacao[]> {
      return apiClient.getData<ProdutoVariacao[]>(`/inventory/produtos/${produtoId}/variacoes/`);
    },

    async createVariacao(produtoId: string, data: ProdutoVariacaoPayload): Promise<ProdutoVariacao> {
      return apiClient.postData<ProdutoVariacao>(`/inventory/produtos/${produtoId}/variacoes/`, data);
    },
  },

  variacoes: {
    async update(id: string, data: Partial<ProdutoVariacaoPayload>): Promise<ProdutoVariacao> {
      const response = await apiClient.patch<ProdutoVariacao>(`/inventory/variacoes/${id}/`, data);
      return response.data;
    },

    async deactivate(id: string): Promise<void> {
      await apiClient.delete(`/inventory/variacoes/${id}/`);
    },
  },

  // -------------------------------------------------------------------------
  // Categorias e Marcas (auxiliares para filtros/dropdowns)
  // -------------------------------------------------------------------------
  categorias: {
    async list(): Promise<Categoria[]> {
      const res = await apiClient.getData<{ results: Categoria[] } | Categoria[]>('/inventory/categorias/');
      return Array.isArray(res) ? res : res.results;
    },
  },

  marcas: {
    async list(): Promise<Marca[]> {
      const res = await apiClient.getData<{ results: Marca[] } | Marca[]>('/inventory/marcas/');
      return Array.isArray(res) ? res : res.results;
    },
  },
};
