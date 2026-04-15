/**
 * T053 — PDVPage cart reducer unit tests.
 * Tests cartReducer in isolation:
 * - ADD item → correct total
 * - ADD duplicate → merges quantity and total
 * - UPDATE_QTY → recalculated total
 * - REMOVE → item removed, total updated
 * - CLEAR → state zeroed
 */
import { describe, it, expect } from 'vitest';
import type { PDVCartItem } from '@/types';

// ─── Extract reducer logic inline (mirrors PDVPage.tsx) ──────────────────────

type CartAction =
  | { type: 'ADD'; item: PDVCartItem }
  | { type: 'UPDATE_QTY'; id: number; qty: number }
  | { type: 'REMOVE'; id: number }
  | { type: 'CLEAR' };

function cartReducer(state: PDVCartItem[], action: CartAction): PDVCartItem[] {
  switch (action.type) {
    case 'ADD': {
      const idx = state.findIndex(
        (i) => i.produto_variacao_id === action.item.produto_variacao_id
      );
      if (idx >= 0) {
        return state.map((i, index) =>
          index === idx
            ? {
                ...i,
                quantidade: i.quantidade + action.item.quantidade,
                preco_total:
                  (i.quantidade + action.item.quantidade) * i.preco_unitario,
              }
            : i
        );
      }
      return [...state, action.item];
    }
    case 'UPDATE_QTY':
      return state.map((i) =>
        i.produto_variacao_id === action.id
          ? { ...i, quantidade: action.qty, preco_total: action.qty * i.preco_unitario }
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

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeItem(
  variacao_id: number,
  quantidade: number,
  preco_unitario: number
): PDVCartItem {
  return {
    produto_variacao_id: variacao_id,
    nome: `Produto ${variacao_id}`,
    sku: `SKU-${variacao_id}`,
    quantidade,
    preco_unitario,
    preco_total: quantidade * preco_unitario,
    estoque_disponivel: 99,
  } as PDVCartItem;
}

function totalCart(items: PDVCartItem[]) {
  return items.reduce((acc, i) => acc + i.preco_total, 0);
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('cartReducer', () => {
  describe('ADD', () => {
    it('adds a new item to an empty cart', () => {
      const item = makeItem(1, 2, 10.0);
      const state = cartReducer([], { type: 'ADD', item });
      expect(state).toHaveLength(1);
      expect(state[0].quantidade).toBe(2);
      expect(state[0].preco_total).toBe(20.0);
    });

    it('calculates correct total after adding', () => {
      const item = makeItem(1, 3, 25.0);
      const state = cartReducer([], { type: 'ADD', item });
      expect(totalCart(state)).toBe(75.0);
    });

    it('merges quantity when adding an existing item (same variacao_id)', () => {
      const item = makeItem(1, 2, 10.0);
      let state = cartReducer([], { type: 'ADD', item });
      state = cartReducer(state, { type: 'ADD', item: makeItem(1, 3, 10.0) });

      expect(state).toHaveLength(1);
      expect(state[0].quantidade).toBe(5);
      expect(state[0].preco_total).toBe(50.0);
    });

    it('adds a second distinct item without merging', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 1, 10.0) });
      state = cartReducer(state, { type: 'ADD', item: makeItem(2, 2, 15.0) });

      expect(state).toHaveLength(2);
      expect(totalCart(state)).toBe(40.0);
    });
  });

  describe('UPDATE_QTY', () => {
    it('updates quantity and recalculates preco_total', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 2, 20.0) });
      state = cartReducer(state, { type: 'UPDATE_QTY', id: 1, qty: 5 });

      expect(state[0].quantidade).toBe(5);
      expect(state[0].preco_total).toBe(100.0);
    });

    it('does not affect other items', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 2, 10.0) });
      state = cartReducer(state, { type: 'ADD', item: makeItem(2, 1, 30.0) });
      state = cartReducer(state, { type: 'UPDATE_QTY', id: 1, qty: 4 });

      expect(state[1].quantidade).toBe(1);
      expect(state[1].preco_total).toBe(30.0);
      expect(totalCart(state)).toBe(70.0);
    });
  });

  describe('REMOVE', () => {
    it('removes item by variacao_id', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 2, 10.0) });
      state = cartReducer(state, { type: 'ADD', item: makeItem(2, 1, 5.0) });
      state = cartReducer(state, { type: 'REMOVE', id: 1 });

      expect(state).toHaveLength(1);
      expect(state[0].produto_variacao_id).toBe(2);
    });

    it('returns empty array when last item is removed', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 1, 10.0) });
      state = cartReducer(state, { type: 'REMOVE', id: 1 });
      expect(state).toHaveLength(0);
      expect(totalCart(state)).toBe(0);
    });

    it('updates total after removal', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 2, 10.0) });
      state = cartReducer(state, { type: 'ADD', item: makeItem(2, 3, 5.0) });
      state = cartReducer(state, { type: 'REMOVE', id: 1 }); // remove 20.00

      expect(totalCart(state)).toBe(15.0);
    });
  });

  describe('CLEAR', () => {
    it('clears all items', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 2, 10.0) });
      state = cartReducer(state, { type: 'ADD', item: makeItem(2, 1, 5.0) });
      state = cartReducer(state, { type: 'CLEAR' });

      expect(state).toHaveLength(0);
    });

    it('total is zero after clear', () => {
      let state = cartReducer([], { type: 'ADD', item: makeItem(1, 5, 100.0) });
      state = cartReducer(state, { type: 'CLEAR' });
      expect(totalCart(state)).toBe(0);
    });

    it('does not mutate original state', () => {
      const original = [makeItem(1, 1, 10.0)];
      const newState = cartReducer(original, { type: 'CLEAR' });
      expect(original).toHaveLength(1);
      expect(newState).toHaveLength(0);
    });
  });
});
