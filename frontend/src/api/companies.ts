import { apiClient } from './client';
import type { Loja } from '@/types';

export const companiesAPI = {
  lojas: {
    async list(): Promise<Loja[]> {
      // The backend returns a paginated response; we take results
      const res = await apiClient.getData<{ results: Loja[] } | Loja[]>('/companies/lojas/');
      return Array.isArray(res) ? res : res.results;
    },
  },
};
