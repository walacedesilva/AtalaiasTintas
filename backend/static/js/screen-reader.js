/**
 * Screen Reader Compatibility System
 * 
 * Provides comprehensive screen reader support and testing including:
 * - NVDA, JAWS, VoiceOver, and TalkBack compatibility
 * - Screen reader specific optimizations and announcements
 * - Alternative content generation for complex elements
 * - Live region management and announcement queuing
 * - Audio descriptions and alternative text management
 * - Screen reader testing utilities and simulation
 * - Voice commands and speech synthesis integration
 */

class ScreenReaderCompatibility {
    constructor() {
        this.isScreenReaderActive = false;
        this.screenReaderType = null;
        this.speechSynthesis = null;
        this.announcementQueue = [];
        this.isProcessingQueue = false;
        this.liveRegions = new Map();
        
        // Screen reader detection patterns
        this.screenReaderPatterns = {
            nvda: /nvda/i,
            jaws: /jaws|freedom scientific/i,
            voiceover: /voiceover/i,
            talkback: /talkback/i,
            orca: /orca/i,
            narrator: /narrator/i,
            dragon: /dragon|naturally speaking/i
        };

        this.config = {
            announcePageChanges: true,
            announceFormErrors: true,
            announceFormSuccess: true,
            announceDataUpdates: true,
            announceNavigationChanges: true,
            voiceRate: 1.0,
            voicePitch: 1.0,
            voiceVolume: 1.0,
            preferredVoice: null,
            autoDescribeImages: true,
            announceLoadingStates: true,
            maxAnnouncementLength: 200,
            announcementDelay: 500
        };

        this.init();
    }

    /**
     * Initialize screen reader compatibility system
     */
    init() {
        this.detectScreenReader();
        this.setupSpeechSynthesis();
        this.createLiveRegions();
        this.enhanceForScreenReaders();
        this.setupNavigationAnnouncements();
        this.setupFormAnnouncements();
        this.setupContentAnnouncements();
        this.loadUserPreferences();
        this.startCompatibilityMonitoring();
        
        // Add to global scope for debugging and testing
        window.ScreenReaderCompatibility = this;
        
        console.log('Screen Reader Compatibility System initialized', {
            detected: this.isScreenReaderActive,
            type: this.screenReaderType
        });
        
        // Announce system ready
        this.announce('Sistema de acessibilidade carregado', 'polite');
    }

    /**
     * Detect if a screen reader is active
     */
    detectScreenReader() {
        // Multiple detection methods for better accuracy
        const detectionMethods = [
            this.detectByUserAgent.bind(this),
            this.detectByAccessibilityAPI.bind(this),
            this.detectByTestElement.bind(this),
            this.detectByFocusBehavior.bind(this)
        ];

        for (const method of detectionMethods) {
            const result = method();
            if (result.detected) {
                this.isScreenReaderActive = true;
                this.screenReaderType = result.type;
                break;
            }
        }

        // Enable enhanced mode if screen reader detected
        if (this.isScreenReaderActive) {
            document.documentElement.classList.add('screen-reader-active', `sr-${this.screenReaderType}`);
            this.enableScreenReaderEnhancements();
        }
    }

    /**
     * Detect screen reader by user agent
     */
    detectByUserAgent() {
        const userAgent = navigator.userAgent;
        
        for (const [type, pattern] of Object.entries(this.screenReaderPatterns)) {
            if (pattern.test(userAgent)) {
                return { detected: true, type };
            }
        }
        
        return { detected: false, type: null };
    }

    /**
     * Detect screen reader using accessibility API
     */
    detectByAccessibilityAPI() {
        try {
            // Check for Windows accessibility API
            if (typeof window.external !== 'undefined' && window.external.msAccessibilityEnabled) {
                return { detected: true, type: 'windows-at' };
            }

            // Check for macOS VoiceOver
            if (navigator.userAgent.includes('Mac') && window.speechSynthesis) {
                const voices = speechSynthesis.getVoices();
                const systemVoices = voices.filter(voice => voice.localService && voice.name.includes('System'));
                if (systemVoices.length > 0) {
                    return { detected: true, type: 'voiceover' };
                }
            }

            // Check for mobile screen readers
            if ('ontouchstart' in window) {
                if (navigator.userAgent.includes('iPhone') || navigator.userAgent.includes('iPad')) {
                    return { detected: true, type: 'voiceover' };
                }
                if (navigator.userAgent.includes('Android')) {
                    return { detected: true, type: 'talkback' };
                }
            }
        } catch (e) {
            console.debug('Accessibility API detection failed:', e);
        }
        
        return { detected: false, type: null };
    }

    /**
     * Detect screen reader using test element method
     */
    detectByTestElement() {
        try {
            const testElement = document.createElement('div');
            testElement.setAttribute('aria-hidden', 'true');
            testElement.style.position = 'absolute';
            testElement.style.left = '-10000px';
            testElement.textContent = 'Screen reader test';
            
            document.body.appendChild(testElement);
            
            const isDetected = testElement.offsetHeight > 0 || testElement.offsetWidth > 0;
            
            document.body.removeChild(testElement);
            
            if (isDetected) {
                return { detected: true, type: 'generic' };
            }
        } catch (e) {
            console.debug('Test element detection failed:', e);
        }
        
        return { detected: false, type: null };
    }

    /**
     * Detect screen reader by focus behavior
     */
    detectByFocusBehavior() {
        // This is more of a heuristic - look for accessibility-focused behavior
        const hasHighContrastPreference = window.matchMedia('(prefers-contrast: high)').matches;
        const hasReducedMotionPreference = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const hasLargeTextPreference = window.matchMedia('(min-resolution: 120dpi)').matches;
        
        const accessibilityScore = [
            hasHighContrastPreference,
            hasReducedMotionPreference,
            hasLargeTextPreference
        ].filter(Boolean).length;
        
        // If multiple accessibility preferences are set, likely using assistive technology
        if (accessibilityScore >= 2) {
            return { detected: true, type: 'assistive-technology' };
        }
        
        return { detected: false, type: null };
    }

    /**
     * Setup speech synthesis for announcements
     */
    setupSpeechSynthesis() {
        if (!window.speechSynthesis) {
            console.warn('Speech synthesis not supported');
            return;
        }
        
        this.speechSynthesis = window.speechSynthesis;
        
        // Wait for voices to load
        if (this.speechSynthesis.getVoices().length === 0) {
            this.speechSynthesis.addEventListener('voiceschanged', () => {
                this.selectPreferredVoice();
            });
        } else {
            this.selectPreferredVoice();
        }
    }

    /**
     * Select the best voice for announcements
     */
    selectPreferredVoice() {
        const voices = this.speechSynthesis.getVoices();
        
        // Prefer Portuguese voices
        let preferredVoice = voices.find(voice => 
            voice.lang.startsWith('pt') && voice.localService
        );
        
        // Fallback to any Portuguese voice
        if (!preferredVoice) {
            preferredVoice = voices.find(voice => voice.lang.startsWith('pt'));
        }
        
        // Fallback to default voice
        if (!preferredVoice) {
            preferredVoice = voices.find(voice => voice.default);
        }
        
        this.config.preferredVoice = preferredVoice;
    }

    /**
     * Create and manage live regions for announcements
     */
    createLiveRegions() {
        // Polite announcements (non-interrupting)
        this.createLiveRegion('polite', 'polite', 'Anúncios informativos');
        
        // Assertive announcements (interrupting)
        this.createLiveRegion('assertive', 'assertive', 'Anúncios urgentes');
        
        // Status announcements
        this.createLiveRegion('status', 'polite', 'Atualizações de status');
        
        // Error announcements
        this.createLiveRegion('errors', 'assertive', 'Anúncios de erro');
        
        // Loading announcements
        this.createLiveRegion('loading', 'polite', 'Estados de carregamento');
    }

    /**
     * Create a specific live region
     */
    createLiveRegion(id, priority, description) {
        const region = document.createElement('div');
        region.id = `live-region-${id}`;
        region.setAttribute('aria-live', priority);
        region.setAttribute('aria-atomic', 'true');
        region.setAttribute('aria-label', description);
        region.className = 'visually-hidden';
        
        document.body.appendChild(region);
        this.liveRegions.set(id, region);
    }

    /**
     * Enhanced screen reader optimizations
     */
    enableScreenReaderEnhancements() {
        // Add screen reader specific CSS class
        document.documentElement.classList.add('enhanced-for-screen-reader');
        
        // Enhance focus management
        this.enhanceFocusManagement();
        
        // Add landmark navigation
        this.enhanceLandmarkNavigation();
        
        // Improve table navigation
        this.enhanceTableNavigation();
        
        // Add heading navigation
        this.enhanceHeadingNavigation();
        
        // Enhance form navigation
        this.enhanceFormNavigation();
    }

    /**
     * Enhance focus management for screen readers
     */
    enhanceFocusManagement() {
        // Ensure proper focus order
        const focusableElements = document.querySelectorAll(`
            a[href]:not([tabindex="-1"]),
            button:not([disabled]):not([tabindex="-1"]),
            input:not([disabled]):not([tabindex="-1"]),
            select:not([disabled]):not([tabindex="-1"]),
            textarea:not([disabled]):not([tabindex="-1"]),
            [tabindex]:not([tabindex="-1"])
        `);
        
        focusableElements.forEach((element, index) => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
        });

        // Add focus announcements
        document.addEventListener('focusin', (e) => {
            this.handleFocusChange(e.target);
        });
    }

    /**
     * Handle focus changes with appropriate announcements
     */
    handleFocusChange(element) {
        if (!this.isScreenReaderActive) return;

        let announcement = '';
        
        // Determine appropriate announcement based on element type
        if (element.tagName === 'BUTTON') {
            announcement = this.getButtonAnnouncement(element);
        } else if (element.tagName === 'A') {
            announcement = this.getLinkAnnouncement(element);
        } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
            announcement = this.getFormFieldAnnouncement(element);
        } else if (element.hasAttribute('role')) {
            announcement = this.getRoleBasedAnnouncement(element);
        }

        if (announcement) {
            this.announce(announcement, 'polite', true);
        }
    }

    /**
     * Get button announcement
     */
    getButtonAnnouncement(button) {
        let text = button.textContent?.trim() || button.getAttribute('aria-label') || 'Botão';
        
        if (button.hasAttribute('aria-expanded')) {
            const expanded = button.getAttribute('aria-expanded') === 'true';
            text += expanded ? ' expandido' : ' recolhido';
        }
        
        if (button.hasAttribute('aria-pressed')) {
            const pressed = button.getAttribute('aria-pressed') === 'true';
            text += pressed ? ' pressionado' : ' não pressionado';
        }
        
        return `Botão: ${text}`;
    }

    /**
     * Get link announcement
     */
    getLinkAnnouncement(link) {
        let text = link.textContent?.trim() || link.getAttribute('aria-label') || 'Link';
        
        if (link.hasAttribute('target') && link.getAttribute('target') === '_blank') {
            text += ' (abre em nova janela)';
        }
        
        if (link.hasAttribute('download')) {
            text += ' (download)';
        }
        
        return `Link: ${text}`;
    }

    /**
     * Get form field announcement
     */
    getFormFieldAnnouncement(field) {
        let announcement = '';
        
        // Get label
        const label = this.getFieldLabel(field);
        if (label) {
            announcement += label + ': ';
        }
        
        // Get field type
        announcement += this.getFieldType(field);
        
        // Get value if appropriate
        if (field.value && field.type !== 'password') {
            announcement += `, valor: ${field.value}`;
        }
        
        // Get validation state
        if (field.hasAttribute('aria-invalid') && field.getAttribute('aria-invalid') === 'true') {
            announcement += ', inválido';
        }
        
        if (field.hasAttribute('required')) {
            announcement += ', obrigatório';
        }
        
        return announcement;
    }

    /**
     * Get field label from various sources
     */
    getFieldLabel(field) {
        // Try aria-labelledby first
        const labelledBy = field.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelElement = document.getElementById(labelledBy);
            if (labelElement) {
                return labelElement.textContent?.trim();
            }
        }
        
        // Try aria-label
        const ariaLabel = field.getAttribute('aria-label');
        if (ariaLabel) {
            return ariaLabel;
        }
        
        // Try associated label element
        const label = field.labels?.[0] || document.querySelector(`label[for="${field.id}"]`);
        if (label) {
            return label.textContent?.trim();
        }
        
        // Try placeholder as fallback
        return field.getAttribute('placeholder') || null;
    }

    /**
     * Get field type description
     */
    getFieldType(field) {
        const typeMap = {
            'text': 'campo de texto',
            'email': 'campo de e-mail',
            'password': 'campo de senha',
            'number': 'campo numérico',
            'tel': 'campo de telefone',
            'url': 'campo de URL',
            'search': 'campo de busca',
            'textarea': 'área de texto',
            'select-one': 'lista de seleção',
            'select-multiple': 'lista de seleção múltipla',
            'checkbox': 'caixa de seleção',
            'radio': 'botão de opção'
        };
        
        const type = field.type || field.tagName.toLowerCase();
        return typeMap[type] || 'campo';
    }

    /**
     * Get role-based announcement
     */
    getRoleBasedAnnouncement(element) {
        const role = element.getAttribute('role');
        const roleMap = {
            'tab': 'aba',
            'tabpanel': 'painel de aba',
            'dialog': 'diálogo',
            'alert': 'alerta',
            'status': 'status',
            'menu': 'menu',
            'menuitem': 'item de menu',
            'toolbar': 'barra de ferramentas',
            'grid': 'grade',
            'tree': 'árvore'
        };
        
        const roleDescription = roleMap[role] || role;
        const text = element.textContent?.trim() || element.getAttribute('aria-label') || '';
        
        return `${roleDescription}: ${text}`;
    }

    /**
     * Enhance landmark navigation
     */
    enhanceLandmarkNavigation() {
        const landmarks = document.querySelectorAll(`
            main[role="main"], [role="main"],
            nav[role="navigation"], [role="navigation"],
            aside[role="complementary"], [role="complementary"],
            header[role="banner"], [role="banner"],
            footer[role="contentinfo"], [role="contentinfo"],
            section[role="region"], [role="region"]
        `);

        landmarks.forEach(landmark => {
            // Ensure all landmarks have proper labels
            if (!landmark.hasAttribute('aria-label') && !landmark.hasAttribute('aria-labelledby')) {
                const role = landmark.getAttribute('role') || landmark.tagName.toLowerCase();
                const defaultLabels = {
                    'main': 'Conteúdo principal',
                    'navigation': 'Navegação',
                    'complementary': 'Conteúdo complementar',
                    'banner': 'Cabeçalho',
                    'contentinfo': 'Rodapé',
                    'region': 'Região'
                };
                
                landmark.setAttribute('aria-label', defaultLabels[role] || `Região ${role}`);
            }
        });
    }

    /**
     * Enhance table navigation for screen readers
     */
    enhanceTableNavigation() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            // Add table summary if missing
            if (!table.hasAttribute('aria-label') && !table.querySelector('caption')) {
                const headers = table.querySelectorAll('th');
                const rows = table.querySelectorAll('tbody tr').length;
                const summary = `Tabela com ${headers.length} colunas e ${rows} linhas`;
                table.setAttribute('aria-label', summary);
            }
            
            // Enhance headers
            const headers = table.querySelectorAll('th');
            headers.forEach(header => {
                if (!header.hasAttribute('scope')) {
                    // Determine if it's a row or column header
                    const isRowHeader = header.parentElement.querySelector('th') === header;
                    header.setAttribute('scope', isRowHeader ? 'row' : 'col');
                }
            });
            
            // Add navigation instructions
            if (!table.hasAttribute('aria-describedby')) {
                const instructionId = 'table-navigation-' + Math.random().toString(36).substr(2, 9);
                const instructions = document.createElement('div');
                instructions.id = instructionId;
                instructions.className = 'visually-hidden';
                instructions.textContent = 'Use as setas para navegar pela tabela';
                
                table.parentNode.insertBefore(instructions, table.nextSibling);
                table.setAttribute('aria-describedby', instructionId);
            }
        });
    }

    /**
     * Enhance heading navigation
     */
    enhanceHeadingNavigation() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        
        headings.forEach((heading, index) => {
            // Ensure headings are focusable for screen reader navigation
            if (!heading.hasAttribute('tabindex')) {
                heading.setAttribute('tabindex', '-1');
            }
            
            // Add unique IDs for navigation
            if (!heading.id) {
                heading.id = `heading-${index + 1}`;
            }
            
            // Add level information if not clear
            const level = heading.tagName.charAt(1);
            if (!heading.hasAttribute('aria-level')) {
                heading.setAttribute('aria-level', level);
            }
        });
    }

    /**
     * Enhance form navigation
     */
    enhanceFormNavigation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Add form landmark
            if (!form.hasAttribute('role')) {
                form.setAttribute('role', 'form');
            }
            
            // Add form label if missing
            if (!form.hasAttribute('aria-label') && !form.hasAttribute('aria-labelledby')) {
                const legend = form.querySelector('legend');
                const heading = form.querySelector('h1, h2, h3, h4, h5, h6');
                
                if (legend) {
                    form.setAttribute('aria-labelledby', legend.id || this.generateId());
                } else if (heading) {
                    form.setAttribute('aria-labelledby', heading.id || this.generateId());
                } else {
                    form.setAttribute('aria-label', 'Formulário');
                }
            }
        });
    }

    /**
     * Setup navigation announcements
     */
    setupNavigationAnnouncements() {
        // Route changes (for SPAs)
        window.addEventListener('popstate', () => {
            this.announcePageChange('Página anterior carregada');
        });
        
        // Hash changes
        window.addEventListener('hashchange', () => {
            const target = document.querySelector(window.location.hash);
            if (target) {
                const text = target.textContent?.trim() || target.getAttribute('aria-label') || 'Seção';
                this.announce(`Navegado para: ${text}`, 'assertive');
            }
        });
        
        // Link clicks
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' && e.target.hasAttribute('href')) {
                const href = e.target.getAttribute('href');
                if (href.startsWith('#')) {
                    // Internal anchor
                    const target = document.querySelector(href);
                    if (target) {
                        setTimeout(() => {
                            target.focus();
                            const text = target.textContent?.trim() || target.getAttribute('aria-label') || 'Conteúdo';
                            this.announce(`Navegado para: ${text}`, 'assertive');
                        }, 100);
                    }
                } else if (!href.startsWith('javascript:')) {
                    // External or page navigation
                    this.announce('Carregando nova página...', 'polite');
                }
            }
        });
    }

    /**
     * Setup form announcements
     */
    setupFormAnnouncements() {
        // Form submissions
        document.addEventListener('submit', (e) => {
            this.announce('Formulário enviado', 'polite');
        });
        
        // Form field changes
        document.addEventListener('change', (e) => {
            if (e.target.tagName === 'SELECT') {
                const selectedOption = e.target.options[e.target.selectedIndex];
                this.announce(`Selecionado: ${selectedOption.textContent}`, 'polite');
            }
        });
        
        // Checkbox and radio changes
        document.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                const label = this.getFieldLabel(e.target) || 'Opção';
                const state = e.target.checked ? 'marcada' : 'desmarcada';
                this.announce(`${label} ${state}`, 'polite');
            } else if (e.target.type === 'radio') {
                const label = this.getFieldLabel(e.target) || 'Opção';
                this.announce(`${label} selecionada`, 'polite');
            }
        });
        
        // Form validation
        this.setupFormValidationAnnouncements();
    }

    /**
     * Setup form validation announcements
     */
    setupFormValidationAnnouncements() {
        // Listen for validation events
        document.addEventListener('invalid', (e) => {
            const field = e.target;
            const label = this.getFieldLabel(field) || 'Campo';
            const message = field.validationMessage || 'Valor inválido';
            
            this.announce(`Erro em ${label}: ${message}`, 'assertive');
        });

        // Monitor aria-invalid changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'aria-invalid') {
                    const element = mutation.target;
                    if (element.getAttribute('aria-invalid') === 'true') {
                        const label = this.getFieldLabel(element) || 'Campo';
                        const errorMsg = element.getAttribute('aria-describedby');
                        let message = 'inválido';
                        
                        if (errorMsg) {
                            const errorElement = document.getElementById(errorMsg);
                            if (errorElement) {
                                message = errorElement.textContent?.trim() || message;
                            }
                        }
                        
                        this.announce(`${label}: ${message}`, 'assertive');
                    }
                }
            });
        });

        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ['aria-invalid'],
            subtree: true
        });
    }

    /**
     * Setup content announcements for dynamic updates
     */
    setupContentAnnouncements() {
        // Monitor dynamic content changes
        const contentObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.handleNewContent(node);
                        }
                    });
                }
            });
        });

        contentObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Handle new content being added to the page
     */
    handleNewContent(element) {
        // Announce new alerts or important content
        if (element.classList?.contains('alert') || element.getAttribute('role') === 'alert') {
            const text = element.textContent?.trim();
            if (text) {
                this.announce(text, 'assertive');
            }
        }
        
        // Announce loading states
        if (element.classList?.contains('loading') || element.hasAttribute('aria-busy')) {
            this.announce('Carregando...', 'polite');
        }
        
        // Auto-enhance new elements
        if (this.isScreenReaderActive) {
            this.enhanceNewElementsForScreenReader(element);
        }
    }

    /**
     * Enhance new elements for screen reader compatibility
     */
    enhanceNewElementsForScreenReader(container) {
        // Add missing ARIA labels
        const unlabeledButtons = container.querySelectorAll?.('button:not([aria-label]):not([aria-labelledby])') || [];
        unlabeledButtons.forEach(button => {
            const text = button.textContent?.trim();
            if (!text) {
                button.setAttribute('aria-label', 'Botão');
            }
        });
        
        // Add missing alt text to images
        const images = container.querySelectorAll?.('img:not([alt])') || [];
        images.forEach(img => {
            img.setAttribute('alt', this.generateImageDescription(img));
        });
        
        // Enhance form fields
        const formFields = container.querySelectorAll?.('input, textarea, select') || [];
        formFields.forEach(field => {
            if (!this.getFieldLabel(field)) {
                const placeholder = field.getAttribute('placeholder');
                if (placeholder) {
                    field.setAttribute('aria-label', placeholder);
                }
            }
        });
    }

    /**
     * Generate automatic image descriptions
     */
    generateImageDescription(img) {
        const src = img.src || '';
        const fileName = src.split('/').pop()?.split('.')[0] || '';
        
        // Try to infer content from filename or context
        if (fileName.includes('logo')) {
            return 'Logo';
        } else if (fileName.includes('icon')) {
            return 'Ícone';
        } else if (fileName.includes('avatar') || fileName.includes('profile')) {
            return 'Foto de perfil';
        } else if (img.classList.contains('color-preview')) {
            return 'Amostra de cor';
        } else {
            return 'Imagem';
        }
    }

    /**
     * Main announcement function
     */
    announce(message, priority = 'polite', skipQueue = false) {
        if (!message || !this.config.announcePageChanges) return;
        
        // Truncate long messages
        if (message.length > this.config.maxAnnouncementLength) {
            message = message.substring(0, this.config.maxAnnouncementLength - 3) + '...';
        }
        
        if (skipQueue) {
            this.makeAnnouncement(message, priority);
        } else {
            this.queueAnnouncement(message, priority);
        }
    }

    /**
     * Queue announcements to avoid overwhelming screen readers
     */
    queueAnnouncement(message, priority) {
        this.announcementQueue.push({ message, priority, timestamp: Date.now() });
        
        if (!this.isProcessingQueue) {
            this.processAnnouncementQueue();
        }
    }

    /**
     * Process the announcement queue
     */
    async processAnnouncementQueue() {
        this.isProcessingQueue = true;
        
        while (this.announcementQueue.length > 0) {
            const announcement = this.announcementQueue.shift();
            
            // Skip old announcements
            if (Date.now() - announcement.timestamp > 10000) {
                continue;
            }
            
            await this.makeAnnouncement(announcement.message, announcement.priority);
            await this.delay(this.config.announcementDelay);
        }
        
        this.isProcessingQueue = false;
    }

    /**
     * Make the actual announcement
     */
    async makeAnnouncement(message, priority) {
        // Use live regions first (preferred by screen readers)
        this.announceToLiveRegion(message, priority);
        
        // Also use speech synthesis if available and appropriate
        if (this.shouldUseSpeechSynthesis()) {
            this.announceWithSpeech(message);
        }
    }

    /**
     * Announce to appropriate live region
     */
    announceToLiveRegion(message, priority) {
        let regionId;
        
        if (message.toLowerCase().includes('erro') || priority === 'assertive') {
            regionId = 'errors';
        } else if (message.toLowerCase().includes('carregando') || message.toLowerCase().includes('loading')) {
            regionId = 'loading';
        } else if (message.toLowerCase().includes('status') || message.toLowerCase().includes('sucesso')) {
            regionId = 'status';
        } else if (priority === 'assertive') {
            regionId = 'assertive';
        } else {
            regionId = 'polite';
        }
        
        const region = this.liveRegions.get(regionId);
        if (region) {
            // Clear and set new message
            region.textContent = '';
            setTimeout(() => {
                region.textContent = message;
            }, 50);
        }
    }

    /**
     * Announce with speech synthesis
     */
    announceWithSpeech(message) {
        if (!this.speechSynthesis || !this.config.preferredVoice) return;
        
        // Cancel any ongoing speech
        this.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(message);
        utterance.voice = this.config.preferredVoice;
        utterance.rate = this.config.voiceRate;
        utterance.pitch = this.config.voicePitch;
        utterance.volume = this.config.voiceVolume;
        
        this.speechSynthesis.speak(utterance);
    }

    /**
     * Determine if speech synthesis should be used
     */
    shouldUseSpeechSynthesis() {
        // Don't use speech if a screen reader is already active
        // (to avoid double announcements)
        if (this.isScreenReaderActive && this.screenReaderType !== 'assistive-technology') {
            return false;
        }
        
        // Use speech for browsers without good screen reader support
        return true;
    }

    /**
     * Announce page changes
     */
    announcePageChange(message) {
        if (!this.config.announcePageChanges) return;
        
        this.announce(message || 'Página carregada', 'assertive');
        
        // Also announce page title
        setTimeout(() => {
            const title = document.title;
            if (title) {
                this.announce(`Página: ${title}`, 'polite');
            }
        }, 1000);
    }

    /**
     * Start monitoring for compatibility issues
     */
    startCompatibilityMonitoring() {
        // Monitor for common accessibility issues
        setInterval(() => {
            this.checkForAccessibilityIssues();
        }, 30000); // Check every 30 seconds
        
        // Monitor for screen reader changes
        setInterval(() => {
            this.recheckScreenReaderStatus();
        }, 60000); // Check every minute
    }

    /**
     * Check for common accessibility issues
     */
    checkForAccessibilityIssues() {
        const issues = [];
        
        // Check for missing alt text
        const imagesWithoutAlt = document.querySelectorAll('img:not([alt])');
        if (imagesWithoutAlt.length > 0) {
            issues.push(`${imagesWithoutAlt.length} imagens sem texto alternativo`);
        }
        
        // Check for missing form labels
        const unlabeledFields = Array.from(document.querySelectorAll('input, textarea, select')).filter(field => {
            return !this.getFieldLabel(field) && field.type !== 'hidden' && field.type !== 'submit';
        });
        if (unlabeledFields.length > 0) {
            issues.push(`${unlabeledFields.length} campos de formulário sem rótulo`);
        }
        
        // Check for missing headings
        const hasH1 = document.querySelector('h1');
        if (!hasH1) {
            issues.push('Página sem título principal (H1)');
        }
        
        // Log issues for debugging
        if (issues.length > 0) {
            console.warn('Problemas de acessibilidade detectados:', issues);
        }
    }

    /**
     * Recheck screen reader status
     */
    recheckScreenReaderStatus() {
        const previousStatus = this.isScreenReaderActive;
        this.detectScreenReader();
        
        if (this.isScreenReaderActive !== previousStatus) {
            if (this.isScreenReaderActive) {
                this.enableScreenReaderEnhancements();
                this.announce('Suporte a leitor de tela ativado', 'polite');
            } else {
                document.documentElement.classList.remove('screen-reader-active', `sr-${this.screenReaderType}`);
                console.log('Screen reader support disabled');
            }
        }
    }

    /**
     * Load user preferences
     */
    loadUserPreferences() {
        const prefs = JSON.parse(localStorage.getItem('screenReaderPrefs') || '{}');
        
        this.config = { ...this.config, ...prefs };
    }

    /**
     * Save user preferences
     */
    saveUserPreferences() {
        localStorage.setItem('screenReaderPrefs', JSON.stringify(this.config));
    }

    /**
     * Utility functions
     */
    generateId() {
        return 'sr-id-' + Math.random().toString(36).substr(2, 9);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Public API methods
     */
    
    /**
     * Test screen reader functionality
     */
    runAccessibilityTest() {
        console.log('Running accessibility test...');
        
        this.announce('Iniciando teste de acessibilidade', 'assertive');
        
        setTimeout(() => {
            this.announce('Teste de anúncio polido', 'polite');
        }, 1000);
        
        setTimeout(() => {
            this.announce('Teste de anúncio assertivo', 'assertive');
        }, 2000);
        
        setTimeout(() => {
            this.checkForAccessibilityIssues();
            this.announce('Teste de acessibilidade concluído', 'polite');
        }, 3000);
    }

    /**
     * Get current status
     */
    getStatus() {
        return {
            screenReaderActive: this.isScreenReaderActive,
            screenReaderType: this.screenReaderType,
            speechSynthesisAvailable: !!this.speechSynthesis,
            preferredVoice: this.config.preferredVoice?.name,
            liveRegionsCount: this.liveRegions.size,
            queueLength: this.announcementQueue.length,
            config: this.config
        };
    }

    /**
     * Toggle feature
     */
    toggleFeature(feature, enabled) {
        if (this.config.hasOwnProperty(feature)) {
            this.config[feature] = enabled;
            this.saveUserPreferences();
            this.announce(`${feature} ${enabled ? 'ativado' : 'desativado'}`, 'polite');
        }
    }

    /**
     * Update voice settings
     */
    updateVoiceSettings(settings) {
        this.config = { ...this.config, ...settings };
        this.saveUserPreferences();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ScreenReaderCompatibility();
    });
} else {
    new ScreenReaderCompatibility();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScreenReaderCompatibility;
}