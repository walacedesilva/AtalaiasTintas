import { apiClient } from './client';
import type {
  Pigmento,
  LequeCorDefinida,
  FormulaTintometrica,
  MisturaTinta,
  EstoquePigmento,
  EtiquetaMistura,
  MisturaCalculationRequest,
  MisturaCalculationResponse,
  ColorAnalysisRequest,
  ColorAnalysisResponse,
  PaginatedResponse,
  SearchFilters,
  DashboardStats
} from '@/types';
import type {
  CalculationResult,
  CreateCalculationPayload,
  QuickCalculatePayload,
  CustomerHistoryResponse,
  LowStockAlertsResponse
} from '@/types/tintometry';

/**
 * Tintometry API module
 * Handles all paint mixing, color matching, and inventory operations
 */

export const tintometryAPI = {
  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return apiClient.getData<DashboardStats>('/tintometry/dashboard/stats/');
  },

  // Pigmentos (Pigments)
  pigmentos: {
    async list(filters?: SearchFilters): Promise<PaginatedResponse<Pigmento>> {
      const params: Record<string, any> = {
        ordering: filters?.ordering || 'nome',
        page: filters?.page || 1,
        page_size: filters?.page_size || 50
      };
      if (filters?.query) params.search = filters.query;
      if (filters?.cor_base) params.cor_base = filters.cor_base;
      if (filters?.include_inactive) params.include_inactive = '1';
      return apiClient.getData<PaginatedResponse<Pigmento>>('/tintometry/pigmentos/', params);
    },

    async get(id: number): Promise<Pigmento> {
      return apiClient.getData<Pigmento>(`/tintometry/pigmentos/${id}/`);
    },

    async create(pigmento: Omit<Pigmento, 'id' | 'created_at' | 'updated_at'>): Promise<Pigmento> {
      return apiClient.postData<Pigmento>('/tintometry/pigmentos/', pigmento);
    },

    async update(id: number, pigmento: Partial<Pigmento>): Promise<Pigmento> {
      return apiClient.putData<Pigmento>(`/tintometry/pigmentos/${id}/`, pigmento);
    },

    async delete(id: number): Promise<void> {
      await apiClient.delete(`/tintometry/pigmentos/${id}/`);
    },

    async getStockLevel(id: number): Promise<EstoquePigmento> {
      return apiClient.getData<EstoquePigmento>(`/tintometry/pigmentos/${id}/stock/`);
    }
  },

  // Cores (Color Fan/Definitions)
  cores: {
    async list(filters?: SearchFilters): Promise<PaginatedResponse<LequeCorDefinida>> {
      const params: Record<string, unknown> = {
        ordering: filters?.ordering || 'nome_cor',
        page: filters?.page || 1,
        page_size: filters?.page_size || 50
      };
      if (filters?.query) params.search = filters.query;
      if (filters?.categoria) params.familia_cor = filters.categoria;
      if (filters?.include_inactive) params.include_inactive = '1';
      return apiClient.getData<PaginatedResponse<LequeCorDefinida>>('/tintometry/cores/', params);
    },

    async get(id: number): Promise<LequeCorDefinida> {
      return apiClient.getData<LequeCorDefinida>(`/tintometry/cores/${id}/`);
    },

    async create(cor: Omit<LequeCorDefinida, 'id' | 'created_at' | 'updated_at'>): Promise<LequeCorDefinida> {
      return apiClient.postData<LequeCorDefinida>('/tintometry/cores/', cor);
    },

    async update(id: number, cor: Partial<LequeCorDefinida>): Promise<LequeCorDefinida> {
      return apiClient.putData<LequeCorDefinida>(`/tintometry/cores/${id}/`, cor);
    },

    async delete(id: number): Promise<void> {
      await apiClient.delete(`/tintometry/cores/${id}/`);
    },

    async search(query: string): Promise<LequeCorDefinida[]> {
      const params = { search: query, page_size: 50 };
      const response = await apiClient.getData<PaginatedResponse<LequeCorDefinida>>('/tintometry/cores/', params);
      return response.results;
    },

    async getPopular(limit: number = 10): Promise<LequeCorDefinida[]> {
      const params = { ordering: 'nome_cor', page_size: limit };
      const response = await apiClient.getData<PaginatedResponse<LequeCorDefinida>>('/tintometry/cores/', params);
      return response.results;
    }
  },

  // Formulas
  formulas: {
    async list(filters?: SearchFilters): Promise<PaginatedResponse<FormulaTintometrica>> {
      const params: Record<string, unknown> = {
        ordering: filters?.ordering || 'nome_formula',
        page: filters?.page || 1,
        page_size: filters?.page_size || 50
      };
      if (filters?.query) params.search = filters.query;
      if (filters?.include_inactive) params.include_inactive = '1';
      return apiClient.getData<PaginatedResponse<FormulaTintometrica>>('/tintometry/formulas/', params);
    },

    async get(id: number): Promise<FormulaTintometrica> {
      return apiClient.getData<FormulaTintometrica>(`/tintometry/formulas/${id}/`);
    },

    async create(formula: Omit<FormulaTintometrica, 'id' | 'created_at' | 'updated_at'>): Promise<FormulaTintometrica> {
      return apiClient.postData<FormulaTintometrica>('/tintometry/formulas/', formula);
    },

    async update(id: number, formula: Partial<FormulaTintometrica>): Promise<FormulaTintometrica> {
      return apiClient.putData<FormulaTintometrica>(`/tintometry/formulas/${id}/`, formula);
    },

    async delete(id: number): Promise<void> {
      await apiClient.delete(`/tintometry/formulas/${id}/`);
    },

    async calculate(calculationRequest: MisturaCalculationRequest): Promise<MisturaCalculationResponse> {
      return apiClient.postData<MisturaCalculationResponse>('/tintometry/formulas/calculate/', calculationRequest);
    },

    async duplicate(id: number, newName: string): Promise<FormulaTintometrica> {
      return apiClient.postData<FormulaTintometrica>(`/tintometry/formulas/${id}/duplicate/`, { nome: newName });
    }
  },

  // Misturas (Mixtures)
  misturas: {
    async list(filters?: SearchFilters): Promise<PaginatedResponse<MisturaTinta>> {
      const params = {
        search: filters?.query,
        status: filters?.status,
        user_id: filters?.user_id,
        date_from: filters?.date_from,
        date_to: filters?.date_to,
        ordering: filters?.ordering || '-created_at',
        page: filters?.page || 1,
        page_size: filters?.page_size || 20
      };
      return apiClient.getData<PaginatedResponse<MisturaTinta>>('/tintometry/misturas/', params);
    },

    async get(id: number): Promise<MisturaTinta> {
      return apiClient.getData<MisturaTinta>(`/tintometry/misturas/${id}/`);
    },

    async create(mistura: Omit<MisturaTinta, 'id' | 'created_at' | 'updated_at' | 'operador'>): Promise<MisturaTinta> {
      return apiClient.postData<MisturaTinta>('/tintometry/misturas/', mistura);
    },

    async update(id: number, mistura: Partial<MisturaTinta>): Promise<MisturaTinta> {
      return apiClient.patchData<MisturaTinta>(`/tintometry/misturas/${id}/`, mistura);
    },

    async delete(id: number): Promise<void> {
      await apiClient.delete(`/tintometry/misturas/${id}/`);
    },

    async start(id: number): Promise<MisturaTinta> {
      return apiClient.postData<MisturaTinta>(`/tintometry/misturas/${id}/start/`, {});
    },

    async complete(id: number, observacoes?: string): Promise<MisturaTinta> {
      return apiClient.postData<MisturaTinta>(`/tintometry/misturas/${id}/complete/`, { observacoes });
    },

    async cancel(id: number, motivo: string): Promise<MisturaTinta> {
      return apiClient.postData<MisturaTinta>(`/tintometry/misturas/${id}/cancel/`, { motivo });
    },

    async createCalculation(payload: CreateCalculationPayload): Promise<CalculationResult> {
      return apiClient.postData<CalculationResult>('/tintometry/misturas/create_calculation/', payload);
    },

    async confirm(id: number): Promise<CalculationResult> {
      return apiClient.postData<CalculationResult>(`/tintometry/misturas/${id}/confirm/`, {});
    },

    async reproduceFromHistory(id: number): Promise<{ success: boolean; prefill: Record<string, unknown>; formula: FormulaTintometrica }> {
      return apiClient.postData(`/tintometry/misturas/${id}/reproduce_from_history/`, {});
    }
  },

  // Estoque (Stock)
  estoque: {
    async list(filters?: SearchFilters): Promise<PaginatedResponse<EstoquePigmento>> {
      const params = {
        search: filters?.query,
        ordering: filters?.ordering || 'pigmento__nome',
        page: filters?.page || 1,
        page_size: filters?.page_size || 20
      };
      return apiClient.getData<PaginatedResponse<EstoquePigmento>>('/tintometry/estoque/', params);
    },

    async get(id: number): Promise<EstoquePigmento> {
      return apiClient.getData<EstoquePigmento>(`/tintometry/estoque/${id}/`);
    },

    async update(id: number, estoque: Partial<EstoquePigmento>): Promise<EstoquePigmento> {
      return apiClient.patchData<EstoquePigmento>(`/tintometry/estoque/${id}/`, estoque);
    },

    async getLowStock(): Promise<EstoquePigmento[]> {
      const response = await apiClient.getData<PaginatedResponse<EstoquePigmento>>('/tintometry/estoque/low-stock/');
      return response.results;
    },

    async addStock(pigmentoId: number, quantidade: string, observacoes?: string): Promise<EstoquePigmento> {
      return apiClient.postData<EstoquePigmento>(`/tintometry/estoque/add-stock/`, {
        pigmento_id: pigmentoId,
        quantidade,
        observacoes
      });
    },

    async adjustStock(pigmentoId: number, novaQuantidade: string, motivo: string): Promise<EstoquePigmento> {
      return apiClient.postData<EstoquePigmento>(`/tintometry/estoque/adjust/`, {
        pigmento_id: pigmentoId,
        nova_quantidade: novaQuantidade,
        motivo
      });
    },

    async getLowStockAlerts(lojaId?: number): Promise<LowStockAlertsResponse> {
      const params: Record<string, unknown> = {};
      if (lojaId) params.loja_id = lojaId;
      return apiClient.getData<LowStockAlertsResponse>('/tintometry/estoque/low_stock_alerts/', params);
    }
  },

  // Etiquetas (Labels)
  etiquetas: {
    async list(filters?: SearchFilters): Promise<PaginatedResponse<EtiquetaMistura>> {
      const params = {
        search: filters?.query,
        date_from: filters?.date_from,
        date_to: filters?.date_to,
        ordering: filters?.ordering || '-created_at',
        page: filters?.page || 1,
        page_size: filters?.page_size || 20
      };
      return apiClient.getData<PaginatedResponse<EtiquetaMistura>>('/tintometry/etiquetas/', params);
    },

    async get(id: number): Promise<EtiquetaMistura> {
      return apiClient.getData<EtiquetaMistura>(`/tintometry/etiquetas/${id}/`);
    },

    async generate(misturaId: number, templateId?: string): Promise<EtiquetaMistura> {
      return apiClient.postData<EtiquetaMistura>('/tintometry/labels/generate/', {
        mistura_id: misturaId,
        template_id: templateId
      });
    },

    async print(id: number): Promise<void> {
      await apiClient.postData(`/tintometry/etiquetas/${id}/print/`, {});
    },

    async getPreview(misturaId: number, templateId?: string): Promise<string> {
      const params = { mistura_id: misturaId, template_id: templateId };
      const response = await apiClient.getData<{ preview_url: string }>('/tintometry/labels/preview/', params);
      return response.preview_url;
    }
  },

  // Color Analysis
  colors: {
    async analyze(request: ColorAnalysisRequest): Promise<ColorAnalysisResponse> {
      return apiClient.postData<ColorAnalysisResponse>('/tintometry/colors/analyze/', request);
    },

    async findSimilar(corHex: string, tolerancia?: number): Promise<LequeCorDefinida[]> {
      const params = { cor_hex: corHex, tolerancia: tolerancia || 10 };
      const response = await apiClient.getData<ColorAnalysisResponse>('/tintometry/colors/analyze/', params);
      return response.cores_similares;
    },

    async suggestFormula(corHex: string): Promise<FormulaTintometrica[]> {
      const params = { cor_hex: corHex };
      const response = await apiClient.getData<ColorAnalysisResponse>('/tintometry/colors/analyze/', params);
      return response.sugestoes_formula;
    }
  },

  // Quick calculate (no mixture created)
  async quickCalculate(payload: QuickCalculatePayload): Promise<CalculationResult> {
    return apiClient.postData<CalculationResult>('/tintometry/quick-calculate/', payload);
  },

  // Customer history
  customerHistory: {
    async getByPhone(phone: string): Promise<CustomerHistoryResponse> {
      return apiClient.getData<CustomerHistoryResponse>('/tintometry/customer-history/', {
        cliente_telefone: phone
      });
    }
  }
};

// Export for easier imports
export default tintometryAPI;