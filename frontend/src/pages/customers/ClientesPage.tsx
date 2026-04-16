import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Users,
  Search,
  Plus,
  Pencil,
  ToggleLeft,
  ToggleRight,
  X,
  Building2,
  User,
  RefreshCw,
  History,
  ShoppingBag,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { salesAPI } from '@/api/sales';
import type { Cliente, TipoCliente, PedidoVenda } from '@/types';
import type { ClientePayload } from '@/api/sales';

// ─── Schema ───────────────────────────────────────────────────────────────────
const clienteSchema = z
  .object({
    tipo_cliente: z.enum(['PF', 'PJ']),
    nome: z.string().min(2, 'Nome obrigatório'),
    razao_social: z.string().optional().nullable(),
    nome_fantasia: z.string().optional().nullable(),
    cnpj: z.string().optional().nullable(),
    cpf: z.string().optional().nullable(),
    email: z.string().email('E-mail inválido').optional().or(z.literal('')).nullable(),
    telefone_principal: z.string().optional().nullable(),
    celular: z.string().optional().nullable(),
  })
  .superRefine((val, ctx) => {
    if (val.tipo_cliente === 'PJ' && !val.cnpj?.trim()) {
      ctx.addIssue({ code: 'custom', path: ['cnpj'], message: 'CNPJ obrigatório para PJ' });
    }
    if (val.tipo_cliente === 'PF' && !val.cpf?.trim()) {
      ctx.addIssue({ code: 'custom', path: ['cpf'], message: 'CPF obrigatório para PF' });
    }
  });

type ClienteForm = z.infer<typeof clienteSchema>;

// ─── Modal ────────────────────────────────────────────────────────────────────
interface ClienteModalProps {
  cliente?: Cliente | null;
  onClose: () => void;
}

function ClienteModal({ cliente, onClose }: ClienteModalProps) {
  const qc = useQueryClient();

  const {
    register,
    handleSubmit,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ClienteForm>({
    resolver: zodResolver(clienteSchema),
    defaultValues: {
      tipo_cliente: cliente?.tipo_cliente ?? 'PF',
      nome: cliente?.nome ?? '',
      razao_social: cliente?.razao_social ?? '',
      nome_fantasia: cliente?.nome_fantasia ?? '',
      cnpj: cliente?.cnpj ?? '',
      cpf: cliente?.cpf ?? '',
      email: cliente?.email ?? '',
      telefone_principal: cliente?.telefone_principal ?? '',
      celular: cliente?.celular ?? '',
    },
  });

  const tipo = watch('tipo_cliente');

  const saveMutation = useMutation({
    mutationFn: (data: ClientePayload) =>
      cliente
        ? salesAPI.clientes.update(cliente.id, data)
        : salesAPI.clientes.create(data),
    onSuccess: () => {
      toast.success(cliente ? 'Cliente atualizado.' : 'Cliente criado.');
      qc.invalidateQueries({ queryKey: ['clientes'] });
      onClose();
    },
    onError: (err: any) => {
      const fieldErrors: Record<string, string[]> = err?.errors ?? {};
      const hasFieldErrors = Object.keys(fieldErrors).length > 0;
      if (hasFieldErrors) {
        Object.entries(fieldErrors).forEach(([field, msgs]) => {
          const msg = Array.isArray(msgs) ? msgs[0] : String(msgs);
          setError(field as keyof ClienteForm, { message: msg });
        });
        toast.error('Corrija os erros no formulário.');
      } else {
        toast.error(err?.detail ?? 'Erro ao salvar cliente.');
      }
    },
  });

  const onSubmit = (data: ClienteForm) => {
    const payload: ClientePayload = {
      ...data,
      email: data.email || null,
      cnpj: data.cnpj || null,
      cpf: data.cpf || null,
      telefone_principal: data.telefone_principal || null,
      celular: data.celular || null,
      razao_social: data.razao_social || null,
      nome_fantasia: data.nome_fantasia || null,
    };
    saveMutation.mutate(payload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600">
              <Users className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-base font-semibold text-slate-900">
              {cliente ? 'Editar Cliente' : 'Novo Cliente'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          {/* Tipo */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Tipo</label>
            <div className="flex gap-3">
              {(['PF', 'PJ'] as TipoCliente[]).map((t) => (
                <label
                  key={t}
                  className={`flex flex-1 cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm transition-colors ${
                    tipo === t
                      ? 'border-brand-600 bg-brand-50 text-brand-700 ring-1 ring-brand-600'
                      : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <input type="radio" value={t} {...register('tipo_cliente')} className="hidden" />
                  {t === 'PF' ? <User className="h-4 w-4" /> : <Building2 className="h-4 w-4" />}
                  {t === 'PF' ? 'Pessoa Física' : 'Pessoa Jurídica'}
                </label>
              ))}
            </div>
          </div>

          {/* Nome */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              {tipo === 'PJ' ? 'Razão Social' : 'Nome Completo'} *
            </label>
            <input
              type="text"
              {...register('nome')}
              className={`form-input w-full ${errors.nome ? 'border-red-500' : ''}`}
              placeholder={tipo === 'PJ' ? 'Ex: Empresa LTDA' : 'Ex: João da Silva'}
            />
            {errors.nome && <p className="mt-1 text-xs text-red-600">{errors.nome.message}</p>}
          </div>

          {/* PJ fields */}
          {tipo === 'PJ' && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-700">CNPJ *</label>
                  <input
                    type="text"
                    {...register('cnpj')}
                    className={`form-input w-full ${errors.cnpj ? 'border-red-500' : ''}`}
                    placeholder="00.000.000/0000-00"
                  />
                  {errors.cnpj && <p className="mt-1 text-xs text-red-600">{errors.cnpj.message}</p>}
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-700">Nome Fantasia</label>
                  <input
                    type="text"
                    {...register('nome_fantasia')}
                    className="form-input w-full"
                    placeholder="Nome fantasia"
                  />
                </div>
              </div>
            </>
          )}

          {/* PF fields */}
          {tipo === 'PF' && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">CPF *</label>
              <input
                type="text"
                {...register('cpf')}
                className={`form-input w-full ${errors.cpf ? 'border-red-500' : ''}`}
                placeholder="000.000.000-00"
              />
              {errors.cpf && <p className="mt-1 text-xs text-red-600">{errors.cpf.message}</p>}
            </div>
          )}

          {/* Contact */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Telefone</label>
              <input
                type="text"
                {...register('telefone_principal')}
                className="form-input w-full"
                placeholder="(00) 0000-0000"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Celular</label>
              <input
                type="text"
                {...register('celular')}
                className="form-input w-full"
                placeholder="(00) 90000-0000"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">E-mail</label>
            <input
              type="email"
              {...register('email')}
              className={`form-input w-full ${errors.email ? 'border-red-500' : ''}`}
              placeholder="contato@exemplo.com"
            />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando…' : cliente ? 'Salvar alterações' : 'Criar cliente'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Historico Panel ─────────────────────────────────────────────────────────
function HistoricoPanel({ cliente, onClose }: { cliente: Cliente; onClose: () => void }) {
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ['clientes', cliente.id, 'historico'],
    queryFn: () => salesAPI.clientes.historico(cliente.id),
    staleTime: 30_000,
  });

  const pedidos: PedidoVenda[] = (data as { results?: PedidoVenda[] })?.results ?? (data as PedidoVenda[] | undefined) ?? [];

  const fmt = (v: string) =>
    parseFloat(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="fixed inset-0 z-40 flex" role="dialog" aria-modal="true" aria-labelledby="historico-title">
      <button className="flex-1 bg-black/30" onClick={onClose} aria-label="Fechar painel" />
      <div className="flex w-full max-w-lg flex-col bg-white shadow-2xl">
        {/* header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 id="historico-title" className="font-semibold text-slate-900">Histórico de Compras</h2>
            <p className="text-xs text-slate-500">{cliente.nome_completo}</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100" aria-label="Fechar">
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        {/* body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {isLoading && <p className="text-center text-sm text-slate-400 py-8">Carregando…</p>}
          {!isLoading && pedidos.length === 0 && (
            <div className="flex flex-col items-center py-12 text-slate-400">
              <ShoppingBag className="h-8 w-8 mb-2" aria-hidden="true" />
              <p className="text-sm">Nenhum pedido encontrado</p>
            </div>
          )}
          {pedidos.map((p) => (
            <div key={p.id} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-slate-800">{p.numero_pedido}</p>
                  <p className="text-xs text-slate-500">{new Date(p.data_pedido).toLocaleDateString('pt-BR')}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-slate-900">{fmt(p.valor_total)}</p>
                  <p className="text-xs text-slate-500 capitalize">{p.situacao.toLowerCase()}</p>
                </div>
              </div>
              {p.itens && p.itens.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {p.itens.slice(0, 3).map((item) => (
                    <li key={item.id} className="flex justify-between text-xs text-slate-600">
                      <span>{item.produto_nome}</span>
                      <span>{item.quantidade}×</span>
                    </li>
                  ))}
                  {p.itens.length > 3 && (
                    <li className="text-xs text-slate-400">…e mais {p.itens.length - 3} item(s)</li>
                  )}
                </ul>
              )}
              <div className="mt-3 flex justify-end">
                <button
                  className="btn-secondary text-xs py-1 px-3"
                  onClick={() => navigate('/pdv', { state: { itens: p.itens } })}
                >
                  Reordenar
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function ClientesPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState('');
  const [tipoFiltro, setTipoFiltro] = useState<'' | 'PF' | 'PJ'>('');
  const [apenasAtivos, setApenasAtivos] = useState(true);
  const [page, setPage] = useState(1);
  const [modalCliente, setModalCliente] = useState<Cliente | null | undefined>(undefined);
  const [historicoCliente, setHistoricoCliente] = useState<Cliente | null>(null);

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['clientes', search, tipoFiltro, apenasAtivos, page],
    queryFn: () =>
      salesAPI.clientes.list({
        search: search || undefined,
        tipo_cliente: tipoFiltro || undefined,
        ativo: apenasAtivos ? true : undefined,
        page,
        page_size: 20,
      }),
    staleTime: 30_000,
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => salesAPI.clientes.toggleAtivo(id),
    onSuccess: (updated) => {
      toast.success(updated.ativo ? 'Cliente ativado.' : 'Cliente desativado.');
      qc.invalidateQueries({ queryKey: ['clientes'] });
    },
    onError: () => toast.error('Erro ao alterar status.'),
  });

  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  return (
    <>
      {modalCliente !== undefined && (
        <ClienteModal
          cliente={modalCliente}
          onClose={() => setModalCliente(undefined)}
        />
      )}
      {historicoCliente && (
        <HistoricoPanel
          cliente={historicoCliente}
          onClose={() => setHistoricoCliente(null)}
        />
      )}

      <div className="flex-1 overflow-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600">
              <Users className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Clientes</h1>
              <p className="text-sm text-slate-500">
                {data ? `${data.count} cliente${data.count !== 1 ? 's' : ''}` : ''}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              className="btn-secondary flex items-center gap-2"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
            <button
              className="btn-primary flex items-center gap-2"
              onClick={() => setModalCliente(null)}
            >
              <Plus className="h-4 w-4" />
              Novo cliente
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-4 flex flex-wrap gap-3">
          <label className="relative flex flex-1 min-w-[200px] items-center">
            <Search className="absolute left-3 h-4 w-4 text-slate-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Buscar por nome, CPF ou CNPJ…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="form-input pl-9 w-full"
            />
          </label>

          <select
            value={tipoFiltro}
            onChange={(e) => { setTipoFiltro(e.target.value as '' | 'PF' | 'PJ'); setPage(1); }}
            className="form-input min-w-[140px]"
          >
            <option value="">Todos os tipos</option>
            <option value="PF">Pessoa Física</option>
            <option value="PJ">Pessoa Jurídica</option>
          </select>

          <label className="flex items-center gap-2 cursor-pointer select-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
            <input
              type="checkbox"
              checked={apenasAtivos}
              onChange={(e) => { setApenasAtivos(e.target.checked); setPage(1); }}
              className="h-4 w-4 rounded accent-brand-600"
            />
            Apenas ativos
          </label>
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Código</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Nome</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">Tipo</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">CPF / CNPJ</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Contato</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">Status</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600">Ações</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-slate-100 animate-pulse">
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 rounded bg-slate-100" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : data?.results.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-16 text-center">
                      <Users className="mx-auto mb-3 h-10 w-10 text-slate-200" />
                      <p className="mb-2 text-sm text-slate-400">Nenhum cliente encontrado</p>
                      <button
                        className="btn-primary text-xs"
                        onClick={() => setModalCliente(null)}
                      >
                        Cadastrar primeiro cliente
                      </button>
                    </td>
                  </tr>
                ) : (
                  data?.results.map((cliente) => (
                    <tr
                      key={cliente.id}
                      className={`border-b border-slate-100 transition-colors hover:bg-slate-50 ${
                        !cliente.ativo ? 'opacity-60' : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">
                        {cliente.codigo_cliente}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">{cliente.nome_completo}</div>
                        {cliente.nome_fantasia && (
                          <div className="text-xs text-slate-400">{cliente.nome_fantasia}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            cliente.tipo_cliente === 'PJ'
                              ? 'bg-violet-50 text-violet-700 ring-1 ring-violet-200'
                              : 'bg-sky-50 text-sky-700 ring-1 ring-sky-200'
                          }`}
                        >
                          {cliente.tipo_cliente === 'PJ' ? (
                            <Building2 className="h-3 w-3" />
                          ) : (
                            <User className="h-3 w-3" />
                          )}
                          {cliente.tipo_cliente}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-600">
                        {cliente.cnpj ?? cliente.cpf ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        <div>{cliente.telefone_principal ?? cliente.celular ?? '—'}</div>
                        {cliente.email && (
                          <div className="text-xs text-slate-400">{cliente.email}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            cliente.ativo
                              ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                              : 'bg-slate-100 text-slate-500 ring-1 ring-slate-200'
                          }`}
                        >
                          {cliente.ativo ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          <button
                            className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-500 transition hover:bg-slate-50 hover:text-brand-600"
                            title="Editar"
                            onClick={() => setModalCliente(cliente)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          <button
                            className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-500 transition hover:bg-slate-50"
                            title={cliente.ativo ? 'Desativar' : 'Ativar'}
                            onClick={() => toggleMutation.mutate(cliente.id)}
                          >
                            {cliente.ativo ? (
                              <ToggleRight className="h-3.5 w-3.5 text-emerald-600" />
                            ) : (
                              <ToggleLeft className="h-3.5 w-3.5 text-slate-400" />
                            )}
                          </button>
                          <button
                            className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-500 transition hover:bg-slate-50 hover:text-brand-600"
                            title="Histórico de compras"
                            onClick={() => setHistoricoCliente(cliente)}
                          >
                            <History className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-4 py-3">
              <span className="text-xs text-slate-500">
                Página {page} de {totalPages} · {data?.count} registros
              </span>
              <div className="flex gap-1">
                <button
                  className="btn-secondary px-3 py-1 text-xs"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Anterior
                </button>
                <button
                  className="btn-secondary px-3 py-1 text-xs"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Próxima
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
