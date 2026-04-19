/**
 * ===================================
 * PERFORMANCE OPTIMIZATION SYSTEM
 * Feature: 3-modern-web-interface
 * Task: T021 - Optimize CSS Delivery
 * Task: T022 - JavaScript Optimization
 * Task: T023 - Performance Monitoring
 * ===================================
 */

class PerformanceOptimizer {
    constructor() {
        this.criticalResources = new Set();
        this.deferredResources = new Set();
        this.performanceObserver = null;
        this.webVitals = {
            FCP: null, // First Contentful Paint
            LCP: null, // Largest Contentful Paint
            FID: null, // First Input Delay
            CLS: null, // Cumulative Layout Shift
            TTFB: null // Time to First Byte
        };
        this.performanceBudgets = {
            FCP: 1800, // 1.8s
            LCP: 2500, // 2.5s
            FID: 100,  // 100ms
            CLS: 0.1   // 0.1 units
        };
        
        this.init();
    }

    /**
     * Initialize performance optimization system
     */
    init() {
        this.setupCSSOptimization();
        this.setupJavaScriptOptimization();
        this.setupPerformanceMonitoring();
        this.setupResourceHints();
        this.setupLazyLoading();
        
        console.log('🚀 Performance Optimization System initialized');
    }

    /**
     * CSS Delivery Optimization (T021)
     */
    setupCSSOptimization() {
        // Inline critical CSS detection and management
        this.inlineCriticalCSS();
        
        // Asynchronous non-critical CSS loading
        this.loadNonCriticalCSS();
        
        // Font loading optimization
        this.optimizeFontLoading();
        
        // Remove unused CSS (production only)
        if (this.isProduction()) {
            this.removeUnusedCSS();
        }
        
        console.log('✅ CSS delivery optimized');
    }

    /**
     * Inline critical CSS for above-the-fold content
     */
    inlineCriticalCSS() {
        // Check if critical CSS is already inlined
        if (document.querySelector('#critical-css-inline')) return;

        const criticalCSS = `
            /* Critical CSS - Above the fold */
            :root {
                --primary-color: #2563eb;
                --secondary-color: #64748b;
                --text-primary: #111827;
                --bg-primary: #ffffff;
                --border-color: #e5e7eb;
            }
            
            body {
                font-family: system-ui, -apple-system, sans-serif;
                margin: 0;
                padding: 0;
                line-height: 1.6;
                color: var(--text-primary);
                background: var(--bg-primary);
            }
            
            .app-container {
                display: grid;
                grid-template-columns: 280px 1fr;
                min-height: 100vh;
            }
            
            .app-header {
                background: var(--bg-primary);
                border-bottom: 1px solid var(--border-color);
                padding: 0.75rem 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                z-index: 1000;
            }
            
            .app-sidebar {
                background: #f8fafc;
                border-right: 1px solid var(--border-color);
                overflow-y: auto;
            }
            
            .app-main {
                padding: 1rem;
                overflow: auto;
            }
            
            /* Mobile first */
            @media (max-width: 1024px) {
                .app-container {
                    grid-template-columns: 1fr;
                }
                .app-sidebar {
                    position: fixed;
                    left: -280px;
                    width: 280px;
                    height: 100vh;
                    transition: left 0.3s ease;
                    z-index: 1100;
                }
                .app-sidebar.show {
                    left: 0;
                }
            }
            
            /* Skip links */
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: var(--primary-color);
                color: white;
                padding: 8px;
                text-decoration: none;
                border-radius: 0 0 4px 4px;
                z-index: 9999;
                transition: top 0.2s;
            }
            .skip-link:focus {
                top: 0;
            }
            
            /* Loading states */
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.9);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            }
            .loading-overlay.active {
                display: flex;
            }
            .spinner {
                width: 2rem;
                height: 2rem;
                border: 2px solid var(--border-color);
                border-top: 2px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;

        // Inject critical CSS
        const style = document.createElement('style');
        style.id = 'critical-css-inline';
        style.textContent = criticalCSS;
        document.head.insertBefore(style, document.head.firstChild);

        // Mark as critical resource
        this.criticalResources.add('critical-css');
    }

    /**
     * Load non-critical CSS asynchronously
     */
    loadNonCriticalCSS() {
        const nonCriticalCSS = [
            '/static/css/components.css',
            '/static/css/typography.css', 
            '/static/css/color-accessibility.css',
            '/static/css/screen-reader.css'
        ];

        nonCriticalCSS.forEach(href => {
            this.loadCSSAsync(href);
        });
    }

    /**
     * Load CSS file asynchronously
     */
    loadCSSAsync(href) {
        // Check if already loaded
        if (document.querySelector(`link[href="${href}"]`)) return;

        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'style';
        link.href = href;
        link.onload = function() {
            this.onload = null;
            this.rel = 'stylesheet';
        };
        
        // Fallback for browsers that don't support preload
        const noscript = document.createElement('noscript');
        const fallbackLink = document.createElement('link');
        fallbackLink.rel = 'stylesheet';
        fallbackLink.href = href;
        noscript.appendChild(fallbackLink);
        
        document.head.appendChild(link);
        document.head.appendChild(noscript);
        
        this.deferredResources.add(href);
    }

    /**
     * Optimize font loading
     */
    optimizeFontLoading() {
        // Ensure proper font loading without conflicting @font-face rules
        // Only add preload hints for actually used fonts
        const existingFontLinks = document.querySelectorAll('link[href*="fonts.googleapis.com"]');
        
        if (existingFontLinks.length > 0) {
            existingFontLinks.forEach(link => {
                if (!link.hasAttribute('rel') || link.rel !== 'preload') {
                    // Convert to preload for better performance
                    const preloadLink = document.createElement('link');
                    preloadLink.rel = 'preload';
                    preloadLink.as = 'style';
                    preloadLink.href = link.href;
                    preloadLink.crossOrigin = 'anonymous';
                    document.head.insertBefore(preloadLink, link);
                }
            });
        }

        // Add font-display: swap via CSS
        if (!document.querySelector('#font-optimization')) {
            const style = document.createElement('style');
            style.id = 'font-optimization';
            style.textContent = `
                * {
                    font-display: swap;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Remove unused CSS (production build step simulation)
     */
    removeUnusedCSS() {
        // This would typically be done at build time with tools like PurgeCSS
        // Here we simulate by removing known unused Bootstrap components
        const unusedSelectors = [
            '.accordion',
            '.carousel',
            '.offcanvas',
            '.toast',
            '.popover'
        ];

        // In a real implementation, this would be part of the build process
        console.log('📦 Unused CSS removal would happen at build time');
    }

    /**
     * JavaScript Optimization (T022)
     */
    setupJavaScriptOptimization() {
        this.deferNonCriticalJS();
        this.enableCodeSplitting();
        this.loadPolyfillsConditionally();
        this.preventMainThreadBlocking();
        
        console.log('✅ JavaScript optimization enabled');
    }

    /**
     * Defer non-critical JavaScript
     */
    deferNonCriticalJS() {
        // Identify and defer non-critical scripts
        const scripts = document.querySelectorAll('script[src]');
        
        scripts.forEach(script => {
            const src = script.getAttribute('src');
            
            // Skip critical scripts (framework, polyfills)
            if (this.isCriticalScript(src)) return;
            
            // Add defer attribute if not already present
            if (!script.hasAttribute('defer') && !script.hasAttribute('async')) {
                script.setAttribute('defer', '');
            }
        });
    }

    /**
     * Check if script is critical for initial page load
     */
    isCriticalScript(src) {
        const criticalPatterns = [
            'bootstrap.bundle',
            'accessibility.js',
            'critical'
        ];
        
        return criticalPatterns.some(pattern => src.includes(pattern));
    }

    /**
     * Enable code splitting for large modules
     */
    enableCodeSplitting() {
        // Dynamic imports for large features
        this.setupDynamicImports();
    }

    /**
     * Setup dynamic imports for features
     */
    setupDynamicImports() {
        // Chart.js - only load when needed
        window.loadCharts = async () => {
            if (!window.Chart) {
                const { Chart } = await import('https://cdn.jsdelivr.net/npm/chart.js');
                window.Chart = Chart;
                console.log('📊 Chart.js loaded dynamically');
            }
            return window.Chart;
        };

        // Search enhancements - load on first search
        window.loadSearchEnhancements = async () => {
            if (!window.SearchEnhanced) {
                const module = await import('/static/js/search-enhanced.js');
                window.SearchEnhanced = module.SearchEnhanced;
                console.log('🔍 Enhanced search loaded dynamically');
            }
            return window.SearchEnhanced;
        };
    }

    /**
     * Load polyfills conditionally based on browser support
     */
    loadPolyfillsConditionally() {
        const polyfillsNeeded = [];

        // Check for modern JS features
        if (!window.fetch) polyfillsNeeded.push('fetch');
        if (!window.IntersectionObserver) polyfillsNeeded.push('intersection-observer');
        if (!window.ResizeObserver) polyfillsNeeded.push('resize-observer');
        if (!Array.prototype.includes) polyfillsNeeded.push('array-includes');

        // Load polyfills if needed
        if (polyfillsNeeded.length > 0) {
            this.loadPolyfills(polyfillsNeeded);
        }
    }

    /**
     * Load required polyfills
     */
    loadPolyfills(polyfills) {
        const polyfillScript = document.createElement('script');
        polyfillScript.src = `https://polyfill.io/v3/polyfill.min.js?features=${polyfills.join(',')}`;
        polyfillScript.async = true;
        document.head.appendChild(polyfillScript);
        
        console.log('🔧 Polyfills loaded:', polyfills);
    }

    /**
     * Prevent main thread blocking
     */
    preventMainThreadBlocking() {
        // Use requestIdleCallback for non-critical work
        this.setupIdleTaskProcessing();
        
        // Break up long tasks
        this.setupTaskScheduling();
    }

    /**
     * Setup idle task processing
     */
    setupIdleTaskProcessing() {
        if ('requestIdleCallback' in window) {
            window.scheduleIdleWork = (callback) => {
                requestIdleCallback(callback, { timeout: 5000 });
            };
        } else {
            // Fallback for unsupported browsers
            window.scheduleIdleWork = (callback) => {
                setTimeout(callback, 0);
            };
        }
    }

    /**
     * Setup task scheduling to prevent blocking
     */
    setupTaskScheduling() {
        window.yieldToMain = () => {
            return new Promise(resolve => {
                setTimeout(resolve, 0);
            });
        };

        // Break up long loops
        window.processLargeArray = async (array, processor) => {
            const batchSize = 100;
            for (let i = 0; i < array.length; i += batchSize) {
                const batch = array.slice(i, i + batchSize);
                batch.forEach(processor);
                await window.yieldToMain();
            }
        };
    }

    /**
     * Performance Monitoring (T023)
     */
    setupPerformanceMonitoring() {
        this.measureWebVitals();
        this.setupPerformanceObserver();
        this.trackUserInteractions();
        this.setupPerformanceBudgets();
        this.setupResourceTiming();
        
        console.log('✅ Performance monitoring active');
    }

    /**
     * Measure Core Web Vitals
     */
    measureWebVitals() {
        // Largest Contentful Paint (LCP)
        this.measureLCP();
        
        // First Input Delay (FID)
        this.measureFID();
        
        // Cumulative Layout Shift (CLS)
        this.measureCLS();
        
        // Additional metrics
        this.measureTTFB();
        this.measureFCP();
    }

    /**
     * Measure Largest Contentful Paint
     */
    measureLCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const lastEntry = entries[entries.length - 1];
                
                this.webVitals.LCP = lastEntry.startTime;
                this.checkPerformanceBudget('LCP', lastEntry.startTime);
                
                console.log('📊 LCP:', lastEntry.startTime.toFixed(2) + 'ms');
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
        }
    }

    /**
     * Measure First Input Delay
     */
    measureFID() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const firstEntry = entries[0];
                
                this.webVitals.FID = firstEntry.processingStart - firstEntry.startTime;
                this.checkPerformanceBudget('FID', this.webVitals.FID);
                
                console.log('📊 FID:', this.webVitals.FID.toFixed(2) + 'ms');
            });
            
            observer.observe({ entryTypes: ['first-input'] });
        }
    }

    /**
     * Measure Cumulative Layout Shift
     */
    measureCLS() {
        if ('PerformanceObserver' in window) {
            let clsValue = 0;
            
            const observer = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                
                for (const entry of entries) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                }
                
                this.webVitals.CLS = clsValue;
                this.checkPerformanceBudget('CLS', clsValue);
                
                console.log('📊 CLS:', clsValue.toFixed(3));
            });
            
            observer.observe({ entryTypes: ['layout-shift'] });
        }
    }

    /**
     * Measure Time to First Byte
     */
    measureTTFB() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const navigationEntry = entries[0];
                
                if (navigationEntry) {
                    this.webVitals.TTFB = navigationEntry.responseStart - navigationEntry.requestStart;
                    console.log('📊 TTFB:', this.webVitals.TTFB.toFixed(2) + 'ms');
                }
            });
            
            observer.observe({ entryTypes: ['navigation'] });
        }
    }

    /**
     * Measure First Contentful Paint
     */
    measureFCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
                
                if (fcpEntry) {
                    this.webVitals.FCP = fcpEntry.startTime;
                    console.log('📊 FCP:', fcpEntry.startTime.toFixed(2) + 'ms');
                }
            });
            
            observer.observe({ entryTypes: ['paint'] });
        }
    }

    /**
     * Setup Performance Observer for additional monitoring
     */
    setupPerformanceObserver() {
        if ('PerformanceObserver' in window) {
            this.performanceObserver = new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                
                entries.forEach(entry => {
                    // Log long tasks
                    if (entry.entryType === 'longtask') {
                        console.warn('⚠️ Long task detected:', entry.duration.toFixed(2) + 'ms');
                    }
                    
                    // Monitor resource loading
                    if (entry.entryType === 'resource') {
                        this.analyzeResourceTiming(entry);
                    }
                });
            });
            
            // Observe different performance entry types
            try {
                this.performanceObserver.observe({ entryTypes: ['longtask', 'resource'] });
            } catch (e) {
                console.log('Some performance entry types not supported');
            }
        }
    }

    /**
     * Analyze resource loading performance
     */
    analyzeResourceTiming(entry) {
        const duration = entry.responseEnd - entry.requestStart;
        
        // Flag slow resources
        if (duration > 1000) {
            console.warn('🐌 Slow resource:', entry.name, duration.toFixed(2) + 'ms');
        }
        
        // Track resource sizes
        if (entry.transferSize > 100000) { // 100KB
            console.warn('📦 Large resource:', entry.name, (entry.transferSize / 1024).toFixed(2) + 'KB');
        }
    }

    /**
     * Track user interactions for performance
     */
    trackUserInteractions() {
        const interactionEvents = ['click', 'keydown', 'scroll'];
        
        interactionEvents.forEach(eventType => {
            document.addEventListener(eventType, this.measureInteractionPerformance.bind(this), {
                passive: true,
                capture: true
            });
        });
    }

    /**
     * Measure interaction to paint performance
     */
    measureInteractionPerformance(event) {
        const startTime = performance.now();
        
        requestAnimationFrame(() => {
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            // Log slow interactions
            if (duration > 16) { // > 1 frame at 60fps
                console.warn('🐌 Slow interaction:', event.type, duration.toFixed(2) + 'ms');
            }
        });
    }

    /**
     * Check performance against budgets
     */
    checkPerformanceBudget(metric, value) {
        const budget = this.performanceBudgets[metric];
        if (!budget) return;
        
        if (value > budget) {
            console.warn(`💰 Performance budget exceeded for ${metric}: ${value.toFixed(2)} > ${budget}`);
            this.reportPerformanceIssue(metric, value, budget);
        } else {
            console.log(`✅ Performance budget OK for ${metric}: ${value.toFixed(2)} <= ${budget}`);
        }
    }

    /**
     * Setup performance budgets monitoring
     */
    setupPerformanceBudgets() {
        // Set up alerts for budget violations
        this.budgetViolations = [];
        
        // Check budgets periodically
        setInterval(() => {
            this.auditPerformanceBudgets();
        }, 30000); // Every 30 seconds
    }

    /**
     * Audit all performance budgets
     */
    auditPerformanceBudgets() {
        Object.entries(this.webVitals).forEach(([metric, value]) => {
            if (value !== null) {
                this.checkPerformanceBudget(metric, value);
            }
        });
    }

    /**
     * Setup resource timing monitoring
     */
    setupResourceTiming() {
        // Monitor resource loading timing
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.analyzeResourceTimings();
            }, 1000);
        });
    }

    /**
     * Analyze all resource timings
     */
    analyzeResourceTimings() {
        const resources = performance.getEntriesByType('resource');
        
        const resourceStats = {
            css: { count: 0, totalSize: 0, totalTime: 0 },
            js: { count: 0, totalSize: 0, totalTime: 0 },
            images: { count: 0, totalSize: 0, totalTime: 0 },
            fonts: { count: 0, totalSize: 0, totalTime: 0 },
            other: { count: 0, totalSize: 0, totalTime: 0 }
        };
        
        resources.forEach(resource => {
            const category = this.categorizeResource(resource.name);
            const stats = resourceStats[category];
            
            stats.count++;
            stats.totalSize += resource.transferSize || 0;
            stats.totalTime += resource.duration || 0;
        });
        
        console.group('📈 Resource Performance Analysis');
        Object.entries(resourceStats).forEach(([category, stats]) => {
            if (stats.count > 0) {
                console.log(`${category.toUpperCase()}: ${stats.count} files, ${(stats.totalSize / 1024).toFixed(2)}KB, ${stats.totalTime.toFixed(2)}ms`);
            }
        });
        console.groupEnd();
    }

    /**
     * Categorize resource by file extension/type
     */
    categorizeResource(url) {
        if (url.includes('.css') || url.includes('font')) return 'css';
        if (url.includes('.js')) return 'js';
        if (url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) return 'images';
        if (url.match(/\.(woff|woff2|ttf|eot)$/i)) return 'fonts';
        return 'other';
    }

    /**
     * Setup resource hints for performance
     */
    setupResourceHints() {
        this.addDNSPrefetch();
        this.addPreconnectHints();
        this.addPreloadHints();
    }

    /**
     * Add DNS prefetch for external domains
     */
    addDNSPrefetch() {
        const domains = [
            '//cdn.jsdelivr.net',
            '//fonts.googleapis.com',
            '//fonts.gstatic.com'
        ];
        
        domains.forEach(domain => {
            if (!document.querySelector(`link[href="${domain}"]`)) {
                const link = document.createElement('link');
                link.rel = 'dns-prefetch';
                link.href = domain;
                document.head.appendChild(link);
            }
        });
    }

    /**
     * Add preconnect hints for critical external resources
     */
    addPreconnectHints() {
        const preconnects = [
            'https://cdn.jsdelivr.net',
            'https://fonts.googleapis.com'
        ];
        
        preconnects.forEach(url => {
            if (!document.querySelector(`link[href="${url}"]`)) {
                const link = document.createElement('link');
                link.rel = 'preconnect';
                link.href = url;
                link.crossOrigin = '';
                document.head.appendChild(link);
            }
        });
    }

    /**
     * Add preload hints for critical resources
     */
    addPreloadHints() {
        // Preload critical CSS that's already referenced in HTML
        const criticalCSS = document.querySelectorAll('link[rel="stylesheet"][href*="bootstrap"], link[rel="stylesheet"][href*="main"]');
        criticalCSS.forEach(css => {
            if (!document.querySelector(`link[rel="preload"][href="${css.href}"]`)) {
                const preloadLink = document.createElement('link');
                preloadLink.rel = 'preload';
                preloadLink.as = 'style';
                preloadLink.href = css.href;
                document.head.insertBefore(preloadLink, css);
            }
        });
    }

    /**
     * Setup lazy loading for images and content
     */
    setupLazyLoading() {
        // Use Intersection Observer for lazy loading
        if ('IntersectionObserver' in window) {
            this.setupImageLazyLoading();
            this.setupContentLazyLoading();
        }
    }

    /**
     * Setup lazy loading for images
     */
    setupImageLazyLoading() {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;
                    
                    if (src) {
                        img.src = src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });
        
        // Observe all images with data-src
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    /**
     * Setup lazy loading for content sections
     */
    setupContentLazyLoading() {
        const contentObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const loadFunction = element.dataset.lazyLoad;
                    
                    if (loadFunction && window[loadFunction]) {
                        window[loadFunction](element);
                        contentObserver.unobserve(element);
                    }
                }
            });
        });
        
        // Observe elements with lazy loading
        document.querySelectorAll('[data-lazy-load]').forEach(element => {
            contentObserver.observe(element);
        });
    }

    /**
     * Report performance issue
     */
    reportPerformanceIssue(metric, value, budget) {
        const issue = {
            metric,
            value,
            budget,
            timestamp: Date.now(),
            url: location.href,
            userAgent: navigator.userAgent
        };
        
        this.budgetViolations.push(issue);
        
        // In a real application, you would send this to analytics
        console.warn('📊 Performance issue reported:', issue);
    }

    /**
     * Get performance report
     */
    getPerformanceReport() {
        return {
            webVitals: this.webVitals,
            budgets: this.performanceBudgets,
            violations: this.budgetViolations,
            timestamp: Date.now()
        };
    }

    /**
     * Check if running in production environment
     */
    isProduction() {
        return location.hostname !== 'localhost' && location.hostname !== '127.0.0.1';
    }

    /**
     * Environment detection
     */
    isDevelopment() {
        return !this.isProduction();
    }
}

// ========================================
// AUTO-INITIALIZATION AND GLOBAL API
// ========================================

let performanceOptimizer;

function initializePerformanceOptimizer() {
    if (performanceOptimizer) return performanceOptimizer;
    
    performanceOptimizer = new PerformanceOptimizer();
    window.performanceOptimizer = performanceOptimizer;
    
    console.log('⚡ Performance Optimization System activated');
    return performanceOptimizer;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePerformanceOptimizer);
} else {
    initializePerformanceOptimizer();
}

// Global performance API
window.getPerformanceReport = function() {
    return performanceOptimizer ? performanceOptimizer.getPerformanceReport() : null;
};

window.checkPerformanceBudgets = function() {
    if (performanceOptimizer) {
        performanceOptimizer.auditPerformanceBudgets();
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PerformanceOptimizer };
}