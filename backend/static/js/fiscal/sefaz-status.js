/**
 * SEFAZ Status — T050
 *
 * Checks SEFAZ service availability and shows a visual indicator.
 *
 * Usage:
 *   const widget = new SefazStatusWidget(document.getElementById('sefaz-status'));
 *   widget.iniciarPolling();          // checks every 5 min
 *   widget.verificar();               // one-shot check
 */

'use strict';

const SEFAZ_STATUS_INFO = {
    online:     { label: 'SEFAZ Online',     css: 'sefaz-online',     icon: '●' },
    degradado:  { label: 'Serviço Degradado', css: 'sefaz-degradado',  icon: '◐' },
    offline:    { label: 'SEFAZ Offline',    css: 'sefaz-offline',    icon: '○' },
    desconhecido: { label: 'Verificando…',   css: 'sefaz-desconhecido', icon: '◌' },
};

class SefazStatusWidget {
    constructor(element, options = {}) {
        this.el              = element;
        this.apiBase         = options.apiBase || '/api/fiscal';
        this.intervaloMs     = options.intervaloMs || 5 * 60 * 1000; // 5 min
        this.onStatusChange  = options.onStatusChange || null;
        this._timer          = null;
        this._lastStatus     = null;
    }

    // ------------------------------------------------------------------
    // Lifecycle
    // ------------------------------------------------------------------

    async verificar() {
        this._renderizar('desconhecido');
        try {
            const resp = await fetch(`${this.apiBase}/sefaz/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' },
            });
            if (!resp.ok) {
                this._renderizar('degradado', `HTTP ${resp.status}`);
                return;
            }
            const data = await resp.json();
            this._processarResposta(data);
        } catch (err) {
            this._renderizar('offline', 'Sem conexão');
            console.warn('SefazStatusWidget:', err);
        }
    }

    iniciarPolling() {
        this.verificar();
        this._timer = setInterval(() => this.verificar(), this.intervaloMs);
    }

    pararPolling() {
        if (this._timer) {
            clearInterval(this._timer);
            this._timer = null;
        }
    }

    // ------------------------------------------------------------------
    // Private
    // ------------------------------------------------------------------

    _processarResposta(data) {
        // The API returns { status: 'online'|'offline'|'degradado', mensagem: '...' }
        const status = data.status || 'desconhecido';
        const mensagem = data.mensagem || data.motivo || '';
        this._renderizar(status, mensagem);
    }

    _renderizar(status, mensagem) {
        const info = SEFAZ_STATUS_INFO[status] || SEFAZ_STATUS_INFO.desconhecido;

        if (this._lastStatus !== status) {
            this._lastStatus = status;
            if (this.onStatusChange) this.onStatusChange(status, mensagem, info);
        }

        if (!this.el) return;

        this.el.className      = `sefaz-status-widget ${info.css}`;
        this.el.dataset.status = status;
        this.el.setAttribute('aria-label', info.label + (mensagem ? `: ${mensagem}` : ''));
        this.el.innerHTML = `
          <span class="sefaz-status__icon" aria-hidden="true">${info.icon}</span>
          <span class="sefaz-status__label">${info.label}</span>
          ${mensagem ? `<span class="sefaz-status__msg">${_escHtml(mensagem)}</span>` : ''}
        `;
    }
}

// ------------------------------------------------------------------
// SefazStatusBanner — a full-page dismissible banner for outages
// ------------------------------------------------------------------

class SefazStatusBanner {
    constructor(options = {}) {
        this.apiBase     = options.apiBase    || '/api/fiscal';
        this.intervaloMs = options.intervaloMs || 5 * 60 * 1000;
        this._banner     = null;
        this._timer      = null;
    }

    iniciar() {
        this._verificar();
        this._timer = setInterval(() => this._verificar(), this.intervaloMs);
    }

    parar() {
        if (this._timer) { clearInterval(this._timer); this._timer = null; }
        if (this._banner) { this._banner.remove(); this._banner = null; }
    }

    async _verificar() {
        try {
            const resp = await fetch(`${this.apiBase}/sefaz/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' },
            });
            const data = resp.ok ? await resp.json() : { status: 'offline' };
            if (data.status === 'offline' || data.status === 'degradado') {
                this._mostrarBanner(data);
            } else {
                this._esconderBanner();
            }
        } catch {
            this._mostrarBanner({ status: 'offline', mensagem: 'Sem conexão com a internet' });
        }
    }

    _mostrarBanner(data) {
        if (this._banner) return; // already visible
        const isOffline = data.status === 'offline';
        const banner = document.createElement('div');
        banner.className = `sefaz-banner sefaz-banner--${data.status}`;
        banner.setAttribute('role', 'alert');
        banner.innerHTML = `
          <span class="sefaz-banner__text">
            <strong>Atenção:</strong>
            ${isOffline ? 'SEFAZ indisponível' : 'Serviço SEFAZ com degradação'}.
            NF-e serão enfileiradas e enviadas quando o serviço voltar.
            ${data.mensagem ? `<em>${_escHtml(data.mensagem)}</em>` : ''}
          </span>
          <button class="sefaz-banner__close" aria-label="Fechar aviso" type="button">×</button>
        `;
        banner.querySelector('.sefaz-banner__close').addEventListener('click', () => {
            banner.remove();
            this._banner = null;
        });
        document.body.prepend(banner);
        this._banner = banner;
    }

    _esconderBanner() {
        if (this._banner) {
            this._banner.remove();
            this._banner = null;
        }
    }
}

// ------------------------------------------------------------------
// Utility
// ------------------------------------------------------------------

function _escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Auto-wire [data-sefaz-status-widget] elements
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-sefaz-status-widget]').forEach(el => {
        const widget = new SefazStatusWidget(el);
        el._sefazWidget = widget;
        widget.iniciarPolling();
    });

    // Start banner if data-sefaz-banner-auto is set on body or #app
    if (document.body.dataset.sefazBannerAuto !== undefined) {
        const banner = new SefazStatusBanner();
        banner.iniciar();
    }
});
