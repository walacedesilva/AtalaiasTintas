/**
 * Form Helpers - State Preservation & Management
 * 
 * Feature: 3-modern-web-interface
 * Task: T013 - Implement Form State Preservation
 * 
 * This module provides client-side form state management with auto-save,
 * restoration, and unsaved changes tracking for the Tintas System.
 */

'use strict';

// ===================================
// FORM STATE MANAGER
// ===================================

class FormStateManager {
    constructor(options = {}) {
        this.options = {
            autoSaveInterval: 30000, // 30 seconds
            storagePrefix: 'tintas_form_',
            excludeFields: ['password', 'csrf_token', 'csrfmiddlewaretoken'],
            showUnsavedIndicator: true,
            confirmBeforeLeave: true,
            debugMode: false,
            ...options
        };

        this.trackedForms = new Map();
        this.autoSaveTimers = new Map();
        this.unsavedForms = new Set();
        this.isInitialized = false;

        this.init();
    }

    init() {
        if (this.isInitialized) return;

        this.bindEvents();
        this.discoverForms();
        this.restoreFormStates();
        this.createUnsavedIndicator();
        
        this.isInitialized = true;
        this.log('FormStateManager initialized successfully');
    }

    /**
     * Bind global event handlers
     */
    bindEvents() {
        // Handle page unload
        window.addEventListener('beforeunload', (e) => this.handleBeforeUnload(e));
        
        // Handle successful form submissions
        document.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Handle navigation
        window.addEventListener('pagehide', () => this.saveAllFormStates());
        
        // Handle visibility changes (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.saveAllFormStates();
            }
        });

        // Clean up old storage periodically
        this.startStorageCleanup();
    }

    /**
     * Automatically discover and register forms on the page
     */
    discoverForms() {
        const forms = document.querySelectorAll('form[data-preserve-state], .form-preserve-state, form.preserve-state');
        
        forms.forEach(form => {
            if (!form.id) {
                form.id = this.generateFormId(form);
            }
            this.registerForm(form.id);
        });

        // Also register forms with specific classes or data attributes
        document.querySelectorAll('form').forEach(form => {
            if (this.shouldTrackForm(form)) {
                if (!form.id) {
                    form.id = this.generateFormId(form);
                }
                this.registerForm(form.id);
            }
        });
    }

    /**
     * Determine if a form should be automatically tracked
     */
    shouldTrackForm(form) {
        // Skip forms with data-no-preserve attribute
        if (form.hasAttribute('data-no-preserve')) return false;
        
        // Skip login/password forms
        if (form.classList.contains('login-form') || form.querySelector('input[type="password"]')) return false;
        
        // Skip search forms
        if (form.classList.contains('search-form') || form.querySelector('input[type="search"]')) return false;
        
        // Track forms with specific characteristics
        const hasTextInputs = form.querySelector('input[type="text"], textarea, select');
        const isLongForm = form.querySelectorAll('input, textarea, select').length > 3;
        
        return hasTextInputs && isLongForm;
    }

    /**
     * Generate unique ID for forms without IDs
     */
    generateFormId(form) {
        const action = form.action || window.location.pathname;
        const hash = this.simpleHash(action + form.outerHTML.substring(0, 200));
        return `auto_form_${hash}`;
    }

    /**
     * Simple hash function for generating IDs
     */
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(36);
    }

    /**
     * Register a form for state preservation
     */
    registerForm(formId, options = {}) {
        const form = document.getElementById(formId);
        if (!form) {
            console.warn(`Form with ID "${formId}" not found`);
            return false;
        }

        const formOptions = {
            autoSave: true,
            showIndicator: true,
            confirmLeave: true,
            ...options
        };

        this.trackedForms.set(formId, {
            element: form,
            options: formOptions,
            lastSaved: null,
            originalState: null
        });

        this.bindFormEvents(form);
        this.startAutoSave(formId);
        
        // Store original state for comparison
        this.trackedForms.get(formId).originalState = this.getFormState(form);
        
        this.log(`Form "${formId}" registered for state preservation`);
        return true;
    }

    /**
     * Bind events to a specific form
     */
    bindFormEvents(form) {
        // Track changes
        form.addEventListener('input', () => this.handleFormChange(form));
        form.addEventListener('change', () => this.handleFormChange(form));
        
        // Handle paste events
        form.addEventListener('paste', () => {
            setTimeout(() => this.handleFormChange(form), 100);
        });

        // Add unsaved indicator when form becomes dirty
        form.addEventListener('input', () => this.updateUnsavedIndicator(form), { once: false });
    }

    /**
     * Handle form changes
     */
    handleFormChange(form) {
        const formId = form.id;
        const formData = this.trackedForms.get(formId);
        
        if (!formData) return;

        // Mark form as having unsaved changes
        this.markFormAsUnsaved(formId);
        
        // Update form state in memory
        const currentState = this.getFormState(form);
        formData.currentState = currentState;
        
        // Show unsaved indicator
        if (formData.options.showIndicator) {
            this.showUnsavedIndicator(form);
        }

        this.log(`Form "${formId}" changed`);
    }

    /**
     * Get the current state of a form
     */
    getFormState(form) {
        const formData = new FormData(form);
        const state = {};
        
        // Include all form fields except excluded ones
        for (const [name, value] of formData.entries()) {
            if (!this.options.excludeFields.includes(name)) {
                // Handle multiple values (checkboxes, multi-select)
                if (state[name]) {
                    if (Array.isArray(state[name])) {
                        state[name].push(value);
                    } else {
                        state[name] = [state[name], value];
                    }
                } else {
                    state[name] = value;
                }
            }
        }

        // Include unchecked checkboxes and radio buttons
        const uncheckedInputs = form.querySelectorAll('input[type="checkbox"]:not(:checked), input[type="radio"]:not(:checked)');
        uncheckedInputs.forEach(input => {
            if (!this.options.excludeFields.includes(input.name) && !state.hasOwnProperty(input.name)) {
                state[input.name] = '';
            }
        });

        return {
            data: state,
            timestamp: Date.now(),
            url: window.location.href,
            formAction: form.action || window.location.href
        };
    }

    /**
     * Save form state to localStorage
     */
    saveFormState(formId) {
        const formData = this.trackedForms.get(formId);
        if (!formData) return false;

        try {
            const state = this.getFormState(formData.element);
            const storageKey = this.options.storagePrefix + formId;
            
            localStorage.setItem(storageKey, JSON.stringify(state));
            formData.lastSaved = Date.now();
            
            this.log(`Form "${formId}" state saved to localStorage`);
            return true;
        } catch (error) {
            console.error('Failed to save form state:', error);
            return false;
        }
    }

    /**
     * Restore form state from localStorage
     */
    restoreFormState(formId) {
        const formData = this.trackedForms.get(formId);
        if (!formData) return false;

        try {
            const storageKey = this.options.storagePrefix + formId;
            const savedState = localStorage.getItem(storageKey);
            
            if (!savedState) return false;

            const state = JSON.parse(savedState);
            
            // Check if state is recent (within 1 hour by default)
            const maxAge = 60 * 60 * 1000; // 1 hour
            if (Date.now() - state.timestamp > maxAge) {
                this.clearFormState(formId);
                return false;
            }

            // Check if we're on the same page/form
            if (state.url !== window.location.href && state.formAction !== formData.element.action) {
                return false;
            }

            this.applyFormState(formData.element, state.data);
            this.showRestoreNotification(formId, state.timestamp);
            
            this.log(`Form "${formId}" state restored from localStorage`);
            return true;
        } catch (error) {
            console.error('Failed to restore form state:', error);
            return false;
        }
    }

    /**
     * Apply saved state data to form elements
     */
    applyFormState(form, stateData) {
        Object.entries(stateData).forEach(([name, value]) => {
            const elements = form.querySelectorAll(`[name="${name}"]`);
            
            elements.forEach(element => {
                if (element.type === 'checkbox' || element.type === 'radio') {
                    if (Array.isArray(value)) {
                        element.checked = value.includes(element.value);
                    } else {
                        element.checked = element.value === value || value === 'on';
                    }
                } else if (element.type === 'select-multiple') {
                    const values = Array.isArray(value) ? value : [value];
                    Array.from(element.options).forEach(option => {
                        option.selected = values.includes(option.value);
                    });
                } else {
                    element.value = Array.isArray(value) ? value[0] : value;
                }

                // Trigger change event to update any dependent UI
                element.dispatchEvent(new Event('change', { bubbles: true }));
            });
        });
    }

    /**
     * Start auto-save timer for a form
     */
    startAutoSave(formId) {
        if (this.autoSaveTimers.has(formId)) {
            clearInterval(this.autoSaveTimers.get(formId));
        }

        const timer = setInterval(() => {
            if (this.unsavedForms.has(formId)) {
                this.saveFormState(formId);
            }
        }, this.options.autoSaveInterval);

        this.autoSaveTimers.set(formId, timer);
    }

    /**
     * Mark form as having unsaved changes
     */
    markFormAsUnsaved(formId) {
        this.unsavedForms.add(formId);
        this.updateGlobalUnsavedIndicator();
    }

    /**
     * Mark form as saved/clean
     */
    markFormAsSaved(formId) {
        this.unsavedForms.delete(formId);
        const formData = this.trackedForms.get(formId);
        if (formData) {
            this.hideUnsavedIndicator(formData.element);
        }
        this.updateGlobalUnsavedIndicator();
    }

    /**
     * Check if form has unsaved changes compared to original state
     */
    hasUnsavedChanges(formId) {
        const formData = this.trackedForms.get(formId);
        if (!formData) return false;

        const currentState = this.getFormState(formData.element);
        const originalState = formData.originalState;

        return JSON.stringify(currentState.data) !== JSON.stringify(originalState.data);
    }

    /**
     * Handle page unload
     */
    handleBeforeUnload(event) {
        if (this.unsavedForms.size > 0 && this.options.confirmBeforeLeave) {
            const message = 'Você tem alterações não salvas. Deseja realmente sair da página?';
            event.preventDefault();
            event.returnValue = message;
            return message;
        }
    }

    /**
     * Handle form submission
     */
    handleFormSubmit(event) {
        const form = event.target;
        const formId = form.id;
        
        if (this.trackedForms.has(formId)) {
            // Clean up saved state on successful submission
            setTimeout(() => {
                this.clearFormState(formId);
                this.markFormAsSaved(formId);
            }, 1000);
        }
    }

    /**
     * Save all tracked form states
     */
    saveAllFormStates() {
        this.trackedForms.forEach((formData, formId) => {
            if (this.unsavedForms.has(formId)) {
                this.saveFormState(formId);
            }
        });
    }

    /**
     * Restore states for all tracked forms
     */
    restoreFormStates() {
        this.trackedForms.forEach((formData, formId) => {
            this.restoreFormState(formId);
        });
    }

    /**
     * Clear saved state for a form
     */
    clearFormState(formId) {
        try {
            const storageKey = this.options.storagePrefix + formId;
            localStorage.removeItem(storageKey);
            this.markFormAsSaved(formId);
            
            this.log(`Form "${formId}" state cleared from localStorage`);
        } catch (error) {
            console.error('Failed to clear form state:', error);
        }
    }

    /**
     * Create global unsaved changes indicator
     */
    createUnsavedIndicator() {
        if (!this.options.showUnsavedIndicator) return;

        // Create global indicator
        const indicator = document.createElement('div');
        indicator.id = 'unsaved-changes-indicator';
        indicator.className = 'unsaved-changes-indicator';
        indicator.innerHTML = `
            <div class="indicator-content">
                <i class="bi bi-exclamation-triangle"></i>
                <span>Alterações não salvas</span>
                <button type="button" class="btn-close" onclick="formStateManager.hideGlobalIndicator()"></button>
            </div>
        `;
        indicator.style.display = 'none';
        
        document.body.appendChild(indicator);
    }

    /**
     * Show unsaved indicator on specific form
     */
    showUnsavedIndicator(form) {
        let indicator = form.querySelector('.form-unsaved-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'form-unsaved-indicator';
            indicator.innerHTML = `
                <i class="bi bi-circle-fill"></i>
                <span>Alterações não salvas</span>
            `;
            
            // Insert at the top of the form
            form.insertBefore(indicator, form.firstChild);
        }
        
        indicator.style.display = 'flex';
    }

    /**
     * Hide unsaved indicator on specific form
     */
    hideUnsavedIndicator(form) {
        const indicator = form.querySelector('.form-unsaved-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Update global unsaved changes indicator
     */
    updateGlobalUnsavedIndicator() {
        const globalIndicator = document.getElementById('unsaved-changes-indicator');
        if (!globalIndicator) return;

        if (this.unsavedForms.size > 0) {
            globalIndicator.style.display = 'block';
            const span = globalIndicator.querySelector('span');
            if (span) {
                const count = this.unsavedForms.size;
                span.textContent = count === 1 ? 'Alterações não salvas' : `${count} formulários com alterações`;
            }
        } else {
            globalIndicator.style.display = 'none';
        }
    }

    /**
     * Hide global indicator (called from UI)
     */
    hideGlobalIndicator() {
        const globalIndicator = document.getElementById('unsaved-changes-indicator');
        if (globalIndicator) {
            globalIndicator.style.display = 'none';
        }
    }

    /**
     * Show restore notification
     */
    showRestoreNotification(formId, timestamp) {
        const timeAgo = this.formatTimeAgo(timestamp);
        
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show restore-notification';
        notification.innerHTML = `
            <i class="bi bi-info-circle"></i>
            Dados do formulário restaurados (salvos ${timeAgo})
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Find the form and insert notification before it
        const form = document.getElementById(formId);
        if (form) {
            form.parentNode.insertBefore(notification, form);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
        }
    }

    /**
     * Format timestamp as "time ago"
     */
    formatTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        
        if (minutes < 1) return 'há poucos segundos';
        if (minutes < 60) return `há ${minutes} minuto${minutes > 1 ? 's' : ''}`;
        if (hours < 24) return `há ${hours} hora${hours > 1 ? 's' : ''}`;
        
        return new Date(timestamp).toLocaleDateString('pt-BR');
    }

    /**
     * Start periodic cleanup of old stored data
     */
    startStorageCleanup() {
        // Clean up every 5 minutes
        setInterval(() => {
            this.cleanupOldStorage();
        }, 5 * 60 * 1000);
        
        // Also run cleanup on initialization
        setTimeout(() => this.cleanupOldStorage(), 1000);
    }

    /**
     * Clean up old form state data from localStorage
     */
    cleanupOldStorage() {
        try {
            const maxAge = 24 * 60 * 60 * 1000; // 24 hours
            const now = Date.now();
            
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith(this.options.storagePrefix)) {
                    try {
                        const data = JSON.parse(localStorage.getItem(key));
                        if (data && data.timestamp && (now - data.timestamp > maxAge)) {
                            localStorage.removeItem(key);
                            this.log(`Cleaned up old form state: ${key}`);
                        }
                    } catch (error) {
                        // Remove invalid data
                        localStorage.removeItem(key);
                    }
                }
            });
        } catch (error) {
            console.error('Failed to cleanup old storage:', error);
        }
    }

    /**
     * Get storage usage statistics
     */
    getStorageStats() {
        let count = 0;
        let totalSize = 0;
        
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(this.options.storagePrefix)) {
                count++;
                totalSize += localStorage.getItem(key).length;
            }
        });
        
        return {
            storedForms: count,
            totalSize: totalSize,
            formattedSize: this.formatBytes(totalSize)
        };
    }

    /**
     * Format bytes for display
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Debug logging
     */
    log(message) {
        if (this.options.debugMode) {
            console.log(`[FormStateManager] ${message}`);
        }
    }

    /**
     * Destroy the manager and clean up resources
     */
    destroy() {
        // Clear all auto-save timers
        this.autoSaveTimers.forEach(timer => clearInterval(timer));
        this.autoSaveTimers.clear();
        
        // Remove event listeners (this is simplified - in real implementation you'd track listeners)
        window.removeEventListener('beforeunload', this.handleBeforeUnload);
        
        // Clear data structures
        this.trackedForms.clear();
        this.unsavedForms.clear();
        
        this.isInitialized = false;
        this.log('FormStateManager destroyed');
    }
}

// ===================================
// AUTO-INITIALIZATION & GLOBAL ACCESS
// ===================================

let formStateManager;

// Initialize when DOM is ready
function initializeFormStateManager() {
    // Check if already initialized
    if (formStateManager) return;
    
    // Create global instance
    formStateManager = new FormStateManager({
        debugMode: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    });
    
    // Make globally available
    window.formStateManager = formStateManager;
    
    console.log('📝 Form State Manager initialized successfully');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeFormStateManager);
} else {
    initializeFormStateManager();
}

// ===================================
// PUBLIC API FUNCTIONS
// ===================================

/**
 * Register a form for state preservation
 * @param {string} formId - The ID of the form
 * @param {Object} options - Configuration options
 */
window.registerFormStatePreservation = function(formId, options = {}) {
    if (formStateManager) {
        return formStateManager.registerForm(formId, options);
    }
    console.warn('FormStateManager not initialized');
    return false;
};

/**
 * Save form state manually
 * @param {string} formId - The ID of the form
 */
window.saveFormState = function(formId) {
    if (formStateManager) {
        return formStateManager.saveFormState(formId);
    }
    return false;
};

/**
 * Clear saved form state
 * @param {string} formId - The ID of the form
 */
window.clearFormState = function(formId) {
    if (formStateManager) {
        formStateManager.clearFormState(formId);
    }
};

/**
 * Check if form has unsaved changes
 * @param {string} formId - The ID of the form
 */
window.hasUnsavedChanges = function(formId) {
    if (formStateManager) {
        return formStateManager.hasUnsavedChanges(formId);
    }
    return false;
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FormStateManager };
}