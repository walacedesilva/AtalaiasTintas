import { apiClient } from './client';

export const fiscalAPI = {
  nfe: {
    async emitir(vendaId: string): Promise<{ mensagem: string }> {
      return apiClient.postData('/fiscal/nfe-automacao/emitir/', { venda_id: vendaId });
    },

    async reprocessar(vendaId: string): Promise<{ mensagem: string }> {
      return apiClient.postData('/fiscal/nfe-automacao/reprocessar/', { venda_id: vendaId });
    },
  },
};
