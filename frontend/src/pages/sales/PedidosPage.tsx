import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShoppingBag,
  Plus,
  Search,
  RefreshCw,
  X,
  Trash2,
  CheckCircle2,
  Clock,
  Ban,
  Layers,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Truck,
  Printer,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { salesAPI, type PedidoCreatePayload, type ItemAddPayload } from '@/api/sales';
import { companiesAPI } from '@/api/companies';
import { inventoryAPI } from '@/api/inventory';
import type { PedidoVenda, SituacaoPedido, Loja, EstoqueLojaItem, Cliente } from '@/types';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { OrcamentoPrintLayout } from '@/components/print/OrcamentoPrintLayout';

// ─── Status badge ─────────────────────────────────────────────────────────────
const STATUS_CONFIG: Record<SituacaoPedido, { label: string; className: string; icon: React.ReactNode }> = {
  ORCAMENTO: {
    label: 'Orçamento',
    className: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
    icon: <Clock className="h-3 w-3" />,
  },
  APROVADO: {
    label: 'Aprovado',
    className: 'bg-teal-50 text-teal-700 ring-1 ring-teal-200',
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  PRODUCAO: {
    label: 'Em Produção',
    className: 'bg-violet-50 text-violet-700 ring-1 ring-violet-200',
    icon: <Layers className="h-3 w-3" />,
  },
  PRONTO: {
    label: 'Pronto',
    className: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  ENTREGUE: {
    label: 'Entregue',
    className: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  CANCELADO: {
    label: 'Cancelado',
    className: 'bg-red-50 text-red-700 ring-1 ring-red-200',
    icon: <Ban className="h-3 w-3" />,
  },
};

function SituacaoBadge({ situacao }: { situacao: SituacaoPedido }) {
  const cfg = STATUS_CONFIG[situacao] ?? STATUS_CONFIG.ORCAMENTO;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cfg.className}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ─── CancelarPedidoModal ───────────────────────────────────────────────
function CancelarPedidoModal({
  pedido,
  onClose,
  onConfirm,
}: {
  pedido: PedidoVenda;
  onClose: () => void;
  onConfirm: (motivo: string) => void;
}) {
  const [motivo, setMotivo] = useState('');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="cancelar-pedido-title">
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-2xl">
        <div className="border-b border-slate-100 px-6 py-4">
          <h2 id="cancelar-pedido-title" className="font-semibold text-slate-900">Cancelar Pedido</h2>
          <p className="text-xs text-slate-500 mt-0.5">{pedido.numero_pedido} — {pedido.cliente_nome}</p>
        </div>
        <div className="px-6 py-4 space-y-3">
          <div>
            <label htmlFor="motivo-cancelar" className="block text-sm font-medium text-slate-700 mb-1">Motivo (obrigatório)</label>
            <input id="motivo-cancelar" type="text" value={motivo} onChange={(e) => setMotivo(e.target.value)} className="form-input w-full" />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="btn-secondary">Voltar</button>
            <button type="button" disabled={!motivo.trim()} onClick={() => onConfirm(motivo.trim())} className="btn-primary bg-rose-600 hover:bg-rose-700 disabled:opacity-50">
              Cancelar pedido
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Expandable row ───────────────────────────────────────────────
function PedidoRow({
  pedido,
  onFinalizar,
  isFinalizando,
  onAprovar,
  isAprovando,
  onFinalizarEntrega,
  isFinalizandoEntrega,
  onCancelar,
  loja: _loja,
  onPrint,
}: {
  pedido: PedidoVenda;
  onFinalizar: (id: string) => void;
  isFinalizando: boolean;
  onAprovar: (id: string) => void;
  isAprovando: boolean;
  onFinalizarEntrega: (id: string) => void;
  isFinalizandoEntrega: boolean;
  onCancelar: (pedido: PedidoVenda) => void;
  loja: Loja | undefined;
  onPrint: (pedido: PedidoVenda) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const fmt = (v: string) => parseFloat(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const fmtDate = (iso: string) =>
    new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });

  const canFinalizar = pedido.situacao === 'ORCAMENTO' || pedido.situacao === 'APROVADO';

  return (
    <>
      <tr
        className={`border-b border-slate-100 transition-colors hover:bg-slate-50 ${
          pedido.situacao === 'CANCELADO' ? 'opacity-60' : ''
        }`}
      >
        <td className="px-4 py-3 font-mono text-xs font-medium text-slate-900">{pedido.numero_pedido}</td>
        <td className="px-4 py-3 text-slate-700">{pedido.cliente_nome}</td>
        <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{fmtDate(pedido.data_pedido)}</td>
        <td className="px-4 py-3 text-right font-medium text-slate-900">{fmt(pedido.valor_total)}</td>
        <td className="px-4 py-3 text-center">
          <SituacaoBadge situacao={pedido.situacao} />
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center justify-end gap-2">
            {pedido.situacao === 'ORCAMENTO' && (
              <button
                className="inline-flex items-center gap-1 rounded-lg bg-teal-600 px-2.5 py-1 text-xs font-medium text-white transition hover:bg-teal-700 disabled:opacity-50"
                disabled={isAprovando}
                onClick={() => onAprovar(pedido.id)}
              >
                {isAprovando ? 'Aprovando…' : 'Aprovar'}
              </button>
            )}
            {canFinalizar && (
              <button
                className="inline-flex items-center gap-1 rounded-lg bg-brand-600 px-2.5 py-1 text-xs font-medium text-white transition hover:bg-brand-700 disabled:opacity-50"
                disabled={isFinalizando}
                onClick={() => onFinalizar(pedido.id)}
              >
                {isFinalizando ? 'Finalizando…' : 'Finalizar Venda'}
              </button>
            )}
            {pedido.situacao === 'PRONTO' && (
              <button
                className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-2.5 py-1 text-xs font-medium text-white transition hover:bg-emerald-700 disabled:opacity-50"
                disabled={isFinalizandoEntrega}
                onClick={() => onFinalizarEntrega(pedido.id)}
              >
                <Truck className="h-3 w-3" aria-hidden="true" />
                {isFinalizandoEntrega ? 'Registrando…' : 'Finalizar Entrega'}
              </button>
            )}
            {pedido.situacao !== 'CANCELADO' && pedido.situacao !== 'ENTREGUE' && (
              <button
                className="rounded-lg border border-rose-200 p-1 text-rose-500 hover:bg-rose-50"
                title="Cancelar pedido"
                onClick={() => onCancelar(pedido)}
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            )}
            {pedido.situacao !== 'CANCELADO' && (
              <button
                className="rounded-lg border border-slate-200 p-1 text-slate-500 hover:bg-slate-100"
                title="Imprimir orçamento"
                onClick={() => onPrint(pedido)}
              >
                <Printer className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            )}
            <button
              className="rounded-lg border border-slate-200 p-1 text-slate-500 hover:bg-slate-100"
              onClick={() => setExpanded((e) => !e)}
              title="Ver itens"
            >
              {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            </button>
          </div>
        </td>
      </tr>
      {expanded && pedido.itens.length > 0 && (
        <tr className="border-b border-slate-100 bg-slate-50">
          <td colSpan={6} className="px-6 py-3">
            <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-slate-500">
                  <th className="pb-1 text-left font-medium">Produto</th>
                  <th className="pb-1 text-right font-medium">Qtd</th>
                  <th className="pb-1 text-right font-medium">Preço Unit.</th>
                  <th className="pb-1 text-right font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                {pedido.itens.map((item) => (
                  <tr key={item.id}>
                    <td className="py-0.5 text-slate-700">{item.nome_produto || `Produto #${item.produto_variacao}`}</td>
                    <td className="py-0.5 text-right text-slate-600">{item.quantidade}</td>
                    <td className="py-0.5 text-right text-slate-600">{parseFloat(item.preco_unitario).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                    <td className="py-0.5 text-right font-medium text-slate-900">{parseFloat(item.preco_total).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ─── Product search autocomplete ─────────────────────────────────────────────

function stockColor(qty: number): string {
  if (qty < 3) return 'text-red-600';
  if (qty < 10) return 'text-amber-600';
  return 'text-emerald-600';
}

function ProductSearch({
  lojaId,
  onSelect,
  inputRef,
}: {
  lojaId: number | null;
  onSelect: (item: EstoqueLojaItem) => void;
  inputRef?: React.RefObject<HTMLInputElement>;
}) {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);

  const { data } = useQuery({
    queryKey: ['estoque-search', lojaId, search],
    queryFn: () =>
      inventoryAPI.estoque.list({ loja_id: lojaId ?? undefined, search, page_size: 8 }),
    enabled: !!lojaId && search.length >= 2,
    staleTime: 15_000,
  });

  const results = data?.results ?? [];

  useEffect(() => { setActiveIndex(-1); }, [search]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const selectItem = (item: EstoqueLojaItem) => {
    onSelect(item);
    setSearch('');
    setOpen(false);
    setActiveIndex(-1);
  };

  return (
    <div ref={ref} className="relative">
      <input
        ref={inputRef}
        type="text"
        placeholder="Buscar produto pelo nome ou código…"
        value={search}
        onChange={(e) => { setSearch(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={(e) => {
          if (!open || results.length === 0) return;
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActiveIndex((i) => Math.min(i + 1, results.length - 1));
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActiveIndex((i) => Math.max(i - 1, -1));
          } else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault();
            selectItem(results[activeIndex]);
          } else if (e.key === 'Enter' && results.length === 1) {
            e.preventDefault();
            selectItem(results[0]);
          } else if (e.key === 'Escape') {
            setOpen(false);
          }
        }}
        className="form-input w-full"
        aria-autocomplete="list"
        aria-controls={open && results.length > 0 ? 'product-search-list' : undefined}
        aria-activedescendant={activeIndex >= 0 ? `ps-item-${activeIndex}` : undefined}
        disabled={!lojaId}
      />
      {open && results.length > 0 && (
        <ul
          id="product-search-list"
          role="listbox"
          className="absolute z-50 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden max-h-64 overflow-y-auto"
        >
          {results.map((item, idx) => {
            const qty = parseFloat(item.quantidade_disponivel || '0');
            const isLow = qty < 3;
            return (
              <li
                key={item.id}
                id={`ps-item-${idx}`}
                role="option"
                aria-selected={idx === activeIndex}
                className={`flex cursor-pointer items-center justify-between px-3 py-2.5 text-sm transition-colors ${
                  idx === activeIndex ? 'bg-blue-50' : 'hover:bg-slate-50'
                }`}
                onMouseEnter={() => setActiveIndex(idx)}
                onMouseDown={() => selectItem(item)}
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-slate-900 truncate">{item.produto_nome}</p>
                  <p className="text-xs text-slate-500 truncate">{item.produto_base_nome} · {item.unidade_sigla}</p>
                </div>
                <div className="ml-3 shrink-0 text-right text-xs">
                  <p className="font-semibold text-brand-600">
                    {parseFloat(item.preco_venda || '0').toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </p>
                  <p className={`flex items-center justify-end gap-0.5 font-medium ${stockColor(qty)}`}>
                    {isLow && <AlertTriangle className="h-3 w-3" />}
                    Disp: {item.quantidade_disponivel}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

// ─── Quick Add Cliente Modal ──────────────────────────────────────────────────
function QuickAddClienteModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (c: Cliente) => void;
}) {
  const [nome, setNome] = useState('');
  const [telefone, setTelefone] = useState('');
  const [cpfCnpj, setCpfCnpj] = useState('');

  const mutation = useMutation({
    mutationFn: () =>
      salesAPI.clientes.create({
        tipo_cliente: 'PF',
        nome,
        telefone_principal: telefone || null,
        cpf: cpfCnpj || null,
      }),
    onSuccess: (c) => onCreated(c),
    onError: (err: Error) => toast.error(err.message || 'Erro ao cadastrar cliente'),
  });

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="quick-add-cliente-title"
    >
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h3 id="quick-add-cliente-title" className="text-sm font-semibold text-slate-900">
            Cadastro Rápido de Cliente
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
            aria-label="Fechar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form
          className="space-y-3 px-5 py-4"
          onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }}
        >
          <div>
            <label htmlFor="qac-nome" className="mb-1 block text-xs font-medium text-slate-700">
              Nome *
            </label>
            <input
              id="qac-nome"
              type="text"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              className="form-input w-full"
              required
              autoFocus
              placeholder="Nome completo"
            />
          </div>
          <div>
            <label htmlFor="qac-telefone" className="mb-1 block text-xs font-medium text-slate-700">
              Telefone
            </label>
            <input
              id="qac-telefone"
              type="tel"
              value={telefone}
              onChange={(e) => setTelefone(e.target.value)}
              className="form-input w-full"
              placeholder="(00) 00000-0000"
            />
          </div>
          <div>
            <label htmlFor="qac-cpf" className="mb-1 block text-xs font-medium text-slate-700">
              CPF / CNPJ
            </label>
            <input
              id="qac-cpf"
              type="text"
              value={cpfCnpj}
              onChange={(e) => setCpfCnpj(e.target.value)}
              className="form-input w-full"
              placeholder="000.000.000-00"
            />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary text-sm">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!nome.trim() || mutation.isPending}
              className="btn-primary text-sm disabled:opacity-50"
            >
              {mutation.isPending ? 'Salvando…' : 'Salvar Cliente'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Cart item line ───────────────────────────────────────────────────────────
interface CartItem {
  estoqueItem: EstoqueLojaItem;
  quantidade: string;
  preco_unitario: string;
}

// ─── Nova Venda Drawer ────────────────────────────────────────────────────────

const PARCELAVEL = ['CARTAO_CREDITO', 'CREDIARIO'];
const CARD_FORMAS = ['CARTAO_CREDITO', 'CARTAO_DEBITO'];
const ENTREGA_EXTERNA = ['DELIVERY', 'TRANSPORTADORA'];

function NovaPedidoDrawer({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const qc = useQueryClient();

  // Form state
  const [lojaId, setLojaId] = useState<number | ''>('');
  const [clienteSearch, setClienteSearch] = useState('');
  const [clienteId, setClienteId] = useState<number | null>(null);
  const [clienteNome, setClienteNome] = useState('');
  const [clienteOpen, setClienteOpen] = useState(false);
  const clienteRef = useRef<HTMLDivElement>(null);
  const clienteInputRef = useRef<HTMLInputElement>(null);

  const [forma, setForma] = useState('DINHEIRO');
  const [bandeira, setBandeira] = useState('');
  const [parcelas, setParcelas] = useState('1');
  const [tipoEntrega, setTipoEntrega] = useState('BALCAO');
  const [enderecoEntrega, setEnderecoEntrega] = useState('');
  const [cidadeEntrega, setCidadeEntrega] = useState('');
  const [observacoes, setObservacoes] = useState('');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [showQuickAdd, setShowQuickAdd] = useState(false);

  // Derived
  const parcelasDisabled = !PARCELAVEL.includes(forma);
  const showBandeira = CARD_FORMAS.includes(forma);
  const showEnderecoEntrega = ENTREGA_EXTERNA.includes(tipoEntrega);

  // Lojas
  const { data: lojas = [] } = useQuery({ queryKey: ['lojas'], queryFn: companiesAPI.lojas.list, staleTime: 300_000 });

  // Cliente autocomplete
  const { data: clientesData } = useQuery({
    queryKey: ['clientes-search', clienteSearch],
    queryFn: () => salesAPI.clientes.list({ search: clienteSearch, page_size: 6 }),
    enabled: clienteSearch.length >= 2,
    staleTime: 15_000,
  });

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (clienteRef.current && !clienteRef.current.contains(e.target as Node)) setClienteOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Auto-select first loja
  useEffect(() => {
    if (lojas.length > 0 && lojaId === '') setLojaId(lojas[0].id);
  }, [lojas, lojaId]);

  // Autofocus on cliente input when drawer mounts
  useEffect(() => {
    const timer = setTimeout(() => clienteInputRef.current?.focus(), 80);
    return () => clearTimeout(timer);
  }, []);

  // When forma changes to non-parcelável, reset parcelas to 1
  useEffect(() => {
    if (parcelasDisabled) setParcelas('1');
  }, [parcelasDisabled]);

  // Ctrl+Enter to finalize
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        if (!isPending && cart.length > 0 && lojaId && clienteId) finalizarMutation.mutate();
      }
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart.length, clienteId, lojaId]);

  const addToCart = (item: EstoqueLojaItem) => {
    setCart((prev) => {
      const existing = prev.findIndex((c) => c.estoqueItem.produto_id === item.produto_id);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = {
          ...updated[existing],
          quantidade: String(parseFloat(updated[existing].quantidade) + 1),
        };
        return updated;
      }
      return [...prev, { estoqueItem: item, quantidade: '1', preco_unitario: item.preco_venda || item.preco_custo }];
    });
  };

  const updateCart = (index: number, field: 'quantidade' | 'preco_unitario', value: string) => {
    setCart((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const removeFromCart = (index: number) => {
    setCart((prev) => prev.filter((_, i) => i !== index));
  };

  const subtotal = cart.reduce(
    (sum, c) => sum + parseFloat(c.quantidade || '0') * parseFloat(c.preco_unitario || '0'),
    0,
  );

  const fmt = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  // Build observações including entrega address if needed
  const buildObservacoes = () => {
    const parts: string[] = [];
    if (showEnderecoEntrega && enderecoEntrega) parts.push(`Endereço: ${enderecoEntrega}${cidadeEntrega ? ` — ${cidadeEntrega}` : ''}`);
    if (showBandeira && bandeira) parts.push(`Bandeira: ${bandeira}`);
    if (observacoes) parts.push(observacoes);
    return parts.join(' | ') || null;
  };

  // Mutation: create pedido + add items + checkout + finalizar
  const finalizarMutation = useMutation({
    mutationFn: async () => {
      if (!lojaId) throw new Error('Selecione a loja');
      if (!clienteId) throw new Error('Selecione um cliente');
      if (cart.length === 0) throw new Error('Adicione ao menos um item');

      // 1. Create pedido
      const payload: PedidoCreatePayload = {
        loja: lojaId as number,
        cliente: clienteId,
        forma_pagamento: forma,
        parcelas: parseInt(parcelas),
        tipo_entrega: tipoEntrega,
        observacoes: buildObservacoes(),
      };
      const pedido = await salesAPI.pedidos.create(payload);

      // 2. Add items
      for (const c of cart) {
        const itemPayload: ItemAddPayload = {
          produto_variacao: c.estoqueItem.produto_id,
          quantidade: c.quantidade,
          preco_unitario: c.preco_unitario,
        };
        await salesAPI.pedidos.addItem(pedido.id, itemPayload);
      }

      // 3. Checkout (reserve stock)
      const checkout = await salesAPI.pedidos.iniciarCheckout(pedido.id);

      // 4. Finalizar (creates Venda + triggers NF-e)
      const venda = await salesAPI.pedidos.finalizar(pedido.id, checkout.sessao_checkout);
      return venda;
    },
    onSuccess: (venda) => {
      toast.success(`Venda ${venda.numero_venda} finalizada! NF-e: ${venda.nfe_situacao_display}`);
      qc.invalidateQueries({ queryKey: ['pedidos'] });
      qc.invalidateQueries({ queryKey: ['vendas'] });
      onSuccess();
    },
    onError: (err: Error) => toast.error(err.message || 'Erro ao finalizar venda'),
  });

  // Mutation: only create pedido (save as orcamento)
  const salvarMutation = useMutation({
    mutationFn: async () => {
      if (!lojaId) throw new Error('Selecione a loja');
      if (!clienteId) throw new Error('Selecione um cliente');
      if (cart.length === 0) throw new Error('Adicione ao menos um item');

      const payload: PedidoCreatePayload = {
        loja: lojaId as number,
        cliente: clienteId,
        forma_pagamento: forma,
        parcelas: parseInt(parcelas),
        tipo_entrega: tipoEntrega,
        observacoes: buildObservacoes(),
      };
      const pedido = await salesAPI.pedidos.create(payload);
      for (const c of cart) {
        await salesAPI.pedidos.addItem(pedido.id, {
          produto_variacao: c.estoqueItem.produto_id,
          quantidade: c.quantidade,
          preco_unitario: c.preco_unitario,
        });
      }
      return pedido;
    },
    onSuccess: (pedido) => {
      toast.success(`Pedido ${pedido.numero_pedido} salvo como orçamento`);
      qc.invalidateQueries({ queryKey: ['pedidos'] });
      onSuccess();
    },
    onError: (err: Error) => toast.error(err.message || 'Erro ao salvar pedido'),
  });

  const isPending = finalizarMutation.isPending || salvarMutation.isPending;

  return (
    <>
      {showQuickAdd && (
        <QuickAddClienteModal
          onClose={() => setShowQuickAdd(false)}
          onCreated={(c) => {
            setClienteId(c.id);
            setClienteNome(c.nome_razao || c.nome_completo || c.nome || '');
            setShowQuickAdd(false);
          }}
        />
      )}

      <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-label="Nova Venda">
        {/* Backdrop */}
        <div className="flex-1 bg-black/40 backdrop-blur-sm" onClick={onClose} />

        {/* Drawer — 2-col on lg */}
        <div className="flex h-full w-full max-w-4xl flex-col bg-white shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-slate-50 px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600">
                <ShoppingBag className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-900">Nova Venda</h2>
                <p className="text-xs text-slate-500">Preencha os dados e adicione os produtos</p>
              </div>
            </div>
            <button
              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-200"
              onClick={onClose}
              aria-label="Fechar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Body: 2 columns on lg */}
          <div className="flex flex-1 overflow-hidden flex-col lg:flex-row">

            {/* LEFT: Form fields */}
            <div className="overflow-y-auto border-b border-slate-200 p-6 space-y-4 lg:w-[380px] lg:shrink-0 lg:border-b-0 lg:border-r">

              {/* Loja */}
              <div>
                <label htmlFor="nd-loja" className="mb-1 block text-xs font-medium text-slate-700">Loja *</label>
                <select
                  id="nd-loja"
                  value={lojaId}
                  onChange={(e) => setLojaId(Number(e.target.value))}
                  className="form-input w-full"
                >
                  {lojas.map((l: Loja) => (
                    <option key={l.id} value={l.id}>{l.nome}</option>
                  ))}
                </select>
              </div>

              {/* Cliente */}
              <div ref={clienteRef}>
                <div className="mb-1 flex items-center justify-between">
                  <label className="text-xs font-medium text-slate-700">Cliente *</label>
                  <button
                    type="button"
                    onClick={() => setShowQuickAdd(true)}
                    className="flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium text-brand-600 hover:bg-brand-50 transition-colors"
                    title="Cadastrar novo cliente"
                  >
                    <Plus className="h-3 w-3" />
                    Novo
                  </button>
                </div>
                {clienteId ? (
                  <div className="flex items-center justify-between rounded-lg border border-teal-300 bg-teal-50 px-3 py-2 text-sm">
                    <span className="font-medium text-teal-800">{clienteNome}</span>
                    <button
                      type="button"
                      aria-label="Remover cliente"
                      className="text-teal-500 hover:text-teal-700"
                      onClick={() => { setClienteId(null); setClienteNome(''); setClienteSearch(''); setTimeout(() => clienteInputRef.current?.focus(), 50); }}
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <div className="relative">
                    <input
                      ref={clienteInputRef}
                      type="text"
                      placeholder="Buscar por nome ou CPF/CNPJ…"
                      value={clienteSearch}
                      onChange={(e) => { setClienteSearch(e.target.value); setClienteOpen(true); }}
                      onFocus={() => setClienteOpen(true)}
                      className="form-input w-full"
                      aria-label="Buscar cliente"
                      aria-autocomplete="list"
                    />
                    {clienteOpen && clientesData && clientesData.results.length > 0 && (
                      <ul className="absolute z-50 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden max-h-48 overflow-y-auto">
                        {clientesData.results.map((c) => (
                          <li
                            key={c.id}
                            className="cursor-pointer px-3 py-2 text-sm hover:bg-slate-50"
                            onMouseDown={() => {
                              setClienteId(c.id);
                              setClienteNome(c.nome_completo || c.nome);
                              setClienteOpen(false);
                              setClienteSearch('');
                            }}
                          >
                            <p className="font-medium text-slate-900">{c.nome_completo || c.nome}</p>
                            <p className="text-xs text-slate-500">{c.cpf || c.cnpj || ''}</p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              {/* Pagamento */}
              <div>
                <label htmlFor="nd-forma" className="mb-1 block text-xs font-medium text-slate-700">Pagamento *</label>
                <select
                  id="nd-forma"
                  value={forma}
                  onChange={(e) => setForma(e.target.value)}
                  className="form-input w-full"
                >
                  <option value="DINHEIRO">Dinheiro</option>
                  <option value="CARTAO_DEBITO">Cartão Débito</option>
                  <option value="CARTAO_CREDITO">Cartão Crédito</option>
                  <option value="PIX">PIX</option>
                  <option value="TRANSFERENCIA">Transferência</option>
                  <option value="CHEQUE">Cheque</option>
                  <option value="CREDIARIO">Crediário</option>
                  <option value="FIADO">Fiado</option>
                </select>
              </div>

              {/* Bandeira (conditional) */}
              {showBandeira && (
                <div>
                  <label htmlFor="nd-bandeira" className="mb-1 block text-xs font-medium text-slate-700">Bandeira do Cartão</label>
                  <select
                    id="nd-bandeira"
                    value={bandeira}
                    onChange={(e) => setBandeira(e.target.value)}
                    className="form-input w-full"
                  >
                    <option value="">Selecionar…</option>
                    <option value="Visa">Visa</option>
                    <option value="Mastercard">Mastercard</option>
                    <option value="Elo">Elo</option>
                    <option value="American Express">American Express</option>
                    <option value="Hipercard">Hipercard</option>
                    <option value="Outro">Outro</option>
                  </select>
                </div>
              )}

              {/* Parcelas (smart) */}
              <div>
                <label htmlFor="nd-parcelas" className="mb-1 block text-xs font-medium text-slate-700">
                  Parcelas
                  {parcelasDisabled && (
                    <span className="ml-1 text-slate-400">(à vista)</span>
                  )}
                </label>
                <input
                  id="nd-parcelas"
                  type="number"
                  min="1"
                  max="24"
                  value={parcelasDisabled ? '1' : parcelas}
                  onChange={(e) => setParcelas(e.target.value)}
                  disabled={parcelasDisabled}
                  className="form-input w-full disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>

              {/* Tipo Entrega */}
              <div>
                <label htmlFor="nd-entrega" className="mb-1 block text-xs font-medium text-slate-700">Tipo de Entrega</label>
                <select
                  id="nd-entrega"
                  value={tipoEntrega}
                  onChange={(e) => setTipoEntrega(e.target.value)}
                  className="form-input w-full"
                >
                  <option value="BALCAO">Retirada no Balcão</option>
                  <option value="DELIVERY">Entrega</option>
                  <option value="TRANSPORTADORA">Transportadora</option>
                </select>
              </div>

              {/* Endereço de Entrega (conditional) */}
              {showEnderecoEntrega && (
                <div className="space-y-2 rounded-lg border border-blue-100 bg-blue-50 p-3">
                  <p className="flex items-center gap-1.5 text-xs font-semibold text-blue-700">
                    <Truck className="h-3.5 w-3.5" />
                    Dados de Entrega
                  </p>
                  <div>
                    <label htmlFor="nd-endereco" className="mb-0.5 block text-xs font-medium text-slate-700">Endereço</label>
                    <input
                      id="nd-endereco"
                      type="text"
                      value={enderecoEntrega}
                      onChange={(e) => setEnderecoEntrega(e.target.value)}
                      className="form-input w-full text-sm"
                      placeholder="Rua, número, complemento…"
                    />
                  </div>
                  <div>
                    <label htmlFor="nd-cidade" className="mb-0.5 block text-xs font-medium text-slate-700">Cidade / Bairro</label>
                    <input
                      id="nd-cidade"
                      type="text"
                      value={cidadeEntrega}
                      onChange={(e) => setCidadeEntrega(e.target.value)}
                      className="form-input w-full text-sm"
                      placeholder="Cidade ou bairro…"
                    />
                  </div>
                </div>
              )}

              {/* Observações */}
              <div>
                <label htmlFor="nd-obs" className="mb-1 block text-xs font-medium text-slate-700">Observações</label>
                <textarea
                  id="nd-obs"
                  rows={2}
                  value={observacoes}
                  onChange={(e) => setObservacoes(e.target.value)}
                  placeholder="Observações do pedido (opcional)…"
                  className="form-input w-full resize-none"
                />
              </div>
            </div>

            {/* RIGHT: Products + Cart */}
            <div className="flex flex-1 flex-col gap-4 overflow-hidden p-6">
              {/* Product search */}
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Buscar Produto</label>
                <ProductSearch lojaId={lojaId ? Number(lojaId) : null} onSelect={addToCart} />
              </div>

              {/* Cart */}
              <div className="flex-1 overflow-y-auto">
                {cart.length === 0 ? (
                  <div className="flex h-full flex-col items-center justify-center gap-2 py-8 text-slate-400">
                    <ShoppingBag className="h-10 w-10 text-slate-200" />
                    <p className="text-sm">Adicione produtos acima</p>
                  </div>
                ) : (
                  <div className="rounded-xl border border-slate-200 overflow-hidden">
                    <div className="bg-slate-50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Itens do Pedido
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-200 bg-white text-xs text-slate-500">
                            <th className="px-3 py-2 text-left">Produto</th>
                            <th className="px-3 py-2 text-right">Qtd</th>
                            <th className="px-3 py-2 text-right">Preço</th>
                            <th className="px-3 py-2 text-right">Total</th>
                            <th className="px-3 py-2" />
                          </tr>
                        </thead>
                        <tbody>
                          {cart.map((c, i) => {
                            const total = parseFloat(c.quantidade || '0') * parseFloat(c.preco_unitario || '0');
                            return (
                              <tr key={c.estoqueItem.produto_id} className="border-b border-slate-100">
                                <td className="px-3 py-2">
                                  <p className="font-medium text-slate-900 text-xs">{c.estoqueItem.produto_nome}</p>
                                  <p className="text-xs text-slate-400">{c.estoqueItem.unidade_sigla}</p>
                                </td>
                                <td className="px-3 py-2">
                                  <input
                                    type="number"
                                    min="0.01"
                                    step="0.01"
                                    value={c.quantidade}
                                    onChange={(e) => updateCart(i, 'quantidade', e.target.value)}
                                    className="form-input w-16 text-right text-xs py-1"
                                    aria-label="Quantidade"
                                  />
                                </td>
                                <td className="px-3 py-2">
                                  <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={c.preco_unitario}
                                    onChange={(e) => updateCart(i, 'preco_unitario', e.target.value)}
                                    className="form-input w-24 text-right text-xs py-1"
                                    aria-label="Preço unitário"
                                  />
                                </td>
                                <td className="px-3 py-2 text-right text-xs font-medium text-slate-900">
                                  {fmt(total)}
                                </td>
                                <td className="px-3 py-2 text-right">
                                  <button
                                    type="button"
                                    aria-label="Remover item"
                                    className="text-red-400 hover:text-red-600"
                                    onClick={() => removeFromCart(i)}
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              {/* Total card */}
              {cart.length > 0 && (
                <div className="shrink-0 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-600">Total Geral</span>
                    <span className="text-2xl font-bold text-slate-900">
                      {fmt(subtotal)}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {cart.length} {cart.length === 1 ? 'item' : 'itens'}
                    {!parcelasDisabled && parseInt(parcelas) > 1 ? ` · ${parcelas}x de ${fmt(subtotal / parseInt(parcelas))}` : ''}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="shrink-0 border-t border-slate-200 bg-slate-50 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button className="btn-secondary" onClick={onClose} disabled={isPending}>
                  Cancelar
                </button>
                <p className="hidden text-xs text-slate-400 sm:block">
                  Ctrl+Enter: Finalizar · ESC: Fechar
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  className="btn-secondary"
                  disabled={isPending || cart.length === 0 || !lojaId || !clienteId}
                  onClick={() => salvarMutation.mutate()}
                >
                  {salvarMutation.isPending ? 'Salvando…' : 'Salvar Orçamento'}
                </button>
                <button
                  className="btn-primary"
                  disabled={isPending || cart.length === 0 || !lojaId || !clienteId}
                  onClick={() => finalizarMutation.mutate()}
                  title="Ctrl+Enter"
                >
                  {finalizarMutation.isPending
                    ? 'Finalizando…'
                    : `Finalizar${subtotal > 0 ? ` (${fmt(subtotal)})` : ' Venda'}`}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
export default function PedidosPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState('');
  const [situacao, setSituacao] = useState('');
  const [page, setPage] = useState(1);
  const [showDrawer, setShowDrawer] = useState(false);
  const [finalizandoId, setFinalizandoId] = useState<string | null>(null);
  const [aprovandoId, setAprovandoId] = useState<string | null>(null);
  const [finalizandoEntregaId, setFinalizandoEntregaId] = useState<string | null>(null);
  const [cancelarPedido, setCancelarPedido] = useState<import('@/types').PedidoVenda | null>(null);
  const [printPedido, setPrintPedido] = useState<import('@/types').PedidoVenda | null>(null);

  const { data: lojas = [] } = useQuery({
    queryKey: ['lojas'],
    queryFn: companiesAPI.lojas.list,
    staleTime: 300_000,
  });

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['pedidos', search, situacao, page],
    queryFn: () =>
      salesAPI.pedidos.list({
        search: search || undefined,
        situacao: situacao || undefined,
        page,
        page_size: 20,
      }),
    staleTime: 30_000,
  });

  const finalizarMutation = useMutation({
    mutationFn: async (id: string) => {
      setFinalizandoId(id);
      const checkout = await salesAPI.pedidos.iniciarCheckout(id);
      const venda = await salesAPI.pedidos.finalizar(id, checkout.sessao_checkout);
      return venda;
    },
    onSuccess: (venda) => {
      toast.success(`Venda ${venda.numero_venda} criada! NF-e: ${venda.nfe_situacao_display}`);
      qc.invalidateQueries({ queryKey: ['pedidos'] });
      qc.invalidateQueries({ queryKey: ['vendas'] });
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Erro ao finalizar venda');
    },
    onSettled: () => setFinalizandoId(null),
  });

  const aprovarMutation = useMutation({
    mutationFn: async (id: string) => {
      setAprovandoId(id);
      return salesAPI.pedidos.aprovar(id);
    },
    onSuccess: () => {
      toast.success('Pedido aprovado!');
      qc.invalidateQueries({ queryKey: ['pedidos'] });
    },
    onError: (err: Error) => toast.error(err.message || 'Erro ao aprovar pedido'),
    onSettled: () => setAprovandoId(null),
  });

  const finalizarEntregaMutation = useMutation({
    mutationFn: async (id: string) => {
      setFinalizandoEntregaId(id);
      return salesAPI.pedidos.finalizarEntrega(id);
    },
    onSuccess: (data) => {
      toast.success(`Entrega finalizada! Venda ${data.numero_venda}`);
      qc.invalidateQueries({ queryKey: ['pedidos'] });
    },
    onError: (err: Error) => toast.error(err.message || 'Erro ao finalizar entrega'),
    onSettled: () => setFinalizandoEntregaId(null),
  });

  const cancelarMutation = useMutation({
    mutationFn: ({ id, motivo }: { id: string; motivo: string }) =>
      salesAPI.pedidos.cancelar(id, motivo),
    onSuccess: () => {
      toast.success('Pedido cancelado.');
      qc.invalidateQueries({ queryKey: ['pedidos'] });
      setCancelarPedido(null);
    },
    onError: (err: Error) => toast.error(err.message || 'Erro ao cancelar pedido'),
  });

  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  return (
    <>
      {showDrawer && (
        <NovaPedidoDrawer
          onClose={() => setShowDrawer(false)}
          onSuccess={() => setShowDrawer(false)}
        />
      )}
      {cancelarPedido && (
        <CancelarPedidoModal
          pedido={cancelarPedido}
          onClose={() => setCancelarPedido(null)}
          onConfirm={(motivo) => cancelarMutation.mutate({ id: cancelarPedido.id, motivo })}
        />
      )}

      {printPedido && (
        <PrintPreviewModal
          isOpen={!!printPedido}
          onClose={() => setPrintPedido(null)}
          title={`Orçamento Nº ${printPedido.numero_pedido}`}
        >
          <OrcamentoPrintLayout
            pedido={printPedido}
            loja={lojas.find((l) => l.id === printPedido.loja) ?? {
              id: printPedido.loja,
              nome: 'Loja',
              uf: null,
              cidade: null,
              ativa: true,
              endereco: null,
              numero: null,
              bairro: null,
              telefone: null,
              empresa_data: null,
            }}
          />
        </PrintPreviewModal>
      )}

      <div className="flex-1 overflow-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600">
              <ShoppingBag className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Pedidos de Venda</h1>
              <p className="text-sm text-slate-500">
                {data ? `${data.count} registro${data.count !== 1 ? 's' : ''}` : ''}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="btn-secondary flex items-center gap-2"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
            <button
              className="btn-primary flex items-center gap-2"
              onClick={() => setShowDrawer(true)}
            >
              <Plus className="h-4 w-4" />
              Nova Venda
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-4 flex flex-wrap gap-3">
          <label className="relative flex flex-1 min-w-[200px] items-center">
            <Search className="absolute left-3 h-4 w-4 text-slate-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Buscar por nº pedido ou cliente…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="form-input pl-9 w-full"
            />
          </label>
          <select
            value={situacao}
            onChange={(e) => { setSituacao(e.target.value); setPage(1); }}
            className="form-input min-w-[160px]"
          >
            <option value="">Todas situações</option>
            <option value="ORCAMENTO">Orçamento</option>
            <option value="APROVADO">Aprovado</option>
            <option value="PRODUCAO">Em Produção</option>
            <option value="PRONTO">Pronto</option>
            <option value="ENTREGUE">Entregue</option>
            <option value="CANCELADO">Cancelado</option>
          </select>
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Nº Pedido</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Cliente</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Data</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600">Valor</th>
                  <th className="px-4 py-3 text-center font-medium text-slate-600">Situação</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-600">Ações</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-slate-100 animate-pulse">
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 rounded bg-slate-100" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : data?.results.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-16 text-center">
                      <ShoppingBag className="mx-auto mb-3 h-10 w-10 text-slate-200" />
                      <p className="text-sm text-slate-400">Nenhum pedido encontrado</p>
                      <button
                        className="mt-3 btn-primary text-sm"
                        onClick={() => setShowDrawer(true)}
                      >
                        <Plus className="mr-1 h-4 w-4 inline" />
                        Nova Venda
                      </button>
                    </td>
                  </tr>
                ) : (
                  data?.results.map((pedido) => (
                    <PedidoRow
                      key={pedido.id}
                      pedido={pedido}
                      onFinalizar={(id) => finalizarMutation.mutate(id)}
                      isFinalizando={finalizandoId === pedido.id && finalizarMutation.isPending}
                      onAprovar={(id) => aprovarMutation.mutate(id)}
                      isAprovando={aprovandoId === pedido.id && aprovarMutation.isPending}
                      onFinalizarEntrega={(id) => finalizarEntregaMutation.mutate(id)}
                      isFinalizandoEntrega={finalizandoEntregaId === pedido.id && finalizarEntregaMutation.isPending}
                      onCancelar={setCancelarPedido}
                      loja={lojas.find((l) => l.id === pedido.loja)}
                      onPrint={setPrintPedido}
                    />
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
                <button className="btn-secondary px-3 py-1 text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
                  Anterior
                </button>
                <button className="btn-secondary px-3 py-1 text-xs" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
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
