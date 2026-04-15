/**
 * Stock Reservation — T028
 *
 * Manages checkout stock reservations via the EstoqueReserva API.
 * Creates, extends, and releases reservations for cart items.
 *
 * Usage:
 *   const mgr = new StockReservationManager({ lojaId: 1, sessaoCheckout: 'abc123' });
 *   const reserva = await mgr.reservar(produtoVariacaoId, quantidade, unidadeId);
 *   await mgr.liberarTodas();
 */

'use strict';

class StockReservationManager {
    constructor(options = {}) {
        this.lojaId           = options.lojaId || null;
        this.sessaoCheckout   = options.sessaoCheckout || _gerarSessaoId();
        this.apiBase          = options.apiBase || '/api/inventory';
        this.minutosExpiracao = options.minutosExpiracao || 30;
        this.onStockInsuficiente = options.onStockInsuficiente || null; // callback(produtoId, erro)
        this.onReservaExpirada   = options.onReservaExpirada   || null; // callback(reservaId)

        this._reservas = new Map(); // produtoVariacaoId -> reservaId
        this._renewTimers = new Map();
    }

    // ------------------------------------------------------------------
    // Core operations
    // ------------------------------------------------------------------

    /**
     * Create a stock reservation for a product/quantity.
     * Returns the reservation object on success.
     * Calls onStockInsuficiente and returns null on stock failure.
     */
    async reservar(produtoVariacaoId, quantidade, unidadeId) {
        const csrfToken = _getCsrfToken();
        const payload = {
            produto_variacao: produtoVariacaoId,
            loja: this.lojaId,
            quantidade: quantidade,
            unidade: unidadeId,
            sessao_checkout: this.sessaoCheckout,
            minutos_expiracao: this.minutosExpiracao,
        };

        try {
            const resp = await fetch(`${this.apiBase}/reservas/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(payload),
            });

            if (resp.status === 400) {
                const err = await resp.json();
                if (this.onStockInsuficiente) {
                    this.onStockInsuficiente(produtoVariacaoId, err.detail || err);
                }
                return null;
            }

            if (!resp.ok) {
                throw new Error(`Erro ao reservar estoque: HTTP ${resp.status}`);
            }

            const reserva = await resp.json();
            this._reservas.set(produtoVariacaoId, reserva.id);
            this._agendarRenovacao(reserva.id);
            return reserva;
        } catch (err) {
            console.error('StockReservationManager.reservar:', err);
            throw err;
        }
    }

    /**
     * Release a single reservation by product variant ID.
     */
    async liberar(produtoVariacaoId) {
        const reservaId = this._reservas.get(produtoVariacaoId);
        if (!reservaId) return;

        this._cancelarRenovacao(reservaId);
        await this._deletarReserva(reservaId);
        this._reservas.delete(produtoVariacaoId);
    }

    /**
     * Release all active reservations (call on cart abort or page unload).
     */
    async liberarTodas() {
        const promises = [];
        for (const [prodId] of this._reservas) {
            promises.push(this.liberar(prodId));
        }
        await Promise.allSettled(promises);
    }

    /**
     * Confirm all reservations (call on payment success to convert to firm stock).
     */
    async confirmarTodas() {
        const promises = [];
        for (const [, reservaId] of this._reservas) {
            promises.push(this._confirmarReserva(reservaId));
        }
        const results = await Promise.allSettled(promises);
        this._reservas.clear();
        this._renewTimers.forEach(t => clearTimeout(t));
        this._renewTimers.clear();
        return results;
    }

    // ------------------------------------------------------------------
    // Availability query (used before adding to cart)
    // ------------------------------------------------------------------

    async verificarDisponibilidade(produtoVariacaoId, quantidade, unidadeId) {
        const params = new URLSearchParams({
            produto_variacao: produtoVariacaoId,
            loja: this.lojaId,
            quantidade: quantidade,
            unidade: unidadeId,
        });
        const resp = await fetch(`${this.apiBase}/estoque/disponibilidade/?${params}`, {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' },
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return resp.json(); // { disponivel: bool, quantidade_disponivel: X }
    }

    // ------------------------------------------------------------------
    // Private helpers
    // ------------------------------------------------------------------

    _agendarRenovacao(reservaId) {
        // Renew 5 minutes before expiry
        const ms = (this.minutosExpiracao - 5) * 60 * 1000;
        if (ms <= 0) return;

        const timer = setTimeout(async () => {
            try {
                await this._renovarReserva(reservaId);
                this._agendarRenovacao(reservaId); // schedule next renewal
            } catch {
                if (this.onReservaExpirada) this.onReservaExpirada(reservaId);
            }
        }, ms);

        this._renewTimers.set(reservaId, timer);
    }

    _cancelarRenovacao(reservaId) {
        const timer = this._renewTimers.get(reservaId);
        if (timer) {
            clearTimeout(timer);
            this._renewTimers.delete(reservaId);
        }
    }

    async _renovarReserva(reservaId) {
        const resp = await fetch(`${this.apiBase}/reservas/${reservaId}/renovar/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': _getCsrfToken() },
        });
        if (!resp.ok) throw new Error(`Renovation failed: HTTP ${resp.status}`);
        return resp.json();
    }

    async _confirmarReserva(reservaId) {
        const resp = await fetch(`${this.apiBase}/reservas/${reservaId}/confirmar/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': _getCsrfToken() },
        });
        if (!resp.ok) throw new Error(`Confirmação falhou: HTTP ${resp.status}`);
        return resp.json();
    }

    async _deletarReserva(reservaId) {
        const resp = await fetch(`${this.apiBase}/reservas/${reservaId}/`, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': _getCsrfToken() },
        });
        // 204 or 404 (already expired) are both fine
        if (resp.status !== 204 && resp.status !== 404) {
            throw new Error(`Liberar reserva falhou: HTTP ${resp.status}`);
        }
    }
}

// ------------------------------------------------------------------
// StockAvailabilityWidget — lightweight badge that shows "X em estoque"
// ------------------------------------------------------------------

class StockAvailabilityWidget {
    constructor(element, options = {}) {
        this.el      = element;
        this.apiBase = options.apiBase || '/api/inventory';
        this.lojaId  = options.lojaId  || element.dataset.lojaId;
    }

    async atualizar(produtoVariacaoId, unidadeId) {
        const params = new URLSearchParams({ produto_variacao: produtoVariacaoId, loja: this.lojaId });
        if (unidadeId) params.set('unidade', unidadeId);

        try {
            const resp = await fetch(`${this.apiBase}/estoque/disponibilidade/?${params}`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' },
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this._renderizar(data);
        } catch (err) {
            this.el.textContent = '';
            console.warn('StockAvailabilityWidget:', err);
        }
    }

    _renderizar({ quantidade_disponivel, disponivel }) {
        const qty = parseFloat(quantidade_disponivel) || 0;
        this.el.className = `stock-badge ${disponivel ? 'stock-ok' : 'stock-zero'}`;
        this.el.textContent = disponivel
            ? `${qty.toFixed(2)} em estoque`
            : 'Sem estoque';
        this.el.setAttribute('aria-label', this.el.textContent);
    }
}

// ------------------------------------------------------------------
// Utilities
// ------------------------------------------------------------------

function _getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function _gerarSessaoId() {
    return 'checkout_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
}

// Release all reservations safely on page unload
window.addEventListener('beforeunload', () => {
    document
        .querySelectorAll('[data-reservation-manager]')
        .forEach(el => el._reservationManager && el._reservationManager.liberarTodas());
});
