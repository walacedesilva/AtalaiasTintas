import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { User, Mail, AtSign, ShieldCheck, Calendar, Settings } from 'lucide-react';

export default function ProfilePage(): React.ReactElement {
  const { user } = useAuth();

  const initials =
    user?.first_name && user?.last_name
      ? `${user.first_name[0]}${user.last_name[0]}`
      : (user?.username?.[0] ?? '?').toUpperCase();

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Meu Perfil</h1>
        <p className="text-sm text-slate-500 mt-0.5">Informações da sua conta</p>
      </div>

      {/* Profile card */}
      <div className="card overflow-hidden">
        {/* Cover */}
        <div className="h-24 bg-gradient-to-br from-teal-600 to-teal-800" />
        <div className="px-6 pb-6">
          <div className="-mt-10 mb-4 flex items-end justify-between">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-slate-900 border-4 border-white text-2xl font-bold text-white shadow-md">
              {initials}
            </div>
            <span className={`badge ${user?.is_active ? 'badge-green' : 'badge-red'} mb-2`}>
              {user?.is_active ? 'Conta ativa' : 'Conta inativa'}
            </span>
          </div>

          <h2 className="text-xl font-bold text-slate-900">
            {user?.first_name && user?.last_name
              ? `${user.first_name} ${user.last_name}`
              : user?.username}
          </h2>
          {user?.is_staff && (
            <span className="mt-1 badge badge-blue">Administrador</span>
          )}
        </div>
      </div>

      {/* Details */}
      <div className="card divide-y divide-slate-100">
        {[
          { icon: User,       label: 'Nome completo',    value: user ? `${user.first_name} ${user.last_name}`.trim() || '—' : '—' },
          { icon: AtSign,     label: 'Nome de usuário',  value: user?.username ?? '—' },
          { icon: Mail,       label: 'E-mail',            value: user?.email ?? '—' },
          { icon: ShieldCheck,label: 'Permissões',       value: user?.is_staff ? 'Administrador' : 'Usuário padrão' },
          { icon: Calendar,   label: 'Membro desde',     value: user?.date_joined ? new Date(user.date_joined).toLocaleDateString('pt-BR', { year: 'numeric', month: 'long', day: 'numeric' }) : '—' },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex items-center gap-4 px-6 py-4">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-50">
              <Icon className="h-4 w-4 text-slate-400" aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-400">{label}</p>
              <p className="text-sm font-medium text-slate-900 truncate">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Edit coming soon */}
      <div className="card p-5 flex items-center gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100">
          <Settings className="h-5 w-5 text-slate-400" aria-hidden="true" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-700">Edição de perfil</p>
          <p className="text-xs text-slate-400">Alteração de senha e dados pessoais em breve</p>
        </div>
        <span className="badge badge-gray">Em breve</span>
      </div>
    </div>
  );
}