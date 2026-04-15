/**
 * NFe Automation — T049
 *
 * Manages NF-e emission requests, status polling, and retry-manual
 * workflows from the sales and fiscal management interfaces.
 *
 * Usage:
 *   const nfe = new NFeAutomacao({ vendaId: '...', csrfToken: '...' });
 *   await nfe.emitir();
 *   nfe.iniciarPolling(onStatusChange);
 */

'use strict';

const NFE_SITUACOES = {
    NAO_APLICAVEL:    { label: 'Não Aplicável',       css: 'nfe-na' },
    PENDENTE:         { label: 'Pendente',             css: 'nfe-pendente' },
    PROCESSANDO:      { label: 'Processando…',         css: 'nfe-processando' },
    AUTORIZADA:       { label: 'Autorizada',           css: 'nfe-autorizada' },
    REJEITADA:        { label: 'Rejeitada',            css: 'nfe-rejeitada' },
    CANCELADA:        { label: 'Cancelada',            css: 'nfe-cancelada' },
    ERRO_TECNICO:     { label: 'Erro Técnico',         css: 'nfe-erro' },
    AGUARDANDO_RETRY: { label: 'Aguardando Retry',     css: 'nfe-retry' },
};

class NFeAutomacao {
    constructor(options = {}) {
        this.vendaId   = options.vendaId   || null;
        this.apiBase   = options.apiBase   || '/api/fiscal';
        this.csrfToken = options.csrfToken || _getCsrfToken();
        this._pollingTimer = null;
        this._pollingInterval = options.pollingInterval || 5000; // ms
    }

    // ------------------------------------------------------------------
    // Actions
    // ------------------------------------------------------------------

    async emitir() {
        return this._post(`${this.apiBase}/nfe-automacao/${this.vendaId}/emitir/`);
    }

    async reprocessar() {
        return this._post(`${this.apiBase}/nfe-automacao/${this.vendaId}/reprocessar/`);
    }

    async retryManual() {
        return this._post(`${this.apiBase}/nfe-automacao/${this.vendaId}/retry-manual/`);
    }

    async consultarStatus() {
        const resp = await fetch(`${this.apiBase}/nfe-automacao/${this.vendaId}/`, {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' },
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        return resp.json();
    }

    // ------------------------------------------------------------------
    // Status polling
    // ------------------------------------------------------------------

    /**
     * Start polling the NF-e status every `pollingInterval` ms.
     * @param {Function} onStatusChange — called with (situacao, data) on each update
     * @param {Function} stopWhen       — optional predicate(situacao) → if true, stop polling
     */
    iniciarPolling(onStatusChange, stopWhen) {
        this._stopPolling();
        const tick = async () => {
            try {
                const data = await this.consultarStatus();
                const situacao = data.nfe_situacao;
                onStatusChange(situacao, data);
                if (stopWhen && stopWhen(situacao)) {
                    this._stopPolling();
                    return;
                }
            } catch (err) {
                console.warn('NFeAutomacao polling error:', err);
            }
        };
        tick();
        this._pollingTimer = setInterval(tick, this._pollingInterval);
    }

    pararPolling() {
        this._stopPolling();
    }

    // ------------------------------------------------------------------
    // DOM helpers (static utility methods)
    // ------------------------------------------------------------------

    /**
     * Render an NF-e status badge into *element*.
     */
    static renderizarBadge(element, situacao) {
        const info = NFE_SITUACOES[situacao] || { label: situacao, css: 'nfe-desconhecida' };
        element.className = `nfe-badge ${info.css}`;
        element.textContent = info.label;
        element.setAttribute('data-situacao', situacao);
    }

    /**
     * Bind all [data-nfe-venda-id] elements in *container* (or document).
     * Each element gets an NFeAutomacao instance on ._nfe and action buttons wired.
     */
    static autowire(container) {
        const root = container || document;
        root.querySelectorAll('[data-nfe-venda-id]').forEach(el => {
            const vendaId = el.dataset.nfeVendaId;
            if (!vendaId) return;

            const nfe = new NFeAutomacao({ vendaId });
            el._nfe = nfe;

            // Badge element
            const badge = el.querySelector('[data-nfe-badge]');

            // Buttons
            el.querySelector('[data-nfe-btn-emitir]')?.addEventListener('click', async (e) => {
                e.preventDefault();
                _setLoading(e.currentTarget, true);
                try {
                    await nfe.emitir();
                    if (badge) NFeAutomacao.renderizarBadge(badge, 'PROCESSANDO');
                    nfe.iniciarPolling(
                        (sit, data) => badge && NFeAutomacao.renderizarBadge(badge, sit),
                        (sit) => ['AUTORIZADA', 'REJEITADA', 'ERRO_TECNICO', 'AGUARDANDO_RETRY'].includes(sit)
                    );
                } catch (err) {
                    _mostrarErro(el, err.message);
                } finally {
                    _setLoading(e.currentTarget, false);
                }
            });

            el.querySelector('[data-nfe-btn-retry]')?.addEventListener('click', async (e) => {
                e.preventDefault();
                _setLoading(e.currentTarget, true);
                try {
                    await nfe.retryManual();
                    if (badge) NFeAutomacao.renderizarBadge(badge, 'PROCESSANDO');
                } catch (err) {
                    _mostrarErro(el, err.message);
                } finally {
                    _setLoading(e.currentTarget, false);
                }
            });
        });
    }

    // ------------------------------------------------------------------
    // Private
    // ------------------------------------------------------------------

    _stopPolling() {
        if (this._pollingTimer) {
            clearInterval(this._pollingTimer);
            this._pollingTimer = null;
        }
    }

    async _post(url, body) {
        const resp = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
            },
            body: body ? JSON.stringify(body) : undefined,
        });
        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.detail || data.erro || `HTTP ${resp.status}`);
        }
        return resp.json();
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

function _setLoading(btn, loading) {
    if (!btn) return;
    btn.disabled = loading;
    btn.setAttribute('aria-busy', loading ? 'true' : 'false');
    const span = btn.querySelector('.btn-label');
    if (span) span.textContent = loading ? 'Aguarde…' : btn.dataset.originalLabel || span.textContent;
}

function _mostrarErro(el, msg) {
    let alertEl = el.querySelector('.nfe-error-msg');
    if (!alertEl) {
        alertEl = document.createElement('p');
        alertEl.className = 'nfe-error-msg';
        alertEl.setAttribute('role', 'alert');
        el.appendChild(alertEl);
    }
    alertEl.textContent = msg;
    setTimeout(() => { alertEl.textContent = ''; }, 8000);
}

// Auto-wire on load
document.addEventListener('DOMContentLoaded', () => NFeAutomacao.autowire());
