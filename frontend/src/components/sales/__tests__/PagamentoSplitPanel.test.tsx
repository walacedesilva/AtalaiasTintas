/**
 * T051 — PagamentoSplitPanel unit tests.
 * - Troco calculado corretamente para DINHEIRO
 * - Botão finalizar desabilitado quando soma ≠ total
 * - Adição/remoção de formas de pagamento
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PagamentoSplitPanel from '../PagamentoSplitPanel';

function renderPanel(props: { valorLiquido?: number; onConfirm?: ReturnType<typeof vi.fn>; disabled?: boolean } = {}) {
  const onConfirm = props.onConfirm ?? vi.fn();
  render(
    <PagamentoSplitPanel
      valorLiquido={props.valorLiquido ?? 100.0}
      onConfirm={onConfirm}
      disabled={props.disabled}
    />
  );
  return { onConfirm };
}

// Helper to get the confirm button
const confirmBtn = () => screen.getByRole('button', { name: /confirmar pagamento/i });

describe('PagamentoSplitPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial state', () => {
    it('renders confirm button initially disabled (no value entered)', () => {
      renderPanel({ valorLiquido: 100.0 });
      expect(confirmBtn()).toBeDisabled();
    });

    it('shows the required total', () => {
      renderPanel({ valorLiquido: 150.75 });
      expect(screen.getByText('R$ 150.75')).toBeInTheDocument();
    });

    it('has one payment row by default with DINHEIRO selected', () => {
      renderPanel();
      const select = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      expect(select.value).toBe('DINHEIRO');
    });
  });

  describe('Troco calculado para DINHEIRO', () => {
    it('shows troco when cash paid exceeds total', async () => {
      const user = userEvent.setup();
      renderPanel({ valorLiquido: 50.0 });

      const valorInput = screen.getByPlaceholderText(/0,00/i);
      await user.clear(valorInput);
      await user.type(valorInput, '60');

      // troco = 60 - 50 = 10
      expect(screen.getByText(/R\$ 10\.00/)).toBeInTheDocument();
    });

    it('does not show troco when payment equals total', async () => {
      const user = userEvent.setup();
      renderPanel({ valorLiquido: 100.0 });

      const valorInput = screen.getByPlaceholderText(/0,00/i);
      await user.clear(valorInput);
      await user.type(valorInput, '100');

      expect(screen.queryByText(/troco/i)).not.toBeInTheDocument();
    });

    it('does not show troco for PIX even if amount exceeds total', async () => {
      const user = userEvent.setup();
      renderPanel({ valorLiquido: 50.0 });

      const select = screen.getAllByRole('combobox')[0];
      await user.selectOptions(select, 'PIX');

      const valorInput = screen.getByPlaceholderText(/0,00/i);
      await user.clear(valorInput);
      await user.type(valorInput, '60');

      expect(screen.queryByText(/troco/i)).not.toBeInTheDocument();
    });
  });

  describe('Botão confirm desabilitado quando soma ≠ total', () => {
    it('enables confirm when payment sum equals total', async () => {
      const user = userEvent.setup();
      renderPanel({ valorLiquido: 100.0 });

      const valorInput = screen.getByPlaceholderText(/0,00/i);
      await user.clear(valorInput);
      await user.type(valorInput, '100');

      expect(confirmBtn()).not.toBeDisabled();
    });

    it('keeps confirm disabled when sum < total', async () => {
      const user = userEvent.setup();
      renderPanel({ valorLiquido: 100.0 });

      const valorInput = screen.getByPlaceholderText(/0,00/i);
      await user.clear(valorInput);
      await user.type(valorInput, '80');

      expect(confirmBtn()).toBeDisabled();
    });

    it('keeps confirm disabled when sum > total (non-cash overpay)', async () => {
      const user = userEvent.setup();
      renderPanel({ valorLiquido: 100.0 });

      const select = screen.getAllByRole('combobox')[0];
      await user.selectOptions(select, 'PIX');

      const valorInput = screen.getByPlaceholderText(/0,00/i);
      await user.clear(valorInput);
      await user.type(valorInput, '120');

      expect(confirmBtn()).toBeDisabled();
    });

    it('shows deficit message when sum < total', async () => {
      const user = userEvent.setup();
      renderPanel({ valorLiquido: 100.0 });

      const valorInput = screen.getByPlaceholderText(/0,00/i);
      await user.clear(valorInput);
      await user.type(valorInput, '60');

      expect(screen.getByText(/faltam/i)).toBeInTheDocument();
    });
  });

  describe('Adição/remoção de formas de pagamento', () => {
    it('adds a second payment row when clicking Adicionar forma', async () => {
      const user = userEvent.setup();
      renderPanel();

      await user.click(screen.getByRole('button', { name: /adicionar forma/i }));

      const selects = screen.getAllByRole('combobox');
      expect(selects).toHaveLength(2);
    });

    it('confirms with multiple payment rows summing to total', async () => {
      const user = userEvent.setup();
      const { onConfirm } = renderPanel({ valorLiquido: 100.0 });

      // Fill first row
      const valorInputs = screen.getAllByPlaceholderText(/0,00/i);
      await user.clear(valorInputs[0]);
      await user.type(valorInputs[0], '60');

      // Add second row
      await user.click(screen.getByRole('button', { name: /adicionar forma/i }));

      // Fill second row
      const valorInputs2 = screen.getAllByPlaceholderText(/0,00/i);
      const select2 = screen.getAllByRole('combobox')[1];
      await user.selectOptions(select2, 'PIX');
      await user.clear(valorInputs2[1]);
      await user.type(valorInputs2[1], '40');

      await user.click(confirmBtn());

      expect(onConfirm).toHaveBeenCalledWith([
        { forma: 'DINHEIRO', valor: 60 },
        { forma: 'PIX', valor: 40 },
      ]);
    });

    it('remove button is disabled when only one row exists', () => {
      renderPanel();
      const removeBtn = screen.getByRole('button', { name: /remover pagamento 1/i });
      expect(removeBtn).toBeDisabled();
    });

    it('can remove a row when more than one exists', async () => {
      const user = userEvent.setup();
      renderPanel();

      await user.click(screen.getByRole('button', { name: /adicionar forma/i }));
      expect(screen.getAllByRole('combobox')).toHaveLength(2);

      await user.click(screen.getByRole('button', { name: /remover pagamento 2/i }));
      expect(screen.getAllByRole('combobox')).toHaveLength(1);
    });
  });

  describe('Disabled state', () => {
    it('disables inputs when disabled prop is true', () => {
      renderPanel({ disabled: true });
      const select = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      expect(select).toBeDisabled();
    });
  });
});
