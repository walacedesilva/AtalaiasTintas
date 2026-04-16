/**
 * T044 — PDVPage: Point-of-Sale screen.
 * useReducer for cart state; F10 opens payment, ESC clears cart.
 */
import { useReducer, useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, Search, Trash2, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useQuery, useMutation } from '@tanstack/react-query';
import { salesAPI } from '@/api/sales';
import { inventoryAPI } from '@/api/inventory';
import { companiesAPI } from '@/api/companies';
import ClienteQuickSearch from '@/components/sales/ClienteQuickSearch';
import CarrinhoTable from '@/components/sales/CarrinhoTable';
import PagamentoSplitPanel from '@/components/sales/PagamentoSplitPanel';
import DescontoAprovacaoModal from '@/components/sales/DescontoAprovacaoModal';
import type { PDVCartItem, Cliente, FormaPagamento, EstoqueLojaItem, Loja } from '@/types';

// ─── Cart Reducer ─────────────────────────────────────────────────────────────

type CartAction =
  | { type: 'ADD'; item: PDVCartItem }
  | { type: 'UPDATE_QTY'; id: string; qty: string }
  | { type: 'REMOVE'; id: string }
  | { type: 'CLEAR' };

function cartReducer(state: PDVCartItem[], action: CartAction): PDVCartItem[] {
  switch (action.type) {
    case 'ADD': {
      const idx = state.findIndex((i) => i.produto_variacao_id === action.item.produto_variacao_id);
      if (idx >= 0) {
        return state.map((i, index) => {
          if (index !== idx) return i;
          const newQty = (parseFloat(i.quantidade) + parseFloat(action.item.quantidade)).toString();
          const newTotal = (parseFloat(newQty) * parseFloat(i.preco_unitario)).toFixed(2);
          return { ...i, quantidade: newQty, preco_total: newTotal };
        });
      }
      return [...state, action.item];
    }
    case 'UPDATE_QTY':
      return state.map((i) =>
        i.produto_variacao_id === action.id
          ? { ...i, quantidade: action.qty, preco_total: (parseFloat(action.qty) * parseFloat(i.preco_unitario)).toFixed(2) }
          : i
      );
    case 'REMOVE':
      return state.filter((i) => i.produto_variacao_id !== action.id);
    case 'CLEAR':
      return [];
    default:
      return state;
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const DISCOUNT_THRESHOLD = 5; // % above which approval is needed

function calcTotals(items: PDVCartItem[], desconto = 0) {
  const subtotal = items.reduce((a, i) => a + parseFloat(i.preco_total), 0);
  const valorDesconto = (subtotal * desconto) / 100;
  return { subtotal, valorDesconto, liquido: subtotal - valorDesconto };
}

// ─── PDV Page ─────────────────────────────────────────────────────────────────

export default function PDVPage() {
  const navigate = useNavigate();

  // Loja selection
  const { data: lojas = [] } = useQuery<Loja[]>({
    queryKey: ['companies', 'lojas'],
    queryFn: companiesAPI.lojas.list,
    staleTime: 60_000,
  });
  const [lojaId, setLojaId] = useState<number | null>(null);
  useEffect(() => {
    if (!lojaId && lojas.length) setLojaId(lojas[0].id);
  }, [lojas, lojaId]);

  // Cart state
  const [cart, dispatch] = useReducer(cartReducer, []);
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [desconto, setDesconto] = useState('');
  const [showPagamento, setShowPagamento] = useState(false);
  const [showDescontoModal, setShowDescontoModal] = useState(false);
  const [pendingDesconto, setPendingDesconto] = useState('');

  // Product search
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<EstoqueLojaItem[]>([]);
  const [searchIdx, setSearchIdx] = useState(-1);
  const [isSearching, setIsSearching] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Success state
  const [vendaNumero, setVendaNumero] = useState<string | null>(null);

  // Mobile panel toggle
  const [activePanel, setActivePanel] = useState<'products' | 'cart'>('products');

  const { subtotal, valorDesconto, liquido } = calcTotals(cart, parseFloat(desconto) || 0);

  // ── Product search debounce ────────────────────────────────────────────────
  useEffect(() => {
    if (!searchTerm.trim() || !lojaId) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      abortRef.current?.abort();
      abortRef.current = new AbortController();
      setIsSearching(true);
      try {
        const res = await inventoryAPI.estoque.list({ search: searchTerm, loja_id: lojaId });
        const items = (res as { results?: EstoqueLojaItem[] }).results ?? (res as EstoqueLojaItem[]);
        setSearchResults(items.filter((i) => !i.bloqueado_venda && parseFloat(i.quantidade_disponivel) > 0));
        setSearchIdx(-1);
      } catch {
        // aborted or error — ignore
      } finally {
        setIsSearching(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm, lojaId]);

  // ── Add item to cart ────────────────────────────────────────────────────────
  const addToCart = useCallback((item: EstoqueLojaItem) => {
    dispatch({
      type: 'ADD',
      item: {
        produto_variacao_id: item.produto_id,
        sku: item.produto_codigo,
        nome: `${item.produto_base_nome} — ${item.produto_nome}`,
        quantidade: '1',
        unidade_id: 0,
        preco_unitario: item.preco_venda,
        desconto_valor: '0',
        preco_total: item.preco_venda,
        estoque_disponivel: item.quantidade_disponivel,
      },
    });
    setSearchTerm('');
    setSearchResults([]);
    searchRef.current?.focus();
  }, []);

  // ── Keyboard shortcuts ───────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'F10') { e.preventDefault(); if (cart.length) setShowPagamento(true); }
      if (e.key === 'Escape') {
        if (showPagamento) { setShowPagamento(false); return; }
        if (showDescontoModal) return;
        if (searchResults.length) { setSearchResults([]); setSearchTerm(''); return; }
        if (cart.length) { dispatch({ type: 'CLEAR' }); setCliente(null); setDesconto(''); }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [cart.length, showPagamento, showDescontoModal, searchResults.length]);

  // ── Desconto handler ────────────────────────────────────────────────────────
  const handleDescontoChange = (val: string) => {
    setDesconto(val);
    const pct = parseFloat(val) || 0;
    if (pct > DISCOUNT_THRESHOLD) {
      setPendingDesconto(val);
      setShowDescontoModal(true);
    }
  };

  // ── Checkout mutation ────────────────────────────────────────────────────────
  const mutation = useMutation({
    mutationFn: (pagamentos: Array<{ forma: FormaPagamento; valor: number }>) =>
      salesAPI.pdv.checkout({
        loja_id: lojaId!,
        cliente_id: cliente?.id,
        itens: cart.map((i) => ({
          produto_variacao_id: i.produto_variacao_id,
          quantidade: i.quantidade,
          unidade_id: i.unidade_id || undefined,
          preco_unitario: i.preco_unitario,
          desconto_valor: i.desconto_valor,
        })),
        pagamentos: pagamentos.map((p) => ({ forma: p.forma, valor: p.valor.toFixed(2) })),
        desconto_total: valorDesconto > 0 ? valorDesconto.toFixed(2) : undefined,
      }),
    onSuccess: (data) => {
      setVendaNumero(data.numero_venda);
      dispatch({ type: 'CLEAR' });
      setCliente(null);
      setDesconto('');
      setShowPagamento(false);
      toast.success(`Venda ${data.numero_venda} finalizada!`);
    },
    onError: (err: unknown) => {
      const msg = (err as { message?: string })?.message || 'Erro ao finalizar venda';
      toast.error(msg);
    },
  });

  // ── Success screen ───────────────────────────────────────────────────────────
  if (vendaNumero) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 p-8 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100">
          <CheckCircle2 className="h-10 w-10 text-emerald-600" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Venda finalizada!</h1>
          <p className="mt-1 text-slate-500">
            Número da venda: <span className="font-mono font-semibold text-slate-800">{vendaNumero}</span>
          </p>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary" onClick={() => navigate('/sales')}>
            Ver vendas
          </button>
          <button className="btn-primary" onClick={() => setVendaNumero(null)} autoFocus>
            Nova venda
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-screen flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <ShoppingCart className="h-6 w-6 text-blue-600" aria-hidden="true" />
          <h1 className="text-lg font-semibold text-slate-900">PDV — Ponto de Venda</h1>
        </div>
        <div className="flex items-center gap-3">
          {/* Loja selector */}
          {lojas.length > 1 && (
            <select
              value={lojaId ?? ''}
              onChange={(e) => setLojaId(Number(e.target.value))}
              className="form-input text-sm"
              aria-label="Selecionar loja"
            >
              {lojas.map((l) => (
                <option key={l.id} value={l.id}>{l.nome}</option>
              ))}
            </select>
          )}
          <span className="hidden text-xs text-slate-400 sm:block">F10 = Pagar · ESC = Limpar</span>
        </div>
      </div>

      {/* Body: two-column on desktop, single panel on mobile */}
      {/* Mobile panel toggle */}
      <div className="flex border-b border-slate-200 lg:hidden">
        <button
          className={`flex-1 py-2.5 text-sm font-medium transition-colors ${activePanel === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
          onClick={() => setActivePanel('products')}
        >
          Produtos
        </button>
        <button
          className={`flex-1 py-2.5 text-sm font-medium transition-colors ${activePanel === 'cart' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
          onClick={() => setActivePanel('cart')}
        >
          Carrinho {cart.length > 0 && <span className="ml-1 rounded-full bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">{cart.length}</span>}
        </button>
      </div>

      <div className="flex flex-1 gap-0 overflow-hidden">
        {/* LEFT: search + cart */}
        <div className={`flex flex-1 flex-col gap-4 overflow-y-auto p-6 ${activePanel === 'products' ? 'flex' : 'hidden'} lg:flex`}>
          {/* Cliente */}
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
              Cliente (opcional)
            </label>
            <ClienteQuickSearch onSelect={setCliente} />
          </div>

          {/* Product search */}
          <div className="relative">
            <label htmlFor="pdv-search" className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
              Buscar produto
            </label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
              <input
                ref={searchRef}
                id="pdv-search"
                type="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    setSearchIdx((i) => Math.min(i + 1, searchResults.length - 1));
                  } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    setSearchIdx((i) => Math.max(i - 1, -1));
                  } else if (e.key === 'Enter' && searchIdx >= 0) {
                    e.preventDefault();
                    addToCart(searchResults[searchIdx]);
                  } else if (e.key === 'Enter' && searchResults.length === 1) {
                    e.preventDefault();
                    addToCart(searchResults[0]);
                  }
                }}
                className="form-input w-full pl-9"
                placeholder="Código, nome ou SKU…"
                autoFocus
                autoComplete="off"
                aria-autocomplete="list"
                aria-controls={searchResults.length ? 'pdv-results' : undefined}
                aria-activedescendant={searchIdx >= 0 ? `pdv-result-${searchIdx}` : undefined}
                disabled={!lojaId}
              />
            </div>

            {/* Results dropdown */}
            {searchResults.length > 0 && (
              <ul
                id="pdv-results"
                role="listbox"
                className="absolute z-30 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg"
              >
                {isSearching && (
                  <li className="px-4 py-2 text-xs text-slate-400" aria-live="polite">Buscando…</li>
                )}
                {searchResults.map((item, idx) => (
                  <li
                    key={item.id}
                    id={`pdv-result-${idx}`}
                    role="option"
                    aria-selected={idx === searchIdx}
                    className={`cursor-pointer px-4 py-2.5 text-sm hover:bg-blue-50 ${idx === searchIdx ? 'bg-blue-50' : ''}`}
                    onMouseDown={() => addToCart(item)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium text-slate-800">{item.produto_nome}</span>
                        <span className="ml-2 text-xs text-slate-400">{item.produto_codigo}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-slate-900">
                          {parseFloat(item.preco_venda).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </div>
                        <div className="text-xs text-slate-400">
                          Disp: {item.quantidade_disponivel} {item.unidade_sigla}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Cart */}
          <div className="flex-1">
            <CarrinhoTable
              items={cart}
              onUpdate={(id, qty) => dispatch({ type: 'UPDATE_QTY', id, qty })}
              onRemove={(id) => dispatch({ type: 'REMOVE', id })}
            />
          </div>

          {/* Desconto */}
          {cart.length > 0 && (
            <div className="flex items-center gap-3">
              <label htmlFor="desconto-pct" className="text-sm font-medium text-slate-700 whitespace-nowrap">
                Desconto (%)
              </label>
              <input
                id="desconto-pct"
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={desconto}
                onChange={(e) => handleDescontoChange(e.target.value)}
                className="form-input w-24 text-right"
                placeholder="0"
              />
              {parseFloat(desconto) > 0 && (
                <button
                  type="button"
                  className="text-xs text-slate-400 hover:text-rose-600"
                  onClick={() => setDesconto('')}
                  aria-label="Remover desconto"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              )}
            </div>
          )}
        </div>

        {/* RIGHT: totals + payment */}
        <div className={`flex w-full flex-col gap-4 border-t border-slate-200 bg-slate-50 p-6 lg:w-80 lg:border-l lg:border-t-0 ${activePanel === 'cart' ? 'flex' : 'hidden'} lg:flex`}>
          {/* Totals summary */}
          <div className="rounded-2xl bg-white px-5 py-4 shadow-sm space-y-2 text-sm">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Resumo</h2>
            {cliente && (
              <p className="text-xs text-blue-600">
                Cliente: <span className="font-medium">{cliente.nome_razao}</span>
              </p>
            )}
            <div className="flex justify-between">
              <span className="text-slate-600">Subtotal</span>
              <span className="font-medium">
                {subtotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
            </div>
            {valorDesconto > 0 && (
              <div className="flex justify-between text-emerald-700">
                <span>Desconto ({desconto}%)</span>
                <span>− {valorDesconto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>
              </div>
            )}
            <div className="flex justify-between border-t border-slate-100 pt-2 font-semibold text-slate-900">
              <span>Total</span>
              <span>{liquido.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>
            </div>
          </div>

          {/* Payment panel */}
          {showPagamento ? (
            <PagamentoSplitPanel
              valorLiquido={liquido}
              onConfirm={(pagamentos) => mutation.mutate(pagamentos)}
              disabled={mutation.isPending}
            />
          ) : (
            <button
              type="button"
              className="btn-primary w-full"
              disabled={cart.length === 0}
              onClick={() => setShowPagamento(true)}
            >
              Pagar (F10)
            </button>
          )}

          {showPagamento && (
            <button
              type="button"
              className="btn-secondary w-full text-sm"
              onClick={() => setShowPagamento(false)}
            >
              Voltar ao carrinho
            </button>
          )}
        </div>
      </div>

      {/* Desconto Aprovação Modal */}
      {showDescontoModal && (
        <DescontoAprovacaoModal
          pedidoId=""
          percentual={pendingDesconto}
          nivel="gerente"
          tipo="TOTAL"
          aprovadores={[]}
          onSuccess={() => {
            setDesconto(pendingDesconto);
            setShowDescontoModal(false);
          }}
          onClose={() => {
            setPendingDesconto('');
            setShowDescontoModal(false);
            setDesconto('');
          }}
        />
      )}
    </div>
  );
}
