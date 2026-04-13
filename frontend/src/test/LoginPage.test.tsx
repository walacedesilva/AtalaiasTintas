import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import LoginPage from '../pages/auth/LoginPage';

/**
 * LoginPage Component Tests
 * Following TDD approach - comprehensive testing of authentication flow
 */

// Mock API module
vi.mock('@/api', () => ({
  authAPI: {
    login: vi.fn(),
    isAuthenticated: vi.fn(() => false)
  }
}));

// Mock environment
vi.mock('@/utils/env', () => ({
  APP_NAME: 'Atalaia Tintas Test'
}));

// Test wrapper component
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
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render login form with all required fields', () => {
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      // Check for app branding
      expect(screen.getByText('Atalaia Tintas Test')).toBeInTheDocument();
      expect(screen.getByText('Sistema de Gestão de Tintas e Etiquetas')).toBeInTheDocument();

      // Check form title
      expect(screen.getByText('Fazer login na sua conta')).toBeInTheDocument();

      // Check form fields
      const usernameField = screen.getByLabelText('Nome de usuário');
      const passwordField = screen.getByLabelText('Senha');
      const submitButton = screen.getByRole('button', { name: /entrar/i });

      expect(usernameField).toBeInTheDocument();
      expect(passwordField).toBeInTheDocument();
      expect(submitButton).toBeInTheDocument();

      // Check password field is initially hidden
      expect(passwordField).toHaveAttribute('type', 'password');
    });

    it('should have proper accessibility attributes', () => {
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const usernameField = screen.getByLabelText('Nome de usuário');
      const passwordField = screen.getByLabelText('Senha');
      const form = screen.getByRole('form', { name: /login/i });

      // Check ARIA attributes
      expect(usernameField).toHaveAttribute('autoComplete', 'username');
      expect(passwordField).toHaveAttribute('autoComplete', 'current-password');
      expect(form).toBeInTheDocument();
    });

    it('should focus on username field when mounted', async () => {
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const usernameField = screen.getByLabelText('Nome de usuário');
      
      // Wait for focus to be set
      await waitFor(() => {
        expect(usernameField).toHaveFocus();
      });
    });
  });

  describe('Form Validation', () => {
    it('should show validation errors for empty fields', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /entrar/i });
      
      // Try to submit empty form
      await user.click(submitButton);

      // Check for validation messages
      await waitFor(() => {
        expect(screen.getByText('Nome de usuário é obrigatório')).toBeInTheDocument();
        expect(screen.getByText('Senha é obrigatória')).toBeInTheDocument();
      });
    });

    it('should show validation errors for short inputs', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const usernameField = screen.getByLabelText('Nome de usuário');
      const passwordField = screen.getByLabelText('Senha');
      const submitButton = screen.getByRole('button', { name: /entrar/i });

      // Enter short inputs
      await user.type(usernameField, 'ab'); // Less than 3 chars
      await user.type(passwordField, '123'); // Less than 6 chars
      await user.click(submitButton);

      // Check for validation messages
      await waitFor(() => {
        expect(screen.getByText('Nome de usuário deve ter pelo menos 3 caracteres')).toBeInTheDocument();
        expect(screen.getByText('Senha deve ter pelo menos 6 caracteres')).toBeInTheDocument();
      });
    });

    it('should not show errors for valid inputs', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const usernameField = screen.getByLabelText('Nome de usuário');
      const passwordField = screen.getByLabelText('Senha');

      // Enter valid inputs
      await user.type(usernameField, 'validuser');
      await user.type(passwordField, 'validpassword123');

      // Should not have validation error messages
      expect(screen.queryByText(/Nome de usuário/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Senha/)).not.toBeInTheDocument();
    });
  });

  describe('Password Visibility Toggle', () => {
    it('should toggle password visibility when show/hide button is clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const passwordField = screen.getByLabelText('Senha');
      const toggleButton = screen.getByLabelText('Mostrar senha');

      // Initially password should be hidden
      expect(passwordField).toHaveAttribute('type', 'password');

      // Click to show password
      await user.click(toggleButton);
      expect(passwordField).toHaveAttribute('type', 'text');
      expect(screen.getByLabelText('Ocultar senha')).toBeInTheDocument();

      // Click to hide password again
      await user.click(screen.getByLabelText('Ocultar senha'));
      expect(passwordField).toHaveAttribute('type', 'password');
      expect(screen.getByLabelText('Mostrar senha')).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('should disable submit button and show loading state during submission', async () => {
      const user = userEvent.setup();
      
      // Mock delayed API response
      const mockLogin = vi.fn(() => new Promise(resolve => setTimeout(resolve, 1000)));
      vi.mocked(require('@/api').authAPI.login).mockImplementation(mockLogin);

      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const usernameField = screen.getByLabelText('Nome de usuário');
      const passwordField = screen.getByLabelText('Senha');
      const submitButton = screen.getByRole('button', { name: /entrar/i });

      // Fill form with valid data
      await user.type(usernameField, 'testuser');
      await user.type(passwordField, 'testpassword123');

      // Submit form
      await user.click(submitButton);

      // Check loading state
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
        expect(screen.getByText('Entrando...')).toBeInTheDocument();
      });
    });

    it('should call login API with correct credentials', async () => {
      const user = userEvent.setup();
      const mockLogin = vi.fn().mockResolvedValue({
        access: 'token',
        refresh: 'refresh',
        user: { id: 1, username: 'testuser' }
      });
      
      vi.mocked(require('@/api').authAPI.login).mockImplementation(mockLogin);

      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const usernameField = screen.getByLabelText('Nome de usuário');
      const passwordField = screen.getByLabelText('Senha');
      const submitButton = screen.getByRole('button', { name: /entrar/i });

      // Fill and submit form
      await user.type(usernameField, 'testuser');
      await user.type(passwordField, 'testpass123');
      await user.click(submitButton);

      // Verify API was called with correct data
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'testpass123'
        });
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      // Check form has proper role and labels
      const usernameField = screen.getByLabelText('Nome de usuário');
      const passwordField = screen.getByLabelText('Senha');
      const submitButton = screen.getByRole('button', { name: /entrar/i });

      expect(usernameField).toHaveAttribute('aria-invalid', 'false');
      expect(passwordField).toHaveAttribute('aria-invalid', 'false');
      expect(submitButton).toBeInTheDocument();
    });

    it('should announce validation errors to screen readers', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /entrar/i });
      
      // Submit empty form to trigger validation
      await user.click(submitButton);

      await waitFor(() => {
        const usernameError = screen.getByRole('alert');
        expect(usernameError).toBeInTheDocument();
        expect(usernameError).toHaveTextContent('Nome de usuário é obrigatório');
      });
    });

    it('should have proper focus management', async () => {
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const usernameField = screen.getByLabelText('Nome de usuário');
      
      // Username should be focused on mount
      await waitFor(() => {
        expect(usernameField).toHaveFocus();
      });
    });
  });
});