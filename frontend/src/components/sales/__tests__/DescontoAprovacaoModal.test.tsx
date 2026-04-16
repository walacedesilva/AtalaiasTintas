/**
 * T050 — DescontoAprovacaoModal unit tests.
 * ACC-3: focus trap; PIN type=password; max 3 attempts lockout; ESC closes.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DescontoAprovacaoModal from '../DescontoAprovacaoModal';

// Mock salesAPI
vi.mock('@/api/sales', () => ({
  salesAPI: {
    pedidos: {
      aprovarDesconto: vi.fn(),
    },
  },
}));

import { salesAPI } from '@/api/sales';

const mockAprovadores = [
  { id: 1, username: 'gerente1', label: 'Ana Costa (Gerente)' },
  { id: 2, username: 'diretor1', label: 'João Lima (Diretor)' },
];

const defaultProps = {
  pedidoId: 'test-uuid-0042',
  percentual: '15',
  nivel: 'gerente' as const,
  tipo: 'TOTAL' as const,
  aprovadores: mockAprovadores,
  onSuccess: vi.fn(),
  onClose: vi.fn(),
};

function renderModal(props = {}) {
  return render(<DescontoAprovacaoModal {...defaultProps} {...props} />);
}

describe('DescontoAprovacaoModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders with correct ARIA dialog attributes', () => {
      renderModal();
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('renders PIN field as password type', () => {
      renderModal();
      const pinInput = screen.getByLabelText(/pin/i);
      expect(pinInput).toHaveAttribute('type', 'password');
    });

    it('renders motivo textarea', () => {
      renderModal();
      expect(screen.getByLabelText(/motivo/i)).toBeInTheDocument();
    });

    it('renders aprovador select with all options', () => {
      renderModal();
      const select = screen.getByLabelText(/^aprovador/i);
      expect(select).toBeInTheDocument();
      expect(screen.getByText('Ana Costa (Gerente)')).toBeInTheDocument();
      expect(screen.getByText('João Lima (Diretor)')).toBeInTheDocument();
    });

    it('auto-selects aprovador when only one is provided', () => {
      renderModal({ aprovadores: [mockAprovadores[0]] });
      const select = screen.getByLabelText(/^aprovador/i) as HTMLSelectElement;
      expect(select.value).toBe('1');
    });

    it('shows percentual in heading', () => {
      renderModal();
      expect(screen.getByText(/15/)).toBeInTheDocument();
    });
  });

  describe('ESC closes without submitting', () => {
    it('calls onClose when ESC is pressed', async () => {
      const user = userEvent.setup();
      renderModal();
      await user.keyboard('{Escape}');
      expect(defaultProps.onClose).toHaveBeenCalledOnce();
      expect(salesAPI.pedidos.aprovarDesconto).not.toHaveBeenCalled();
    });
  });

  describe('Form validation', () => {
    it('shows error when motivo is empty on submit', async () => {
      const user = userEvent.setup();
      renderModal({ aprovadores: [mockAprovadores[0]] });

      await user.type(screen.getByLabelText(/pin/i), '1234');
      await user.click(screen.getByRole('button', { name: /aprovar/i }));

      expect(await screen.findByText(/motivo obrigatório/i)).toBeInTheDocument();
      expect(salesAPI.pedidos.aprovarDesconto).not.toHaveBeenCalled();
    });

    it('shows error when PIN is empty on submit', async () => {
      const user = userEvent.setup();
      renderModal({ aprovadores: [mockAprovadores[0]] });

      await user.type(screen.getByLabelText(/motivo/i), 'Promoção relâmpago');
      await user.click(screen.getByRole('button', { name: /aprovar/i }));

      expect(await screen.findByText(/pin obrigatório/i)).toBeInTheDocument();
    });
  });

  describe('3 wrong attempts — lockout', () => {
    it('disables submit button after 3 failed attempts', async () => {
      const user = userEvent.setup();
      vi.mocked(salesAPI.pedidos.aprovarDesconto).mockRejectedValue(
        new Error('PIN incorreto')
      );
      renderModal({ aprovadores: [mockAprovadores[0]] });

      const pinField = screen.getByLabelText(/pin/i);
      const motivoField = screen.getByLabelText(/motivo/i);
      const submitBtn = screen.getByRole('button', { name: /aprovar/i });

      for (let i = 0; i < 3; i++) {
        await user.clear(pinField);
        await user.type(pinField, 'wrong');
        await user.clear(motivoField);
        await user.type(motivoField, 'Promoção');
        await user.click(submitBtn);
        await waitFor(() =>
          expect(salesAPI.pedidos.aprovarDesconto).toHaveBeenCalledTimes(i + 1)
        );
      }

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /aprovar/i })).toBeDisabled()
      );
    });

    it('shows lockout message after 3 failed attempts', async () => {
      const user = userEvent.setup();
      vi.mocked(salesAPI.pedidos.aprovarDesconto).mockRejectedValue(
        new Error('PIN incorreto')
      );
      renderModal({ aprovadores: [mockAprovadores[0]] });

      const pinField = screen.getByLabelText(/pin/i);
      const motivoField = screen.getByLabelText(/motivo/i);
      const submitBtn = screen.getByRole('button', { name: /aprovar/i });

      for (let i = 0; i < 3; i++) {
        await user.clear(pinField);
        await user.type(pinField, 'wrong');
        await user.clear(motivoField);
        await user.type(motivoField, 'Promoção');
        await user.click(submitBtn);
        await waitFor(() =>
          expect(salesAPI.pedidos.aprovarDesconto).toHaveBeenCalledTimes(i + 1)
        );
      }

      expect(
        await screen.findByText(/número máximo de tentativas/i)
      ).toBeInTheDocument();
    });
  });

  describe('Focus trap (ACC-3)', () => {
    it('focusable elements exist within the dialog', () => {
      renderModal();
      const dialog = screen.getByRole('dialog');
      const focusable = dialog.querySelectorAll(
        'button:not([disabled]), input:not([disabled]), select:not([disabled])'
      );
      expect(focusable.length).toBeGreaterThan(1);
    });
  });

  describe('Successful submission', () => {
    it('calls onSuccess after successful API call', async () => {
      const user = userEvent.setup();
      vi.mocked(salesAPI.pedidos.aprovarDesconto).mockResolvedValue(undefined as never);
      renderModal({ aprovadores: [mockAprovadores[0]] });

      await user.type(screen.getByLabelText(/motivo/i), 'Promoção especial');
      await user.type(screen.getByLabelText(/pin/i), '9999');
      await user.click(screen.getByRole('button', { name: /aprovar/i }));

      await waitFor(() => expect(defaultProps.onSuccess).toHaveBeenCalledOnce());
    });

    it('passes correct payload to API', async () => {
      const user = userEvent.setup();
      vi.mocked(salesAPI.pedidos.aprovarDesconto).mockResolvedValue(undefined as never);
      renderModal({ aprovadores: [mockAprovadores[0]] });

      await user.type(screen.getByLabelText(/motivo/i), 'Promoção especial');
      await user.type(screen.getByLabelText(/pin/i), '9999');
      await user.click(screen.getByRole('button', { name: /aprovar/i }));

      await waitFor(() =>
        expect(salesAPI.pedidos.aprovarDesconto).toHaveBeenCalledWith(
          'test-uuid-0042',
          expect.objectContaining({
            percentual: '15',
            motivo: 'Promoção especial',
            pin: '9999',
            aprovador_id: 1,
            tipo: 'TOTAL',
          })
        )
      );
    });
  });
});
