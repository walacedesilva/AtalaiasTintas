/**
 * NotaFiscalPage — unit tests
 *
 * Covers:
 *  1. Renderização inicial — cards, abas, status SEFAZ
 *  2. Aba Notas Fiscais — listagem, busca, estado vazio
 *  3. Aba Pendentes — listagem, botão Emitir, estado vazio
 *  4. Aba Falhadas — listagem, botão Reprocessar, estado vazio
 *  5. Botão Atualizar — refetch de todas as queries
 *  6. Status SEFAZ online / offline
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import NotaFiscalPage from '../NotaFiscalPage';

// ─── Mock fiscalAPI ────────────────────────────────────────────────────────
vi.mock('@/api/fiscal', () => ({
  fiscalAPI: {
    listarNotas: vi.fn(),
    pendentes: vi.fn(),
    falhadas: vi.fn(),
    statusSefaz: vi.fn(),
    nfe: {
      emitir: vi.fn(),
      reprocessar: vi.fn(),
    },
  },
}));

import { fiscalAPI } from '@/api/fiscal';

// ─── Fixtures ─────────────────────────────────────────────────────────────
const notaEmitida = {
  id: 1,
  numero: '000001',
  serie: '001',
  chave_acesso: '35260412345678901234550010000000011000000012',
  situacao: 'EMITIDA',
  tipo_nota: 'NF-e',
  valor_total_nota: '250.00',
  data_emissao: '2026-04-16T10:00:00Z',
  data_autorizacao: '2026-04-16T10:01:00Z',
  protocolo_autorizacao: '135260000000000',
  motivo_cancelamento: null,
};

const notaCancelada = {
  id: 2,
  numero: '000002',
  serie: '001',
  chave_acesso: '35260412345678901234550010000000021000000023',
  situacao: 'CANCELADA',
  tipo_nota: 'NF-e',
  valor_total_nota: '100.00',
  data_emissao: '2026-04-15T09:00:00Z',
  data_autorizacao: null,
  protocolo_autorizacao: null,
  motivo_cancelamento: 'Erro na emissão',
};

const vendaPendente = {
  id: 101,
  numero_venda: '2026-0101',
  nfe_situacao: 'PENDENTE',
  nfe_tentativas: 0,
  nfe_ultima_tentativa: null,
};

const vendaFalhada = {
  id: 202,
  numero_venda: '2026-0202',
  nfe_situacao: 'ERRO_TECNICO',
  nfe_erro: 'Timeout na comunicação com SEFAZ',
  nfe_tentativas: 3,
  nfe_ultima_tentativa: '2026-04-16T08:00:00Z',
  nfe_requer_retry_manual: true,
};

// ─── Helpers ──────────────────────────────────────────────────────────────
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

function renderPage(qc = makeQueryClient()) {
  return render(
    <BrowserRouter>
      <QueryClientProvider client={qc}>
        <NotaFiscalPage />
        <Toaster />
      </QueryClientProvider>
    </BrowserRouter>,
  );
}

// ─── Tests ────────────────────────────────────────────────────────────────
describe('NotaFiscalPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default happy-path responses
    vi.mocked(fiscalAPI.listarNotas).mockResolvedValue([notaEmitida, notaCancelada]);
    vi.mocked(fiscalAPI.pendentes).mockResolvedValue([vendaPendente]);
    vi.mocked(fiscalAPI.falhadas).mockResolvedValue([vendaFalhada]);
    vi.mocked(fiscalAPI.statusSefaz).mockResolvedValue({ disponivel: true, ambiente: 'HOMOLOGACAO' });
  });

  // ── 1. Renderização inicial ───────────────────────────────────────────
  describe('Renderização inicial', () => {
    it('exibe o título da página', async () => {
      renderPage();
      expect(screen.getByText('Nota Fiscal Eletrônica')).toBeInTheDocument();
    });

    it('exibe as 3 abas', async () => {
      renderPage();
      expect(screen.getByRole('button', { name: /notas fiscais/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /pendentes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /falhadas/i })).toBeInTheDocument();
    });

    it('exibe botão Atualizar', async () => {
      renderPage();
      expect(screen.getByRole('button', { name: /atualizar/i })).toBeInTheDocument();
    });

    it('exibe os cards de resumo após carregar', async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText('Notas Emitidas')).toBeInTheDocument();
        expect(screen.getByText('Com Falha')).toBeInTheDocument();
        // "Pendentes" aparece no card e na aba — verificamos pelo card label
        const allPendentes = screen.getAllByText('Pendentes');
        expect(allPendentes.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('contagem correta nos cards de resumo', async () => {
      renderPage();
      await waitFor(() => {
        // 1 emitida, 1 pendente, 1 falhada
        const cards = screen.getAllByText(/^[0-9]+$/);
        const values = cards.map((el) => el.textContent);
        expect(values).toContain('1'); // emitidas
      });
    });
  });

  // ── 2. Status SEFAZ ───────────────────────────────────────────────────
  describe('Status SEFAZ', () => {
    it('exibe "SEFAZ Online" quando disponível', async () => {
      vi.mocked(fiscalAPI.statusSefaz).mockResolvedValue({ disponivel: true });
      renderPage();
      await waitFor(() => {
        expect(screen.getByText(/sefaz online/i)).toBeInTheDocument();
      });
    });

    it('exibe "SEFAZ Offline" quando indisponível', async () => {
      vi.mocked(fiscalAPI.statusSefaz).mockResolvedValue({ disponivel: false });
      renderPage();
      await waitFor(() => {
        expect(screen.getByText(/sefaz offline/i)).toBeInTheDocument();
      });
    });

    it('exibe "SEFAZ Offline" quando API retorna erro', async () => {
      vi.mocked(fiscalAPI.statusSefaz).mockRejectedValue(new Error('Network error'));
      renderPage();
      await waitFor(() => {
        expect(screen.getByText(/sefaz offline/i)).toBeInTheDocument();
      });
    });
  });

  // ── 3. Aba Notas Fiscais ──────────────────────────────────────────────
  describe('Aba Notas Fiscais', () => {
    it('exibe notas carregadas', async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText('001-000001')).toBeInTheDocument();
        expect(screen.getByText('001-000002')).toBeInTheDocument();
      });
    });

    it('exibe badge "Emitida" para nota emitida', async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText('Emitida')).toBeInTheDocument();
      });
    });

    it('exibe badge "Cancelada" para nota cancelada', async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText('Cancelada')).toBeInTheDocument();
      });
    });

    it('exibe valor formatado em reais', async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText(/R\$ 250,00/)).toBeInTheDocument();
      });
    });

    it('filtra notas pelo campo de busca (número)', async () => {
      const user = userEvent.setup();
      renderPage();
      await waitFor(() => {
        expect(screen.getByText('001-000001')).toBeInTheDocument();
      });
      const input = screen.getByPlaceholderText(/buscar por número/i);
      await user.type(input, '000001');
      expect(screen.getByText('001-000001')).toBeInTheDocument();
      expect(screen.queryByText('001-000002')).not.toBeInTheDocument();
    });

    it('filtra notas pela situação', async () => {
      const user = userEvent.setup();
      renderPage();
      await waitFor(() => expect(screen.getByText('001-000002')).toBeInTheDocument());
      const input = screen.getByPlaceholderText(/buscar por número/i);
      await user.type(input, 'cancelada');
      expect(screen.getByText('001-000002')).toBeInTheDocument();
      expect(screen.queryByText('001-000001')).not.toBeInTheDocument();
    });

    it('exibe estado vazio quando não há notas', async () => {
      vi.mocked(fiscalAPI.listarNotas).mockResolvedValue([]);
      renderPage();
      await waitFor(() => {
        expect(screen.getByText(/nenhuma nota fiscal encontrada/i)).toBeInTheDocument();
      });
    });

    it('busca vazia exibe todas as notas novamente', async () => {
      const user = userEvent.setup();
      renderPage();
      await waitFor(() => expect(screen.getByText('001-000001')).toBeInTheDocument());
      const input = screen.getByPlaceholderText(/buscar por número/i);
      await user.type(input, '000001');
      await user.clear(input);
      expect(screen.getByText('001-000001')).toBeInTheDocument();
      expect(screen.getByText('001-000002')).toBeInTheDocument();
    });
  });

  // ── 4. Aba Pendentes ─────────────────────────────────────────────────
  describe('Aba Pendentes', () => {
    async function goToPendentes() {
      const user = userEvent.setup();
      renderPage();
      await waitFor(() => expect(screen.getByRole('button', { name: /pendentes/i })).toBeInTheDocument());
      await user.click(screen.getByRole('button', { name: /pendentes/i }));
      return user;
    }

    it('exibe a venda pendente', async () => {
      await goToPendentes();
      await waitFor(() => {
        expect(screen.getByText(/#2026-0101/)).toBeInTheDocument();
      });
    });

    it('exibe badge "Pendente"', async () => {
      await goToPendentes();
      await waitFor(() => {
        expect(screen.getByText('Pendente')).toBeInTheDocument();
      });
    });

    it('botão Emitir está presente', async () => {
      await goToPendentes();
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /emitir/i })).toBeInTheDocument();
      });
    });

    it('clique em Emitir chama fiscalAPI.nfe.emitir com id correto', async () => {
      vi.mocked(fiscalAPI.nfe.emitir).mockResolvedValue({ mensagem: 'NF-e agendada' });
      const user = await goToPendentes();
      await waitFor(() => screen.getByRole('button', { name: /emitir/i }));
      await user.click(screen.getByRole('button', { name: /emitir/i }));
      await waitFor(() => {
        expect(fiscalAPI.nfe.emitir).toHaveBeenCalledWith('101');
      });
    });

    it('exibe estado vazio quando não há pendentes', async () => {
      vi.mocked(fiscalAPI.pendentes).mockResolvedValue([]);
      await goToPendentes();
      await waitFor(() => {
        expect(screen.getByText(/nenhuma nf-e pendente/i)).toBeInTheDocument();
      });
    });

    it('botão Emitir fica desabilitado enquanto mutation está pendente', async () => {
      // Emitir never resolves during the test
      vi.mocked(fiscalAPI.nfe.emitir).mockImplementation(() => new Promise(() => {}));
      const user = await goToPendentes();
      await waitFor(() => screen.getByRole('button', { name: /emitir/i }));
      await user.click(screen.getByRole('button', { name: /emitir/i }));
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /emitir/i })).toBeDisabled();
      });
    });
  });

  // ── 5. Aba Falhadas ───────────────────────────────────────────────────
  describe('Aba Falhadas', () => {
    async function goToFalhadas() {
      const user = userEvent.setup();
      renderPage();
      await waitFor(() => expect(screen.getByRole('button', { name: /falhadas/i })).toBeInTheDocument());
      await user.click(screen.getByRole('button', { name: /falhadas/i }));
      return user;
    }

    it('exibe a venda falhada', async () => {
      await goToFalhadas();
      await waitFor(() => {
        expect(screen.getByText(/#2026-0202/)).toBeInTheDocument();
      });
    });

    it('exibe badge "Erro Técnico"', async () => {
      await goToFalhadas();
      await waitFor(() => {
        expect(screen.getByText('Erro Técnico')).toBeInTheDocument();
      });
    });

    it('exibe número de tentativas', async () => {
      await goToFalhadas();
      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    it('botão Reprocessar está presente', async () => {
      await goToFalhadas();
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reprocessar/i })).toBeInTheDocument();
      });
    });

    it('clique em Reprocessar chama fiscalAPI.nfe.reprocessar com id correto', async () => {
      vi.mocked(fiscalAPI.nfe.reprocessar).mockResolvedValue({ mensagem: 'Reenviado' });
      const user = await goToFalhadas();
      await waitFor(() => screen.getByRole('button', { name: /reprocessar/i }));
      await user.click(screen.getByRole('button', { name: /reprocessar/i }));
      await waitFor(() => {
        expect(fiscalAPI.nfe.reprocessar).toHaveBeenCalledWith('202');
      });
    });

    it('exibe estado vazio quando não há falhadas', async () => {
      vi.mocked(fiscalAPI.falhadas).mockResolvedValue([]);
      await goToFalhadas();
      await waitFor(() => {
        expect(screen.getByText(/nenhuma nf-e com falha/i)).toBeInTheDocument();
      });
    });

    it('botão Reprocessar fica desabilitado enquanto mutation está pendente', async () => {
      vi.mocked(fiscalAPI.nfe.reprocessar).mockImplementation(() => new Promise(() => {}));
      const user = await goToFalhadas();
      await waitFor(() => screen.getByRole('button', { name: /reprocessar/i }));
      await user.click(screen.getByRole('button', { name: /reprocessar/i }));
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reprocessar/i })).toBeDisabled();
      });
    });
  });

  // ── 6. Botão Atualizar ────────────────────────────────────────────────
  describe('Botão Atualizar', () => {
    it('chama listarNotas, pendentes e falhadas ao clicar', async () => {
      const user = userEvent.setup();
      renderPage();
      // wait initial load
      await waitFor(() => expect(fiscalAPI.listarNotas).toHaveBeenCalledTimes(1));

      await user.click(screen.getByRole('button', { name: /atualizar/i }));

      await waitFor(() => {
        expect(fiscalAPI.listarNotas).toHaveBeenCalledTimes(2);
        expect(fiscalAPI.pendentes).toHaveBeenCalledTimes(2);
        expect(fiscalAPI.falhadas).toHaveBeenCalledTimes(2);
      });
    });
  });

  // ── 7. Navegação entre abas ───────────────────────────────────────────
  describe('Navegação entre abas', () => {
    it('aba Notas Fiscais está ativa por padrão', () => {
      renderPage();
      const tabNotas = screen.getByRole('button', { name: /notas fiscais/i });
      expect(tabNotas.className).toContain('border-brand-600');
    });

    it('troca para aba Pendentes ao clicar', async () => {
      const user = userEvent.setup();
      renderPage();
      await user.click(screen.getByRole('button', { name: /pendentes/i }));
      const tabPendentes = screen.getByRole('button', { name: /pendentes/i });
      expect(tabPendentes.className).toContain('border-brand-600');
    });

    it('troca para aba Falhadas ao clicar', async () => {
      const user = userEvent.setup();
      renderPage();
      await user.click(screen.getByRole('button', { name: /falhadas/i }));
      const tabFalhadas = screen.getByRole('button', { name: /falhadas/i });
      expect(tabFalhadas.className).toContain('border-brand-600');
    });

    it('campo de busca só aparece na aba Notas Fiscais', async () => {
      const user = userEvent.setup();
      renderPage();
      expect(screen.getByPlaceholderText(/buscar por número/i)).toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: /pendentes/i }));
      expect(screen.queryByPlaceholderText(/buscar por número/i)).not.toBeInTheDocument();
    });
  });

  // ── 8. Contadores nas abas ────────────────────────────────────────────
  describe('Contadores nas abas', () => {
    it('exibe contagem de notas na aba', async () => {
      renderPage();
      await waitFor(() => {
        // "Notas Fiscais" tab has badge with 2
        const tabNotas = screen.getByRole('button', { name: /notas fiscais/i });
        expect(within(tabNotas).getByText('2')).toBeInTheDocument();
      });
    });

    it('exibe contagem de pendentes na aba', async () => {
      renderPage();
      await waitFor(() => {
        const tabPendentes = screen.getByRole('button', { name: /pendentes/i });
        expect(within(tabPendentes).getByText('1')).toBeInTheDocument();
      });
    });

    it('exibe contagem de falhadas na aba', async () => {
      renderPage();
      await waitFor(() => {
        const tabFalhadas = screen.getByRole('button', { name: /falhadas/i });
        expect(within(tabFalhadas).getByText('1')).toBeInTheDocument();
      });
    });
  });
});
