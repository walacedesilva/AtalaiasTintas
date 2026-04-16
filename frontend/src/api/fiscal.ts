import { apiClient } from './client';

export const fiscalAPI = {
  async listarNotas(params?: Record<string, string>): Promise<any[]> {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    const res = await apiClient.get<{ results: any[] } | any[]>(`/fiscal/notas-fiscais/${qs}`);
    return Array.isArray(res) ? res : res.results ?? [];
  },

  async pendentes(): Promise<any[]> {
    return apiClient.get('/fiscal/nfe-automacao/pendentes/');
  },

  async falhadas(): Promise<any[]> {
    return apiClient.get('/fiscal/nfe-automacao/falhadas/');
  },

  async statusSefaz(): Promise<{ disponivel: boolean; ambiente?: string }> {
    return apiClient.get('/fiscal/sefaz/');
  },

  nfe: {
    async emitir(vendaId: string): Promise<{ mensagem: string }> {
      return apiClient.postData('/fiscal/nfe-automacao/emitir/', { venda_id: vendaId });
    },

    async reprocessar(vendaId: string): Promise<{ mensagem: string }> {
      return apiClient.postData('/fiscal/nfe-automacao/reprocessar/', { venda_id: vendaId });
    },
  },
};
