import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PigmentCard } from './PigmentCard';
import type { Pigmento } from '@/types';

/**
 * PigmentCard Component Tests
 * Testing display and interaction of pigment information cards
 */

// Test wrapper
function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
}

// Mock pigment data
const mockPigmento: Pigmento = {
  id: 1,
  codigo: 'PIG001',
  nome: 'Azul Cobalto',
  densidade: '2.5',
  preco_litro: '85.50',
  cor_hex: '#0047AB',
  ativo: true,
  observacoes: 'Pigmento de alta qualidade',
  created_at: '2024-04-12T10:00:00Z',
  updated_at: '2024-04-12T10:00:00Z'
};

const mockInactivePigmento: Pigmento = {
  ...mockPigmento,
  id: 2,
  codigo: 'PIG002',
  nome: 'Vermelho Cadmium',
  cor_hex: '#E30022',
  ativo: false
};

describe('PigmentCard', () => {
  it('should display pigment information correctly', () => {
    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} />
      </TestWrapper>
    );

    // Check basic information is displayed
    expect(screen.getByText('Azul Cobalto')).toBeInTheDocument();
    expect(screen.getByText('PIG001')).toBeInTheDocument();
    expect(screen.getByText('Densidade:')).toBeInTheDocument();
    expect(screen.getByText('2.5')).toBeInTheDocument();
    expect(screen.getByText(/R\$ 85,50/)).toBeInTheDocument();
    
    // Check color preview is present
    const colorPreview = screen.getByLabelText('Cor Azul Cobalto');
    expect(colorPreview).toHaveStyle('background-color: #0047AB');
  });

  it('should show active status badge for active pigments', () => {
    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} />
      </TestWrapper>
    );

    expect(screen.getByText('Ativo')).toBeInTheDocument();
    expect(screen.getByText('Ativo')).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('should show inactive status badge for inactive pigments', () => {
    render(
      <TestWrapper>
        <PigmentCard pigmento={mockInactivePigmento} />
      </TestWrapper>
    );

    expect(screen.getByText('Inativo')).toBeInTheDocument();
    expect(screen.getByText('Inativo')).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('should display observations when present', () => {
    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} />
      </TestWrapper>
    );

    expect(screen.getByText('Pigmento de alta qualidade')).toBeInTheDocument();
  });

  it('should not display observations section when empty', () => {
    const { observacoes: _obs, ...pigmentWithoutObservations } = mockPigmento;

    render(
      <TestWrapper>
        <PigmentCard pigmento={pigmentWithoutObservations} />
      </TestWrapper>
    );

    expect(screen.queryByText('Observações:')).not.toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} />
      </TestWrapper>
    );

    // Color preview should have proper aria-label
    const colorPreview = screen.getByLabelText('Cor Azul Cobalto');
    expect(colorPreview).toBeInTheDocument();

    // Status badge should be accessible
    const statusBadge = screen.getByText('Ativo');
    expect(statusBadge).toHaveAttribute('aria-label', 'Status: Ativo');

    // Price should have proper formatting for screen readers
    const price = screen.getByText(/R\$ 85,50/);
    expect(price).toHaveAttribute('aria-label', 'Preço por litro: R$ 85,50');
  });

  it('should handle edit action when onEdit is provided', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} onEdit={onEdit} />
      </TestWrapper>
    );

    const editButton = screen.getByRole('button', { name: /editar/i });
    await user.click(editButton);

    expect(onEdit).toHaveBeenCalledWith(mockPigmento);
  });

  it('should handle delete action when onDelete is provided', async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} onDelete={onDelete} />
      </TestWrapper>
    );

    const deleteButton = screen.getByRole('button', { name: /excluir/i });
    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith(mockPigmento);
  });

  it('should not show action buttons when no handlers provided', () => {
    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} />
      </TestWrapper>
    );

    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /excluir/i })).not.toBeInTheDocument();
  });

  it('should be keyboard navigable', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(
      <TestWrapper>
        <PigmentCard pigmento={mockPigmento} onEdit={onEdit} />
      </TestWrapper>
    );

    const editButton = screen.getByRole('button', { name: /editar/i });
    
    // Tab to button and press Enter
    await user.tab();
    expect(editButton).toHaveFocus();
    
    await user.keyboard('{Enter}');
    expect(onEdit).toHaveBeenCalledWith(mockPigmento);
  });
});