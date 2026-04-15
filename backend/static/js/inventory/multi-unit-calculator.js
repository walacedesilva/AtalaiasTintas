/**
 * Multi-Unit Calculator — T023
 *
 * Converts sale quantities between units using conversion factors
 * fetched from /api/inventory/conversao/ endpoints.
 *
 * Usage:
 *   const calc = new MultiUnitCalculator({ produtoVariacaoId: '...', lojaId: 1 });
 *   await calc.init();
 *   calc.attach(formElement);
 */

'use strict';

class MultiUnitCalculator {
    constructor(options = {}) {
        this.produtoVariacaoId = options.produtoVariacaoId || null;
        this.lojaId = options.lojaId || null;
        this.apiBase = options.apiBase || '/api/inventory';
        this.onConvertido = options.onConvertido || null; // callback(qtdBase, fator)

        this._unidades = [];   // cache {id, sigla, nome, fator_conversao}
        this._unidadeBase = null;
        this._initialized = false;
    }

    // ------------------------------------------------------------------
    // Lifecycle
    // ------------------------------------------------------------------

    async init() {
        if (!this.produtoVariacaoId) {
            throw new Error('MultiUnitCalculator: produtoVariacaoId é obrigatório');
        }
        await this._carregarUnidades();
        this._initialized = true;
        return this;
    }

    /**
     * Attach calculator behaviour to a form or container element.
     * Looks for:
     *   [data-multi-unit-qty]    — quantity input
     *   [data-multi-unit-select] — unit <select>
     *   [data-multi-unit-base]   — hidden/readonly input for base quantity
     *   [data-multi-unit-fator]  — hidden input for applied conversion factor
     *   [data-multi-unit-preview]— span/div to show "= X litros" preview
     */
    attach(container) {
        if (!this._initialized) {
            throw new Error('Call init() before attach()');
        }

        const qtyInput    = container.querySelector('[data-multi-unit-qty]');
        const unitSelect  = container.querySelector('[data-multi-unit-select]');
        const baseInput   = container.querySelector('[data-multi-unit-base]');
        const fatorInput  = container.querySelector('[data-multi-unit-fator]');
        const preview     = container.querySelector('[data-multi-unit-preview]');

        if (!qtyInput || !unitSelect) return;

        this._populateSelect(unitSelect);

        const recalcular = () => {
            const quantidade = parseFloat(qtyInput.value) || 0;
            const unidadeId  = parseInt(unitSelect.value, 10);
            const { qtdBase, fator } = this._converter(quantidade, unidadeId);

            if (baseInput)  baseInput.value  = qtdBase.toFixed(4);
            if (fatorInput) fatorInput.value = fator.toFixed(6);
            if (preview)    preview.textContent = this._previewText(qtdBase);
            if (this.onConvertido) this.onConvertido(qtdBase, fator);
        };

        qtyInput.addEventListener('input', recalcular);
        unitSelect.addEventListener('change', recalcular);

        // Run once on attach if values already present
        recalcular();
    }

    // ------------------------------------------------------------------
    // Programmatic API
    // ------------------------------------------------------------------

    /**
     * Convert *quantidade* in *unidadeId* to base unit.
     * Returns { qtdBase: number, fator: number }.
     */
    converter(quantidade, unidadeId) {
        this._assertInit();
        return this._converter(quantidade, unidadeId);
    }

    /**
     * Convert *qtdBase* (base unit) to display unit *unidadeId*.
     * Returns the converted quantity as a number.
     */
    converterParaUnidade(qtdBase, unidadeId) {
        this._assertInit();
        const unidade = this._unidades.find(u => u.id === unidadeId);
        if (!unidade) return qtdBase;
        if (unidade.fator_conversao === 0) return qtdBase;
        return qtdBase / unidade.fator_conversao;
    }

    getUnidades() {
        this._assertInit();
        return [...this._unidades];
    }

    getUnidadeBase() {
        this._assertInit();
        return this._unidadeBase;
    }

    // ------------------------------------------------------------------
    // Private helpers
    // ------------------------------------------------------------------

    async _carregarUnidades() {
        const url = `${this.apiBase}/conversao/unidades-produto/?produto_variacao=${encodeURIComponent(this.produtoVariacaoId)}`;
        const response = await fetch(url, {
            headers: { 'Accept': 'application/json' },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            throw new Error(`MultiUnitCalculator: falha ao buscar unidades (HTTP ${response.status})`);
        }

        const data = await response.json();
        this._unidades   = data.unidades || [];
        this._unidadeBase = data.unidade_base || null;
    }

    _populateSelect(selectEl) {
        selectEl.innerHTML = '';
        for (const u of this._unidades) {
            const opt = document.createElement('option');
            opt.value       = u.id;
            opt.textContent = `${u.sigla} — ${u.nome}`;
            if (this._unidadeBase && u.id === this._unidadeBase.id) {
                opt.selected = true;
            }
            selectEl.appendChild(opt);
        }
    }

    _converter(quantidade, unidadeId) {
        const unidade = this._unidades.find(u => u.id === unidadeId);
        if (!unidade) return { qtdBase: quantidade, fator: 1 };
        const fator   = unidade.fator_conversao || 1;
        const qtdBase = quantidade * fator;
        return { qtdBase, fator };
    }

    _previewText(qtdBase) {
        const sigla  = this._unidadeBase ? this._unidadeBase.sigla : '';
        return `= ${qtdBase.toFixed(4)} ${sigla}`.trim();
    }

    _assertInit() {
        if (!this._initialized) {
            throw new Error('MultiUnitCalculator: chame init() primeiro');
        }
    }
}

// Auto-wire elements with [data-multi-unit-calc] attribute on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-multi-unit-calc]').forEach(async (el) => {
        const produtoVariacaoId = el.dataset.multiUnitCalc;
        const lojaId = parseInt(el.dataset.lojaId, 10) || null;
        if (!produtoVariacaoId) return;

        try {
            const calc = new MultiUnitCalculator({ produtoVariacaoId, lojaId });
            await calc.init();
            calc.attach(el);
        } catch (err) {
            console.warn('MultiUnitCalculator auto-wire failed:', err);
        }
    });
});
