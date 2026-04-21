/**
 * ===================================
 * ACCESSIBILITY NAVIGATION SYSTEM
 * Feature: 3-modern-web-interface
 * Task: T017 - Keyboard Navigation System
 * Task: T018 - ARIA Labels and Semantics  
 * ===================================
 * 
 * Comprehensive keyboard navigation and accessibility support
 * WCAG 2.1 AA compliant keyboard interaction patterns
 * ARIA labeling and semantic enhancement system
 */

class AccessibilityManager {
    constructor() {
        // Keyboard Navigation properties
        this.focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'textarea:not([disabled])',
            'select:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]',
            'audio[controls]',
            'video[controls]',
            'iframe',
            'object',
            'embed',
            'area[href]',
            'summary'
        ].join(', ');

        this.focusTraps = new Map();
        this.skipLinks = [];
        this.keyboardShortcuts = new Map();
        this.roving = new Map();
        this.lastFocusedElement = null;
        this.isTrappingFocus = false;
        
        // ARIA Management properties
        this.ariaLiveRegions = new Map();
        this.dynamicAriaStates = new Map();
        this.ariaDescriptions = new Map();
        this.componentRoles = new Map();
        this.interactionStates = new Map();
        
        this.init();
    }

    /**
     * Initialize accessibility system
     */
    init() {
        this.setupSkipLinks();
        this.setupTabOrderManagement();
        this.setupFocusTraps();
        this.setupKeyboardShortcuts();
        this.setupRovingTabindex();
        this.setupFocusManagement();
        this.setupModalAccessibility();
        this.setupFormAccessibility();
        this.setupEscapeHandling();
        
        // ARIA Features
        this.setupAriaLiveRegions();
        this.setupAriaLabeling();
        this.setupAriaStates();
        this.setupSemanticEnhancements();
        this.setupDynamicAriaUpdates();
        
        this.log('Accessibility Manager initialized with ARIA support');
    }

    /**
     * Create and manage skip links for main content areas
     */
    setupSkipLinks() {
        // Remove existing skip links to avoid duplicates
        document.querySelectorAll('.skip-link').forEach(link => link.remove());

        const skipLinksContainer = document.createElement('div');
        skipLinksContainer.className = 'skip-links';
        skipLinksContainer.setAttribute('aria-label', 'Links de navegação rápida');

        const skipLinks = [
            {
                href: '#main-content',
                text: 'Pular para o conteúdo principal',
                key: '1'
            },
            {
                href: '#navigation',
                text: 'Pular para a navegação',
                key: '2'
            },
            {
                href: '#search',
                text: 'Pular para a busca',
                key: '3'
            },
            {
                href: '#quick-actions',
                text: 'Pular para ações rápidas',
                key: '4'
            }
        ];

        skipLinks.forEach((linkInfo, index) => {
            const target = document.querySelector(linkInfo.href);
            if (target) {
                const link = document.createElement('a');
                link.href = linkInfo.href;
                link.textContent = linkInfo.text;
                link.className = 'skip-link';
                link.setAttribute('accesskey', linkInfo.key);
                link.setAttribute('tabindex', '0');
                
                // Enhanced skip link behavior
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.skipToContent(target, linkInfo.text);
                });

                skipLinksContainer.appendChild(link);
                this.skipLinks.push(link);
            }
        });

        // Insert skip links at the very beginning of the body
        document.body.insertBefore(skipLinksContainer, document.body.firstChild);
    }

    /**
     * Skip to specific content area with announcement
     */
    skipToContent(target, description) {
        // Ensure target is focusable
        if (!target.hasAttribute('tabindex')) {
            target.setAttribute('tabindex', '-1');
        }

        // Focus the target
        target.focus();

        // Announce the skip action to screen readers
        this.announceToScreenReader(`Navegou para: ${description}`);

        // Remove tabindex after focus if it wasn't originally present
        setTimeout(() => {
            if (target.getAttribute('tabindex') === '-1') {
                target.removeAttribute('tabindex');
            }
        }, 100);
    }

    /**
     * Manage logical tab order for all interactive elements
     */
    setupTabOrderManagement() {
        // Ensure proper tab order by checking and fixing tabindex values
        this.auditTabOrder();

        // Monitor for dynamically added elements
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) { // Element node
                            this.processNewElement(node);
                        }
                    });
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    /**
     * Audit and fix tab order issues
     */
    auditTabOrder() {
        const focusableElements = document.querySelectorAll(this.focusableSelectors);
        const issues = [];

        focusableElements.forEach((element, index) => {
            // Check for logical tab order
            const tabIndex = parseInt(element.getAttribute('tabindex')) || 0;
            
            // Warn about positive tabindex values (not recommended)
            if (tabIndex > 0) {
                issues.push({
                    element,
                    issue: 'positive-tabindex',
                    message: 'Positive tabindex detected - consider using 0 or -1'
                });
            }

            // Ensure focusable elements have visible focus indicators
            if (!this.hasFocusStyles(element)) {
                issues.push({
                    element,
                    issue: 'missing-focus-styles',
                    message: 'Element may be missing focus styles'
                });
            }
        });

        if (issues.length > 0 && this.isDevelopment()) {
            console.warn('Tab order issues detected:', issues);
        }

        return issues;
    }

    /**
     * Process newly added elements for accessibility
     */
    processNewElement(element) {
        // Find all focusable elements within the new element
        const focusableElements = element.matches?.(this.focusableSelectors) ? 
                                  [element] : 
                                  Array.from(element.querySelectorAll?.(this.focusableSelectors) || []);

        focusableElements.forEach(el => {
            this.enhanceElementAccessibility(el);
        });

        // Check if it's a modal or dialog
        if (element.matches?.('.modal, .dialog, [role="dialog"]')) {
            this.setupModalFocusTrap(element);
        }
    }

    /**
     * Enhance individual element accessibility
     */
    enhanceElementAccessibility(element) {
        // Ensure buttons have proper attributes
        if (element.matches('button, [role="button"]')) {
            if (!element.hasAttribute('type') && element.tagName === 'BUTTON') {
                element.setAttribute('type', 'button');
            }
        }

        // Ensure links have proper attributes
        if (element.matches('a')) {
            if (!element.getAttribute('href') || element.getAttribute('href') === '#') {
                element.setAttribute('role', 'button');
                element.setAttribute('tabindex', '0');
            }
        }

        // Ensure form controls have labels
        if (element.matches('input, textarea, select')) {
            this.ensureFormControlLabel(element);
        }
    }

    /**
     * Setup focus trap management for modal dialogs
     */
    setupFocusTraps() {
        // Listen for modal events
        document.addEventListener('shown.bs.modal', (e) => {
            this.trapFocus(e.target);
        });

        document.addEventListener('hidden.bs.modal', (e) => {
            this.releaseFocusTrap(e.target);
        });

        // Generic focus trap setup for any element with data-focus-trap
        document.querySelectorAll('[data-focus-trap]').forEach(element => {
            this.setupModalFocusTrap(element);
        });
    }

    /**
     * Create focus trap for specific modal
     */
    trapFocus(modal) {
        const focusableElements = modal.querySelectorAll(this.focusableSelectors);
        
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        // Store the element that was focused before opening the modal
        this.lastFocusedElement = document.activeElement;
        this.isTrappingFocus = true;

        // Focus the first element
        setTimeout(() => {
            firstElement.focus();
        }, 100);

        const trapHandler = (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        };

        modal.addEventListener('keydown', trapHandler);
        
        // Store trap info for later cleanup
        this.focusTraps.set(modal, {
            handler: trapHandler,
            firstElement,
            lastElement,
            previousFocus: this.lastFocusedElement
        });
    }

    /**
     * Release focus trap for modal
     */
    releaseFocusTrap(modal) {
        const trapInfo = this.focusTraps.get(modal);
        
        if (trapInfo) {
            modal.removeEventListener('keydown', trapInfo.handler);
            
            // Return focus to previous element
            if (trapInfo.previousFocus && trapInfo.previousFocus.focus) {
                try {
                    trapInfo.previousFocus.focus();
                } catch (e) {
                    // Element may no longer be in DOM
                    document.body.focus();
                }
            }
            
            this.focusTraps.delete(modal);
            this.isTrappingFocus = false;
        }
    }

    /**
     * Setup modal-specific focus trap
     */
    setupModalFocusTrap(modal) {
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.handleTabInModal(e, modal);
            }
        });
    }

    /**
     * Handle Tab key in modal context
     */
    handleTabInModal(e, modal) {
        const focusableElements = Array.from(modal.querySelectorAll(this.focusableSelectors))
            .filter(el => this.isElementVisible(el) && !el.disabled);

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        const currentElement = document.activeElement;

        if (e.shiftKey) {
            // Shift + Tab
            if (currentElement === firstElement || !modal.contains(currentElement)) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            // Tab
            if (currentElement === lastElement || !modal.contains(currentElement)) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }

    /**
     * Setup keyboard shortcuts for frequent actions
     */
    setupKeyboardShortcuts() {
        const shortcuts = [
            // Navigation shortcuts
            { key: 'h', alt: true, action: () => this.navigateToHome(), description: 'Ir para a página inicial' },
            { key: 'd', alt: true, action: () => this.navigateToDashboard(), description: 'Ir para o dashboard' },
            { key: 'n', alt: true, action: () => this.navigateToNew(), description: 'Criar novo item' },
            
            // Search shortcuts
            { key: 'k', ctrl: true, action: () => this.focusSearch(), description: 'Focar no campo de busca' },
            { key: 'f', alt: true, action: () => this.focusSearch(), description: 'Focar no campo de busca' },
            
            // Action shortcuts
            { key: 's', ctrl: true, action: (e) => this.saveForm(e), description: 'Salvar formulário atual' },
            { key: 'Enter', ctrl: true, action: (e) => this.saveForm(e), description: 'Salvar formulário atual' },
            
            // Quick actions
            { key: 'q', alt: true, action: () => this.openQuickActions(), description: 'Abrir ações rápidas' },
            { key: '1', alt: true, action: () => this.triggerQuickAction(1), description: 'Ação rápida 1' },
            { key: '2', alt: true, action: () => this.triggerQuickAction(2), description: 'Ação rápida 2' },
            { key: '3', alt: true, action: () => this.triggerQuickAction(3), description: 'Ação rápida 3' },
            { key: '4', alt: true, action: () => this.triggerQuickAction(4), description: 'Ação rápida 4' },
            
            // Modal shortcuts
            { key: 'Escape', action: () => this.closeModal(), description: 'Fechar modal/dropdown' },
            
            // Help
            { key: '?', shift: true, action: () => this.showKeyboardHelp(), description: 'Mostrar atalhos de teclado' },
            { key: 'F1', action: (e) => this.showKeyboardHelp(e), description: 'Mostrar ajuda' }
        ];

        shortcuts.forEach(shortcut => {
            this.registerKeyboardShortcut(shortcut);
        });

        // Global keydown listener
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeydown(e);
        });
    }

    /**
     * Register a keyboard shortcut
     */
    registerKeyboardShortcut(shortcut) {
        const key = this.generateShortcutKey(shortcut);
        this.keyboardShortcuts.set(key, shortcut);
    }

    /**
     * Generate unique key for shortcut combination
     */
    generateShortcutKey(shortcut) {
        const parts = [];
        if (shortcut.ctrl) parts.push('ctrl');
        if (shortcut.alt) parts.push('alt');
        if (shortcut.shift) parts.push('shift');
        if (shortcut.meta) parts.push('meta');
        parts.push(shortcut.key.toLowerCase());
        return parts.join('+');
    }

    /**
     * Handle global keydown events
     */
    handleGlobalKeydown(e) {
        // Don't interfere with text input
        if (this.isInTextInput(e.target)) {
            // Only handle Ctrl+S and Escape in text inputs
            if ((e.key === 's' && e.ctrlKey) || e.key === 'Escape') {
                // Allow these specific shortcuts
            } else {
                return;
            }
        }

        const shortcutKey = this.generateShortcutKey({
            key: e.key,
            ctrl: e.ctrlKey,
            alt: e.altKey,
            shift: e.shiftKey,
            meta: e.metaKey
        });

        const shortcut = this.keyboardShortcuts.get(shortcutKey);
        
        if (shortcut) {
            e.preventDefault();
            try {
                shortcut.action(e);
                this.announceShortcut(shortcut.description);
            } catch (error) {
                console.warn('Keyboard shortcut error:', error);
            }
        }
    }

    /**
     * Check if element is a text input
     */
    isInTextInput(element) {
        const textInputs = ['input', 'textarea', 'select'];
        const editableElements = element.matches?.('[contenteditable="true"]');
        
        return textInputs.includes(element.tagName.toLowerCase()) || editableElements;
    }

    /**
     * Setup roving tabindex for component groups
     */
    setupRovingTabindex() {
        // Setup for toolbar groups
        document.querySelectorAll('[role="toolbar"], .btn-toolbar').forEach(toolbar => {
            this.setupRovingTabindexGroup(toolbar, 'button, [role="button"]');
        });

        // Setup for tab lists
        document.querySelectorAll('[role="tablist"]').forEach(tablist => {
            this.setupRovingTabindexGroup(tablist, '[role="tab"]');
        });

        // Setup for menu bars
        document.querySelectorAll('[role="menubar"]').forEach(menubar => {
            this.setupRovingTabindexGroup(menubar, '[role="menuitem"]');
        });
    }

    /**
     * Setup roving tabindex for a specific group
     */
    setupRovingTabindexGroup(container, selector) {
        const items = Array.from(container.querySelectorAll(selector));
        
        if (items.length === 0) return;

        // Set initial tabindex values
        items.forEach((item, index) => {
            item.setAttribute('tabindex', index === 0 ? '0' : '-1');
        });

        // Add keyboard navigation
        container.addEventListener('keydown', (e) => {
            this.handleRovingTabindex(e, items);
        });

        // Store roving group info
        this.roving.set(container, { items, selector });
    }

    /**
     * Handle roving tabindex navigation
     */
    handleRovingTabindex(e, items) {
        const currentIndex = items.findIndex(item => item === document.activeElement);
        
        if (currentIndex === -1) return;

        let newIndex = currentIndex;

        switch (e.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                break;
            case 'Home':
                newIndex = 0;
                break;
            case 'End':
                newIndex = items.length - 1;
                break;
            default:
                return;
        }

        if (newIndex !== currentIndex) {
            e.preventDefault();
            
            // Update tabindex values
            items[currentIndex].setAttribute('tabindex', '-1');
            items[newIndex].setAttribute('tabindex', '0');
            
            // Focus new item
            items[newIndex].focus();
        }
    }

    /**
     * Setup general focus management
     */
    setupFocusManagement() {
        // Track focus for debugging
        document.addEventListener('focusin', (e) => {
            if (this.isDevelopment()) {
                console.debug('Focus:', e.target);
            }
        });

        // Handle focus loss
        document.addEventListener('focusout', (e) => {
            // Prevent focus loss from the page
            setTimeout(() => {
                if (!document.activeElement || document.activeElement === document.body) {
                    // Focus went nowhere, return to a safe element
                    this.focusSafeElement();
                }
            }, 0);
        });

        // Handle clicks that might break keyboard navigation
        document.addEventListener('click', (e) => {
            // If clicking a non-focusable element, don't steal focus
            if (!e.target.matches(this.focusableSelectors)) {
                e.preventDefault();
            }
        });
    }

    /**
     * Focus a safe element when focus is lost
     */
    focusSafeElement() {
        // Try to focus the first skip link, then the main content, then body
        const safeElements = [
            document.querySelector('.skip-link'),
            document.querySelector('#main-content'),
            document.querySelector('main'),
            document.body
        ];

        for (const element of safeElements) {
            if (element) {
                try {
                    element.focus();
                    break;
                } catch (e) {
                    continue;
                }
            }
        }
    }

    /**
     * Setup modal accessibility features
     */
    setupModalAccessibility() {
        // Ensure modals have proper ARIA attributes
        document.querySelectorAll('.modal').forEach(modal => {
            if (!modal.getAttribute('role')) {
                modal.setAttribute('role', 'dialog');
            }
            if (!modal.getAttribute('aria-modal')) {
                modal.setAttribute('aria-modal', 'true');
            }
            if (!modal.getAttribute('aria-labelledby') && !modal.getAttribute('aria-label')) {
                const title = modal.querySelector('.modal-title');
                if (title) {
                    const id = title.id || `modal-title-${Date.now()}`;
                    title.id = id;
                    modal.setAttribute('aria-labelledby', id);
                }
            }
        });
    }

    /**
     * Setup form accessibility features
     */
    setupFormAccessibility() {
        // Ensure form controls have proper labels
        document.querySelectorAll('input, textarea, select').forEach(control => {
            this.ensureFormControlLabel(control);
        });

        // Setup fieldset/legend relationships
        document.querySelectorAll('fieldset').forEach(fieldset => {
            if (!fieldset.querySelector('legend')) {
                console.warn('Fieldset without legend detected:', fieldset);
            }
        });

        // Setup error message associations
        document.querySelectorAll('.invalid-feedback, .error-message').forEach(error => {
            const control = error.parentElement?.querySelector('input, textarea, select');
            if (control && !control.getAttribute('aria-describedby')) {
                const id = error.id || `error-${Date.now()}`;
                error.id = id;
                control.setAttribute('aria-describedby', id);
            }
        });
    }

    /**
     * Ensure form control has proper label
     */
    ensureFormControlLabel(control) {
        const id = control.id;
        const name = control.name;
        
        // Check for explicit label
        let label = id ? document.querySelector(`label[for="${id}"]`) : null;
        
        // Check for implicit label (control inside label)
        if (!label) {
            label = control.closest('label');
        }
        
        // Check for aria-label or aria-labelledby
        const hasAriaLabel = control.getAttribute('aria-label') || control.getAttribute('aria-labelledby');
        
        if (!label && !hasAriaLabel) {
            console.warn('Form control without proper label:', control);
            
            // Try to find nearby text that could be a label
            const possibleLabel = control.parentElement?.querySelector('.form-label, .control-label');
            if (possibleLabel && !possibleLabel.getAttribute('for')) {
                const controlId = id || `control-${Date.now()}`;
                control.id = controlId;
                possibleLabel.setAttribute('for', controlId);
            }
        }
    }

    /**
     * Setup escape key handling
     */
    setupEscapeHandling() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleEscapeKey(e);
            }
        });
    }

    /**
     * Handle escape key press
     */
    handleEscapeKey(e) {
        // Check for open modals
        const openModal = document.querySelector('.modal.show');
        if (openModal && bootstrap?.Modal) {
            const modalInstance = bootstrap.Modal.getInstance(openModal);
            if (modalInstance) {
                modalInstance.hide();
                return;
            }
        }

        // Check for open dropdowns
        const openDropdown = document.querySelector('.dropdown.show');
        if (openDropdown) {
            openDropdown.classList.remove('show');
            return;
        }

        // Check for focus traps
        if (this.isTrappingFocus) {
            // Let the focus trap handle it
            return;
        }

        // Clear any selections or active states
        document.querySelectorAll('.active').forEach(element => {
            if (element.classList.contains('removeable-active')) {
                element.classList.remove('active');
            }
        });
    }

    // ========================================
    // ARIA LABELS AND SEMANTICS SYSTEM
    // Task: T018 - ARIA Labels and Semantics
    // ========================================

    /**
     * Setup ARIA live regions for dynamic content
     */
    setupAriaLiveRegions() {
        // Create main live regions
        this.createLiveRegion('polite', 'accessibility-live-polite');
        this.createLiveRegion('assertive', 'accessibility-live-assertive');
        this.createLiveRegion('status', 'accessibility-status-region');
        
        // Setup live regions for common dynamic content areas
        this.setupNotificationLiveRegion();
        this.setupLoadingLiveRegion();
        this.setupErrorLiveRegion();
        this.setupFormValidationLiveRegion();
    }

    /**
     * Create a live region with specified politeness level
     */
    createLiveRegion(politeness, id) {
        let region = document.getElementById(id);
        
        if (!region) {
            region = document.createElement('div');
            region.id = id;
            region.setAttribute('aria-live', politeness);
            region.setAttribute('aria-atomic', 'true');
            region.className = 'visually-hidden';
            document.body.appendChild(region);
        }
        
        this.ariaLiveRegions.set(politeness, region);
        return region;
    }

    /**
     * Setup notification live region
     */
    setupNotificationLiveRegion() {
        const notifications = document.querySelector('.messages-container, .notifications, .alerts');
        if (notifications && !notifications.getAttribute('aria-live')) {
            notifications.setAttribute('aria-live', 'polite');
            notifications.setAttribute('aria-atomic', 'false');
        }
    }

    /**
     * Setup loading state live region
     */
    setupLoadingLiveRegion() {
        // Find loading overlays and spinners
        document.querySelectorAll('.loading-overlay, .spinner, .loading').forEach(loader => {
            if (!loader.getAttribute('aria-live')) {
                loader.setAttribute('aria-live', 'polite');
                loader.setAttribute('aria-atomic', 'true');
            }
            if (!loader.getAttribute('aria-label')) {
                loader.setAttribute('aria-label', 'Carregando conteúdo');
            }
        });
    }

    /**
     * Setup error live region  
     */
    setupErrorLiveRegion() {
        // Find error containers
        document.querySelectorAll('.error-container, .alert-danger').forEach(errorContainer => {
            if (!errorContainer.getAttribute('aria-live')) {
                errorContainer.setAttribute('aria-live', 'assertive');
                errorContainer.setAttribute('aria-atomic', 'true');
            }
        });
    }

    /**
     * Setup form validation live region
     */
    setupFormValidationLiveRegion() {
        document.querySelectorAll('.invalid-feedback, .error-message, .validation-error').forEach(feedback => {
            if (!feedback.getAttribute('aria-live')) {
                feedback.setAttribute('aria-live', 'polite');
                feedback.setAttribute('aria-atomic', 'true');
            }
        });
    }

    /**
     * Setup comprehensive ARIA labeling
     */
    setupAriaLabeling() {
        this.labelInteractiveElements();
        this.labelFormControls();
        this.labelComplexComponents();
        this.labelNavigationElements();
        this.labelModalElements();
        this.labelTableElements();
        this.labelListElements();
    }

    /**
     * Add ARIA labels to interactive elements
     */
    labelInteractiveElements() {
        // Buttons without accessible names
        document.querySelectorAll('button').forEach(button => {
            if (!this.hasAccessibleName(button)) {
                this.addAriaLabelToButton(button);
            }
        });

        // Links without accessible names
        document.querySelectorAll('a[href]').forEach(link => {
            if (!this.hasAccessibleName(link)) {
                this.addAriaLabelToLink(link);
            }
        });

        // Icon-only interactive elements
        document.querySelectorAll('.btn-icon, .icon-button, button:has(i:only-child)').forEach(iconButton => {
            if (!this.hasAccessibleName(iconButton)) {
                this.addAriaLabelToIconButton(iconButton);
            }
        });
    }

    /**
     * Enhanced form control labeling
     */
    labelFormControls() {
        document.querySelectorAll('input, textarea, select').forEach(control => {
            this.enhanceFormControlAccessibility(control);
        });

        // Label fieldsets without legends
        document.querySelectorAll('fieldset').forEach(fieldset => {
            if (!fieldset.querySelector('legend') && !fieldset.getAttribute('aria-labelledby')) {
                this.addFieldsetLabel(fieldset);
            }
        });

        // Label form groups
        document.querySelectorAll('.form-group, .mb-3').forEach(group => {
            this.enhanceFormGroupAccessibility(group);
        });
    }

    /**
     * Label complex UI components
     */
    labelComplexComponents() {
        // Dropdown components
        document.querySelectorAll('.dropdown').forEach(dropdown => {
            this.enhanceDropdownAccessibility(dropdown);
        });

        // Tab components
        document.querySelectorAll('[role="tablist"], .nav-tabs').forEach(tablist => {
            this.enhanceTabListAccessibility(tablist);
        });

        // Accordion components
        document.querySelectorAll('.accordion').forEach(accordion => {
            this.enhanceAccordionAccessibility(accordion);
        });

        // Card components
        document.querySelectorAll('.card').forEach(card => {
            this.enhanceCardAccessibility(card);
        });

        // Modal components
        document.querySelectorAll('.modal').forEach(modal => {
            this.enhanceModalAriaLabeling(modal);
        });
    }

    /**
     * Label navigation elements
     */
    labelNavigationElements() {
        // Main navigation
        document.querySelectorAll('nav').forEach(nav => {
            if (!nav.getAttribute('aria-label') && !nav.getAttribute('aria-labelledby')) {
                this.addNavigationLabel(nav);
            }
        });

        // Breadcrumb navigation
        document.querySelectorAll('.breadcrumb').forEach(breadcrumb => {
            if (!breadcrumb.getAttribute('aria-label')) {
                breadcrumb.setAttribute('aria-label', 'Navegação estrutural / breadcrumb');
            }
        });

        // Pagination
        document.querySelectorAll('.pagination').forEach(pagination => {
            if (!pagination.getAttribute('aria-label')) {
                pagination.setAttribute('aria-label', 'Navegação de páginas');
            }
        });
    }

    /**
     * Label modal elements with proper ARIA
     */
    labelModalElements() {
        document.querySelectorAll('.modal').forEach(modal => {
            // Ensure modal has proper role
            if (!modal.getAttribute('role')) {
                modal.setAttribute('role', 'dialog');
            }
            
            // Ensure aria-modal is set
            if (!modal.getAttribute('aria-modal')) {
                modal.setAttribute('aria-modal', 'true');
            }

            // Label modal if not already labeled
            if (!modal.getAttribute('aria-labelledby') && !modal.getAttribute('aria-label')) {
                const title = modal.querySelector('.modal-title, h1, h2, h3, h4, h5, h6');
                if (title) {
                    const titleId = title.id || this.generateUniqueId('modal-title');
                    title.id = titleId;
                    modal.setAttribute('aria-labelledby', titleId);
                } else {
                    modal.setAttribute('aria-label', 'Dialog');
                }
            }

            // Describe modal content
            this.addModalDescription(modal);
        });
    }

    /**
     * Label table elements
     */
    labelTableElements() {
        document.querySelectorAll('table').forEach(table => {
            // Add caption if missing
            if (!table.querySelector('caption') && !table.getAttribute('aria-label')) {
                this.addTableCaption(table);
            }

            // Enhance table headers
            const headers = table.querySelectorAll('th');
            headers.forEach(header => {
                if (!header.getAttribute('scope')) {
                    // Determine scope based on position
                    const row = header.closest('tr');
                    const thead = header.closest('thead');
                    const isFirstRow = thead?.querySelector('tr') === row;
                    const isFirstCell = row?.querySelector('th, td') === header;
                    
                    if (isFirstRow && !isFirstCell) {
                        header.setAttribute('scope', 'col');
                    } else if (isFirstCell) {
                        header.setAttribute('scope', 'row');
                    }
                }
            });
        });
    }

    /**
     * Label list elements
     */
    labelListElements() {
        document.querySelectorAll('ul, ol').forEach(list => {
            // Add description for lists without clear purpose
            if (!list.getAttribute('aria-label') && !list.getAttribute('aria-labelledby')) {
                this.addListDescription(list);
            }
        });

        // Label definition lists
        document.querySelectorAll('dl').forEach(dl => {
            if (!dl.getAttribute('aria-label')) {
                dl.setAttribute('aria-label', 'Lista de definições');
            }
        });
    }

    /**
     * Setup ARIA states and properties
     */
    setupAriaStates() {
        // Setup expandable elements
        document.querySelectorAll('.collapse, .accordion-collapse').forEach(collapsible => {
            this.setupExpandableAriaStates(collapsible);
        });

        // Setup toggleable elements  
        document.querySelectorAll('[data-bs-toggle]').forEach(toggle => {
            this.setupToggleAriaStates(toggle);
        });

        // Setup loading states
        document.querySelectorAll('button[type="submit"], .btn').forEach(button => {
            this.setupButtonAriaStates(button);
        });

        // Setup form validation states
        document.querySelectorAll('.form-control').forEach(control => {
            this.setupFormControlAriaStates(control);
        });
    }

    /**
     * Setup semantic HTML enhancements
     */
    setupSemanticEnhancements() {
        this.enhanceHeadings();
        this.enhanceLandmarks();
        this.enhanceListsAndGroups();
        this.enhanceInteractiveElements();
        this.ensureProperNesting();
    }

    /**
     * Enhance heading structure
     */
    enhanceHeadings() {
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, .h1, .h2, .h3, .h4, .h5, .h6'));
        
        // Check heading hierarchy
        let previousLevel = 0;
        headings.forEach(heading => {
            const level = this.getHeadingLevel(heading);
            
            if (level > previousLevel + 1) {
                console.warn('Heading hierarchy issue detected:', heading, `Jumps from h${previousLevel} to h${level}`);
            }
            
            previousLevel = level;
        });

        // Ensure page has h1
        if (!document.querySelector('h1, .h1')) {
            console.warn('Page missing h1 heading');
        }
    }

    /**
     * Enhance landmark regions
     */
    enhanceLandmarks() {
        // Ensure main landmark exists
        if (!document.querySelector('main, [role="main"]')) {
            const mainContent = document.querySelector('#main-content, .main-content, .app-main');
            if (mainContent && !mainContent.getAttribute('role')) {
                mainContent.setAttribute('role', 'main');
            }
        }

        // Enhance navigation landmarks
        document.querySelectorAll('nav').forEach(nav => {
            if (!nav.getAttribute('aria-label') && !nav.getAttribute('aria-labelledby')) {
                this.assignNavigationLabel(nav);
            }
        });

        // Ensure complementary content is marked
        document.querySelectorAll('aside, .sidebar').forEach(aside => {
            if (!aside.getAttribute('role')) {
                aside.setAttribute('role', 'complementary');
            }
        });
    }

    /**
     * Setup dynamic ARIA updates
     */
    setupDynamicAriaUpdates() {
        // Monitor form changes
        document.addEventListener('input', (e) => {
            this.updateFormControlAriaStates(e.target);
        });

        // Monitor button state changes
        this.observeButtonStates();
        
        // Monitor modal state changes
        this.observeModalStates();
        
        // Monitor loading state changes
        this.observeLoadingStates();
    }

    // ========================================
    // ARIA HELPER METHODS
    // ========================================

    /**
     * Check if element has accessible name
     */
    hasAccessibleName(element) {
        return !!(
            element.getAttribute('aria-label') ||
            element.getAttribute('aria-labelledby') ||
            element.textContent?.trim() ||
            element.getAttribute('title') ||
            element.getAttribute('alt') ||
            element.querySelector('img[alt]')
        );
    }

    /**
     * Add ARIA label to button based on context
     */
    addAriaLabelToButton(button) {
        const icon = button.querySelector('i, svg, .icon');
        const text = button.textContent?.trim();
        
        if (!text && icon) {
            const iconClass = icon.className;
            let label = this.inferButtonLabelFromIcon(iconClass);
            
            // Get label from nearby text or context
            if (!label) {
                label = this.inferButtonLabelFromContext(button);
            }
            
            if (label) {
                button.setAttribute('aria-label', label);
            }
        }
    }

    /**
     * Add ARIA label to link based on context
     */
    addAriaLabelToLink(link) {
        const text = link.textContent?.trim();
        const href = link.getAttribute('href');
        
        if (!text || text === '#') {
            const icon = link.querySelector('i, svg, .icon');
            if (icon) {
                const label = this.inferLinkLabelFromIcon(icon.className) || 
                             this.inferLinkLabelFromHref(href) ||
                             'Link';
                link.setAttribute('aria-label', label);
            }
        }
    }

    /**
     * Add ARIA label to icon button
     */
    addAriaLabelToIconButton(button) {
        const icon = button.querySelector('i, svg, .icon');
        if (icon) {
            const iconClass = icon.className;
            const action = button.getAttribute('onclick') || button.getAttribute('data-action') || '';
            
            let label = this.inferButtonLabelFromIcon(iconClass) ||
                       this.inferButtonLabelFromAction(action) ||
                       'Botão';
                       
            button.setAttribute('aria-label', label);
        }
    }

    /**
     * Enhance form control accessibility
     */
    enhanceFormControlAccessibility(control) {
        // Ensure proper labeling
        this.ensureFormControlLabel(control);
        
        // Add required indicator
        if (control.hasAttribute('required') && !control.getAttribute('aria-required')) {
            control.setAttribute('aria-required', 'true');
        }
        
        // Associate with help text
        const helpText = this.findAssociatedHelpText(control);
        if (helpText) {
            this.associateHelpText(control, helpText);
        }
        
        // Associate with error messages
        const errorText = this.findAssociatedErrorText(control);
        if (errorText) {
            this.associateErrorText(control, errorText);
        }
    }

    /**
     * Enhance dropdown accessibility
     */
    enhanceDropdownAccessibility(dropdown) {
        const trigger = dropdown.querySelector('.dropdown-toggle, [data-bs-toggle="dropdown"]');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (trigger && menu) {
            // Ensure proper ARIA attributes
            if (!trigger.getAttribute('aria-haspopup')) {
                trigger.setAttribute('aria-haspopup', 'true');
            }
            if (!trigger.getAttribute('aria-expanded')) {
                trigger.setAttribute('aria-expanded', 'false');
            }
            
            // Label the menu
            if (!menu.getAttribute('aria-labelledby')) {
                const triggerId = trigger.id || this.generateUniqueId('dropdown-trigger');
                trigger.id = triggerId;
                menu.setAttribute('aria-labelledby', triggerId);
            }
            
            // Update aria-expanded on show/hide  
            dropdown.addEventListener('show.bs.dropdown', () => {
                trigger.setAttribute('aria-expanded', 'true');
            });
            
            dropdown.addEventListener('hide.bs.dropdown', () => {
                trigger.setAttribute('aria-expanded', 'false');
            });
        }
    }

    /**
     * Enhance tab list accessibility
     */
    enhanceTabListAccessibility(tablist) {
        if (!tablist.getAttribute('role')) {
            tablist.setAttribute('role', 'tablist');
        }
        
        const tabs = tablist.querySelectorAll('.nav-link, [role="tab"]');
        tabs.forEach((tab, index) => {
            if (!tab.getAttribute('role')) {
                tab.setAttribute('role', 'tab');
            }
            
            // Set up tab panel relationship
            const panelId = tab.getAttribute('href')?.substring(1) || 
                           tab.getAttribute('aria-controls') ||
                           tab.getAttribute('data-bs-target')?.substring(1);
            
            if (panelId) {
                tab.setAttribute('aria-controls', panelId);
                
                const panel = document.getElementById(panelId);
                if (panel) {
                    panel.setAttribute('role', 'tabpanel');
                    panel.setAttribute('aria-labelledby', tab.id || this.generateUniqueId('tab'));
                }
            }
        });
    }

    /**
     * Announce to screen readers via live region
     */
    announceToScreenReader(message, urgency = 'polite') {
        const region = this.ariaLiveRegions.get(urgency);
        if (region) {
            // Clear and set new message
            region.textContent = '';
            setTimeout(() => {
                region.textContent = message;
            }, 100);
        }
    }

    /**
     * Update ARIA states during user interaction
     */
    updateInteractionState(element, state, value) {
        element.setAttribute(`aria-${state}`, value);
        
        // Store state for later reference
        const elementStates = this.interactionStates.get(element) || {};
        elementStates[state] = value;
        this.interactionStates.set(element, elementStates);
        
        // Announce important state changes
        if (state === 'expanded' || state === 'pressed' || state === 'selected') {
            const announcement = this.generateStateAnnouncement(element, state, value);
            if (announcement) {
                this.announceToScreenReader(announcement);
            }
        }
    }

    /**
     * Generate unique ID
     */
    generateUniqueId(prefix = 'aria') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Infer button label from icon class
     */
    inferButtonLabelFromIcon(iconClass) {
        const iconMappings = {
            'bi-house': 'Ir para início',
            'bi-plus': 'Adicionar',
            'bi-minus': 'Remover',
            'bi-x': 'Fechar',
            'bi-search': 'Buscar',
            'bi-gear': 'Configurações',
            'bi-pencil': 'Editar',
            'bi-trash': 'Excluir',
            'bi-eye': 'Visualizar',
            'bi-download': 'Baixar',
            'bi-upload': 'Enviar',
            'bi-save': 'Salvar',
            'bi-print': 'Imprimir',
            'bi-share': 'Compartilhar',
            'bi-heart': 'Favoritar',
            'bi-star': 'Avaliar',
            'bi-play': 'Reproduzir',
            'bi-pause': 'Pausar',
            'bi-stop': 'Parar',
            'bi-chevron-left': 'Voltar',
            'bi-chevron-right': 'Avançar',
            'bi-arrow-left': 'Voltar',
            'bi-arrow-right': 'Avançar'
        };
        
        for (const [iconClass, label] of Object.entries(iconMappings)) {
            if (iconClass.includes(iconClass)) {
                return label;
            }
        }
        
        return null;
    }

    /**
     * Infer button label from context  
     */
    inferButtonLabelFromContext(button) {
        // Check nearby labels or headings
        const parent = button.closest('.card, .form-group, .modal, .section');
        if (parent) {
            const heading = parent.querySelector('h1, h2, h3, h4, h5, h6, .card-title');
            if (heading) {
                return `${heading.textContent.trim()} - Botão`;
            }
        }
        
        // Check form context
        const form = button.closest('form');
        if (form && button.getAttribute('type') === 'submit') {
            return 'Enviar formulário';
        }
        
        return null;
    }

    /**
     * Get heading level
     */
    getHeadingLevel(heading) {
        const tagName = heading.tagName.toLowerCase();
        if (tagName.match(/h[1-6]/)) {
            return parseInt(tagName.charAt(1));
        }
        
        const className = heading.className;
        const match = className.match(/h([1-6])/);
        return match ? parseInt(match[1]) : 1;
    }

    // ========================================
    // KEYBOARD SHORTCUT ACTION HANDLERS
    // ========================================

    navigateToHome() {
        const homeLink = document.querySelector('a[href="/"], a[href="/etiquetas/"]');
        if (homeLink) {
            homeLink.click();
        } else {
            window.location.href = '/';
        }
    }

    navigateToDashboard() {
        const dashboardLink = document.querySelector('a[href*="dashboard"]');
        if (dashboardLink) {
            dashboardLink.click();
        } else {
            window.location.href = '/etiquetas/dashboard/';
        }
    }

    navigateToNew() {
        const newButton = document.querySelector('[data-action="new"], .btn-new, a[href*="create"]');
        if (newButton) {
            newButton.click();
        }
    }

    focusSearch() {
        const searchInputs = [
            'input[type="search"]',
            'input[name*="search"]',
            'input[placeholder*="buscar"]',
            'input[placeholder*="search"]',
            '#search',
            '.search-input'
        ];

        for (const selector of searchInputs) {
            const input = document.querySelector(selector);
            if (input && this.isElementVisible(input)) {
                input.focus();
                input.select();
                this.announceToScreenReader('Campo de busca focado');
                return;
            }
        }
    }

    saveForm(e) {
        // Find the current form
        const activeForm = document.activeElement?.closest('form') || 
                          document.querySelector('form:not(.no-auto-save)');
        
        if (activeForm) {
            e.preventDefault();
            
            const submitButton = activeForm.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton) {
                submitButton.click();
                this.announceToScreenReader('Formulário enviado');
            }
        }
    }

    openQuickActions() {
        const quickActionsButton = document.querySelector('[data-bs-target="#quickActionsModal"], .quick-actions-toggle');
        if (quickActionsButton) {
            quickActionsButton.click();
        }
    }

    triggerQuickAction(number) {
        const quickAction = document.querySelector(`[data-quick-action="${number}"]`);
        if (quickAction) {
            quickAction.click();
            this.announceToScreenReader(`Ação rápida ${number} executada`);
        }
    }

    closeModal() {
        const openModal = document.querySelector('.modal.show');
        if (openModal && bootstrap?.Modal) {
            const modalInstance = bootstrap.Modal.getInstance(openModal);
            if (modalInstance) {
                modalInstance.hide();
                return;
            }
        }

        // Fallback for non-Bootstrap modals
        document.querySelectorAll('.modal, .dialog, [role="dialog"]').forEach(modal => {
            if (this.isElementVisible(modal)) {
                modal.style.display = 'none';
                modal.setAttribute('aria-hidden', 'true');
            }
        });
    }

    showKeyboardHelp() {
        // Use existing shortcut help if available
        if (window.progressiveEnhancement?.showShortcutHelp) {
            window.progressiveEnhancement.showShortcutHelp();
            return;
        }

        // Fallback help display
        const shortcuts = Array.from(this.keyboardShortcuts.values())
            .map(s => `${s.key.toUpperCase()}: ${s.description}`)
            .join('\n');
        
        alert(`Atalhos de Teclado Disponíveis:\n\n${shortcuts}`);
    }

    // ========================================
    // UTILITY METHODS
    // ========================================

    /**
     * Check if element is visible
     */
    isElementVisible(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0' &&
               element.offsetWidth > 0 && 
               element.offsetHeight > 0;
    }

    /**
     * Check if element has focus styles
     */
    hasFocusStyles(element) {
        // This is a simplified check - in a real implementation you'd check computed styles
        return element.matches(':focus') || element.classList.contains('focus-visible');
    }

    /**
     * Announce message to screen readers
     */
    announceToScreenReader(message) {
        // Create or update live region
        let liveRegion = document.getElementById('accessibility-live-region');
        
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'accessibility-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.style.cssText = `
                position: absolute;
                left: -10000px;
                width: 1px;
                height: 1px;
                overflow: hidden;
            `;
            document.body.appendChild(liveRegion);
        }

        // Clear and set new message
        liveRegion.textContent = '';
        setTimeout(() => {
            liveRegion.textContent = message;
        }, 100);
    }

    /**
     * Announce shortcut activation
     */
    announceShortcut(description) {
        if (this.isDevelopment()) {
            console.log(`Keyboard shortcut: ${description}`);
        }
        
        // Don't announce every shortcut to avoid spam
        const importantShortcuts = ['Campo de busca focado', 'Formulário enviado'];
        if (importantShortcuts.includes(description)) {
            this.announceToScreenReader(description);
        }
    }

    /**
     * Check if in development mode
     */
    isDevelopment() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.port === '8000';
    }

    /**
     * Debug logging
     */
    log(message, ...args) {
        if (this.isDevelopment()) {
            console.log(`[KeyboardNav] ${message}`, ...args);
        }
    }

    /**
     * Get current keyboard shortcuts for help display
     */
    getShortcutsList() {
        return Array.from(this.keyboardShortcuts.values()).map(shortcut => ({
            combination: this.formatShortcutDisplay(shortcut),
            description: shortcut.description
        }));
    }

    /**
     * Format shortcut for user display
     */
    formatShortcutDisplay(shortcut) {
        const parts = [];
        if (shortcut.ctrl) parts.push('Ctrl');
        if (shortcut.alt) parts.push('Alt');
        if (shortcut.shift) parts.push('Shift');
        if (shortcut.meta) parts.push('Cmd');
        parts.push(shortcut.key.toUpperCase());
        return parts.join(' + ');
    }

    /**
     * Destroy and clean up
     */
    destroy() {
        // Remove event listeners
        // (In a real implementation, you'd track and remove all listeners)
        
        // Clear maps
        this.focusTraps.clear();
        this.keyboardShortcuts.clear();
        this.roving.clear();
        
        // Remove skip links
        document.querySelectorAll('.skip-link, .skip-links').forEach(el => el.remove());
        
        // Remove live region
        const liveRegion = document.getElementById('accessibility-live-region');
        if (liveRegion) {
            liveRegion.remove();
        }
        
        this.log('Keyboard Navigation Manager destroyed');
    }
}

// ========================================
// AUTO-INITIALIZATION AND GLOBAL API
// ========================================

let accessibilityManager;

function initializeAccessibilityManager() {
    if (accessibilityManager) return accessibilityManager;
    
    accessibilityManager = new AccessibilityManager();
    window.accessibilityManager = accessibilityManager;
    window.keyboardNavigation = accessibilityManager; // Backward compatibility
    
    console.log('♿ Accessibility Management System activated');
    return accessibilityManager;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAccessibilityManager);
} else {
    initializeAccessibilityManager();
}

// Public API
window.registerKeyboardShortcut = function(key, action, description, options = {}) {
    if (accessibilityManager) {
        accessibilityManager.registerKeyboardShortcut({
            key,
            action,
            description,
            ...options
        });
    }
};

window.trapFocus = function(element) {
    if (accessibilityManager) {
        accessibilityManager.trapFocus(element);
    }
};

window.releaseFocusTrap = function(element) {
    if (accessibilityManager) {
        accessibilityManager.releaseFocusTrap(element);
    }
};

window.announceToScreenReader = function(message, urgency = 'polite') {
    if (accessibilityManager) {
        accessibilityManager.announceToScreenReader(message, urgency);
    }
};

/**
 * Global accessibility validation function
 */
window.validateScreenReaderCompatibility = function() {
    if (accessibilityManager) {
        return accessibilityManager.validateScreenReaderCompatibility();
    }
    
    // Fallback validation if manager not available
    console.log('🔍 Basic Accessibility Check (Accessibility Manager not initialized)');
    
    const validationResults = {
        passed: [],
        warnings: ['Accessibility Manager not initialized - limited validation available'],
        errors: [],
        summary: { passed: 0, warnings: 1, errors: 0, score: 50 }
    };
    
    return validationResults;
};
// Accessibility testing functions for global access
window.validateAccessibility = function() {
    if (accessibilityManager) {
        return accessibilityManager.validateScreenReaderCompatibility();
    }
    console.warn('Accessibility Manager not initialized');
    return null;
};

window.testScreenReaderNavigation = function() {
    if (accessibilityManager) {
        accessibilityManager.testScreenReaderNavigation();
    }
};

window.testScreenReaderCompatibility = function() {
    if (accessibilityManager) {
        accessibilityManager.testScreenReaderCompatibility();
    }
};

window.updateAriaState = function(element, state, value) {
    if (accessibilityManager) {
        accessibilityManager.updateInteractionState(element, state, value);
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AccessibilityManager };
}