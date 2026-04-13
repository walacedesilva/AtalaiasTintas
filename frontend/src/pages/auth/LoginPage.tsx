import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { useLogin } from '@/hooks/useAuth';
import { APP_NAME } from '@/utils/env';
import type { LoginRequest } from '@/types';

/**
 * Login page component
 * Provides user authentication with form validation and error handling
 */

// Form validation schema
const loginSchema = z.object({
  username: z.string()
    .min(1, 'Nome de usuário é obrigatório')
    .min(3, 'Nome de usuário deve ter pelo menos 3 caracteres'),
  password: z.string()
    .min(1, 'Senha é obrigatória')
    .min(6, 'Senha deve ter pelo menos 6 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage(): React.ReactElement {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const loginMutation = useLogin();

  // Redirect reason from query params
  const redirectReason = searchParams.get('reason');

  // Form management with react-hook-form and Zod validation
  const {
    register,
    handleSubmit,
    setFocus,
    formState: { errors, isSubmitting }
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: ''
    }
  });

  // Auto-focus on username field
  useEffect(() => {
    setFocus('username');
  }, [setFocus]);

  // Show redirect reason message
  useEffect(() => {
    if (redirectReason === 'session-expired') {
      toast.error('Sua sessão expirou. Faça login novamente.');
    } else if (redirectReason === 'unauthorized') {
      toast.error('Acesso não autorizado. Faça login para continuar.');
    }
  }, [redirectReason]);

  // Handle form submission
  const onSubmit = async (data: LoginFormData): Promise<void> => {
    try {
      await loginMutation.mutateAsync(data);
      
      // Success message
      toast.success('Login realizado com sucesso!');
      
      // Redirect to dashboard or intended page
      const redirectTo = searchParams.get('redirect') || '/dashboard';
      navigate(redirectTo, { replace: true });
      
    } catch (error: any) {
      // Error handling
      const message = error?.detail || error?.message || 'Erro ao fazer login';
      toast.error(message);
    }
  };

  // Loading state
  const isLoading = isSubmitting || loginMutation.isPending;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-lg flex items-center justify-center mb-6">
            <span className="text-white font-bold text-2xl">AT</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">
            {APP_NAME}
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Sistema de Gestão de Tintas e Etiquetas
          </p>
          <h2 className="mt-6 text-xl font-semibold text-gray-900">
            Fazer login na sua conta
          </h2>
        </div>

        {/* Login Form */}
        <form 
          className="mt-8 space-y-6" 
          onSubmit={handleSubmit(onSubmit)}
          noValidate
        >
          <div className="space-y-4">
            {/* Username Field */}
            <div>
              <label 
                htmlFor="username" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Nome de usuário
              </label>
              <input
                {...register('username')}
                id="username"
                type="text"
                autoComplete="username"
                className={`form-input ${
                  errors.username ? 'border-red-400 focus:border-red-400' : ''
                }`}
                placeholder="Digite seu nome de usuário"
                aria-invalid={errors.username ? 'true' : 'false'}
                aria-describedby={errors.username ? 'username-error' : undefined}
              />
              {errors.username && (
                <p 
                  id="username-error" 
                  className="mt-1 text-sm text-red-600"
                  role="alert"
                >
                  {errors.username.message}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label 
                htmlFor="password" 
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Senha
              </label>
              <div className="relative">
                <input
                  {...register('password')}
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className={`form-input pr-10 ${
                    errors.password ? 'border-red-400 focus:border-red-400' : ''
                  }`}
                  placeholder="Digite sua senha"
                  aria-invalid={errors.password ? 'true' : 'false'}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
                
                {/* Show/Hide Password Button */}
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  {showPassword ? (
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                    </svg>
                  )}
                </button>
              </div>
              {errors.password && (
                <p 
                  id="password-error" 
                  className="mt-1 text-sm text-red-600"
                  role="alert"
                >
                  {errors.password.message}
                </p>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={isLoading}
              className={`
                w-full flex justify-center py-2 px-4 border border-transparent 
                rounded-md shadow-sm text-sm font-medium text-white
                ${isLoading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                }
                transition-colors duration-200
              `}
              aria-describedby="login-status"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Entrando...
                </>
              ) : (
                'Entrar'
              )}
            </button>
            
            {/* Status message for screen readers */}
            <div 
              id="login-status" 
              className="sr-only" 
              role="status" 
              aria-live="polite"
              aria-atomic="true"
            >
              {isLoading ? 'Fazendo login, aguarde...' : ''}
            </div>
          </div>

          {/* Help Links */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Problemas para acessar?{' '}
              <button
                type="button"
                className="font-medium text-blue-600 hover:text-blue-500"
                onClick={() => toast.info('Entre em contato com o administrador do sistema')}
              >
                Contacte o suporte
              </button>
            </p>
          </div>
        </form>

        {/* System Info */}
        <div className="mt-8 text-center text-xs text-gray-500">
          <p>
            Sistema desenvolvido para Atalaia Tintas<br />
            Versão 1.0.0 - Todos os direitos reservados
          </p>
        </div>
      </div>
    </div>
  );
}