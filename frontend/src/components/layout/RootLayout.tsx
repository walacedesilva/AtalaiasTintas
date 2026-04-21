import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';
import Header from './Header';
import { Toaster } from 'react-hot-toast';
import { HelpProvider } from '@/providers/HelpProvider';
import { HelpDrawer } from '@/components/help/HelpDrawer';

const PREF_KEY = 'atalaia_ui_prefs';

function applyAccentColor(hex: string): void {
  const root = document.documentElement;
  const shades: [string, string][] = [
    ['--color-brand-50',  `color-mix(in srgb, ${hex}  8%, white)`],
    ['--color-brand-100', `color-mix(in srgb, ${hex} 15%, white)`],
    ['--color-brand-200', `color-mix(in srgb, ${hex} 25%, white)`],
    ['--color-brand-300', `color-mix(in srgb, ${hex} 40%, white)`],
    ['--color-brand-400', `color-mix(in srgb, ${hex} 60%, white)`],
    ['--color-brand-500', `color-mix(in srgb, ${hex} 80%, white)`],
    ['--color-brand-600', hex],
    ['--color-brand-700', `color-mix(in srgb, ${hex} 80%, black)`],
    ['--color-brand-800', `color-mix(in srgb, ${hex} 65%, black)`],
    ['--color-brand-900', `color-mix(in srgb, ${hex} 50%, black)`],
    ['--color-brand-950', `color-mix(in srgb, ${hex} 35%, black)`],
  ];
  shades.forEach(([prop, val]) => root.style.setProperty(prop, val));
}

function applyFontSize(size: string): void {
  document.documentElement.style.fontSize = ({ sm: '14px', md: '16px', lg: '18px' } as Record<string, string>)[size] ?? '16px';
}

export default function RootLayout(): React.ReactElement {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    try {
      const prefs = JSON.parse(localStorage.getItem(PREF_KEY) ?? '{}');
      if (prefs.accentColor) applyAccentColor(prefs.accentColor);
      if (prefs.fontSize)    applyFontSize(prefs.fontSize);
    } catch { /* ignore */ }
  }, []);

  return (
    <HelpProvider>
    <div className="min-h-screen bg-slate-50">
      {/* Skip links for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:rounded-lg focus:bg-teal-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:shadow-lg"
      >
        Pular para conteúdo principal
      </a>

      {/* Header */}
      <Header onMenuToggle={() => setSidebarOpen((v) => !v)} />

      <div className="flex pt-16">
        {/* Mobile backdrop overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Sidebar Navigation */}
        <Navigation isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main Content */}
        <main
          id="main-content"
          className="flex-1 lg:ml-64 min-h-[calc(100vh-4rem)] p-4 sm:p-6"
          role="main"
          aria-label="Conteúdo principal"
        >
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: '!rounded-xl !shadow-lg !text-sm !font-medium',
          success: {
            duration: 3000,
            iconTheme: { primary: '#0d9488', secondary: '#fff' },
          },
          error: { duration: 5000 },
        }}
        containerStyle={{ top: 72 }}
      />

      <HelpDrawer />
    </div>
    </HelpProvider>
  );
}