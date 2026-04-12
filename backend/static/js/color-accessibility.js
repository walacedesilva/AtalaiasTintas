/**
 * Color Accessibility System
 * 
 * Provides comprehensive color accessibility features including:
 * - WCAG 2.1 AA contrast ratio validation
 * - Color-blind friendly palettes and indicators
 * - High contrast mode support
 * - Alternative visual indicators for color-coded information
 * - Prefers-color-scheme and prefers-contrast detection
 */

class ColorAccessibility {
    constructor() {
        this.contrastThreshold = {
            AA: {
                normal: 4.5,
                large: 3.0
            },
            AAA: {
                normal: 7.0,
                large: 4.5
            }
        };

        this.colorBlindnessTypes = [
            'protanopia',    // Red-blind
            'deuteranopia',  // Green-blind
            'tritanopia',    // Blue-blind
            'achromatopsia'  // Total color blindness
        ];

        this.highContrastEnabled = false;
        this.colorBlindMode = null;
        this.forcedColors = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        this.init();
    }

    /**
     * Initialize color accessibility system
     */
    init() {
        this.loadUserPreferences();
        this.createColorAccessibilityControls();
        this.enhanceColorElements();
        this.validatePageContrast();
        this.setupMediaQueryListeners();
        this.addKeyboardShortcuts();

        // Add accessibility utilities to global scope
        window.ColorAccessibility = this;
        
        console.log('Color Accessibility System initialized');
    }

    /**
     * Load saved user preferences
     */
    loadUserPreferences() {
        const prefs = JSON.parse(localStorage.getItem('colorAccessibilityPrefs') || '{}');
        
        this.highContrastEnabled = prefs.highContrast || false;
        this.colorBlindMode = prefs.colorBlindMode || null;
        
        if (this.highContrastEnabled) {
            this.enableHighContrast();
        }
        
        if (this.colorBlindMode) {
            this.enableColorBlindMode(this.colorBlindMode);
        }
    }

    /**
     * Save user preferences
     */
    saveUserPreferences() {
        const prefs = {
            highContrast: this.highContrastEnabled,
            colorBlindMode: this.colorBlindMode
        };
        
        localStorage.setItem('colorAccessibilityPrefs', JSON.stringify(prefs));
    }

    /**
     * Create accessibility control panel
     */
    createColorAccessibilityControls() {
        // Check if controls already exist
        if (document.getElementById('color-accessibility-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'color-accessibility-panel';
        panel.className = 'color-accessibility-panel';
        panel.setAttribute('role', 'region');
        panel.setAttribute('aria-label', 'Controles de acessibilidade de cores');
        
        panel.innerHTML = `
            <button type="button" 
                    id="color-accessibility-toggle" 
                    class="btn btn-outline-secondary btn-sm"
                    aria-expanded="false"
                    aria-controls="color-accessibility-options"
                    aria-label="Abrir opções de acessibilidade de cores">
                <i class="bi bi-palette" aria-hidden="true"></i>
                <span class="visually-hidden">Acessibilidade de Cores</span>
            </button>
            
            <div id="color-accessibility-options" 
                 class="color-accessibility-options" 
                 role="menu"
                 aria-labelledby="color-accessibility-toggle"
                 hidden>
                <h3 class="h6 mb-2">Acessibilidade de Cores</h3>
                
                <div class="form-check">
                    <input class="form-check-input" 
                           type="checkbox" 
                           id="high-contrast-toggle"
                           ${this.highContrastEnabled ? 'checked' : ''}>
                    <label class="form-check-label" for="high-contrast-toggle">
                        Alto Contraste
                    </label>
                </div>
                
                <hr class="my-2">
                
                <fieldset>
                    <legend class="form-label small">Simulação de Daltonismo:</legend>
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="radio" 
                               name="colorBlindMode" 
                               value="" 
                               id="colorblind-none"
                               ${!this.colorBlindMode ? 'checked' : ''}>
                        <label class="form-check-label" for="colorblind-none">
                            Visão Normal
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="radio" 
                               name="colorBlindMode" 
                               value="protanopia" 
                               id="colorblind-protanopia"
                               ${this.colorBlindMode === 'protanopia' ? 'checked' : ''}>
                        <label class="form-check-label" for="colorblind-protanopia">
                            Protanopia (Deficiência de Vermelho)
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="radio" 
                               name="colorBlindMode" 
                               value="deuteranopia" 
                               id="colorblind-deuteranopia"
                               ${this.colorBlindMode === 'deuteranopia' ? 'checked' : ''}>
                        <label class="form-check-label" for="colorblind-deuteranopia">
                            Deuteranopia (Deficiência de Verde)
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="radio" 
                               name="colorBlindMode" 
                               value="tritanopia" 
                               id="colorblind-tritanopia"
                               ${this.colorBlindMode === 'tritanopia' ? 'checked' : ''}>
                        <label class="form-check-label" for="colorblind-tritanopia">
                            Tritanopia (Deficiência de Azul)
                        </label>
                    </div>
                </fieldset>
                
                <hr class="my-2">
                
                <button type="button" 
                        id="validate-contrast-btn" 
                        class="btn btn-outline-info btn-sm w-100">
                    <i class="bi bi-eye-fill" aria-hidden="true"></i>
                    Validar Contraste da Página
                </button>
            </div>
        `;

        // Add to page (prepend to body or specific container)
        const targetContainer = document.querySelector('.accessibility-controls') || document.body;
        if (document.querySelector('.accessibility-controls')) {
            targetContainer.appendChild(panel);
        } else {
            targetContainer.prepend(panel);
        }

        this.bindControlEvents();
    }

    /**
     * Bind events to accessibility controls
     */
    bindControlEvents() {
        const toggle = document.getElementById('color-accessibility-toggle');
        const options = document.getElementById('color-accessibility-options');
        const highContrastToggle = document.getElementById('high-contrast-toggle');
        const colorBlindRadios = document.querySelectorAll('input[name="colorBlindMode"]');
        const validateBtn = document.getElementById('validate-contrast-btn');

        // Panel toggle
        toggle?.addEventListener('click', () => {
            const isHidden = options.hasAttribute('hidden');
            
            if (isHidden) {
                options.removeAttribute('hidden');
                toggle.setAttribute('aria-expanded', 'true');
            } else {
                options.setAttribute('hidden', '');
                toggle.setAttribute('aria-expanded', 'false');
            }
        });

        // High contrast toggle
        highContrastToggle?.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.enableHighContrast();
            } else {
                this.disableHighContrast();
            }
            this.saveUserPreferences();
        });

        // Color blind mode selection
        colorBlindRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    const mode = e.target.value;
                    if (mode) {
                        this.enableColorBlindMode(mode);
                    } else {
                        this.disableColorBlindMode();
                    }
                    this.saveUserPreferences();
                }
            });
        });

        // Contrast validation
        validateBtn?.addEventListener('click', () => {
            this.validatePageContrast();
        });

        // Close panel on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#color-accessibility-panel')) {
                options?.setAttribute('hidden', '');
                toggle?.setAttribute('aria-expanded', 'false');
            }
        });
    }

    /**
     * Enable high contrast mode
     */
    enableHighContrast() {
        document.documentElement.classList.add('high-contrast');
        this.highContrastEnabled = true;
        
        // Announce to screen readers
        this.announceChange('Alto contraste ativado');
    }

    /**
     * Disable high contrast mode
     */
    disableHighContrast() {
        document.documentElement.classList.remove('high-contrast');
        this.highContrastEnabled = false;
        
        // Announce to screen readers
        this.announceChange('Alto contraste desativado');
    }

    /**
     * Enable color blind simulation mode
     */
    enableColorBlindMode(mode) {
        // Remove any existing color blind mode
        this.disableColorBlindMode();
        
        document.documentElement.classList.add(`colorblind-${mode}`);
        this.colorBlindMode = mode;
        
        // Announce to screen readers
        const modeNames = {
            protanopia: 'Protanopia (deficiência de vermelho)',
            deuteranopia: 'Deuteranopia (deficiência de verde)',
            tritanopia: 'Tritanopia (deficiência de azul)',
            achromatopsia: 'Acromatopsia (daltonismo total)'
        };
        
        this.announceChange(`Simulação ${modeNames[mode]} ativada`);
    }

    /**
     * Disable color blind simulation mode
     */
    disableColorBlindMode() {
        this.colorBlindnessTypes.forEach(type => {
            document.documentElement.classList.remove(`colorblind-${type}`);
        });
        
        this.colorBlindMode = null;
        this.announceChange('Simulação de daltonismo desativada');
    }

    /**
     * Enhance color-coded elements with additional indicators
     */
    enhanceColorElements() {
        // Find elements that rely solely on color for information
        const colorElements = document.querySelectorAll(`
            .badge, .alert, .btn, .text-success, .text-warning, 
            .text-danger, .text-info, .bg-success, .bg-warning, 
            .bg-danger, .bg-info, .stats-card
        `);

        colorElements.forEach(element => {
            this.enhanceColorElement(element);
        });

        // Enhance status indicators
        this.enhanceStatusIndicators();
        
        // Enhance charts and graphs
        this.enhanceDataVisualizations();
    }

    /**
     * Enhance individual color element
     */
    enhanceColorElement(element) {
        // Skip if already enhanced
        if (element.hasAttribute('data-color-enhanced')) return;

        const classes = Array.from(element.classList);
        let indicator = null;
        let pattern = null;

        // Determine appropriate indicator based on semantic meaning
        if (classes.some(cls => cls.includes('success') || cls.includes('green'))) {
            indicator = '✓';
            pattern = 'success-pattern';
            element.setAttribute('aria-label', 
                element.getAttribute('aria-label') || 'Sucesso: ' + element.textContent?.trim());
        } else if (classes.some(cls => cls.includes('warning') || cls.includes('yellow'))) {
            indicator = '⚠';
            pattern = 'warning-pattern';
            element.setAttribute('aria-label', 
                element.getAttribute('aria-label') || 'Aviso: ' + element.textContent?.trim());
        } else if (classes.some(cls => cls.includes('danger') || cls.includes('error') || cls.includes('red'))) {
            indicator = '✗';
            pattern = 'danger-pattern';
            element.setAttribute('aria-label', 
                element.getAttribute('aria-label') || 'Erro: ' + element.textContent?.trim());
        } else if (classes.some(cls => cls.includes('info') || cls.includes('blue'))) {
            indicator = 'ⓘ';
            pattern = 'info-pattern';
            element.setAttribute('aria-label', 
                element.getAttribute('aria-label') || 'Informação: ' + element.textContent?.trim());
        }

        // Add visual indicator
        if (indicator && !element.querySelector('.color-indicator')) {
            const indicatorSpan = document.createElement('span');
            indicatorSpan.className = 'color-indicator';
            indicatorSpan.setAttribute('aria-hidden', 'true');
            indicatorSpan.textContent = indicator;
            
            // Position indicator based on element type
            if (element.classList.contains('badge')) {
                element.prepend(indicatorSpan);
            } else {
                element.appendChild(indicatorSpan);
            }
        }

        // Add pattern class for CSS-based patterns
        if (pattern) {
            element.classList.add(pattern);
        }

        element.setAttribute('data-color-enhanced', 'true');
    }

    /**
     * Enhance status indicators throughout the page
     */
    enhanceStatusIndicators() {
        // Find progress bars
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const value = bar.getAttribute('aria-valuenow') || 
                         bar.style.width?.replace('%', '') || '0';
            
            // Add textual progress indicator
            if (!bar.querySelector('.progress-text')) {
                const textSpan = document.createElement('span');
                textSpan.className = 'progress-text visually-hidden';
                textSpan.textContent = `${value}% completo`;
                bar.appendChild(textSpan);
            }
        });

        // Find color-coded dots/circles
        const colorDots = document.querySelectorAll('.color-dot, .status-dot');
        colorDots.forEach(dot => {
            if (!dot.hasAttribute('aria-label') && !dot.hasAttribute('title')) {
                // Try to infer meaning from color or context
                const computedStyle = getComputedStyle(dot);
                const bgColor = computedStyle.backgroundColor;
                const label = this.inferColorMeaning(bgColor, dot);
                
                if (label) {
                    dot.setAttribute('aria-label', label);
                }
            }
        });
    }

    /**
     * Enhance data visualizations (charts, graphs)
     */
    enhanceDataVisualizations() {
        // This can be extended to work with specific charting libraries
        const charts = document.querySelectorAll('.chart, .graph, canvas');
        
        charts.forEach(chart => {
            // Add alternative text description
            if (!chart.hasAttribute('aria-label')) {
                chart.setAttribute('role', 'img');
                chart.setAttribute('aria-label', 'Gráfico de dados - descrição textual disponível');
            }
            
            // Add patterns or textures for chart elements if possible
            this.addChartPatterns(chart);
        });
    }

    /**
     * Add patterns to chart elements
     */
    addChartPatterns(chartElement) {
        // This would integrate with specific charting libraries
        // For now, we add a general enhancement class
        chartElement.classList.add('chart-accessible');
        
        // Create a description element if it doesn't exist
        if (!chartElement.nextElementSibling?.classList.contains('chart-description')) {
            const description = document.createElement('div');
            description.className = 'chart-description visually-hidden';
            description.innerHTML = `
                <h4>Descrição do Gráfico</h4>
                <p>Use os controles de acessibilidade para melhor visualização dos dados.</p>
            `;
            chartElement.insertAdjacentElement('afterend', description);
        }
    }

    /**
     * Validate color contrast across the page
     */
    validatePageContrast() {
        const results = [];
        
        // Get all text elements
        const textElements = document.querySelectorAll(`
            p, h1, h2, h3, h4, h5, h6, span, div, 
            a, button, label, input, textarea, select,
            .btn, .card-title, .card-text, .form-label
        `);

        textElements.forEach(element => {
            const result = this.checkElementContrast(element);
            if (result && !result.passes) {
                results.push(result);
            }
        });

        this.displayContrastResults(results);
        return results;
    }

    /**
     * Check contrast ratio for a specific element
     */
    checkElementContrast(element) {
        const style = getComputedStyle(element);
        const textColor = style.color;
        const backgroundColor = this.getEffectiveBackgroundColor(element);
        
        if (!backgroundColor || textColor === backgroundColor) {
            return null;
        }

        const contrast = this.calculateContrastRatio(textColor, backgroundColor);
        const fontSize = parseFloat(style.fontSize);
        const fontWeight = style.fontWeight;
        
        const isLargeText = fontSize >= 18 || (fontSize >= 14 && (fontWeight === 'bold' || parseInt(fontWeight) >= 700));
        const requiredRatio = isLargeText ? this.contrastThreshold.AA.large : this.contrastThreshold.AA.normal;
        
        const passes = contrast >= requiredRatio;

        return {
            element,
            textColor,
            backgroundColor,
            contrast: parseFloat(contrast.toFixed(2)),
            requiredRatio,
            passes,
            isLargeText,
            recommendation: this.getContrastRecommendation(contrast, requiredRatio, textColor, backgroundColor)
        };
    }

    /**
     * Get effective background color considering parent elements
     */
    getEffectiveBackgroundColor(element) {
        let current = element;
        
        while (current && current !== document.body) {
            const style = getComputedStyle(current);
            const bgColor = style.backgroundColor;
            
            if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {
                return bgColor;
            }
            
            current = current.parentElement;
        }
        
        // Default to white background
        return 'rgb(255, 255, 255)';
    }

    /**
     * Calculate contrast ratio between two colors
     */
    calculateContrastRatio(color1, color2) {
        const rgb1 = this.getRgbValues(color1);
        const rgb2 = this.getRgbValues(color2);
        
        if (!rgb1 || !rgb2) return 1;
        
        const lum1 = this.getRelativeLuminance(rgb1);
        const lum2 = this.getRelativeLuminance(rgb2);
        
        const lighter = Math.max(lum1, lum2);
        const darker = Math.min(lum1, lum2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    /**
     * Extract RGB values from color string
     */
    getRgbValues(colorString) {
        // Handle rgb(), rgba(), hex, and named colors
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = 1;
        const ctx = canvas.getContext('2d');
        
        ctx.fillStyle = colorString;
        ctx.fillRect(0, 0, 1, 1);
        
        const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
        return { r, g, b };
    }

    /**
     * Calculate relative luminance
     */
    getRelativeLuminance({ r, g, b }) {
        const rsRGB = r / 255;
        const gsRGB = g / 255;
        const bsRGB = b / 255;
        
        const rLin = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
        const gLin = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
        const bLin = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);
        
        return 0.2126 * rLin + 0.7152 * gLin + 0.0722 * bLin;
    }

    /**
     * Get contrast improvement recommendation
     */
    getContrastRecommendation(currentRatio, requiredRatio, textColor, backgroundColor) {
        if (currentRatio >= requiredRatio) {
            return 'Contraste adequado';
        }
        
        const difference = requiredRatio - currentRatio;
        
        if (difference < 1) {
            return 'Ajuste ligeiro necessário na cor do texto ou fundo';
        } else if (difference < 2) {
            return 'Melhoria moderada necessária - considere texto mais escuro ou fundo mais claro';
        } else {
            return 'Melhoria significativa necessária - contraste insuficiente para acessibilidade';
        }
    }

    /**
     * Display contrast validation results
     */
    displayContrastResults(results) {
        // Remove existing results
        const existingResults = document.getElementById('contrast-results');
        if (existingResults) {
            existingResults.remove();
        }

        if (results.length === 0) {
            this.announceChange('Validação de contraste: Todos os elementos passaram no teste WCAG AA');
            return;
        }

        // Create results panel
        const resultsPanel = document.createElement('div');
        resultsPanel.id = 'contrast-results';
        resultsPanel.className = 'contrast-results-panel';
        resultsPanel.setAttribute('role', 'region');
        resultsPanel.setAttribute('aria-label', 'Resultados da validação de contraste');
        
        resultsPanel.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h3 class="h5 mb-0">Problemas de Contraste Encontrados</h3>
                <button type="button" class="btn-close" aria-label="Fechar resultados"></button>
            </div>
            
            <p class="text-warning mb-3">
                <i class="bi bi-exclamation-triangle" aria-hidden="true"></i>
                ${results.length} elemento(s) não atendem aos padrões WCAG 2.1 AA
            </p>
            
            <div class="contrast-results-list" style="max-height: 300px; overflow-y: auto;">
                ${results.map((result, index) => `
                    <div class="contrast-result-item border rounded p-2 mb-2" data-element-index="${index}">
                        <div class="d-flex justify-content-between align-items-start mb-1">
                            <strong class="text-danger">
                                Contraste: ${result.contrast}:1
                            </strong>
                            <small class="text-muted">
                                Exigido: ${result.requiredRatio}:1
                            </small>
                        </div>
                        <p class="mb-1 small">
                            <strong>Elemento:</strong> ${result.element.tagName.toLowerCase()}${result.element.className ? '.' + result.element.className.split(' ')[0] : ''}
                        </p>
                        <p class="mb-1 small">
                            <strong>Texto:</strong> ${result.element.textContent?.slice(0, 50)}${result.element.textContent?.length > 50 ? '...' : ''}
                        </p>
                        <p class="mb-2 small text-info">
                            ${result.recommendation}
                        </p>
                        <button type="button" 
                                class="btn btn-outline-primary btn-sm highlight-element-btn"
                                data-element-index="${index}">
                            <i class="bi bi-cursor" aria-hidden="true"></i>
                            Destacar Elemento
                        </button>
                    </div>
                `).join('')}
            </div>
        `;

        // Add to page
        document.body.appendChild(resultsPanel);

        // Bind events
        resultsPanel.querySelector('.btn-close')?.addEventListener('click', () => {
            resultsPanel.remove();
        });

        resultsPanel.querySelectorAll('.highlight-element-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.closest('.highlight-element-btn').dataset.elementIndex);
                this.highlightElement(results[index].element);
            });
        });

        // Announce results
        this.announceChange(`Validação concluída: ${results.length} problemas de contraste encontrados`);
    }

    /**
     * Highlight a specific element temporarily
     */
    highlightElement(element) {
        // Remove existing highlights
        document.querySelectorAll('.contrast-highlight').forEach(el => {
            el.classList.remove('contrast-highlight');
        });

        // Add highlight
        element.classList.add('contrast-highlight');
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Remove highlight after 3 seconds
        setTimeout(() => {
            element.classList.remove('contrast-highlight');
        }, 3000);
    }

    /**
     * Infer color meaning from context
     */
    inferColorMeaning(bgColor, element) {
        // This is a basic implementation - could be made more sophisticated
        const rgb = this.getRgbValues(bgColor);
        if (!rgb) return null;

        const { r, g, b } = rgb;
        
        if (g > r && g > b && g > 150) {
            return 'Status: Verde (Positivo)';
        } else if (r > g && r > b && r > 150) {
            return 'Status: Vermelho (Atenção)';
        } else if ((r + g) > b && r > 150 && g > 150) {
            return 'Status: Amarelo (Aviso)';
        } else if (b > r && b > g && b > 150) {
            return 'Status: Azul (Informação)';
        }
        
        return 'Indicador colorido';
    }

    /**
     * Setup media query listeners for system preferences
     */
    setupMediaQueryListeners() {
        // Watch for prefers-color-scheme changes
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        darkModeQuery.addEventListener('change', (e) => {
            this.handleSystemColorSchemeChange(e.matches);
        });

        // Watch for prefers-contrast changes
        const contrastQuery = window.matchMedia('(prefers-contrast: high)');
        contrastQuery.addEventListener('change', (e) => {
            if (e.matches && !this.highContrastEnabled) {
                this.enableHighContrast();
                this.saveUserPreferences();
            }
        });

        // Watch for prefers-reduced-motion
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        motionQuery.addEventListener('change', (e) => {
            document.documentElement.classList.toggle('reduce-motion', e.matches);
        });

        // Initialize current states
        if (darkModeQuery.matches) {
            document.documentElement.classList.add('prefers-dark');
        }
        if (contrastQuery.matches && !this.highContrastEnabled) {
            this.enableHighContrast();
        }
        if (motionQuery.matches) {
            document.documentElement.classList.add('reduce-motion');
        }
    }

    /**
     * Handle system color scheme changes
     */
    handleSystemColorSchemeChange(isDark) {
        document.documentElement.classList.toggle('prefers-dark', isDark);
        
        // Re-validate contrasts as they may have changed
        if (document.getElementById('contrast-results')) {
            setTimeout(() => this.validatePageContrast(), 100);
        }
    }

    /**
     * Add keyboard shortcuts for accessibility features
     */
    addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Alt+H: Toggle high contrast
            if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'h') {
                e.preventDefault();
                
                if (this.highContrastEnabled) {
                    this.disableHighContrast();
                } else {
                    this.enableHighContrast();
                }
                this.saveUserPreferences();
            }
            
            // Ctrl+Alt+C: Validate contrast
            if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'c') {
                e.preventDefault();
                this.validatePageContrast();
            }
            
            // Ctrl+Alt+R: Reset color accessibility settings
            if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'r') {
                e.preventDefault();
                this.resetAccessibilitySettings();
            }
        });
    }

    /**
     * Reset all accessibility settings
     */
    resetAccessibilitySettings() {
        this.disableHighContrast();
        this.disableColorBlindMode();
        
        localStorage.removeItem('colorAccessibilityPrefs');
        
        // Update UI controls
        const highContrastToggle = document.getElementById('high-contrast-toggle');
        const colorBlindNone = document.getElementById('colorblind-none');
        
        if (highContrastToggle) highContrastToggle.checked = false;
        if (colorBlindNone) colorBlindNone.checked = true;
        
        this.announceChange('Configurações de acessibilidade resetadas');
    }

    /**
     * Announce changes to screen readers
     */
    announceChange(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    /**
     * Public method to enhance new content dynamically
     */
    enhanceNewContent(container = document) {
        const newColorElements = container.querySelectorAll(`
            .badge:not([data-color-enhanced]), 
            .alert:not([data-color-enhanced]), 
            .btn:not([data-color-enhanced]),
            .text-success:not([data-color-enhanced]), 
            .text-warning:not([data-color-enhanced]), 
            .text-danger:not([data-color-enhanced]), 
            .text-info:not([data-color-enhanced])
        `);

        newColorElements.forEach(element => {
            this.enhanceColorElement(element);
        });
    }

    /**
     * Get current accessibility status
     */
    getStatus() {
        return {
            highContrast: this.highContrastEnabled,
            colorBlindMode: this.colorBlindMode,
            systemPreferences: {
                prefersColorScheme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
                prefersContrast: window.matchMedia('(prefers-contrast: high)').matches ? 'high' : 'normal',
                prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
            }
        };
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ColorAccessibility();
    });
} else {
    new ColorAccessibility();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ColorAccessibility;
}