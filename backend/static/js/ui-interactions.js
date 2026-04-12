/**
 * UI Interactions JavaScript - Loading States & User Interface
 * 
 * Feature: 3-modern-web-interface
 * Task: T009 - Create Loading State Components
 * 
 * This module provides interactive loading states, progress tracking,
 * and smooth user experience enhancements for the Tintas System.
 */

'use strict';

// ===================================
// LOADING STATE MANAGEMENT
// ===================================

class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
        this.globalOverlay = null;
        this.init();
    }

    init() {
        this.createGlobalOverlay();
        this.bindEvents();
    }

    /**
     * Create the global loading overlay element
     */
    createGlobalOverlay() {
        if (document.getElementById('global-loading-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'global-loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-overlay-content">
                <div class="spinner spinner-lg spinner-primary" role="status" aria-label="Carregando"></div>
                <div class="loading-message">Carregando...</div>
                <div class="sr-only-loading" aria-live="polite">Processando solicitação. Por favor, aguarde.</div>
            </div>
        `;
        document.body.appendChild(overlay);
        this.globalOverlay = overlay;
    }

    /**
     * Show global loading overlay
     * @param {string} message - Custom loading message
     */
    showGlobalLoading(message = 'Carregando...') {
        if (this.globalOverlay) {
            const messageEl = this.globalOverlay.querySelector('.loading-message');
            if (messageEl) messageEl.textContent = message;
            this.globalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        }
    }

    /**
     * Hide global loading overlay
     */
    hideGlobalLoading() {
        if (this.globalOverlay) {
            this.globalOverlay.classList.remove('active');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }

    /**
     * Show loading state for a specific container
     * @param {Element|string} target - DOM element or selector
     * @param {string} message - Loading message
     */
    showLocalLoading(target, message = 'Carregando...') {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        // Make container position relative if not already
        const computedStyle = window.getComputedStyle(element);
        if (computedStyle.position === 'static') {
            element.style.position = 'relative';
        }

        element.classList.add('loading-container');

        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay active';
        overlay.innerHTML = `
            <div class="loading-overlay-content">
                <div class="spinner spinner-primary" role="status" aria-label="Carregando"></div>
                <div class="loading-message">${message}</div>
            </div>
        `;

        element.appendChild(overlay);
        this.activeLoaders.add(overlay);
    }

    /**
     * Hide loading state for a specific container
     * @param {Element|string} target - DOM element or selector
     */
    hideLocalLoading(target) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        const overlay = element.querySelector('.loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => {
                overlay.remove();
                element.classList.remove('loading-container');
                this.activeLoaders.delete(overlay);
            }, 150);
        }
    }

    /**
     * Set button loading state
     * @param {Element|string} button - Button element or selector
     * @param {boolean} loading - Loading state
     */
    setButtonLoading(button, loading = true) {
        const btn = typeof button === 'string' ? document.querySelector(button) : button;
        if (!btn) return;

        if (loading) {
            btn.classList.add('btn-loading');
            btn.disabled = true;
            btn.setAttribute('aria-busy', 'true');
        } else {
            btn.classList.remove('btn-loading');
            btn.disabled = false;
            btn.setAttribute('aria-busy', 'false');
        }
    }

    /**
     * Set form loading state
     * @param {Element|string} form - Form element or selector
     * @param {boolean} loading - Loading state
     */
    setFormLoading(form, loading = true) {
        const formEl = typeof form === 'string' ? document.querySelector(form) : form;
        if (!formEl) return;

        if (loading) {
            formEl.classList.add('form-loading');
            formEl.setAttribute('aria-busy', 'true');
        } else {
            formEl.classList.remove('form-loading');
            formEl.setAttribute('aria-busy', 'false');
        }
    }

    /**
     * Bind global event handlers
     */
    bindEvents() {
        // Auto-handle form submissions with loading states
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.dataset.autoLoading !== 'false') {
                this.setFormLoading(form, true);
                
                // Auto-hide after 5 seconds (fallback)
                setTimeout(() => {
                    this.setFormLoading(form, false);
                }, 5000);
            }
        });

        // Handle AJAX requests (if jQuery is available)
        if (window.jQuery) {
            jQuery(document).ajaxStart(() => {
                this.showGlobalLoading('Processando...');
            }).ajaxStop(() => {
                this.hideGlobalLoading();
            });
        }
    }
}

// ===================================
// PROGRESS BAR MANAGEMENT
// ===================================

class ProgressBar {
    constructor(selector, options = {}) {
        this.element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        this.options = {
            animated: false,
            showPercentage: false,
            color: 'primary',
            ...options
        };
        this.value = 0;
        this.init();
    }

    init() {
        if (!this.element) return;

        // Create progress structure if needed
        if (!this.element.classList.contains('progress')) {
            this.element.className = `progress ${this.options.size || ''}`;
            this.element.innerHTML = `<div class="progress-bar progress-bar-${this.options.color}" role="progressbar" style="width: 0%"></div>`;
        }

        this.progressBar = this.element.querySelector('.progress-bar');
        
        if (this.options.animated) {
            this.progressBar.classList.add('progress-bar-animated');
        }

        if (this.options.showPercentage) {
            this.createPercentageDisplay();
        }
    }

    createPercentageDisplay() {
        this.percentageEl = document.createElement('span');
        this.percentageEl.className = 'progress-percentage';
        this.percentageEl.textContent = '0%';
        this.element.parentNode.insertBefore(this.percentageEl, this.element.nextSibling);
    }

    /**
     * Set progress value
     * @param {number} value - Progress value (0-100)
     * @param {boolean} animate - Whether to animate the change
     */
    setValue(value, animate = true) {
        this.value = Math.max(0, Math.min(100, value));
        
        if (animate) {
            this.progressBar.style.transition = 'width 0.3s ease-in-out';
        } else {
            this.progressBar.style.transition = 'none';
        }

        this.progressBar.style.width = `${this.value}%`;
        this.progressBar.setAttribute('aria-valuenow', this.value);

        if (this.percentageEl) {
            this.percentageEl.textContent = `${Math.round(this.value)}%`;
        }

        // Trigger complete event
        if (this.value >= 100) {
            this.element.dispatchEvent(new CustomEvent('progress:complete'));
        }
    }

    /**
     * Increment progress by amount
     * @param {number} amount - Amount to increment
     */
    increment(amount = 10) {
        this.setValue(this.value + amount);
    }

    /**
     * Reset progress to 0
     */
    reset() {
        this.setValue(0, false);
    }

    /**
     * Simulate progress for file uploads
     * @param {number} duration - Duration in milliseconds
     */
    simulate(duration = 2000) {
        const steps = 50;
        const stepDuration = duration / steps;
        let currentStep = 0;

        const interval = setInterval(() => {
            currentStep++;
            const progress = (currentStep / steps) * 100;
            this.setValue(progress);

            if (currentStep >= steps) {
                clearInterval(interval);
            }
        }, stepDuration);
    }
}

// ===================================
// SKELETON LOADING UTILITIES
// ===================================

class SkeletonLoader {
    /**
     * Create skeleton placeholder for content
     * @param {Element|string} target - Target element
     * @param {Object} options - Skeleton options
     */
    static create(target, options = {}) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        const config = {
            lines: 3,
            width: ['100%', '75%', '50%'],
            showAvatar: false,
            showTitle: true,
            ...options
        };

        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-content';

        if (config.showAvatar) {
            skeleton.innerHTML += '<div class="skeleton skeleton-avatar"></div>';
        }

        if (config.showTitle) {
            skeleton.innerHTML += '<div class="skeleton skeleton-title"></div>';
        }

        for (let i = 0; i < config.lines; i++) {
            const width = Array.isArray(config.width) ? config.width[i] || '100%' : config.width;
            skeleton.innerHTML += `<div class="skeleton skeleton-text" style="width: ${width}"></div>`;
        }

        element.innerHTML = '';
        element.appendChild(skeleton);

        return {
            remove: () => {
                skeleton.remove();
            }
        };
    }

    /**
     * Create table skeleton
     * @param {Element|string} target - Target element
     * @param {number} rows - Number of skeleton rows
     * @param {number} cols - Number of columns
     */
    static createTable(target, rows = 5, cols = 4) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-table';

        for (let i = 0; i < rows; i++) {
            const row = document.createElement('div');
            row.className = 'skeleton-table-row';
            row.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

            for (let j = 0; j < cols; j++) {
                row.innerHTML += '<div class="skeleton skeleton-table-cell"></div>';
            }

            skeleton.appendChild(row);
        }

        element.innerHTML = '';
        element.appendChild(skeleton);

        return {
            remove: () => {
                skeleton.remove();
            }
        };
    }
}

// ===================================
// INITIALIZATION & GLOBAL ACCESS
// ===================================

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUIComponents);
} else {
    initializeUIComponents();
}

function initializeUIComponents() {
    // Initialize global loading manager
    window.LoadingManager = new LoadingManager();
    
    // Make classes globally available
    window.ProgressBar = ProgressBar;
    window.SkeletonLoader = SkeletonLoader;
    
    // Global convenience methods
    window.showLoading = (message) => window.LoadingManager.showGlobalLoading(message);
    window.hideLoading = () => window.LoadingManager.hideGlobalLoading();
    
    console.log('🎨 UI Components initialized successfully');
}

// ===================================
// AUTO-LOADING DETECTION
// ===================================

// Automatically handle buttons with data-loading attributes
document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-loading]');
    if (btn) {
        const duration = parseInt(btn.dataset.loading) || 2000;
        window.LoadingManager.setButtonLoading(btn, true);
        
        setTimeout(() => {
            window.LoadingManager.setButtonLoading(btn, false);
        }, duration);
    }
});

// Handle elements with data-skeleton attribute
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-skeleton]').forEach(element => {
        const config = element.dataset.skeleton ? JSON.parse(element.dataset.skeleton) : {};
        SkeletonLoader.create(element, config);
        
        // Auto-remove after specified time
        const duration = parseInt(element.dataset.skeletonDuration) || 3000;
        setTimeout(() => {
            element.removeAttribute('data-skeleton');
            element.innerHTML = element.dataset.skeletonOriginal || '';
        }, duration);
    });
});

// ===================================
// QUICK ACTIONS SYSTEM
// Feature: 3-modern-web-interface
// Task: T012 - Build Quick Actions System
// ===================================

class QuickActionsManager {
    constructor() {
        this.preferences = null;
        this.currentSection = null;
        this.init();
    }

    init() {
        this.loadPreferences();
        this.bindEvents();
        this.setupCustomActions();
        console.log('⚡ Quick Actions Manager initialized');
    }

    /**
     * Load user preferences from localStorage
     */
    loadPreferences() {
        try {
            const saved = localStorage.getItem('quickActionsPreferences');
            this.preferences = saved ? JSON.parse(saved) : this.getDefaultPreferences();
        } catch (error) {
            console.warn('Failed to load quick actions preferences:', error);
            this.preferences = this.getDefaultPreferences();
        }
    }

    /**
     * Get default preferences for all sections
     */
    getDefaultPreferences() {
        return {
            dashboard: {
                enabled: ['view_recent_jobs', 'quick_mix', 'generate_label', 'view_templates'],
                custom: []
            },
            templates: {
                enabled: ['search_templates', 'create_template', 'duplicate_template', 'bulk_edit'],
                custom: []
            },
            mixing: {
                enabled: ['select_formula', 'calculate_quantity', 'generate_mix', 'recent_formulas'],
                custom: []
            },
            jobs: {
                enabled: ['view_status', 'download_labels', 'mark_complete', 'print_queue'],
                custom: []
            }
        };
    }

    /**
     * Save preferences to localStorage
     */
    savePreferences() {
        try {
            localStorage.setItem('quickActionsPreferences', JSON.stringify(this.preferences));
            this.setupCustomActions();
            window.LoadingManager.showGlobalLoading('Salvando configurações...');
            
            setTimeout(() => {
                window.LoadingManager.hideGlobalLoading();
            }, 800);
        } catch (error) {
            console.error('Failed to save preferences:', error);
        }
    }

    /**
     * Setup custom actions based on current section and preferences
     */
    setupCustomActions() {
        const section = this.detectCurrentSection();
        if (!section || !this.preferences[section]) return;

        this.currentSection = section;
        this.renderQuickActions(section);
    }

    /**
     * Detect current section based on URL or page content
     */
    detectCurrentSection() {
        const path = window.location.pathname;
        
        if (path.includes('/dashboard') || path === '/') return 'dashboard';
        if (path.includes('/template')) return 'templates';
        if (path.includes('/mix') || path.includes('/formula')) return 'mixing';
        if (path.includes('/job') || path.includes('/order')) return 'jobs';
        
        return null;
    }

    /**
     * Render quick actions for specified section
     */
    renderQuickActions(section) {
        const container = document.querySelector('.quick-actions-container');
        if (!container) return;

        const actions = this.preferences[section].enabled;
        const customActions = this.preferences[section].custom || [];
        
        container.innerHTML = `
            <div class="quick-actions-grid">
                ${actions.map(action => this.renderAction(action, section)).join('')}
                ${customActions.map(action => this.renderCustomAction(action)).join('')}
            </div>
        `;
    }

    /**
     * Bind event handlers
     */
    bindEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.quick-action-btn')) {
                e.preventDefault();
                this.executeAction(e.target.dataset.action, e.target.dataset.params);
            }
        });
    }
}

// ===================================
// T014 - PROGRESSIVE ENHANCEMENT LAYER
// Feature: 3-modern-web-interface
// Task: T014 - Create Progressive Enhancement Layer
// ===================================

// Feature Detection Module
const FeatureDetection = {
    localStorage: (() => {
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            return true;
        } catch (e) { return false; }
    })(),

    sessionStorage: (() => {
        try {
            sessionStorage.setItem('test', 'test');
            sessionStorage.removeItem('test');
            return true;
        } catch (e) { return false; }
    })(),

    cssTransitions: (() => {
        const el = document.createElement('div');
        return 'transition' in el.style || 'webkitTransition' in el.style;
    })(),

    cssAnimations: (() => {
        const el = document.createElement('div');
        return 'animation' in el.style || 'webkitAnimation' in el.style;
    })(),

    intersectionObserver: 'IntersectionObserver' in window,
    touchEvents: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    fetch: typeof fetch !== 'undefined',
    history: !!(window.history && history.pushState),
    webSockets: 'WebSocket' in window,
    notifications: 'Notification' in window,
    geolocation: 'geolocation' in navigator
};

// Enhanced Form Interactions
class FormEnhancements {
    constructor() {
        this.forms = document.querySelectorAll('form');
        this.init();
    }

    init() {
        this.forms.forEach(form => {
            this.enhanceForm(form);
        });
    }

    enhanceForm(form) {
        this.addRealTimeValidation(form);
        this.addAutoSave(form);
        this.addAjaxSubmission(form);
        this.addUnsavedChangesWarning(form);
    }

    addRealTimeValidation(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateInput(input);
            });
            
            input.addEventListener('input', () => {
                clearTimeout(input.validationTimeout);
                input.validationTimeout = setTimeout(() => {
                    this.validateInput(input);
                }, 500);
            });
        });
    }

    validateInput(input) {
        const isValid = input.validity.valid;
        input.classList.remove('is-valid', 'is-invalid');
        
        if (input.value.trim() === '') {
            if (input.required) {
                input.classList.add('is-invalid');
            }
            return;
        }
        
        input.classList.add(isValid ? 'is-valid' : 'is-invalid');
        
        const feedback = input.parentElement.querySelector('.invalid-feedback');
        if (!isValid && feedback) {
            feedback.textContent = this.getValidationMessage(input);
        }
    }

    getValidationMessage(input) {
        if (input.validity.valueMissing) {
            return `${input.labels[0]?.textContent || 'Este campo'} é obrigatório.`;
        }
        if (input.validity.typeMismatch) {
            return `Por favor, insira um ${input.type} válido.`;
        }
        if (input.validity.patternMismatch) {
            return input.title || 'Por favor, siga o formato solicitado.';
        }
        return 'Por favor, insira um valor válido.';
    }

    addAutoSave(form) {
        if (!FeatureDetection.localStorage) return;

        const formId = form.id || `form_${Date.now()}`;
        const storageKey = `autosave_${formId}`;
        
        this.loadFormData(form, storageKey);
        
        form.addEventListener('input', () => {
            clearTimeout(form.saveTimeout);
            form.saveTimeout = setTimeout(() => {
                this.saveFormData(form, storageKey);
                this.showAutoSaveIndicator(form);
            }, 2000);
        });

        form.addEventListener('submit', () => {
            localStorage.removeItem(storageKey);
        });
    }

    saveFormData(form, storageKey) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        try {
            localStorage.setItem(storageKey, JSON.stringify(data));
        } catch (e) {
            console.warn('Failed to save form data:', e);
        }
    }

    loadFormData(form, storageKey) {
        try {
            const data = localStorage.getItem(storageKey);
            if (!data) return;
            
            const parsedData = JSON.parse(data);
            
            Object.keys(parsedData).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input && input.type !== 'password') {
                    input.value = parsedData[key];
                }
            });
        } catch (e) {
            console.warn('Failed to load form data:', e);
        }
    }

    showAutoSaveIndicator(form) {
        let indicator = form.querySelector('.autosave-indicator');
        
        if (!indicator) {
            indicator = document.createElement('small');
            indicator.className = 'autosave-indicator text-muted ms-2';
            indicator.style.opacity = '0';
            indicator.style.transition = 'opacity 0.2s';
            
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.parentElement.appendChild(indicator);
            }
        }
        
        indicator.textContent = '✓ Salvo automaticamente';
        indicator.style.opacity = '1';
        
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }

    addAjaxSubmission(form) {
        if (!FeatureDetection.fetch) return;
        if (!form.classList.contains('ajax-form')) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitButton = form.querySelector('button[type="submit"]');
            const originalText = submitButton?.innerHTML;
            
            try {
                if (submitButton) {
                    window.LoadingManager.setButtonLoading(submitButton, true);
                }
                
                const formData = new FormData(form);
                const response = await fetch(form.action || window.location.href, {
                    method: form.method || 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                });
                
                if (response.ok) {
                    const result = await response.json().catch(() => null);
                    this.handleFormSuccess(form, result);
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
                
            } catch (error) {
                console.error('Form submission failed:', error);
                this.handleFormError(form, error);
            } finally {
                if (submitButton) {
                    window.LoadingManager.setButtonLoading(submitButton, false);
                }
            }
        });
    }

    addUnsavedChangesWarning(form) {
        let hasUnsavedChanges = false;
        
        form.addEventListener('input', () => {
            hasUnsavedChanges = true;
        });
        
        form.addEventListener('submit', () => {
            hasUnsavedChanges = false;
        });
        
        window.addEventListener('beforeunload', (e) => {
            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = 'Você tem alterações não salvas. Tem certeza que deseja sair?';
                return e.returnValue;
            }
        });
    }

    handleFormSuccess(form, result) {
        this.showFormMessage(form, result?.message || 'Formulário enviado com sucesso!', 'success');
        
        if (result?.resetForm !== false) {
            form.reset();
        }
        
        if (result?.redirect) {
            setTimeout(() => {
                window.location.href = result.redirect;
            }, 1500);
        }
    }

    handleFormError(form, error) {
        this.showFormMessage(form, 'Falha no envio. Tente novamente.', 'error');
    }

    showFormMessage(form, message, type) {
        let messageEl = form.querySelector('.form-message');
        
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.className = 'form-message alert';
            form.insertBefore(messageEl, form.firstChild);
        }
        
        messageEl.className = `form-message alert alert-${type === 'success' ? 'success' : 'danger'}`;
        messageEl.textContent = message;
        messageEl.style.display = 'block';
        
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
    }
}

// Keyboard Shortcuts Manager
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }

    init() {
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        this.registerDefaultShortcuts();
    }

    register(keys, callback, description = '') {
        const keyString = this.normalizeKeys(keys);
        this.shortcuts.set(keyString, { callback, description });
    }

    normalizeKeys(keys) {
        return keys.toLowerCase()
                   .replace(/\s+/g, '')
                   .split('+')
                   .sort()
                   .join('+');
    }

    handleKeyDown(e) {
        if (e.target.matches('input, textarea, select, [contenteditable]')) {
            return;
        }
        
        const keys = [];
        
        if (e.ctrlKey || e.metaKey) keys.push('ctrl');
        if (e.altKey) keys.push('alt');
        if (e.shiftKey) keys.push('shift');
        
        keys.push(e.key.toLowerCase());
        
        const keyString = keys.sort().join('+');
        const shortcut = this.shortcuts.get(keyString);
        
        if (shortcut) {
            e.preventDefault();
            shortcut.callback(e);
        }
    }

    registerDefaultShortcuts() {
        this.register('ctrl+h', () => {
            const homeLink = document.querySelector('a[href="/"], a[href="{% url "home" %}"]');
            homeLink?.click();
        }, 'Ir para Home');
        
        this.register('ctrl+k', () => {
            const searchInput = document.querySelector('input[type="search"], #search');
            searchInput?.focus();
        }, 'Focar Busca');
        
        this.register('ctrl+s', (e) => {
            e.preventDefault();
            const form = document.querySelector('form:not([readonly])');
            form?.requestSubmit();
        }, 'Salvar Formulário');
    }
}

// Accessibility Enhancements
class AccessibilityEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.addSkipLinks();
        this.enhanceFocusManagement();
        this.detectKeyboardNavigation();
    }

    addSkipLinks() {
        if (document.querySelector('.skip-links')) return;

        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="skip-link">Pular para o conteúdo principal</a>
            <a href="#navigation" class="skip-link">Pular para a navegação</a>
        `;
        
        document.body.insertBefore(skipLinks, document.body.firstChild);
    }

    enhanceFocusManagement() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
                    closeBtn?.click();
                }
            }
        });
    }

    detectKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }
}

// Scroll Animations
class ScrollAnimations {
    constructor() {
        this.elements = document.querySelectorAll('.scroll-animate');
        this.init();
    }

    init() {
        if (!FeatureDetection.intersectionObserver) {
            this.elements.forEach(el => el.classList.add('in-view'));
            return;
        }

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                    this.observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '0px 0px -100px 0px',
            threshold: 0.1
        });

        this.elements.forEach(el => {
            this.observer.observe(el);
        });
    }
}

// Enhanced Interactions
class InteractionEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.enhanceButtons();
        this.enhanceCards();
        this.addRippleEffects();
    }

    enhanceButtons() {
        const buttons = document.querySelectorAll('.btn:not(.no-enhance)');
        
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                if (button.dataset.loading === 'auto') {
                    this.showButtonLoading(button);
                }
            });
        });
    }

    enhanceCards() {
        const cards = document.querySelectorAll('.card-clickable');
        
        cards.forEach(card => {
            card.addEventListener('click', () => {
                const link = card.querySelector('a[href]');
                if (link && !window.getSelection().toString()) {
                    window.location.href = link.href;
                }
            });
            
            card.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    card.click();
                }
            });
        });
    }

    addRippleEffects() {
        if (!FeatureDetection.cssAnimations) return;
        
        const rippleElements = document.querySelectorAll('.btn, .card-clickable');
        
        rippleElements.forEach(element => {
            element.addEventListener('click', (e) => {
                this.createRipple(element, e);
            });
        });
    }

    createRipple(element, event) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
}

// Initialize Progressive Enhancement Layer
function initializeProgressiveEnhancements() {
    // Apply feature detection classes
    const html = document.documentElement;
    html.classList.remove('no-js');
    html.classList.add('js-enabled');
    
    Object.keys(FeatureDetection).forEach(feature => {
        const className = FeatureDetection[feature] ? `js-${feature}` : `no-${feature}`;
        html.classList.add(className);
    });
    
    // Initialize enhancement components
    new FormEnhancements();
    new KeyboardShortcuts();
    new AccessibilityEnhancer();
    new ScrollAnimations();
    new InteractionEnhancer();
    
    console.log('🚀 Progressive Enhancement Layer initialized with features:', FeatureDetection);
}

// Enhanced Initialization
function initializeAllUIComponents() {
    // Initialize original components
    initializeUIComponents();
    
    // Initialize Quick Actions
    window.QuickActionsManager = new QuickActionsManager();
    
    // Initialize Progressive Enhancements
    initializeProgressiveEnhancements();
    
    console.log('✨ All UI components and enhancements initialized successfully');
}

// Update initialization to include all enhancements
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllUIComponents);
} else {
    initializeAllUIComponents();
}

// Add CSS for progressive enhancements
if (!document.querySelector('#progressive-enhancement-styles')) {
    const style = document.createElement('style');
    style.id = 'progressive-enhancement-styles';
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .skip-links {
            position: absolute;
            top: -40px;
            left: 6px;
            z-index: 1000;
        }
        
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            transition: top 0.3s ease;
        }
        
        .skip-link:focus {
            top: 6px;
        }
        
        .keyboard-navigation *:focus {
            outline: 2px solid var(--bs-primary) !important;
            outline-offset: 2px;
        }
        
        .scroll-animate {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .scroll-animate.in-view {
            opacity: 1;
            transform: translateY(0);
        }
        
        .autosave-indicator {
            font-size: 0.875em;
            color: var(--bs-success) !important;
        }
        
        /* Respect reduced motion preferences */
        @media (prefers-reduced-motion: reduce) {
            .scroll-animate,
            .ripple-effect,
            * {
                transition: none !important;
                animation: none !important;
            }
        }
    `;
    document.head.appendChild(style);
}

// Export enhanced classes for global access
window.UIEnhancements = {
    FeatureDetection,
    FormEnhancements,
    KeyboardShortcuts,
    AccessibilityEnhancer,
    ScrollAnimations,
    InteractionEnhancer
};
            
            // Simulate API call to server
            setTimeout(() => {
                window.LoadingManager.hideGlobalLoading();
                this.showNotification('Configurações salvas com sucesso!', 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('customizeActionsModal'));
                if (modal) modal.hide();
            }, 1000);
        } catch (error) {
            console.error('Failed to save quick actions preferences:', error);
            this.showNotification('Erro ao salvar configurações', 'error');
        }
    }

    /**
     * Setup custom actions display
     */
    setupCustomActions() {
        this.currentSection = this.getCurrentSection();
        if (!this.currentSection || !this.preferences[this.currentSection]) return;

        const customActionsContainer = document.getElementById('customActions');
        const customActionsGrid = document.getElementById('customActionsGrid');
        
        if (!customActionsContainer || !customActionsGrid) return;

        const customActions = this.preferences[this.currentSection].custom || [];
        
        if (customActions.length > 0) {
            customActionsGrid.innerHTML = '';
            customActions.forEach(action => {
                const actionElement = this.createCustomActionElement(action);
                customActionsGrid.appendChild(actionElement);
            });
            customActionsContainer.style.display = 'block';
        } else {
            customActionsContainer.style.display = 'none';
        }
    }

    /**
     * Get current section from page context
     */
    getCurrentSection() {
        const container = document.querySelector('.quick-actions-container');
        return container ? container.dataset.section : null;
    }

    /**
     * Create custom action element
     */
    createCustomActionElement(action) {
        const div = document.createElement('div');
        div.className = 'quick-action-item';
        div.innerHTML = `
            <button type="button" 
                    class="btn btn-outline-secondary quick-action-btn"
                    onclick="quickActions.executeCustomAction('${action.id}')"
                    title="${action.name}">
                <i class="bi ${action.icon}"></i>
                <span>${action.name}</span>
            </button>
        `;
        return div;
    }

    /**
     * Execute custom action
     */
    executeCustomAction(actionId) {
        const customActions = this.preferences[this.currentSection]?.custom || [];
        const action = customActions.find(a => a.id === actionId);
        
        if (!action) return;

        if (action.url.startsWith('javascript:') || action.url.includes('()')) {
            // Execute JavaScript function
            try {
                eval(action.url.replace('javascript:', ''));
            } catch (error) {
                console.error('Error executing custom action:', error);
                this.showNotification('Erro ao executar ação personalizada', 'error');
            }
        } else {
            // Navigate to URL
            window.location.href = action.url;
        }
    }

    /**
     * Bind event handlers
     */
    bindEvents() {
        // Custom action form submission
        const customActionForm = document.getElementById('customActionForm');
        if (customActionForm) {
            customActionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addCustomAction();
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // Alt + Q: Toggle quick actions visibility
        if (e.altKey && e.key === 'q') {
            e.preventDefault();
            this.toggleQuickActions();
        }

        // Alt + 1-9: Execute quick actions by position
        if (e.altKey && e.key >= '1' && e.key <= '9') {
            e.preventDefault();
            const index = parseInt(e.key) - 1;
            this.executeQuickActionByIndex(index);
        }
    }

    /**
     * Toggle quick actions visibility
     */
    toggleQuickActions() {
        const container = document.querySelector('.quick-actions-container');
        if (container) {
            container.style.display = container.style.display === 'none' ? 'block' : 'none';
        }
    }

    /**
     * Execute quick action by index
     */
    executeQuickActionByIndex(index) {
        const buttons = document.querySelectorAll('.quick-action-btn');
        if (buttons[index]) {
            buttons[index].click();
        }
    }

    /**
     * Add custom action from form
     */
    addCustomAction() {
        const form = document.getElementById('customActionForm');
        const formData = new FormData(form);
        
        const action = {
            id: 'custom_' + Date.now(),
            name: formData.get('actionName') || document.getElementById('actionName').value,
            icon: formData.get('actionIcon') || document.getElementById('actionIcon').value || 'bi-star',
            url: formData.get('actionUrl') || document.getElementById('actionUrl').value
        };

        if (!action.name || !action.url) {
            this.showNotification('Nome e URL são obrigatórios', 'error');
            return;
        }

        this.currentSection = this.getCurrentSection();
        if (!this.preferences[this.currentSection]) {
            this.preferences[this.currentSection] = { enabled: [], custom: [] };
        }

        this.preferences[this.currentSection].custom.push(action);
        form.reset();
        this.showNotification('Ação personalizada adicionada!', 'success');
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.body.appendChild(notification);

        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // ===================================
    // SECTION-SPECIFIC QUICK ACTIONS
    // ===================================

    /**
     * Dashboard Quick Actions
     */
    viewRecentJobs() {
        window.LoadingManager.showGlobalLoading('Carregando jobs recentes...');
        
        // Mock API call - replace with actual endpoint
        setTimeout(() => {
            window.LoadingManager.hideGlobalLoading();
            this.showJobsModal();
        }, 800);
    }

    showJobsModal() {
        // Create and show recent jobs modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'recentJobsModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="bi bi-clock-history"></i> Jobs Recentes</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="list-group">
                            <!-- Recent jobs will be loaded here -->
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Etiqueta #001234</h6>
                                    <small>há 3 minutos</small>
                                </div>
                                <p class="mb-1">Tinta Branca - Fórmula Premium</p>
                                <small>Status: Concluído</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Remove modal when hidden
        modal.addEventListener('hidden.bs.modal', () => modal.remove());
    }

    /**
     * Template Quick Actions
     */
    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[name="search"], #search');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    duplicateTemplate() {
        // Check if any template is selected
        const selectedTemplate = document.querySelector('.template-item.selected, input[name="template"]:checked');
        
        if (!selectedTemplate) {
            this.showNotification('Selecione um template para duplicar', 'warning');
            return;
        }

        this.showNotification('Funcionalidade de duplicação será implementada', 'info');
    }

    toggleBulkEdit() {
        const bulkControls = document.querySelector('.bulk-edit-controls');
        const checkboxes = document.querySelectorAll('.template-checkbox');
        
        checkboxes.forEach(cb => {
            cb.style.display = cb.style.display === 'none' ? 'block' : 'none';
        });

        if (bulkControls) {
            bulkControls.style.display = bulkControls.style.display === 'none' ? 'block' : 'none';
        }
    }

    /**
     * Mixing Quick Actions
     */
    openCalculator() {
        // Create calculator modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'calculatorModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="bi bi-calculator"></i> Calculadora de Pigmentos</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="pigmentCalculatorForm">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Volume Base (L)</label>
                                        <input type="number" class="form-control" id="baseVolume" step="0.1" min="0.1">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group mb-3">
                                        <label class="form-label">Concentração (%)</label>
                                        <input type="number" class="form-control" id="concentration" step="0.1" min="0.1" max="100">
                                    </div>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-primary">Calcular</button>
                        </form>
                        <div id="calculatorResults" style="display: none;" class="mt-3">
                            <!-- Results will appear here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Handle calculator form
        modal.querySelector('#pigmentCalculatorForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.calculatePigments();
        });
        
        // Remove modal when hidden
        modal.addEventListener('hidden.bs.modal', () => modal.remove());
    }

    calculatePigments() {
        const baseVolume = parseFloat(document.getElementById('baseVolume').value);
        const concentration = parseFloat(document.getElementById('concentration').value);
        
        if (!baseVolume || !concentration) {
            this.showNotification('Preencha volume e concentração', 'warning');
            return;
        }

        const pigmentAmount = (baseVolume * concentration) / 100;
        
        const resultsDiv = document.getElementById('calculatorResults');
        resultsDiv.innerHTML = `
            <div class="alert alert-success">
                <h6>Resultado do Cálculo</h6>
                <p><strong>Volume de Pigmento:</strong> ${pigmentAmount.toFixed(2)}L</p>
                <p><strong>Volume Base:</strong> ${(baseVolume - pigmentAmount).toFixed(2)}L</p>
            </div>
        `;
        resultsDiv.style.display = 'block';
    }

    generateMix() {
        this.showNotification('Gerando mistura com parâmetros atuais...', 'info');
        
        window.LoadingManager.showGlobalLoading('Processando mistura...');
        
        // Simulate mixing process
        setTimeout(() => {
            window.LoadingManager.hideGlobalLoading();
            this.showNotification('Mistura gerada com sucesso!', 'success');
        }, 2000);
    }

    showRecentFormulas() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'recentFormulasModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="bi bi-clock-history"></i> Fórmulas Recentes</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="list-group">
                            <div class="list-group-item list-group-item-action">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Branco Premium</h6>
                                    <small class="text-muted">Usado há 2 horas</small>
                                </div>
                                <p class="mb-1">Base: Branco + Azul Ultramarino (2%)</p>
                            </div>
                            <div class="list-group-item list-group-item-action">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Azul Céu</h6>
                                    <small class="text-muted">Usado ontem</small>
                                </div>
                                <p class="mb-1">Base: Branco + Azul Ftalocianina (5%)</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => modal.remove());
    }

    /**
     * Jobs Quick Actions
     */
    refreshJobStatus() {
        window.LoadingManager.showGlobalLoading('Atualizando status...');
        
        // Simulate API call
        setTimeout(() => {
            window.LoadingManager.hideGlobalLoading();
            this.showNotification('Status atualizado!', 'success');
            
            // Refresh the page or update the job list
            if (typeof updateJobList === 'function') {
                updateJobList();
            }
        }, 1000);
    }

    downloadSelectedLabels() {
        const selectedJobs = document.querySelectorAll('input[name="job_ids"]:checked');
        
        if (selectedJobs.length === 0) {
            this.showNotification('Selecione jobs para download', 'warning');
            return;
        }

        window.LoadingManager.showGlobalLoading('Preparando download...');
        
        // Simulate download preparation
        setTimeout(() => {
            window.LoadingManager.hideGlobalLoading();
            this.showNotification(`Baixando ${selectedJobs.length} etiquetas...`, 'success');
        }, 1500);
    }

    markSelectedComplete() {
        const selectedJobs = document.querySelectorAll('input[name="job_ids"]:checked');
        
        if (selectedJobs.length === 0) {
            this.showNotification('Selecione jobs para marcar como completos', 'warning');
            return;
        }

        if (confirm(`Marcar ${selectedJobs.length} jobs como completos?`)) {
            window.LoadingManager.showGlobalLoading('Atualizando jobs...');
            
            // Simulate API call
            setTimeout(() => {
                window.LoadingManager.hideGlobalLoading();
                this.showNotification(`${selectedJobs.length} jobs marcados como completos!`, 'success');
                
                // Update UI
                selectedJobs.forEach(checkbox => {
                    const row = checkbox.closest('tr');
                    if (row) {
                        row.classList.add('table-success');
                        const statusCell = row.querySelector('.job-status');
                        if (statusCell) statusCell.textContent = 'Completo';
                    }
                });
            }, 1000);
        }
    }
}

// Initialize Quick Actions Manager
let quickActions;

function initializeQuickActions() {
    quickActions = new QuickActionsManager();
    window.quickActions = quickActions;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeQuickActions);
} else {
    initializeQuickActions();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LoadingManager, ProgressBar, SkeletonLoader, QuickActionsManager };
}

// ===================================
// PROGRESSIVE ENHANCEMENT LAYER
// Feature: 3-modern-web-interface
// Task: T014 - Progressive Enhancement Layer
// ===================================

class ProgressiveEnhancementManager {
    constructor() {
        this.features = new Map();
        this.keyboardShortcuts = new Map();
        this.ajaxForms = new Set();
        this.isEnabled = true;
        this.init();
    }

    init() {
        this.detectFeatures();
        this.setupEnhancedInteractions();
        this.setupAjaxForms();
        this.setupKeyboardShortcuts();
        this.setupSmoothScrolling();
        this.log('Progressive Enhancement Manager initialized');
    }

    /**
     * Feature detection for JavaScript capabilities
     */
    detectFeatures() {
        const features = {
            // Storage support
            localStorage: this.detectLocalStorage(),
            sessionStorage: this.detectSessionStorage(),
            
            // Modern JavaScript features
            fetch: typeof fetch !== 'undefined',
            promises: typeof Promise !== 'undefined',
            classList: 'classList' in document.createElement('div'),
            
            // CSS features
            cssVariables: CSS && CSS.supports && CSS.supports('color', 'var(--test)'),
            flexbox: CSS && CSS.supports('display', 'flex'),
            grid: CSS && CSS.supports('display', 'grid'),
            
            // Animation features
            requestAnimationFrame: typeof requestAnimationFrame !== 'undefined',
            cssAnimations: this.detectCSSAnimations(),
            cssTransitions: this.detectCSSTransitions(),
            
            // Input features
            touchEvents: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
            pointerEvents: typeof PointerEvent !== 'undefined',
            
            // Network features
            onlineStatus: 'onLine' in navigator,
            connectionAPI: 'connection' in navigator,
            
            // Browser APIs
            intersectionObserver: typeof IntersectionObserver !== 'undefined',
            mutationObserver: typeof MutationObserver !== 'undefined',
            resizeObserver: typeof ResizeObserver !== 'undefined',
            
            // Form features
            formData: typeof FormData !== 'undefined',
            customValidity: 'setCustomValidity' in document.createElement('input'),
            
            // Modern features
            modules: 'noModule' in document.createElement('script'),
            serviceWorker: 'serviceWorker' in navigator,
        };

        this.features = new Map(Object.entries(features));
        
        // Add feature classes to document
        this.addFeatureClasses();
        
        this.log('Feature detection completed:', Object.fromEntries(this.features));
    }

    /**
     * Detect localStorage support
     */
    detectLocalStorage() {
        try {
            const test = 'localStorage-test';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Detect sessionStorage support
     */
    detectSessionStorage() {
        try {
            const test = 'sessionStorage-test';
            sessionStorage.setItem(test, test);
            sessionStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Detect CSS animations support
     */
    detectCSSAnimations() {
        const element = document.createElement('div');
        return 'animationName' in element.style || 
               'webkitAnimationName' in element.style;
    }

    /**
     * Detect CSS transitions support
     */
    detectCSSTransitions() {
        const element = document.createElement('div');
        return 'transition' in element.style ||
               'webkitTransition' in element.style;
    }

    /**
     * Add feature detection classes to document element
     */
    addFeatureClasses() {
        const docEl = document.documentElement;
        
        this.features.forEach((supported, feature) => {
            const className = supported ? `js-${feature}` : `no-${feature}`;
            docEl.classList.add(className);
        });
        
        // Add general JavaScript enabled class
        docEl.classList.add('js-enabled');
        docEl.classList.remove('no-js');
    }

    /**
     * Check if a feature is supported
     */
    hasFeature(feature) {
        return this.features.get(feature) === true;
    }

    /**
     * Setup enhanced interactions with graceful degradation
     */
    setupEnhancedInteractions() {
        // Enhanced hover effects
        if (this.hasFeature('cssTransitions')) {
            this.setupEnhancedHovers();
        }

        // Enhanced focus management
        this.setupFocusManagement();

        // Enhanced form interactions
        this.setupFormEnhancements();

        // Lazy loading for images
        if (this.hasFeature('intersectionObserver')) {
            this.setupLazyLoading();
        }

        // Enhanced animations
        if (this.hasFeature('requestAnimationFrame')) {
            this.setupAnimationEnhancements();
        }
    }

    /**
     * Setup enhanced hover effects
     */
    setupEnhancedHovers() {
        // Add smooth transitions to interactive elements
        const style = document.createElement('style');
        style.textContent = `
            .js-cssTransitions .btn,
            .js-cssTransitions .card,
            .js-cssTransitions .list-group-item {
                transition: all 0.2s ease-in-out;
            }
            
            .js-cssTransitions .btn:hover {
                transform: translateY(-1px);
            }
            
            .js-cssTransitions .card:hover {
                transform: translateY(-2px);
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Setup enhanced focus management
     */
    setupFocusManagement() {
        // Skip links for accessibility
        this.createSkipLinks();
        
        // Focus trap for modals
        this.setupFocusTraps();
        
        // Keyboard navigation indicators
        this.setupKeyboardIndicators();
    }

    /**
     * Create skip links for accessibility
     */
    createSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Pular para o conteúdo principal';
        skipLink.className = 'sr-only sr-only-focusable';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            width: auto;
            height: auto;
            padding: 8px 16px;
            background: #000;
            color: #fff;
            text-decoration: none;
            border-radius: 4px;
            z-index: 10000;
        `;
        
        // Show on focus
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }

    /**
     * Setup focus traps for modals
     */
    setupFocusTraps() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });
    }

    /**
     * Trap focus within element
     */
    trapFocus(e, element) {
        const focusableElements = element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            }
        } else {
            if (document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        }
    }

    /**
     * Setup keyboard navigation indicators
     */
    setupKeyboardIndicators() {
        let isUsingKeyboard = false;
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                isUsingKeyboard = true;
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            isUsingKeyboard = false;
            document.body.classList.remove('keyboard-navigation');
        });
    }

    /**
     * Setup form enhancements
     */
    setupFormEnhancements() {
        // Real-time validation
        if (this.hasFeature('customValidity')) {
            this.setupRealTimeValidation();
        }
        
        // Enhanced file uploads
        this.setupFileUploadEnhancements();
        
        // Form field formatting
        this.setupFieldFormatting();
    }

    /**
     * Setup real-time form validation
     */
    setupRealTimeValidation() {
        document.addEventListener('input', (e) => {
            const field = e.target;
            if (field.matches('input, textarea, select')) {
                this.validateField(field);
            }
        });
    }

    /**
     * Validate individual form field
     */
    validateField(field) {
        const isValid = field.checkValidity();
        
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Add appropriate class
        if (field.value.length > 0) {
            field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        }
        
        // Update custom validation message
        if (!isValid && field.validationMessage) {
            this.showFieldError(field, field.validationMessage);
        } else {
            this.hideFieldError(field);
        }
    }

    /**
     * Show field validation error
     */
    showFieldError(field, message) {
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        
        feedback.textContent = message;
        feedback.style.display = 'block';
    }

    /**
     * Hide field validation error
     */
    hideFieldError(field) {
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.style.display = 'none';
        }
    }

    /**
     * Setup file upload enhancements
     */
    setupFileUploadEnhancements() {
        document.addEventListener('change', (e) => {
            if (e.target.type === 'file') {
                this.enhanceFileUpload(e.target);
            }
        });
    }

    /**
     * Enhance file upload field
     */
    enhanceFileUpload(input) {
        const files = Array.from(input.files);
        
        if (files.length > 0) {
            // Show file names
            const fileList = files.map(file => file.name).join(', ');
            input.title = fileList;
            
            // Create file preview if supported
            if (this.hasFeature('fetch') && files[0].type.startsWith('image/')) {
                this.createImagePreview(input, files[0]);
            }
        }
    }

    /**
     * Create image preview for file uploads
     */
    createImagePreview(input, file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            let preview = input.parentNode.querySelector('.file-preview');
            
            if (!preview) {
                preview = document.createElement('div');
                preview.className = 'file-preview mt-2';
                input.parentNode.appendChild(preview);
            }
            
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 4px;">
                <span class="d-block text-muted small">${file.name} (${this.formatFileSize(file.size)})</span>
            `;
        };
        
        reader.readAsDataURL(file);
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Setup field formatting
     */
    setupFieldFormatting() {
        // Auto-format phone numbers
        document.addEventListener('input', (e) => {
            if (e.target.type === 'tel') {
                this.formatPhoneNumber(e.target);
            }
        });
        
        // Auto-format currency
        document.addEventListener('input', (e) => {
            if (e.target.dataset.format === 'currency') {
                this.formatCurrency(e.target);
            }
        });
    }

    /**
     * Format phone number input
     */
    formatPhoneNumber(input) {
        let value = input.value.replace(/\D/g, '');
        
        if (value.length >= 11) {
            value = value.replace(/^(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        } else if (value.length >= 7) {
            value = value.replace(/^(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
        } else if (value.length >= 3) {
            value = value.replace(/^(\d{2})(\d{0,5})/, '($1) $2');
        }
        
        input.value = value;
    }

    /**
     * Format currency input
     */
    formatCurrency(input) {
        let value = input.value.replace(/[^\d]/g, '');
        value = (parseInt(value) / 100).toFixed(2);
        
        if (value !== 'NaN') {
            input.value = 'R$ ' + value.replace('.', ',');
        }
    }

    /**
     * Setup lazy loading for images
     */
    setupLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    /**
     * Setup animation enhancements
     */
    setupAnimationEnhancements() {
        // Animate elements as they enter viewport
        if (this.hasFeature('intersectionObserver')) {
            this.setupScrollAnimations();
        }
        
        // Enhanced loading animations
        this.setupLoadingAnimations();
    }

    /**
     * Setup scroll-triggered animations
     */
    setupScrollAnimations() {
        const animateElements = document.querySelectorAll('[data-animate]');
        
        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const animation = element.dataset.animate;
                    element.classList.add(`animate-${animation}`);
                }
            });
        }, { threshold: 0.1 });

        animateElements.forEach(el => animationObserver.observe(el));
    }

    /**
     * Setup enhanced loading animations
     */
    setupLoadingAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            .animate-fadeInUp {
                animation: fadeInUp 0.6s ease-out;
            }
            
            .animate-slideInLeft {
                animation: slideInLeft 0.6s ease-out;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes slideInLeft {
                from {
                    opacity: 0;
                    transform: translateX(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Setup AJAX form submissions with fallback
     */
    setupAjaxForms() {
        if (!this.hasFeature('fetch')) {
            this.log('Fetch API not supported, forms will use standard submission');
            return;
        }

        // Auto-discover forms to enhance
        document.querySelectorAll('form[data-ajax], .ajax-form').forEach(form => {
            this.enhanceFormWithAjax(form);
        });
        
        // Listen for dynamically added forms
        if (this.hasFeature('mutationObserver')) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) {
                            const forms = node.matches?.('form[data-ajax]') ? [node] : 
                                         node.querySelectorAll?.('form[data-ajax]') || [];
                            
                            forms.forEach(form => this.enhanceFormWithAjax(form));
                        }
                    });
                });
            });
            
            observer.observe(document.body, { childList: true, subtree: true });
        }
    }

    /**
     * Enhance form with AJAX submission
     */
    enhanceFormWithAjax(form) {
        if (this.ajaxForms.has(form)) return; // Already enhanced

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitFormAjax(form);
        });
        
        this.ajaxForms.add(form);
        this.log(`Form enhanced with AJAX: ${form.id || form.action}`);
    }

    /**
     * Submit form via AJAX
     */
    async submitFormAjax(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        const method = form.method || 'POST';
        
        // Show loading state
        this.setFormLoading(form, true);
        
        try {
            const response = await fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            if (response.ok) {
                await this.handleAjaxSuccess(form, response);
            } else {
                await this.handleAjaxError(form, response);
            }
        } catch (error) {
            this.handleAjaxError(form, null, error);
        } finally {
            this.setFormLoading(form, false);
        }
    }

    /**
     * Handle successful AJAX form submission
     */
    async handleAjaxSuccess(form, response) {
        const contentType = response.headers.get('Content-Type') || '';
        
        if (contentType.includes('application/json')) {
            const data = await response.json();
            
            if (data.redirect) {
                window.location.href = data.redirect;
            } else if (data.message) {
                this.showNotification(data.message, 'success');
            }
            
            // Trigger custom event
            form.dispatchEvent(new CustomEvent('ajax:success', { 
                detail: { data, response } 
            }));
        } else {
            // Handle HTML response
            const html = await response.text();
            this.handleHtmlResponse(form, html);
        }
    }

    /**
     * Handle AJAX form submission error
     */
    async handleAjaxError(form, response, error) {
        let message = 'Erro ao enviar formulário. Tente novamente.';
        
        if (response) {
            try {
                const data = await response.json();
                message = data.message || data.error || message;
            } catch {
                message = `Erro ${response.status}: ${response.statusText}`;
            }
        } else if (error) {
            message = error.message;
        }
        
        this.showNotification(message, 'error');
        
        // Trigger custom event
        form.dispatchEvent(new CustomEvent('ajax:error', { 
            detail: { error, response } 
        }));
    }

    /**
     * Handle HTML response from AJAX form
     */
    handleHtmlResponse(form, html) {
        // Create temporary container
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // Look for form replacement or error messages
        const newForm = temp.querySelector('form');
        const errors = temp.querySelectorAll('.alert-danger, .error-message');
        
        if (newForm && errors.length > 0) {
            // Replace form with new version (contains validation errors)
            form.outerHTML = newForm.outerHTML;
        } else if (newForm) {
            // Form was processed successfully, might redirect or show success
            const success = temp.querySelector('.alert-success');
            if (success) {
                this.showNotification(success.textContent.trim(), 'success');
            }
        }
    }

    /**
     * Set form loading state
     */
    setFormLoading(form, loading) {
        if (window.LoadingManager) {
            window.LoadingManager.setFormLoading(form, loading);
        } else {
            // Fallback method
            const buttons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
            buttons.forEach(btn => {
                btn.disabled = loading;
                if (loading) {
                    btn.dataset.originalText = btn.textContent;
                    btn.textContent = 'Enviando...';
                } else {
                    btn.textContent = btn.dataset.originalText || btn.textContent;
                }
            });
        }
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (window.quickActions && typeof window.quickActions.showNotification === 'function') {
            window.quickActions.showNotification(message, type);
        } else {
            // Fallback notification
            alert(message);
        }
    }

    /**
     * Setup smooth scrolling
     */
    setupSmoothScrolling() {
        // Add smooth scrolling behavior
        if (CSS && CSS.supports('scroll-behavior', 'smooth')) {
            document.documentElement.style.scrollBehavior = 'smooth';
        } else {
            // Polyfill for browsers that don't support smooth scrolling
            this.polyfillSmoothScrolling();
        }
        
        // Enhance anchor links
        document.addEventListener('click', (e) => {
            const anchor = e.target.closest('a[href^="#"]');
            if (anchor) {
                this.handleSmoothScroll(e, anchor);
            }
        });
    }

    /**
     * Handle smooth scroll for anchor links
     */
    handleSmoothScroll(e, anchor) {
        const targetId = anchor.getAttribute('href').substring(1);
        const target = document.getElementById(targetId);
        
        if (target) {
            e.preventDefault();
            
            if (this.hasFeature('requestAnimationFrame')) {
                this.smoothScrollTo(target);
            } else {
                target.scrollIntoView();
            }
        }
    }

    /**
     * Smooth scroll to element using requestAnimationFrame
     */
    smoothScrollTo(element) {
        const targetPosition = element.getBoundingClientRect().top + window.pageYOffset;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        const duration = 800;
        let start = null;

        const animation = (currentTime) => {
            if (start === null) start = currentTime;
            const timeElapsed = currentTime - start;
            const run = this.easeInOutQuad(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            
            if (timeElapsed < duration) {
                requestAnimationFrame(animation);
            }
        };

        requestAnimationFrame(animation);
    }

    /**
     * Easing function for smooth animations
     */
    easeInOutQuad(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }

    /**
     * Polyfill smooth scrolling for older browsers
     */
    polyfillSmoothScrolling() {
        // Add CSS for smooth scrolling fallback
        const style = document.createElement('style');
        style.textContent = `
            html {
                scroll-behavior: smooth;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Setup keyboard shortcut management system
     */
    setupKeyboardShortcuts() {
        // Global keyboard shortcut handler
        document.addEventListener('keydown', (e) => {
            const combination = this.getKeyCombination(e);
            const handler = this.keyboardShortcuts.get(combination);
            
            if (handler && this.shouldTriggerShortcut(e)) {
                e.preventDefault();
                handler(e);
            }
        });

        // Register default shortcuts
        this.registerDefaultShortcuts();
        
        // Show shortcut help
        this.setupShortcutHelp();
    }

    /**
     * Get key combination string from event
     */
    getKeyCombination(e) {
        const parts = [];
        
        if (e.ctrlKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        if (e.metaKey) parts.push('meta');
        
        const key = e.key.toLowerCase();
        if (key !== 'control' && key !== 'alt' && key !== 'shift' && key !== 'meta') {
            parts.push(key);
        }
        
        return parts.join('+');
    }

    /**
     * Check if shortcut should be triggered
     */
    shouldTriggerShortcut(e) {
        const activeElement = document.activeElement;
        const isEditing = activeElement.matches('input, textarea, select, [contenteditable]');
        
        // Don't trigger shortcuts when user is editing
        return !isEditing;
    }

    /**
     * Register a keyboard shortcut
     */
    registerShortcut(combination, handler, description = '') {
        this.keyboardShortcuts.set(combination.toLowerCase(), handler);
        
        if (description) {
            // Store description for help system
            if (!this.shortcutDescriptions) {
                this.shortcutDescriptions = new Map();
            }
            this.shortcutDescriptions.set(combination.toLowerCase(), description);
        }
        
        this.log(`Keyboard shortcut registered: ${combination}`);
    }

    /**
     * Register default keyboard shortcuts
     */
    registerDefaultShortcuts() {
        // Navigation shortcuts
        this.registerShortcut('alt+h', () => {
            window.location.href = '/';
        }, 'Ir para home');
        
        this.registerShortcut('alt+d', () => {
            window.location.href = '/etiquetas/';
        }, 'Ir para dashboard');
        
        // Search shortcut
        this.registerShortcut('ctrl+k', () => {
            const search = document.querySelector('input[type="search"], #search');
            if (search) {
                search.focus();
                search.select();
            }
        }, 'Focar no campo de busca');
        
        // Form shortcuts
        this.registerShortcut('ctrl+s', (e) => {
            const form = e.target.closest('form');
            if (form) {
                form.submit();
            }
        }, 'Salvar formulário');
        
        // Modal shortcuts
        this.registerShortcut('escape', () => {
            const modal = document.querySelector('.modal.show');
            const dropdown = document.querySelector('.dropdown.show');
            
            if (modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            } else if (dropdown) {
                dropdown.classList.remove('show');
            }
        }, 'Fechar modal/dropdown');
        
        // Help shortcut
        this.registerShortcut('ctrl+shift+/', () => {
            this.showShortcutHelp();
        }, 'Mostrar atalhos de teclado');
    }

    /**
     * Setup shortcut help system
     */
    setupShortcutHelp() {
        // Add help indicator
        const helpIndicator = document.createElement('div');
        helpIndicator.className = 'keyboard-shortcuts-indicator';
        helpIndicator.innerHTML = `
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="progressiveEnhancement.showShortcutHelp()">
                <i class="bi bi-keyboard"></i> Atalhos
            </button>
        `;
        helpIndicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            opacity: 0.7;
        `;
        
        // Only show if we have shortcuts registered
        if (this.keyboardShortcuts.size > 0) {
            document.body.appendChild(helpIndicator);
        }
    }

    /**
     * Show keyboard shortcut help
     */
    showShortcutHelp() {
        if (!this.shortcutDescriptions || this.shortcutDescriptions.size === 0) {
            return;
        }
        
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-keyboard"></i> Atalhos de Teclado
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="shortcut-list">
                            ${Array.from(this.shortcutDescriptions.entries()).map(([combo, desc]) => `
                                <div class="shortcut-item d-flex justify-content-between align-items-center mb-2">
                                    <span>${desc}</span>
                                    <kbd class="kbd-combo">${combo.replace(/\+/g, ' + ').toUpperCase()}</kbd>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Clean up when hidden
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    /**
     * Graceful degradation handler
     */
    setupGracefulDegradation() {
        // Monitor for JavaScript errors
        window.addEventListener('error', (e) => {
            this.handleJavaScriptError(e);
        });
        
        // Monitor for unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            this.handlePromiseRejection(e);
        });
        
        // Provide fallbacks for failed enhancements
        this.setupFallbacks();
    }

    /**
     * Handle JavaScript errors gracefully
     */
    handleJavaScriptError(e) {
        console.error('JavaScript error:', e.error);
        
        // Remove any broken enhancements
        this.disableEnhancements();
        
        // Show user-friendly message if critical functionality is broken
        if (e.filename && e.filename.includes('ui-interactions')) {
            this.showNotification('Algumas funcionalidades avançadas foram desabilitadas devido a um erro.', 'warning');
        }
    }

    /**
     * Handle promise rejections gracefully
     */
    handlePromiseRejection(e) {
        console.error('Unhandled promise rejection:', e.reason);
        
        // Don't let promise rejections break the page
        e.preventDefault();
    }

    /**
     * Disable enhancements if they're causing problems
     */
    disableEnhancements() {
        this.isEnabled = false;
        document.documentElement.classList.add('js-fallback');
        
        // Remove problematic event listeners
        // This is a simplified approach - in a real app you'd track listeners
        this.log('Progressive enhancements disabled due to errors');
    }

    /**
     * Setup fallbacks for essential functionality
     */
    setupFallbacks() {
        // Ensure forms still work without AJAX
        document.querySelectorAll('form').forEach(form => {
            if (!form.hasAttribute('action')) {
                form.setAttribute('action', window.location.href);
            }
            
            if (!form.hasAttribute('method')) {
                form.setAttribute('method', 'post');
            }
        });
        
        // Ensure links work without JavaScript
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            if (!link.hasAttribute('href') || link.getAttribute('href') === '#') {
                link.setAttribute('href', 'javascript:void(0)');
            }
        });
    }

    /**
     * Debug logging
     */
    log(message, ...args) {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log(`[ProgressiveEnhancement] ${message}`, ...args);
        }
    }

    /**
     * Destroy and clean up
     */
    destroy() {
        this.keyboardShortcuts.clear();
        this.ajaxForms.clear();
        this.features.clear();
        
        // Remove added classes
        document.documentElement.classList.remove('js-enabled');
        
        this.log('Progressive Enhancement Manager destroyed');
    }
}

// ===================================
// AUTO-INITIALIZATION
// ===================================

let progressiveEnhancement;

function initializeProgressiveEnhancement() {
    if (progressiveEnhancement) return;
    
    progressiveEnhancement = new ProgressiveEnhancementManager();
    window.progressiveEnhancement = progressiveEnhancement;
    
    console.log('🚀 Progressive Enhancement Layer activated successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeProgressiveEnhancement);
} else {
    initializeProgressiveEnhancement();
}

// Public API for registering shortcuts
window.registerKeyboardShortcut = function(combination, handler, description) {
    if (progressiveEnhancement) {
        progressiveEnhancement.registerShortcut(combination, handler, description);
    }
};

// Public API for AJAX form enhancement
window.enhanceFormWithAjax = function(formSelector) {
    if (progressiveEnhancement) {
        const form = typeof formSelector === 'string' ? 
                    document.querySelector(formSelector) : formSelector;
        if (form) {
            progressiveEnhancement.enhanceFormWithAjax(form);
        }
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LoadingManager, ProgressBar, SkeletonLoader, QuickActionsManager, ProgressiveEnhancementManager };
}