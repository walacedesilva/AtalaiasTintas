import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { Eye, EyeOff, Paintbrush, Lock, User as UserIcon, Loader2 } from 'lucide-react';
import { useLogin } from '@/hooks/useAuth';

const loginSchema = z.object({
  username: z.string().min(1, 'Nome de usuário é obrigatório').min(3, 'Mínimo 3 caracteres'),
  password: z.string().min(1, 'Senha é obrigatória').min(6, 'Mínimo 6 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage(): React.ReactElement {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const loginMutation = useLogin();

  const {
    register,
    handleSubmit,
    setFocus,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  useEffect(() => { setFocus('username'); }, [setFocus]);

  useEffect(() => {
    const reason = searchParams.get('reason');
    if (reason === 'session-expired') toast.error('Sua sessão expirou. Faça login novamente.');
    else if (reason === 'unauthorized') toast.error('Acesso não autorizado.');
  }, [searchParams]);

  const onSubmit = async (data: LoginFormData): Promise<void> => {
    try {
      await loginMutation.mutateAsync(data);
      toast.success('Login realizado com sucesso!');
      navigate(searchParams.get('redirect') || '/dashboard', { replace: true });
    } catch (error: any) {
      toast.error(error?.detail || error?.non_field_errors?.[0] || error?.message || 'Credenciais inválidas.');
    }
  };

  const isLoading = isSubmitting || loginMutation.isPending;

  return (
    <div className="min-h-screen flex">
      {/* LEFT PANEL */}
      <div
        className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center bg-slate-900 px-12 py-16 relative overflow-hidden"
        aria-hidden="true"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(13,148,136,0.25)_0%,transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(13,148,136,0.15)_0%,transparent_60%)]" />
        <div className="relative z-10 text-center max-w-sm">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-600 shadow-xl mx-auto mb-8">
            <Paintbrush className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight mb-3">Atalaia Tintas</h1>
          <p className="text-slate-400 text-base leading-relaxed mb-10">
            Gestão inteligente para a sua tintaria. Controle misturas, etiquetas e estoque em um único sistema.
          </p>
          <div className="space-y-3 text-left">
            {[
              { icon: '🎨', text: 'Catálogo completo de cores e fórmulas' },
              { icon: '🧪', text: 'Controle de misturas em tempo real' },
              { icon: '🏷️', text: 'Geração automática de etiquetas' },
              { icon: '📦', text: 'Alertas de estoque inteligentes' },
            ].map(({ icon, text }) => (
              <div key={text} className="flex items-center gap-3 rounded-xl bg-slate-800/60 px-4 py-3">
                <span className="text-xl">{icon}</span>
                <span className="text-sm text-slate-300">{text}</span>
              </div>
            ))}
          </div>
          <p className="mt-10 text-xs text-slate-600">Atalaia Tintas © 2026</p>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="flex flex-1 flex-col items-center justify-center bg-slate-50 px-6 py-12 sm:px-12">
        <div className="w-full max-w-md">
          <div className="flex lg:hidden items-center justify-center gap-2 mb-8">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-600">
              <Paintbrush className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900">Atalaia Tintas</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-1">Bem-vindo de volta!</h2>
          <p className="text-sm text-slate-500 mb-8">Entre com suas credenciais para acessar o sistema.</p>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-700 mb-1.5">
                Nome de usuário
              </label>
              <div className="relative">
                <UserIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
                <input
                  {...register('username')}
                  id="username"
                  type="text"
                  autoComplete="username"
                  placeholder="Digite seu usuário"
                  aria-invalid={errors.username ? 'true' : 'false'}
                  className={`form-input pl-10 ${errors.username ? 'form-input-error' : ''}`}
                />
              </div>
              {errors.username && (
                <p className="mt-1.5 text-xs text-rose-600" role="alert">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
                Senha
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" aria-hidden="true" />
                <input
                  {...register('password')}
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Digite sua senha"
                  aria-invalid={errors.password ? 'true' : 'false'}
                  className={`form-input pl-10 pr-10 ${errors.password ? 'form-input-error' : ''}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="flex justify-end mt-1.5">
                <button
                  type="button"
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium transition-colors"
                  onClick={() => toast('Entre em contato com o administrador.', { icon: 'ℹ️' })}
                >
                  Esqueceu sua senha?
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-rose-600" role="alert">{errors.password.message}</p>
              )}
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary w-full py-2.5">
              {isLoading ? (
                <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />Entrando…</>
              ) : 'Entrar'}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-slate-400">
            Não tem uma conta?{' '}
            <button
              type="button"
              className="font-medium text-teal-600 hover:text-teal-700 transition-colors"
              onClick={() => toast('Solicite acesso ao administrador do sistema.', { icon: 'ℹ️' })}
            >
              Cadastre-se
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}