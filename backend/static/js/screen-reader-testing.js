/**
 * Screen Reader Testing and Integration
 * 
 * Provides testing utilities and integration for the screen reader compatibility system
 */

// Wait for both screen reader and DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize screen reader testing once the system is ready
    waitForScreenReaderSystem();
});

function waitForScreenReaderSystem() {
    if (window.ScreenReaderCompatibility) {
        initScreenReaderTesting();
    } else {
        // Wait a bit more for the system to load
        setTimeout(waitForScreenReaderSystem, 100);
    }
}

function initScreenReaderTesting() {
    console.log('Initializing screen reader testing system...');
    
    // Get buttons
    const testAnnounceBtn = document.getElementById('sr-test-announce');
    const testNavigationBtn = document.getElementById('sr-test-navigation');
    const testFormsBtn = document.getElementById('sr-test-forms');
    const testStatusBtn = document.getElementById('sr-test-status');
    
    if (!testAnnounceBtn) {
        console.warn('Screen reader test buttons not found');
        return;
    }
    
    // Add event listeners
    testAnnounceBtn.addEventListener('click', testAnnouncements);
    testNavigationBtn.addEventListener('click', testNavigation);
    testFormsBtn.addEventListener('click', testForms);
    testStatusBtn.addEventListener('click', showSystemStatus);
    
    // Add keyboard shortcuts for testing
    document.addEventListener('keydown', function(e) {
        // Ctrl+Alt+T for testing panel
        if (e.ctrlKey && e.altKey && e.key === 't') {
            e.preventDefault();
            toggleTestingPanel();
        }
        
        // Ctrl+Alt+A for announcement test
        if (e.ctrlKey && e.altKey && e.key === 'a') {
            e.preventDefault();
            testAnnouncements();
        }
        
        // Ctrl+Alt+N for navigation test
        if (e.ctrlKey && e.altKey && e.key === 'n') {
            e.preventDefault();
            testNavigation();
        }
        
        // Ctrl+Alt+F for forms test
        if (e.ctrlKey && e.altKey && e.key === 'f') {
            e.preventDefault();
            testForms();
        }
        
        // Ctrl+Alt+S for status
        if (e.ctrlKey && e.altKey && e.key === 's') {
            e.preventDefault();
            showSystemStatus();
        }
    });
    
    // Auto-run accessibility test if screen reader detected
    setTimeout(() => {
        if (window.ScreenReaderCompatibility && window.ScreenReaderCompatibility.isScreenReaderActive) {
            console.log('Screen reader detected - running initial accessibility test');
            runInitialAccessibilityTest();
        }
    }, 2000);
    
    console.log('Screen reader testing system initialized');
}

/**
 * Toggle the testing panel visibility
 */
function toggleTestingPanel() {
    const panel = document.getElementById('screen-reader-test-panel');
    if (panel.classList.contains('visually-hidden')) {
        panel.classList.remove('visually-hidden');
        panel.setAttribute('aria-hidden', 'false');
        if (window.ScreenReaderCompatibility) {
            window.ScreenReaderCompatibility.announce('Painel de testes do leitor de tela aberto', 'assertive');
        }
    } else {
        panel.classList.add('visually-hidden');
        panel.setAttribute('aria-hidden', 'true');
        if (window.ScreenReaderCompatibility) {
            window.ScreenReaderCompatibility.announce('Painel de testes do leitor de tela fechado', 'polite');
        }
    }
}

/**
 * Test announcement system
 */
function testAnnouncements() {
    if (!window.ScreenReaderCompatibility) {
        alert('Sistema de leitor de tela não disponível');
        return;
    }
    
    const sr = window.ScreenReaderCompatibility;
    
    // Test different types of announcements
    sr.announce('Teste de anúncio polido - esta mensagem deve ser lida pelo leitor de tela', 'polite');
    
    setTimeout(() => {
        sr.announce('Teste de anúncio assertivo - esta mensagem deve interromper outros anúncios', 'assertive');
    }, 2000);
    
    setTimeout(() => {
        sr.announce('Teste de anúncio de status - confirmação de ação', 'polite');
    }, 4000);
    
    setTimeout(() => {
        sr.announce('Teste de erro - simulação de mensagem de erro', 'assertive');
    }, 6000);
    
    setTimeout(() => {
        sr.announce('Teste de carregamento - simulação de estado de loading', 'polite');
    }, 8000);
    
    console.log('Announcement test completed');
}

/**
 * Test navigation announcements
 */
function testNavigation() {
    if (!window.ScreenReaderCompatibility) {
        alert('Sistema de leitor de tela não disponível');
        return;
    }
    
    const sr = window.ScreenReaderCompatibility;
    
    // Test page change announcement
    sr.announcePageChange('Teste de mudança de página');
    
    setTimeout(() => {
        // Simulate focus changes for testing
        const focusableElements = document.querySelectorAll('button, a, input, select, textarea');
        if (focusableElements.length > 0) {
            const randomIndex = Math.floor(Math.random() * Math.min(5, focusableElements.length));
            const testElement = focusableElements[randomIndex];
            testElement.focus();
            setTimeout(() => testElement.blur(), 1000);
        }
    }, 2000);
    
    setTimeout(() => {
        // Test landmark navigation
        sr.announce('Navegando para seção principal', 'assertive');
        const mainContent = document.getElementById('main-content') || document.querySelector('main');
        if (mainContent) {
            mainContent.focus();
            setTimeout(() => mainContent.blur(), 1000);
        }
    }, 4000);
    
    console.log('Navigation test completed');
}

/**
 * Test form announcements
 */
function testForms() {
    if (!window.ScreenReaderCompatibility) {
        alert('Sistema de leitor de tela não disponível');
        return;
    }
    
    const sr = window.ScreenReaderCompatibility;
    
    // Find form elements to test
    const forms = document.querySelectorAll('form');
    const inputs = document.querySelectorAll('input, textarea, select');
    
    if (forms.length === 0 && inputs.length === 0) {
        sr.announce('Nenhum formulário encontrado na página para testar', 'polite');
        return;
    }
    
    sr.announce('Iniciando teste de formulários', 'polite');
    
    setTimeout(() => {
        // Test form field announcements
        if (inputs.length > 0) {
            const testField = inputs[0];
            testField.focus();
            
            setTimeout(() => {
                // Simulate field change
                if (testField.type === 'text' || testField.tagName === 'TEXTAREA') {
                    const originalValue = testField.value;
                    testField.value = 'Teste de entrada';
                    testField.dispatchEvent(new Event('change'));
                    
                    setTimeout(() => {
                        testField.value = originalValue;
                        testField.blur();
                    }, 2000);
                } else if (testField.type === 'checkbox') {
                    testField.checked = !testField.checked;
                    testField.dispatchEvent(new Event('change'));
                    
                    setTimeout(() => {
                        testField.checked = !testField.checked;
                        testField.blur();
                    }, 2000);
                }
            }, 1000);
        }
    }, 2000);
    
    setTimeout(() => {
        // Test validation announcements
        sr.announce('Teste de erro de validação de formulário', 'assertive');
        
        // Create temporary validation message
        if (inputs.length > 0) {
            const testField = inputs[0];
            testField.setAttribute('aria-invalid', 'true');
            const errorId = 'test-error-' + Date.now();
            const errorMsg = document.createElement('div');
            errorMsg.id = errorId;
            errorMsg.className = 'field-error';
            errorMsg.textContent = 'Este é um teste de mensagem de erro';
            testField.setAttribute('aria-describedby', errorId);
            testField.parentNode.insertBefore(errorMsg, testField.nextSibling);
            
            setTimeout(() => {
                // Clean up test elements
                testField.removeAttribute('aria-invalid');
                testField.removeAttribute('aria-describedby');
                if (errorMsg.parentNode) {
                    errorMsg.parentNode.removeChild(errorMsg);
                }
            }, 3000);
        }
    }, 6000);
    
    console.log('Forms test completed');
}

/**
 * Show system status
 */
function showSystemStatus() {
    if (!window.ScreenReaderCompatibility) {
        alert('Sistema de leitor de tela não disponível');
        return;
    }
    
    const status = window.ScreenReaderCompatibility.getStatus();
    
    // Create status message
    const statusMessages = [
        `Leitor de tela ${status.screenReaderActive ? 'detectado' : 'não detectado'}`,
        status.screenReaderType ? `Tipo: ${status.screenReaderType}` : null,
        `Síntese de voz ${status.speechSynthesisAvailable ? 'disponível' : 'não disponível'}`,
        status.preferredVoice ? `Voz preferida: ${status.preferredVoice}` : null,
        `${status.liveRegionsCount} regiões dinâmicas ativas`,
        `${status.queueLength} anúncios na fila`
    ].filter(Boolean);
    
    const statusText = statusMessages.join('. ');
    
    window.ScreenReaderCompatibility.announce(statusText, 'polite');
    
    // Also log to console for debugging
    console.log('Screen Reader System Status:', status);
    
    // Show in alert for visual users too
    setTimeout(() => {
        const alertMsg = `Status do Sistema de Leitor de Tela:\n\n${statusMessages.join('\\n')}`;
        alert(alertMsg);
    }, 1000);
}

/**
 * Run initial accessibility test
 */
function runInitialAccessibilityTest() {
    if (!window.ScreenReaderCompatibility) return;
    
    console.log('Running initial accessibility test...');
    
    setTimeout(() => {
        window.ScreenReaderCompatibility.runAccessibilityTest();
    }, 1000);
    
    // Add testing shortcuts notice
    setTimeout(() => {
        window.ScreenReaderCompatibility.announce(
            'Atalhos de teste disponíveis: Ctrl+Alt+T para painel, Ctrl+Alt+A para anúncios, Ctrl+Alt+N para navegação', 
            'polite'
        );
    }, 3000);
}

/**
 * Enhanced error handling for screen reader compatibility
 */
window.addEventListener('error', function(e) {
    if (window.ScreenReaderCompatibility) {
        // Don't announce all errors, only critical ones
        if (e.error && e.error.message && e.error.message.includes('accessibility')) {
            window.ScreenReaderCompatibility.announce('Erro de acessibilidade detectado', 'assertive');
        }
    }
});

/**
 * Monitor for dynamic content changes and enhance them
 */
function setupDynamicContentMonitoring() {
    if (!window.ScreenReaderCompatibility) return;
    
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        enhanceNewContent(node);
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

/**
 * Enhance new content for screen readers
 */
function enhanceNewContent(element) {
    // Add missing ARIA labels to buttons
    const buttons = element.querySelectorAll ? element.querySelectorAll('button:not([aria-label]):not([aria-labelledby])') : [];
    buttons.forEach(function(button) {
        if (!button.textContent.trim()) {
            button.setAttribute('aria-label', 'Botão');
        }
    });
    
    // Add missing alt text to images
    const images = element.querySelectorAll ? element.querySelectorAll('img:not([alt])') : [];
    images.forEach(function(img) {
        const src = img.src || '';
        if (src.includes('icon')) {
            img.setAttribute('alt', 'Ícone');
        } else if (src.includes('logo')) {
            img.setAttribute('alt', 'Logo');
        } else {
            img.setAttribute('alt', 'Imagem');
        }
    });
    
    // Ensure form fields have labels
    const formFields = element.querySelectorAll ? element.querySelectorAll('input:not([aria-label]):not([aria-labelledby]), textarea:not([aria-label]):not([aria-labelledby]), select:not([aria-label]):not([aria-labelledby])') : [];
    formFields.forEach(function(field) {
        const placeholder = field.getAttribute('placeholder');
        if (placeholder && !field.labels || field.labels.length === 0) {
            field.setAttribute('aria-label', placeholder);
        }
    });
    
    // Announce significant new content
    if (element.classList && (element.classList.contains('alert') || element.hasAttribute('role') === 'alert')) {
        const text = element.textContent?.trim();
        if (text && window.ScreenReaderCompatibility) {
            window.ScreenReaderCompatibility.announce(text, 'assertive');
        }
    }
}

// Start monitoring once the page is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupDynamicContentMonitoring);
} else {
    setupDynamicContentMonitoring();
}

// Export for debugging
window.ScreenReaderTesting = {
    testAnnouncements,
    testNavigation,
    testForms,
    showSystemStatus,
    toggleTestingPanel,
    runInitialAccessibilityTest
};