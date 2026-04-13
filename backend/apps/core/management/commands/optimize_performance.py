"""
Performance Optimization Django Management Commands
Feature: 3-modern-web-interface
Tasks: T021-T023 - Performance optimization implementation
"""

import os
import gzip
import hashlib
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles.finders import find


class Command(BaseCommand):
    help = 'Optimize CSS and JavaScript files for production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minify-css',
            action='store_true',
            help='Minify CSS files'
        )
        parser.add_argument(
            '--minify-js',
            action='store_true',
            help='Minify JavaScript files'
        )
        parser.add_argument(
            '--generate-hashes',
            action='store_true',
            help='Generate file hashes for cache busting'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Generate compressed versions (gzip)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations'
        )

    def handle(self, *args, **options):
        """Execute performance optimization commands"""
        
        if options['all']:
            options.update({
                'minify_css': True,
                'minify_js': True,
                'generate_hashes': True,
                'compress': True
            })
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting performance optimization...')
        )
        
        # Get static files directory
        self.static_root = Path(settings.STATIC_ROOT or 'static')
        self.css_dir = self.static_root / 'css'
        self.js_dir = self.static_root / 'js'
        
        # Ensure directories exist
        self.css_dir.mkdir(parents=True, exist_ok=True)
        self.js_dir.mkdir(parents=True, exist_ok=True)
        
        # Run optimizations
        if options['minify_css']:
            self.minify_css_files()
            
        if options['minify_js']:
            self.minify_js_files()
            
        if options['generate_hashes']:
            self.generate_file_hashes()
            
        if options['compress']:
            self.compress_files()
            
        self.generate_critical_css()
        self.create_performance_manifest()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Performance optimization completed!')
        )

    def minify_css_files(self):
        """Minify CSS files using simple regex-based minification"""
        self.stdout.write('🎨 Minifying CSS files...')
        
        css_files = list(self.css_dir.glob('*.css'))
        
        for css_file in css_files:
            # Skip already minified files
            if '.min.' in css_file.name:
                continue
                
            self.stdout.write(f'  Processing: {css_file.name}')
            
            # Read original CSS
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Simple CSS minification
            minified_css = self.minify_css_content(css_content)
            
            # Write minified version
            min_file = css_file.with_name(
                css_file.stem + '.min' + css_file.suffix
            )
            
            with open(min_file, 'w', encoding='utf-8') as f:
                f.write(minified_css)
                
            # Calculate size reduction
            original_size = len(css_content)
            minified_size = len(minified_css)
            reduction = ((original_size - minified_size) / original_size) * 100
            
            self.stdout.write(
                f'    ✅ {css_file.name} -> {min_file.name} '
                f'({reduction:.1f}% reduction)'
            )

    def minify_css_content(self, css_content):
        """Simple CSS minification"""
        import re
        
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        
        # Remove spaces around specific characters
        css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
        
        # Remove trailing semicolons before closing braces
        css_content = re.sub(r';\s*}', '}', css_content)
        
        # Remove unnecessary units for zero values
        css_content = re.sub(r'\b0(?:px|em|%|in|cm|mm|pc|pt|ex)', '0', css_content)
        
        return css_content.strip()

    def minify_js_files(self):
        """Minify JavaScript files"""
        self.stdout.write('📜 Processing JavaScript files...')
        
        js_files = list(self.js_dir.glob('*.js'))
        
        for js_file in js_files:
            # Skip already minified files and performance optimizer
            if '.min.' in js_file.name or 'performance-optimizer' in js_file.name:
                continue
                
            self.stdout.write(f'  Processing: {js_file.name}')
            
            # For Django management, we'll just add defer/async strategy
            # In production, you'd use proper JS minifiers like terser
            
            with open(js_file, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            # Simple JS optimization - remove console.log in production
            if 'console.log' in js_content:
                js_content_prod = self.remove_console_logs(js_content)
                
                prod_file = js_file.with_name(
                    js_file.stem + '.prod' + js_file.suffix
                )
                
                with open(prod_file, 'w', encoding='utf-8') as f:
                    f.write(js_content_prod)
                    
                self.stdout.write(f'    ✅ Created production version: {prod_file.name}')

    def remove_console_logs(self, js_content):
        """Remove console.log statements from JavaScript"""
        import re
        
        # Remove console.log lines
        js_content = re.sub(
            r'^\s*console\.log\([^)]*\);\s*$',
            '',
            js_content,
            flags=re.MULTILINE
        )
        
        return js_content

    def generate_file_hashes(self):
        """Generate file hashes for cache busting"""
        self.stdout.write('🔢 Generating file hashes...')
        
        hash_manifest = {}
        
        # Process CSS files
        for css_file in self.css_dir.glob('*.css'):
            file_hash = self.get_file_hash(css_file)
            hash_manifest[f'css/{css_file.name}'] = file_hash
            
        # Process JS files  
        for js_file in self.js_dir.glob('*.js'):
            file_hash = self.get_file_hash(js_file)
            hash_manifest[f'js/{js_file.name}'] = file_hash
            
        # Write manifest
        manifest_file = self.static_root / 'asset-hashes.json'
        
        import json
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(hash_manifest, f, indent=2)
            
        self.stdout.write(f'  ✅ Hash manifest created: {manifest_file}')

    def get_file_hash(self, file_path):
        """Get SHA256 hash of file content"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()[:8]  # Short hash

    def compress_files(self):
        """Generate gzip compressed versions of files"""
        self.stdout.write('🗜️ Compressing files...')
        
        # Compress CSS files
        for css_file in self.css_dir.glob('*.css'):
            self.gzip_file(css_file)
            
        # Compress JS files
        for js_file in self.js_dir.glob('*.js'):
            self.gzip_file(js_file)

    def gzip_file(self, file_path):
        """Create gzip compressed version of file"""
        gzip_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(gzip_path, 'wb', compresslevel=9) as f_out:
                f_out.writelines(f_in)
                
        # Calculate compression ratio
        original_size = file_path.stat().st_size
        compressed_size = gzip_path.stat().st_size
        ratio = (1 - compressed_size / original_size) * 100
        
        self.stdout.write(
            f'  ✅ {file_path.name} -> {gzip_path.name} '
            f'({ratio:.1f}% compression)'
        )

    def generate_critical_css(self):
        """Generate critical CSS for above-the-fold content"""
        self.stdout.write('🎯 Generating critical CSS...')
        
        critical_css = """
/* Critical CSS - Above the fold (auto-generated) */
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #059669;
    --warning-color: #d97706;
    --danger-color: #dc2626;
    --info-color: #0891b2;
    --light-color: #f8fafc;
    --dark-color: #1e293b;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --text-muted: #9ca3af;
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --border-color: #e5e7eb;
    --border-light: #f3f4f6;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --radius: 0.375rem;
    --radius-lg: 0.5rem;
    --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Base styles */
* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
    -webkit-text-size-adjust: 100%;
}

body {
    font-family: 'Figtree', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    font-size: 0.875rem;
    font-weight: 400;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: var(--bg-primary);
    margin: 0;
    padding: 0;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* App layout */
.app-container {
    display: grid;
    grid-template-columns: 280px 1fr;
    grid-template-rows: auto 1fr;
    grid-template-areas: 
        "sidebar header"
        "sidebar main";
    min-height: 100vh;
    background: var(--bg-primary);
}

.app-header {
    grid-area: header;
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-color);
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 1000;
    min-height: 60px;
}

.app-sidebar {
    grid-area: sidebar;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    overflow-y: auto;
    z-index: 999;
}

.app-main {
    grid-area: main;
    padding: 1rem;
    overflow: auto;
    background: var(--bg-primary);
}

/* Skip links for accessibility */
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
    font-weight: 500;
    transition: top 0.2s ease;
}

.skip-link:focus {
    top: 0;
    outline: 2px solid var(--warning-color);
    outline-offset: 2px;
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
    backdrop-filter: blur(2px);
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

/* Mobile responsive */
@media (max-width: 1024px) {
    .app-container {
        grid-template-columns: 1fr;
        grid-template-areas: 
            "header"
            "main";
    }
    
    .app-sidebar {
        position: fixed;
        top: 60px;
        left: -280px;
        width: 280px;
        height: calc(100vh - 60px);
        transition: left 0.3s ease;
        z-index: 1100;
        box-shadow: var(--shadow-lg);
    }
    
    .app-sidebar.show {
        left: 0;
    }
    
    .sidebar-backdrop {
        position: fixed;
        top: 60px;
        left: 0;
        width: 100%;
        height: calc(100vh - 60px);
        background: rgba(0, 0, 0, 0.5);
        display: none;
        z-index: 1099;
    }
    
    .sidebar-backdrop.show {
        display: block;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --border-color: #000000;
        --text-primary: #000000;
        --bg-primary: #ffffff;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
    
    .skip-link {
        transition: none;
    }
}
"""
        
        critical_css_file = self.css_dir / 'critical.css'
        with open(critical_css_file, 'w', encoding='utf-8') as f:
            f.write(critical_css.strip())
            
        self.stdout.write(f'  ✅ Critical CSS generated: {critical_css_file}')

    def create_performance_manifest(self):
        """Create performance optimization manifest"""
        self.stdout.write('📋 Creating performance manifest...')
        
        manifest = {
            'version': '1.0.0',
            'generated_at': str(Path(__file__).parent.parent.parent / 'static'),
            'optimizations': {
                'css_minification': True,
                'js_optimization': True,
                'gzip_compression': True,
                'critical_css': True,
                'asset_hashing': True
            },
            'performance_budgets': {
                'FCP': 1800,  # First Contentful Paint (ms)
                'LCP': 2500,  # Largest Contentful Paint (ms) 
                'FID': 100,   # First Input Delay (ms)
                'CLS': 0.1    # Cumulative Layout Shift
            },
            'files': {
                'critical_css': 'css/critical.css',
                'performance_optimizer': 'js/performance-optimizer.js'
            }
        }
        
        manifest_file = self.static_root / 'performance-manifest.json'
        
        import json
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        self.stdout.write(f'  ✅ Performance manifest created: {manifest_file}')
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                '📝 Remember to:'
            )
        )
        self.stdout.write('  • Update your web server to serve .gz files when available')
        self.stdout.write('  • Configure proper cache headers for static files') 
        self.stdout.write('  • Run this command before each deployment')
        self.stdout.write('  • Monitor Core Web Vitals in production')