import { apiClient } from './client';
import type { FiscalStatus } from '@/types/dashboard';

export const fiscalAPI = {
  async listarNotas(params?: Record<string, string>): Promise<any[]> {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    const res = await apiClient.getData<{ results: any[] } | any[]>(`/fiscal/notas-fiscais/${qs}`);
    return Array.isArray(res) ? res : (res as { results: any[] }).results ?? [];
  },

  async pendentes(): Promise<any[]> {
    return apiClient.getData('/fiscal/nfe-automacao/pendentes/');
  },

  async falhadas(): Promise<any[]> {
    return apiClient.getData('/fiscal/nfe-automacao/falhadas/');
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

  // -----------------------------------------------------------------------
  // Dashboard Methods (T005)
  // -----------------------------------------------------------------------
  dashboard: {
    async getStatus(): Promise<FiscalStatus> {
      // TODO: Connect to real endpoint when backend implements /api/fiscal/dashboard/
      // For now, return mock data
      return mockFiscalStatus();
    },

    async getComplianceAlerts(): Promise<Array<{
      id: string;
      type: 'info' | 'warning' | 'error';
      message: string;
      priority: 'low' | 'medium' | 'high';
      createdAt: string;
    }>> {
      // TODO: Connect to real endpoint when backend implements /api/fiscal/alerts/
      // For now, return mock data
      return mockComplianceAlerts();
    },
  },
};

// ─── Mock Data for Fiscal Dashboard (Remove when backend ready) ──────────────

function mockFiscalStatus(): FiscalStatus {
  return {
    nfeStatus: {
      issued: Math.floor(Math.random() * 100) + 50,
      pending: Math.floor(Math.random() * 10) + 2,
      errors: Math.floor(Math.random() * 3),
      lastUpdate: new Date().toISOString()
    },
    complianceAlerts: [
      {
        id: 'ALERT-001',
        type: 'warning',
        message: 'NFe pendente há mais de 2 horas',
        priority: 'medium',
        createdAt: new Date(Date.now() - 7200000).toISOString()
      }
    ],
    certificateStatus: {
      isValid: true,
      expiresAt: new Date(Date.now() + 86400000 * 180).toISOString(),
      daysUntilExpiry: 180,
      issuer: 'AC SERASA'
    },
    taxSummary: {
      icms: Number((Math.random() * 5000 + 1000).toFixed(2)),
      ipi: Number((Math.random() * 1000 + 200).toFixed(2)),
      pis: Number((Math.random() * 500 + 100).toFixed(2)),
      cofins: Number((Math.random() * 1000 + 300).toFixed(2))
    }
  };
}

function mockComplianceAlerts(): Array<{
  id: string;
  type: 'info' | 'warning' | 'error';
  message: string;
  priority: 'low' | 'medium' | 'high';
  createdAt: string;
}> {
  return [
    {
      id: 'COMP-001',
      type: 'warning',
      message: 'Prazo para transmissão de NFe se aproxima',
      priority: 'medium',
      createdAt: new Date(Date.now() - 3600000).toISOString()
    },
    {
      id: 'COMP-002',
      type: 'info',
      message: 'Backup de certificado digital recomendado',
      priority: 'low',
      createdAt: new Date(Date.now() - 86400000).toISOString()
    }
  ];
}
